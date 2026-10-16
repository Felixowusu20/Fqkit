"""Circuit and state equivalence checks.

Two pure states represent the same physics if they differ by at most a
global phase:

    |ψ⟩ ~ |φ⟩  ⇔  |⟨ψ|φ⟩| = 1
                 (when both are normalized)

Two circuits implement the same unitary (up to global phase) if that holds
for **every** computational-basis input, with one shared phase. Checking only
``|0...0>`` is not enough for science: many different unitaries agree there.

Quick start
-----------
    from fqkit import QuantumCircuit, Hadamard, Identity, circuits_equivalent

    a = QuantumCircuit(1)
    a.add_gate(Hadamard(), [0])
    a.add_gate(Hadamard(), [0])

    b = QuantumCircuit(1)
    b.add_gate(Identity(), [0])

    assert circuits_equivalent(a, b)   # H·H ≡ I
"""

from __future__ import annotations

import numpy as np

from fqkit.core.simulator import run

# Default absolute tolerance for amplitude / overlap checks.
_ATOL = 1e-10


def _as_state(state) -> np.ndarray:
    vec = np.asarray(state, dtype=complex).reshape(-1)
    dim = vec.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"State vector length must be a positive power of two, got {dim}."
        )
    return vec


def _basis_state(index: int, n: int) -> np.ndarray:
    """Computational basis vector |index⟩ (big-endian bitstring)."""
    dim = 2 ** n
    if index < 0 or index >= dim:
        raise ValueError(f"Basis index must be in [0, {dim}), got {index}.")
    ket = np.zeros(dim, dtype=complex)
    ket[index] = 1.0
    return ket


def fidelity(state_a, state_b) -> float:
    """
    Pure-state fidelity F = |⟨a|b⟩|² ∈ [0, 1].

    F = 1 means the states are identical up to a global phase (if normalized).
    """
    a = _as_state(state_a)
    b = _as_state(state_b)
    if a.shape != b.shape:
        raise ValueError(
            f"State lengths differ: {a.shape[0]} vs {b.shape[0]}."
        )
    overlap = np.vdot(a, b)
    return float(np.abs(overlap) ** 2)


def states_equivalent(state_a, state_b, *, phase=True, atol=_ATOL) -> bool:
    """
    Return True if two statevectors describe the same pure state.

    Parameters
    ----------
    phase : bool
        If True (default), allow a global phase: require |⟨a|b⟩| ≈ 1 after
        normalizing. If False, require ``a ≈ b`` componentwise.
    atol : float
        Absolute tolerance.
    """
    a = _as_state(state_a)
    b = _as_state(state_b)
    if a.shape != b.shape:
        raise ValueError(
            f"State lengths differ: {a.shape[0]} vs {b.shape[0]}."
        )

    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < atol or nb < atol:
        return bool(na < atol and nb < atol)

    if not phase:
        return bool(np.allclose(a, b, atol=atol))

    # Normalized overlap magnitude ~ 1.
    overlap = np.vdot(a, b) / (na * nb)
    return bool(abs(abs(overlap) - 1.0) <= atol)


def circuits_equivalent(
    circuit_a,
    circuit_b,
    *,
    phase=True,
    atol=_ATOL,
) -> bool:
    """
    Return True if two circuits implement the same unitary (up to global phase).

    Method
    ------
    For every computational basis input ``|x⟩``, ``x = 0 … 2^n − 1``, run both
    circuits and compare outputs:

    * ``phase=False`` — outputs must match exactly (``allclose``).
    * ``phase=True``  — there must exist one phase ``e^{iθ}`` such that
      ``U|x⟩ = e^{iθ} V|x⟩`` for all ``x`` (standard physical equivalence of
      unitaries).

    This is stronger than comparing only the ``|0...0>`` evolution.
    """
    if circuit_a.num_qubits != circuit_b.num_qubits:
        raise ValueError(
            "Circuits must have the same number of qubits "
            f"({circuit_a.num_qubits} vs {circuit_b.num_qubits})."
        )

    n = circuit_a.num_qubits
    dim = 2 ** n

    if not phase:
        for index in range(dim):
            ket = _basis_state(index, n)
            out_a = run(circuit_a, ket)
            out_b = run(circuit_b, ket)
            if not np.allclose(out_a, out_b, atol=atol):
                return False
        return True

    # Collect ⟨V x | U x⟩ for each basis input x.
    overlaps = np.empty(dim, dtype=complex)
    for index in range(dim):
        ket = _basis_state(index, n)
        out_a = run(circuit_a, ket)
        out_b = run(circuit_b, ket)
        na = np.linalg.norm(out_a)
        nb = np.linalg.norm(out_b)
        if abs(na - 1.0) > 1e-8 or abs(nb - 1.0) > 1e-8:
            # Unitaries must preserve norm; fail loudly for broken engines.
            if abs(na) < atol or abs(nb) < atol:
                return False
        overlaps[index] = np.vdot(out_b, out_a)

    # All overlaps must equal the same unimodular complex number e^{iθ}.
    ref = overlaps[0]
    if abs(abs(ref) - 1.0) > atol:
        return False
    return bool(np.allclose(overlaps, ref, atol=atol))
