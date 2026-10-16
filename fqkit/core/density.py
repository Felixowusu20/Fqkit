"""Density-matrix simulation and Kraus noise channels.

Ideal ``run()`` keeps a pure state |ψ⟩. Real devices and open-system models
need a density matrix ρ (Hermitian, Tr ρ = 1, eigenvalues ≥ 0):

    gate:     ρ  ↦  U ρ U†
    noise:    ρ  ↦  Σ_i K_i ρ K_i†     (Kraus map)

Memory scales as 4^n (a 2^n × 2^n matrix). Use small n (typically ≤ 8–10).

Quick start
-----------
    from fqkit import QuantumCircuit, Hadamard, CNOT, run_density, Noise, purity

    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])

    rho = run_density(qc)                              # pure Bell as ρ
    noisy = run_density(qc, noise=Noise.depolarizing(0.05))
    print(purity(rho), purity(noisy))                  # 1.0  then < 1

Design notes
------------
* Local gates reuse the statevector tensor engine (no full Kronecker U).
* Noise uses proper Kraus operators — not ad-hoc bit flips on amplitudes.
* ``Noise`` factories stay short for researchers: ``Noise.depolarizing(p)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Union

import numpy as np

from fqkit.core.simulator import apply_gate, _gate_matrix

_I = np.array([[1, 0], [0, 1]], dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)


# ---------------------------------------------------------------------------
# Density matrix helpers
# ---------------------------------------------------------------------------

def _as_density(rho) -> np.ndarray:
    mat = np.asarray(rho, dtype=complex)
    if mat.ndim != 2 or mat.shape[0] != mat.shape[1]:
        raise ValueError(
            f"Density matrix must be square 2-D, got shape {mat.shape}."
        )
    dim = mat.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"Density matrix dimension must be a power of two, got {dim}."
        )
    return mat


def to_density(state) -> np.ndarray:
    """Pure state → density matrix: ρ = |ψ⟩⟨ψ|."""
    psi = np.asarray(state, dtype=complex).reshape(-1)
    dim = psi.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"State vector length must be a positive power of two, got {dim}."
        )
    # Outer product; copy-free path via reshape multiply is fine at this size.
    return np.outer(psi, psi.conj())


def trace(rho) -> float:
    """Tr(ρ). Physical states have Tr(ρ) = 1."""
    return float(np.real(np.trace(_as_density(rho))))


def purity(rho) -> float:
    """Tr(ρ²). Equals 1 for pure states; smaller for mixed states."""
    mat = _as_density(rho)
    return float(np.real(np.trace(mat @ mat)))


def entropy(rho, *, base=2) -> float:
    """
    Von Neumann entropy S(ρ) = −Tr(ρ log ρ).

    Uses ``base=2`` by default (qubits / bits). Pure states give S ≈ 0.
    """
    mat = _as_density(rho)
    eig = np.clip(np.linalg.eigvalsh(mat).real, 0.0, None)
    # 0 log 0 → 0
    positive = eig[eig > 1e-15]
    if positive.size == 0:
        return 0.0
    log = np.log(positive) if base is None else np.log(positive) / np.log(base)
    return float(-np.sum(positive * log))


def is_physical(rho, *, atol=1e-8) -> bool:
    """
    True if ρ looks like a physical state:

    * Hermitian (ρ ≈ ρ†)
    * Trace ≈ 1
    * Positive semidefinite (eigenvalues ≥ −atol)
    """
    mat = _as_density(rho)
    if not np.allclose(mat, mat.conj().T, atol=atol):
        return False
    if abs(np.trace(mat) - 1.0) > atol:
        return False
    eig = np.linalg.eigvalsh(mat).real
    return bool(np.min(eig) >= -atol)


def _left_apply(
    rho: np.ndarray, gate: np.ndarray, n: int, targets, *, check_unitary=True
) -> np.ndarray:
    """Apply a local matrix to the ket index: ρ ↦ M ρ."""
    dim = rho.shape[0]
    out = np.empty_like(rho)
    for j in range(dim):
        out[:, j] = apply_gate(
            rho[:, j], gate, n, targets, check_unitary=check_unitary
        )
    return out


def apply_unitary(rho, gate_matrix, num_qubits, target_qubits) -> np.ndarray:
    """
    Apply a unitary channel: ρ ↦ U ρ U†.

    Uses the local tensor engine twice (ket then bra) — O(2^n) work per
    column, no dense Kronecker product of the full n-qubit U.
    """
    mat = _as_density(rho)
    u = np.asarray(gate_matrix, dtype=complex)
    tmp = _left_apply(mat, u, num_qubits, target_qubits, check_unitary=True)
    # (U ρ) U†  ==  left(U*, (U ρ)^T )^T
    return _left_apply(
        tmp.T, u.conj(), num_qubits, target_qubits, check_unitary=True
    ).T


def apply_kraus(rho, kraus_ops, num_qubits, target_qubits) -> np.ndarray:
    """
    Apply a Kraus channel on the target qubits: ρ ↦ Σ_i K_i ρ K_i†.
    """
    mat = _as_density(rho)
    acc = np.zeros_like(mat)
    for kraus in kraus_ops:
        k = np.asarray(kraus, dtype=complex)
        # K ρ K† — same pattern as unitary; Kraus ops are not unitary.
        tmp = _left_apply(mat, k, num_qubits, target_qubits, check_unitary=False)
        acc += _left_apply(
            tmp.T, k.conj(), num_qubits, target_qubits, check_unitary=False
        ).T
    return acc


# ---------------------------------------------------------------------------
# Noise model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Noise:
    """
    A single-qubit noise channel applied to chosen qubits.

    Create with factories (recommended)::

        Noise.bit_flip(0.1)
        Noise.phase_flip(0.1)
        Noise.depolarizing(0.05)
        Noise.amplitude_damping(0.08)

    Parameters
    ----------
    kind : str
        Channel name.
    p : float
        Strength parameter in ``[0, 1]`` (see each factory).
    qubits : tuple[int, ...] or None
        Qubits to apply to. ``None`` means every qubit in the register.
    """

    kind: str
    p: float
    qubits: Optional[tuple] = None

    def __post_init__(self):
        if not 0.0 <= float(self.p) <= 1.0:
            raise ValueError(f"Noise strength must be in [0, 1], got {self.p}.")

    # --- factories --------------------------------------------------------

    @staticmethod
    def bit_flip(p: float, qubits=None) -> "Noise":
        """X errors with probability ``p``."""
        return Noise("bit_flip", float(p), _qubits_tuple(qubits))

    @staticmethod
    def phase_flip(p: float, qubits=None) -> "Noise":
        """Z errors with probability ``p``."""
        return Noise("phase_flip", float(p), _qubits_tuple(qubits))

    @staticmethod
    def depolarizing(p: float, qubits=None) -> "Noise":
        """
        Single-qubit depolarizing channel with error probability ``p``.

        Kraus form (standard textbook parametrization)::

            K0 = √(1 − 3p/4) I
            K1 = √(p/4) X ,  K2 = √(p/4) Y ,  K3 = √(p/4) Z
        """
        return Noise("depolarizing", float(p), _qubits_tuple(qubits))

    @staticmethod
    def amplitude_damping(gamma: float, qubits=None) -> "Noise":
        """
        Energy relaxation |1⟩ → |0⟩ with probability ``gamma``.

        This is the unique open-system channel among the basic set — useful
        for T1-style teaching and research demos.
        """
        return Noise("amplitude_damping", float(gamma), _qubits_tuple(qubits))

    # --- Kraus operators --------------------------------------------------

    def kraus(self) -> list:
        """Return the 2×2 Kraus operators for this channel."""
        p = self.p
        if self.kind == "bit_flip":
            return [np.sqrt(1 - p) * _I, np.sqrt(p) * _X]
        if self.kind == "phase_flip":
            return [np.sqrt(1 - p) * _I, np.sqrt(p) * _Z]
        if self.kind == "depolarizing":
            return [
                np.sqrt(max(1 - 3 * p / 4, 0.0)) * _I,
                np.sqrt(p / 4) * _X,
                np.sqrt(p / 4) * _Y,
                np.sqrt(p / 4) * _Z,
            ]
        if self.kind == "amplitude_damping":
            k0 = np.array([[1, 0], [0, np.sqrt(1 - p)]], dtype=complex)
            k1 = np.array([[0, np.sqrt(p)], [0, 0]], dtype=complex)
            return [k0, k1]
        raise ValueError(f"Unknown noise kind {self.kind!r}.")

    def apply(self, rho, num_qubits: Optional[int] = None):
        """Apply this channel to ``rho`` and return a new density matrix."""
        mat = _as_density(rho)
        n = num_qubits if num_qubits is not None else int(np.log2(mat.shape[0]))
        if 2 ** n != mat.shape[0]:
            raise ValueError("num_qubits does not match density matrix size.")

        targets = self.qubits if self.qubits is not None else tuple(range(n))
        ops = self.kraus()
        out = mat
        for q in targets:
            if q < 0 or q >= n:
                raise ValueError(f"Noise qubit index {q} out of range for n={n}.")
            out = apply_kraus(out, ops, n, [q])
        return out

    def __repr__(self) -> str:
        q = f", qubits={list(self.qubits)}" if self.qubits is not None else ""
        return f"Noise.{self.kind}({self.p}{q})"


def _qubits_tuple(qubits) -> Optional[tuple]:
    if qubits is None:
        return None
    if isinstance(qubits, (int, np.integer)):
        return (int(qubits),)
    return tuple(int(q) for q in qubits)


# ---------------------------------------------------------------------------
# Circuit evolution
# ---------------------------------------------------------------------------

def run_density(
    circuit,
    state=None,
    noise: Union[Noise, Sequence[Noise], None] = None,
    *,
    noise_every_gate: bool = False,
):
    """
    Simulate a circuit in the density-matrix picture.

    Parameters
    ----------
    circuit : QuantumCircuit
        Gates applied in order as ρ ↦ U ρ U†.
    state : array-like, optional
        Initial statevector or density matrix. Default: pure ``|0...0⟩``.
    noise : Noise or sequence of Noise, optional
        Kraus channels. By default applied **once at the end**. Set
        ``noise_every_gate=True`` to apply after every gate (stronger model).
    noise_every_gate : bool
        If True, apply ``noise`` after each gate; else only after the circuit.

    Returns
    -------
    ndarray
        Density matrix of shape ``(2**n, 2**n)``.
    """
    n = circuit.num_qubits
    dim = 2 ** n

    if state is None:
        rho = np.zeros((dim, dim), dtype=complex)
        rho[0, 0] = 1.0
    else:
        arr = np.asarray(state, dtype=complex)
        if arr.ndim == 1:
            rho = to_density(arr)
        else:
            rho = _as_density(arr).copy()
        if rho.shape[0] != dim:
            raise ValueError(
                f"Initial state size {rho.shape} does not match n={n}."
            )

    channels = _normalize_noise(noise)

    for op in circuit.operations:
        u = _gate_matrix(op.gate)
        rho = apply_unitary(rho, u, n, op.qubits)
        if noise_every_gate:
            for ch in channels:
                rho = ch.apply(rho, n)

    if not noise_every_gate:
        for ch in channels:
            rho = ch.apply(rho, n)

    return rho


def _normalize_noise(noise) -> list:
    if noise is None:
        return []
    if isinstance(noise, Noise):
        return [noise]
    return list(noise)
