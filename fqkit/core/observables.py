"""Pauli observables and expectation values.

Researchers usually need a number, not a histogram:

    ⟨O⟩ = ⟨ψ| O |ψ⟩

In near-term algorithms (VQE, QAOA, …) O is a Pauli string or a weighted sum
of Pauli strings (a Hamiltonian).

Quick start
-----------
    from fqkit import QuantumCircuit, Hadamard, CNOT, run, pauli, expectation

    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    state = run(qc)

    print(expectation(state, pauli("ZZ")))   # +1
    print(expectation(state, "XX"))          # +1  (string form also works)
    print(expectation(state, pauli("YY")))   # -1

Hamiltonians (sums of Paulis)
-----------------------------
    from fqkit import Hamiltonian

    H = Hamiltonian(("ZZ", 0.5), ("XX", 0.25))
    energy = expectation(state, H)

Convention
----------
Labels are big-endian like the rest of FQkit: the **leftmost** letter acts on
qubit 0. So ``"ZI"`` is Z on qubit 0 and I on qubit 1.

Performance
-----------
Expectation values are computed by applying the Pauli string to |ψ⟩ with the
existing tensor engine, then taking ⟨ψ|φ⟩. Cost is O(k · 2^n) for k non-identity
letters — not O(4^n) from building a full dense matrix.
"""

from __future__ import annotations

from typing import Iterable, Union

import numpy as np

from fqkit.core.simulator import apply_gate

# 2x2 Pauli matrices (same physics as the gate library).
_I = np.array([[1, 0], [0, 1]], dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)

_PAULI = {"I": _I, "X": _X, "Y": _Y, "Z": _Z}
_LETTERS = frozenset(_PAULI)


def _clean_label(label: str) -> str:
    text = "".join(str(label).split()).upper()
    if not text:
        raise ValueError("Pauli label cannot be empty.")
    bad = set(text) - _LETTERS
    if bad:
        raise ValueError(
            f"Invalid Pauli letter(s) {sorted(bad)} in {label!r}. "
            "Use only I, X, Y, Z."
        )
    return text


def _as_state(state) -> np.ndarray:
    vec = np.asarray(state, dtype=complex).reshape(-1)
    dim = vec.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"State vector length must be a positive power of two, got {dim}."
        )
    return vec


class Pauli:
    """A Pauli string such as ``\"ZZ\"`` or ``\"IXY\"``.

    Create with :func:`pauli`::

        zz = pauli("ZZ")
        x0 = pauli("XI")      # X on qubit 0, I on qubit 1
    """

    __slots__ = ("label",)

    def __init__(self, label: str):
        self.label = _clean_label(label)

    @property
    def n(self) -> int:
        """Number of qubits this operator acts on."""
        return len(self.label)

    def __repr__(self) -> str:
        return f'pauli("{self.label}")'

    def __str__(self) -> str:
        return self.label

    def __eq__(self, other) -> bool:
        return isinstance(other, Pauli) and self.label == other.label

    def __hash__(self) -> int:
        return hash(("Pauli", self.label))

    def __matmul__(self, other: "Pauli") -> "Pauli":
        """Tensor product: ``pauli("Z") @ pauli("Z")`` → ``pauli("ZZ")``."""
        if not isinstance(other, Pauli):
            return NotImplemented
        return Pauli(self.label + other.label)

    def __mul__(self, coeff) -> "Hamiltonian":
        if isinstance(coeff, (int, float, complex, np.number)):
            return Hamiltonian((self, complex(coeff)))
        return NotImplemented

    def __rmul__(self, coeff) -> "Hamiltonian":
        return self.__mul__(coeff)

    def __add__(self, other) -> "Hamiltonian":
        return Hamiltonian((self, 1.0)) + other

    def __radd__(self, other) -> "Hamiltonian":
        if other == 0:  # sum() identity
            return Hamiltonian((self, 1.0))
        return self.__add__(other)

    def __neg__(self) -> "Hamiltonian":
        return Hamiltonian((self, -1.0))

    def __sub__(self, other) -> "Hamiltonian":
        return self + (-other)


class Hamiltonian:
    """Weighted sum of Pauli strings: H = Σ c_i P_i.

    Examples
    --------
        H = Hamiltonian(("ZZ", 0.5), ("XX", 0.25))
        H = 0.5 * pauli("ZZ") + 0.25 * pauli("XX")
    """

    __slots__ = ("terms",)

    def __init__(self, *terms):
        """
        Parameters
        ----------
        terms
            Either ``(label_or_pauli, coeff)`` pairs, or a single iterable of
            those pairs.
        """
        if len(terms) == 1 and _is_term_list(terms[0]):
            raw = list(terms[0])
        else:
            raw = list(terms)

        merged: dict[str, complex] = {}
        for item in raw:
            label, coeff = _split_term(item)
            merged[label] = merged.get(label, 0.0) + complex(coeff)

        self.terms = tuple(
            (Pauli(label), coeff)
            for label, coeff in merged.items()
            if abs(coeff) > 0.0
        )
        if not self.terms:
            raise ValueError("Hamiltonian must contain at least one Pauli term.")

        lengths = {p.n for p, _ in self.terms}
        if len(lengths) != 1:
            raise ValueError(
                f"All Pauli terms must act on the same number of qubits, got {lengths}."
            )

    @property
    def n(self) -> int:
        return self.terms[0][0].n

    def __repr__(self) -> str:
        parts = [f'("{p.label}", {c})' for p, c in self.terms]
        return "Hamiltonian(" + ", ".join(parts) + ")"

    def __add__(self, other) -> "Hamiltonian":
        other_h = _as_hamiltonian(other)
        return Hamiltonian(*(self.terms + other_h.terms))

    def __radd__(self, other) -> "Hamiltonian":
        if other == 0:
            return self
        return self.__add__(other)

    def __mul__(self, coeff) -> "Hamiltonian":
        if not isinstance(coeff, (int, float, complex, np.number)):
            return NotImplemented
        scale = complex(coeff)
        return Hamiltonian(*((p, c * scale) for p, c in self.terms))

    def __rmul__(self, coeff) -> "Hamiltonian":
        return self.__mul__(coeff)

    def __neg__(self) -> "Hamiltonian":
        return self * -1

    def __sub__(self, other) -> "Hamiltonian":
        return self + (-_as_hamiltonian(other))


