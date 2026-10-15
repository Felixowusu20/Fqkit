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
    result = measure_all(run(qc), shots=1024, seed=7)
    print(result.counts)
    print(result.ideal_probabilities)
    print(result.total_variation_distance())
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Optional

import numpy as np

# If | ‖ψ‖² − 1 | is below this, treat the drift as floating-point noise and
# renormalize before sampling. Larger errors are rejected.
_NORM_ATOL = 1e-8


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


def probabilities(state_vector) -> dict[str, float]:
    """
    Ideal Born probabilities P(b) = |a_b|² with **no** sampling.

    Returns a dict ``{bitstring: probability}`` for every basis state
    (including zeros). Prefer this when you need exact theory curves;
    use ``measure_all`` when you need a finite-shot histogram.
    """
    state = _as_statevector(state_vector)
    probs, _, _ = _born_probabilities(state)
    n = int(np.log2(len(probs)))
    return {format(i, f"0{n}b"): float(probs[i]) for i in range(len(probs))}


@dataclass(frozen=True)
class MeasurementResult(Mapping):
    """
    Record of a Z-basis, all-qubit measurement experiment.

    Acts like a ``dict`` of counts for backward compatibility::

        result["00"]           # count for bitstring 00
        dict(result)           # plain counts dict
        sum(result.values())   # == shots

    Scientific fields (unique value for research workflows)
    -------------------------------------------------------
    ideal_probabilities
        Born-rule P(b) from the statevector (theory).
    empirical_probabilities
        counts[b] / shots (finite-sample estimate).
    state_norm
        ‖ψ‖ before sampling.
    renormalized
        Whether probabilities were rescaled to sum to 1.
    total_variation_distance()
        ½ Σ_b |P_emp(b) − P_ideal(b)| ∈ [0, 1].
        Zero means the histogram matches theory exactly; large values mean
        too few shots or a bug.
    """

    counts: dict[str, int]
    shots: int
    seed: Optional[int]
    num_qubits: int
    ideal_probabilities: dict[str, float]
    state_norm: float
    renormalized: bool

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

    def __str__(self) -> str:
        # Tutorials often ``print(measure_all(...))`` and expect counts.
        return str(self.counts)

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


def measure_all(state_vector, shots=1024, seed=None, *, atol=_NORM_ATOL):
    """
    Sample computational-basis measurements of every qubit.

    Parameters
    ----------
    state_vector : array-like
        Length-2**n complex state from ``run(circuit)``.
    shots : int
        Number of independent measurement repetitions (≥ 1).
    seed : int or None
        If set, sampling is reproducible via ``numpy.random.default_rng(seed)``.
        If None, draws are non-deterministic (normal for interactive use).
    atol : float
        Tolerance for ‖ψ‖² ≈ 1 before renormalizing / rejecting.

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

    state = _as_statevector(state_vector)
    dim = state.shape[0]
    num_qubits = int(np.log2(dim))

    probs, state_norm, renormalized = _born_probabilities(state, atol=atol)

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
    )
