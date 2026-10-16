"""Shot-based measurement of a statevector.

Quantum measurement (Z basis, all qubits)
-----------------------------------------
A pure state on n qubits is a vector of 2^n complex amplitudes:

    |ψ⟩ = Σ_b a_b |b⟩

The Born rule says the probability of bitstring b is

    P(b) = |a_b|²

with Σ_b P(b) = 1. Each *shot* draws one bitstring from that distribution.
Repeating many shots builds a histogram (counts).

FQkit convention
----------------
Big-endian labels: qubit 0 is the **leftmost** bit of the bitstring, matching
``run()`` and ``measure_all`` on hardware job helpers.

What this module adds (vs a bare counts dict)
---------------------------------------------
* **Seeded RNG** — ``seed=`` makes experiments replayable (papers, CI, debugging).
* **MeasurementResult** — counts + ideal/empirical probabilities + diagnostics.
* **Dict-compatible** — ``result["00"]``, ``dict(result)``, and ``plot(result)``
  still work with older tutorial code.
* **Total variation distance** — how far the histogram is from the ideal Born
  distribution (useful when comparing simulator shots to theory or hardware).

Example
-------
    from fqkit import QuantumCircuit, Hadamard, CNOT, run, measure_all

    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    print(probabilities(run(qc)))          # ideal P table
    print(measure_all(run(qc), shots=1024, seed=7))  # counts table
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional

import numpy as np

# If | ‖ψ‖² − 1 | is below this, treat the drift as floating-point noise and
# renormalize before sampling. Larger errors are rejected.
_NORM_ATOL = 1e-8


def _box_table(headers, rows) -> str:
    """Render a readable terminal table (not JSON)."""
    cells = [[str(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in cells:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(parts):
        return "| " + " | ".join(parts[i].ljust(widths[i]) for i in range(len(parts))) + " |"

    rule = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    mid = "+=" + "=+=".join("=" * w for w in widths) + "=+"
    lines = [rule, fmt(list(headers)), mid]
    for row in cells:
        lines.append(fmt(row))
    lines.append(rule)
    return "\n".join(lines)


def _bar(fraction: float, width: int = 16) -> str:
    """Simple ASCII probability bar."""
    fraction = max(0.0, min(1.0, float(fraction)))
    filled = int(round(fraction * width))
    return "█" * filled + "░" * (width - filled)


@dataclass(frozen=True)
class ProbabilityTable(Mapping):
    """
    Ideal outcome probabilities with a clean table display.

    Still dict-like::

        probs["00"]
        dict(probs)

    Printing shows a table, not a JSON-like blob::

        print(probabilities(state))
    """

    data: dict
    num_qubits: int

    def __getitem__(self, bitstring: str) -> float:
        return self.data[bitstring]

    def __iter__(self):
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def table(self, *, min_prob: float = 0.0) -> str:
        """Return the formatted table (optionally hide tiny probabilities)."""
        rows = []
        for bitstring in sorted(self.data):
            p = self.data[bitstring]
            if p < min_prob:
                continue
            rows.append(
                [
                    bitstring,
                    f"{p:.6f}",
                    f"{100.0 * p:6.2f}%",
                    _bar(p),
                ]
            )
        if not rows:
            rows.append(["—", "0.000000", "  0.00%", _bar(0.0)])
        body = _box_table(
            ["outcome", "probability", "percent", "distribution"],
            rows,
        )
        return (
            f"Ideal probabilities  (n={self.num_qubits} qubits, Born rule)\n"
            f"{body}\n"
            f"sum(P) = {sum(self.data.values()):.6f}"
        )

    def __str__(self) -> str:
        # Hide exact zeros on larger registers so the table stays readable.
        min_prob = 0.0 if self.num_qubits <= 3 else 1e-12
        return self.table(min_prob=min_prob)

    def __repr__(self) -> str:
        return f"ProbabilityTable({self.data!r})"


def _as_statevector(state_vector) -> np.ndarray:
    state = np.asarray(state_vector, dtype=complex).reshape(-1)
    dim = state.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"State vector length must be a positive power of two, got {dim}."
        )
    return state


def _born_probabilities(state: np.ndarray, *, atol: float = _NORM_ATOL):
    """
    Convert amplitudes to a valid probability vector.

    Returns
    -------
    probabilities : ndarray of float64, shape (2**n,)
    state_norm : float
        ‖ψ‖ before any renormalization.
    renormalized : bool
        True if we rescaled probabilities because ‖ψ‖² was not exactly 1.
    """
    weights = np.abs(state) ** 2
    total = float(np.real(weights.sum()))
    state_norm = float(np.sqrt(max(total, 0.0)))

    if total <= 0.0:
        raise ValueError("State vector has zero norm; cannot sample measurements.")

    deviation = abs(total - 1.0)
    # Clearly broken states (not float dust) are rejected.
    if deviation > max(atol * 1e4, 1e-4):
        raise ValueError(
            f"State vector is not normalized: ‖ψ‖² = {total:.6e} "
            f"(expected 1 ± {atol})."
        )

    # Always sample from a distribution that sums to 1 (stable RNG input).
    probabilities = (weights.real / total).astype(np.float64, copy=False)
    # Flag only meaningful drift, not ~1e-16 roundoff on a valid state.
    renormalized = deviation > atol
    return probabilities, state_norm, renormalized


def _density_probabilities(rho: np.ndarray, *, atol: float = _NORM_ATOL):
    """Born readout from a density matrix: P(b) = ρ_{bb}."""
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError(f"Density matrix must be square, got shape {rho.shape}.")
    dim = rho.shape[0]
    if dim == 0 or (dim & (dim - 1)) != 0:
        raise ValueError(
            f"Density matrix dimension must be a power of two, got {dim}."
        )

    probs = np.real(np.diag(rho)).astype(np.float64, copy=False)
    total = float(probs.sum())
    if total <= 0.0:
        raise ValueError("Density matrix has non-positive diagonal; cannot sample.")

    deviation = abs(total - 1.0)
    if deviation > max(atol * 1e4, 1e-4):
        raise ValueError(
            f"Density matrix diagonal does not sum to 1 (sum={total:.6e})."
        )

    probabilities = probs / total
    renormalized = deviation > atol
    # For density inputs, state_norm stores Tr(ρ) (physical scale check).
    state_norm = float(np.real(np.trace(rho)))
    return probabilities, state_norm, renormalized


def _outcome_probabilities(state_or_rho, *, atol: float = _NORM_ATOL):
    """Accept a statevector or a density matrix."""
    arr = np.asarray(state_or_rho, dtype=complex)
    if arr.ndim == 2:
        return _density_probabilities(arr, atol=atol)
    return _born_probabilities(_as_statevector(arr), atol=atol)


def probabilities(state_or_rho) -> ProbabilityTable:
    """
    Ideal outcome probabilities with **no** sampling.

    * Statevector ``|ψ⟩`` → ``P(b) = |a_b|²``
    * Density matrix ``ρ`` → ``P(b) = ρ_{bb}``

    Returns a :class:`ProbabilityTable` (dict-like). ``print`` shows a table::

        from fqkit import run, probabilities
        print(probabilities(run(qc)))
    """
    probs, _, _ = _outcome_probabilities(state_or_rho)
    n = int(np.log2(len(probs)))
    data = {format(i, f"0{n}b"): float(probs[i]) for i in range(len(probs))}
    return ProbabilityTable(data=data, num_qubits=n)


@dataclass(frozen=True)
class MeasurementResult(Mapping):
    """
    Record of a Z-basis measurement experiment.

    Acts like a ``dict`` of counts for backward compatibility::

        result["00"]           # count for bitstring 00
        dict(result)           # plain counts dict
        sum(result.values())   # == shots

    Scientific fields
    -----------------
    ideal_probabilities
        Born-rule (or diagonal) probabilities for the measured wires.
    empirical_probabilities
        counts[b] / shots.
    measured_qubits
        Which wires were measured, in bitstring order (left → right).
        ``None`` means every qubit (same as ``measure_all``).
    """

    counts: dict[str, int]
    shots: int
    seed: Optional[int]
    num_qubits: int
    ideal_probabilities: dict[str, float]
    state_norm: float
    renormalized: bool
    measured_qubits: Optional[tuple] = None

    # --- dict-like API (Mapping) -----------------------------------------

    def __getitem__(self, bitstring: str) -> int:
        return self.counts[bitstring]

    def __iter__(self):
        return iter(self.counts)

    def __len__(self) -> int:
        return len(self.counts)

    # --- derived views ---------------------------------------------------

    @property
    def empirical_probabilities(self) -> dict[str, float]:
        """Finite-shot estimate P̂(b) = counts[b] / shots."""
        if self.shots == 0:
            return {b: 0.0 for b in self.ideal_probabilities}
        inv = 1.0 / self.shots
        out = {b: 0.0 for b in self.ideal_probabilities}
        for bitstring, count in self.counts.items():
            out[bitstring] = count * inv
        return out

    def total_variation_distance(self) -> float:
        """
        Total variation distance between empirical and ideal distributions.

            TV(P̂, P) = (1/2) Σ_b |P̂(b) − P(b)|

        For a correct sampler, TV → 0 as shots → ∞ (in probability).
        """
        empirical = self.empirical_probabilities
        total = 0.0
        for bitstring, p_ideal in self.ideal_probabilities.items():
            total += abs(empirical.get(bitstring, 0.0) - p_ideal)
        return 0.5 * total

    def most_probable(self) -> str:
        """Bitstring with the largest count (ties: lexicographically first)."""
        if not self.counts:
            raise ValueError("No counts available.")
        best_count = max(self.counts.values())
        candidates = [b for b, c in self.counts.items() if c == best_count]
        return min(candidates)

    def table(self, *, show_zero: bool = False) -> str:
        """Formatted comparison of ideal vs measured outcomes."""
        empirical = self.empirical_probabilities
        rows = []
        for bitstring in sorted(self.ideal_probabilities):
            p_ideal = self.ideal_probabilities[bitstring]
            count = self.counts.get(bitstring, 0)
            p_emp = empirical.get(bitstring, 0.0)
            if not show_zero and count == 0 and p_ideal < 1e-12:
                continue
            rows.append(
                [
                    bitstring,
                    f"{p_ideal:.6f}",
                    str(count),
                    f"{p_emp:.6f}",
                    f"{100.0 * p_emp:6.2f}%",
                    _bar(p_emp),
                ]
            )
        if not rows:
            rows.append(["—", "0.000000", "0", "0.000000", "  0.00%", _bar(0.0)])

        body = _box_table(
            ["outcome", "ideal P", "counts", "empirical P", "percent", "shots"],
            rows,
        )
        seed_txt = "none" if self.seed is None else str(self.seed)
        if self.measured_qubits is None:
            wires = f"all {self.num_qubits} qubits"
        else:
            wires = "qubits " + ",".join(str(q) for q in self.measured_qubits)
        return (
            f"Measurement results  ({wires}, shots={self.shots}, seed={seed_txt})\n"
            f"{body}\n"
            f"TV(ideal, empirical) = {self.total_variation_distance():.6f}"
        )

    def __str__(self) -> str:
        return self.table()

    def __repr__(self) -> str:
        return (
            "MeasurementResult("
            f"shots={self.shots}, seed={self.seed!r}, "
            f"num_qubits={self.num_qubits}, "
            f"counts={self.counts!r}, "
            f"state_norm={self.state_norm:.12g}, "
            f"renormalized={self.renormalized}, "
            f"tv={self.total_variation_distance():.6g})"
        )


def measure_all(state_or_rho, shots=1024, seed=None, *, atol=_NORM_ATOL):
    """
    Sample computational-basis measurements of every qubit.

    Parameters
    ----------
    state_or_rho : array-like
        Statevector from ``run`` or density matrix from ``run_density``.
    shots : int
        Number of independent measurement repetitions (≥ 1).
    seed : int or None
        If set, sampling is reproducible via ``numpy.random.default_rng(seed)``.
        If None, draws are non-deterministic (normal for interactive use).
    atol : float
        Tolerance for probability normalization before sampling.

    Returns
    -------
    MeasurementResult
        Dict-compatible experiment record (counts, probabilities, diagnostics).

    Notes
    -----
    Sampling uses a vectorized histogram (``numpy.bincount``) over outcomes
    drawn with the Born probabilities — O(shots) with no Python per-shot loop.
    """
    if not isinstance(shots, (int, np.integer)) or shots < 1:
        raise ValueError(f"shots must be a positive integer, got {shots!r}.")

    probs, state_norm, renormalized = _outcome_probabilities(state_or_rho, atol=atol)
    dim = probs.shape[0]
    num_qubits = int(np.log2(dim))

    # Isolated Generator: never touches the global np.random state.
    rng = np.random.default_rng(seed)
    samples = rng.choice(dim, size=int(shots), replace=True, p=probs)
    histogram = np.bincount(samples, minlength=dim)

    counts = {
        format(i, f"0{num_qubits}b"): int(histogram[i])
        for i in range(dim)
        if histogram[i]
    }
    ideal = {format(i, f"0{num_qubits}b"): float(probs[i]) for i in range(dim)}

    return MeasurementResult(
        counts=counts,
        shots=int(shots),
        seed=None if seed is None else int(seed),
        num_qubits=num_qubits,
        ideal_probabilities=ideal,
        state_norm=state_norm,
        renormalized=renormalized,
        measured_qubits=None,
    )


def _normalize_qubit_list(qubits, n: int) -> tuple:
    if isinstance(qubits, (int, np.integer)):
        qubits = [int(qubits)]
    else:
        qubits = [int(q) for q in qubits]
    if not qubits:
        raise ValueError("qubits must be a non-empty list of indices.")
    if len(set(qubits)) != len(qubits):
        raise ValueError(f"Duplicate qubit indices in {qubits}.")
    for q in qubits:
        if q < 0 or q >= n:
            raise ValueError(f"Qubit index {q} out of range for n={n}.")
    return tuple(qubits)


def _bit_of(index: int, qubit: int, n: int) -> int:
    """Big-endian: qubit 0 is the MSB of ``index``."""
    return (index >> (n - 1 - qubit)) & 1


def _marginal_probabilities(full_probs: np.ndarray, n: int, qubits: tuple) -> np.ndarray:
    """
    Marginal distribution on ``qubits``.

    Bitstring order follows ``qubits`` left-to-right (``qubits[0]`` is the MSB
    of the marginal outcome).
    """
    m = len(qubits)
    out = np.zeros(2 ** m, dtype=np.float64)
    for index, p in enumerate(full_probs):
        pattern = 0
        for q in qubits:
            pattern = (pattern << 1) | _bit_of(index, q, n)
        out[pattern] += p
    return out


def measure(state_or_rho, qubits, shots=1024, seed=None, *, atol=_NORM_ATOL):
    """
    Z-basis measurement of a **subset** of qubits (partial readout).

    Parameters
    ----------
    state_or_rho
        Statevector or density matrix.
    qubits : int or sequence of int
        Wires to measure. Bitstrings are ordered as this list
        (leftmost bit = first entry).
    shots, seed, atol
        Same meaning as :func:`measure_all`.

    Returns
    -------
    MeasurementResult
        Counts over the measured wires only.

    Notes
    -----
    Probabilities are exact marginals of the Born distribution (or of
    ``diag(ρ)``). This is the correct reduced distribution — not a toy
    truncation of the full bitstring.
    """
    if not isinstance(shots, (int, np.integer)) or shots < 1:
        raise ValueError(f"shots must be a positive integer, got {shots!r}.")

    full_probs, state_norm, renormalized = _outcome_probabilities(
        state_or_rho, atol=atol
    )
    n = int(np.log2(full_probs.shape[0]))
    measured = _normalize_qubit_list(qubits, n)
    m = len(measured)

    probs = _marginal_probabilities(full_probs, n, measured)
    # Numerical guard
    total = float(probs.sum())
    if total <= 0:
        raise ValueError("Marginal probabilities are not positive.")
    probs = probs / total

    rng = np.random.default_rng(seed)
    samples = rng.choice(2 ** m, size=int(shots), replace=True, p=probs)
    histogram = np.bincount(samples, minlength=2 ** m)

    counts = {
        format(i, f"0{m}b"): int(histogram[i])
        for i in range(2 ** m)
        if histogram[i]
    }
    ideal = {format(i, f"0{m}b"): float(probs[i]) for i in range(2 ** m)}

    return MeasurementResult(
        counts=counts,
        shots=int(shots),
        seed=None if seed is None else int(seed),
        num_qubits=m,
        ideal_probabilities=ideal,
        state_norm=state_norm,
        renormalized=renormalized or abs(total - 1.0) > atol,
        measured_qubits=measured,
    )


def collapse(state, qubits, *, seed=None, atol=_NORM_ATOL):
    """
    Single-shot Z measurement with statevector collapse.

    Parameters
    ----------
    state
        Statevector (density-matrix collapse is not implemented here).
    qubits : int or sequence of int
        Wires to measure. Outcome bitstring follows this order.
    seed : int or None
        RNG seed for the single draw.

    Returns
    -------
    outcome : str
        Measured bitstring on ``qubits``.
    new_state : ndarray
        Post-measurement statevector (renormalized projector).

    Example
    -------
        bit, psi = collapse(run(qc), qubits=[0], seed=1)
    """
    arr = np.asarray(state, dtype=complex)
    if arr.ndim != 1:
        raise TypeError(
            "collapse() currently supports statevectors only. "
            "For density matrices use measure(...)."
        )
    psi = _as_statevector(arr)
    full_probs, _, _ = _born_probabilities(psi, atol=atol)
    n = int(np.log2(psi.shape[0]))
    measured = _normalize_qubit_list(qubits, n)
    m = len(measured)

    probs = _marginal_probabilities(full_probs, n, measured)
    total = float(probs.sum())
    probs = probs / total

    rng = np.random.default_rng(seed)
    pattern = int(rng.choice(2 ** m, p=probs))
    outcome = format(pattern, f"0{m}b")

    # Keep amplitudes whose bits on ``measured`` match ``pattern``.
    mask = np.zeros(psi.shape[0], dtype=bool)
    for index in range(psi.shape[0]):
        bits = 0
        for q in measured:
            bits = (bits << 1) | _bit_of(index, q, n)
        mask[index] = bits == pattern

    new_state = psi.copy()
    new_state[~mask] = 0.0
    norm = np.linalg.norm(new_state)
    if norm <= atol:
        raise ValueError("Post-measurement state has near-zero norm.")
    new_state /= norm
    return outcome, new_state