def pauli(label: str) -> Pauli:
    """Build a Pauli string. Example: ``pauli("ZZ")``, ``pauli("IXY")``."""
    return Pauli(label)


def expectation(state, observable) -> float:
    """
    Exact expectation value of a Pauli or Hamiltonian.

    * Pure state ``|ψ⟩`` → ``⟨ψ|O|ψ⟩``
    * Density matrix ``ρ`` → ``Tr(ρ O)``

    Parameters
    ----------
    state
        Statevector from ``run`` or density matrix from ``run_density``.
    observable
        ``pauli("ZZ")``, a label string ``"ZZ"``, or a :class:`Hamiltonian`.

    Returns
    -------
    float
        Real part of the expectation (Hermitian observables).
    """
    arr = np.asarray(state, dtype=complex)
    obs = _as_observable(observable)

    if arr.ndim == 2:
        n = int(np.log2(arr.shape[0]))
        if obs.n != n:
            raise ValueError(
                f"Observable acts on {obs.n} qubit(s) but state has {n} qubit(s)."
            )
        if isinstance(obs, Pauli):
            return float(np.real(_pauli_expectation_density(arr, obs)))
        total = 0.0j
        for p, coeff in obs.terms:
            total += coeff * _pauli_expectation_density(arr, p)
        return float(np.real(total))

    psi = _as_state(arr)
    n = int(np.log2(psi.shape[0]))
    if obs.n != n:
        raise ValueError(
            f"Observable acts on {obs.n} qubit(s) but state has {n} qubit(s)."
        )

    if isinstance(obs, Pauli):
        return float(np.real(_pauli_expectation(psi, obs)))

    total = 0.0j
    for p, coeff in obs.terms:
        total += coeff * _pauli_expectation(psi, p)
    return float(np.real(total))


def _pauli_expectation(psi: np.ndarray, p: Pauli) -> complex:
    """⟨ψ|P|ψ⟩ by applying P to |ψ⟩ then taking the inner product."""
    phi = psi
    n = p.n
    for q, letter in enumerate(p.label):
        if letter == "I":
            continue
        if phi is psi:
            phi = apply_gate(psi, _PAULI[letter], n, [q])
        else:
            phi = apply_gate(phi, _PAULI[letter], n, [q])

    if phi is psi:
        return np.vdot(psi, psi)
    return np.vdot(psi, phi)


def _pauli_expectation_density(rho: np.ndarray, p: Pauli) -> complex:
    """Tr(ρ P) via left-action of the Pauli string, then trace."""
    from fqkit.core.density import _left_apply, _as_density

    mat = _as_density(rho)
    n = p.n
    out = mat
    touched = False
    for q, letter in enumerate(p.label):
        if letter == "I":
            continue
        out = _left_apply(out, _PAULI[letter], n, [q])
        touched = True
    if not touched:
        return np.trace(mat)
    return np.trace(out)


def _is_term_list(value) -> bool:
    """True if ``value`` is a sequence of terms, not a single (label, coeff) pair."""
    if isinstance(value, (str, bytes, Pauli, Hamiltonian)):
        return False
    if not isinstance(value, (list, tuple)):
        # e.g. generator of terms
        return isinstance(value, Iterable)
    if not value:
        return False
    # Single term pair: ("Z", 1.0) or (Pauli, coeff)
    if len(value) == 2 and isinstance(value[1], (int, float, complex, np.number)):
        first = value[0]
        if isinstance(first, (str, Pauli)):
            return False
        if isinstance(first, (list, tuple)):
            return True  # list of pairs starts with a pair
    return _looks_like_term(value[0])


def _looks_like_term(item) -> bool:
    if isinstance(item, (Pauli, Hamiltonian)):
        return True
    if isinstance(item, (tuple, list)) and len(item) == 2:
        return True
    return False


def _split_term(item):
    if isinstance(item, Pauli):
        return item.label, 1.0
    if isinstance(item, (tuple, list)) and len(item) == 2:
        op, coeff = item
        if isinstance(op, Pauli):
            return op.label, complex(coeff)
        return _clean_label(op), complex(coeff)
    raise TypeError(
        f"Hamiltonian term must be (label, coeff) or Pauli, got {item!r}."
    )


def _as_hamiltonian(value) -> Hamiltonian:
    if isinstance(value, Hamiltonian):
        return value
    if isinstance(value, Pauli):
        return Hamiltonian((value, 1.0))
    if isinstance(value, str):
        return Hamiltonian((value, 1.0))
    raise TypeError(f"Cannot convert {type(value).__name__} to Hamiltonian.")


def _as_observable(value) -> Union[Pauli, Hamiltonian]:
    if isinstance(value, (Pauli, Hamiltonian)):
        return value
    if isinstance(value, str):
        return Pauli(value)
    raise TypeError(
        "observable must be a Pauli, Hamiltonian, or label string "
        f"like 'ZZ', got {type(value).__name__}."
    )
