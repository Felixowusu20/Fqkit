# FQkit simulator task board

This is the source of truth for classical-simulator contributions.
Prefer this work over new hardware features until the ideal simulator is
research-grade.

**Suggested order:** Task 1 → 2 → 3, then 4, then 5–6. Extra tasks (A–E) can
run in parallel with 1–3.

Every PR should meet four standards:

1. **Correctness** — compare against analytical results or a trusted reference
2. **Reproducibility** — document seeds and numerical tolerances
3. **Performance** — for heavy features, note runtime/memory impact
4. **Documentation** — one working example plus automated tests

---

## Task 1 — Finish statevector validation

**Status:** Done (see `tests/test_statevector_validation.py`) · **Labels:** `foundation`, `simulator`

### Why it helps

Everything else (measurement, VQE, noise) sits on `run()` / `apply_gate()`.
If a gate matrix, qubit order, or custom gate is wrong, every algorithm
result is wrong. This turns FQkit from a demo simulator into something
collaborators can trust for small-system research.

### Current code

- `fqkit/core/simulator.py` — `apply_gate`, `_gate_matrix`, `run`
- `fqkit/core/gate.py` — built-in gates
- `tests/test_fqkit.py` — Bell, CNOT ordering, Toffoli, etc.

### How to go about it

1. Read the files above and the big-endian note in the root `README.md`.
2. Add contract checks in `apply_gate` (or a helper):
   - `gate_matrix` shape is `(2**k, 2**k)` for `k = len(target_qubits)`
   - optional unitarity: `U†U ≈ I` within a fixed tolerance
   - state length is `2**n`
3. Add missing first-class gates if straightforward: `I`, `X`, `Y`, `Z`, `S`, `T`.
4. Expand tests with table-driven cases:
   - every built-in matrix is unitary
   - H on `|0⟩` → `|+⟩`
   - Bell `|Φ⁺⟩ = (|00⟩+|11⟩)/√2`
   - GHZ-3: `(|000⟩+|111⟩)/√2`
   - norm `‖ψ‖ ≈ 1` after small deep circuits
5. Optionally add a short docs page under `website/src/content/` describing
   endianness and tolerances.

### Acceptance criteria

- [ ] Every supported gate has a matrix and/or known-state test
- [ ] Bad custom gate shapes raise clear errors
- [ ] Bell and GHZ analytical amplitudes pass (e.g. tolerance `1e-10`)
- [ ] `pytest` passes locally

---

## Task 2 — Measurement v2 (seeds, Result, clearer API)

**Status:** Done (see `fqkit/core/measurement.py`, `tests/test_measurement.py`) · **Labels:** `foundation`, `simulator`

### Why it helps

Sampling currently uses the global `np.random` RNG, so experiments are not
reproducible and CI cannot lock golden counts. A proper `Result` object is
what notebooks and variational loops expect (counts + probabilities +
metadata), not a bare `dict`.

### Current code

- `fqkit/core/measurement.py` — `measure_all(state_vector, shots=1024)`

### How to go about it

1. Keep backward compatibility where possible.
2. Prefer an API like:

   ```python
   measure_all(state, shots=1024, seed=None) -> Result
   ```

3. Define a small `Result` (dataclass or simple class) with at least:
   - `counts: dict[str, int]`
   - `shots: int`
   - probabilities (ideal and/or empirical — document which)
   - `seed` when provided
4. Use `np.random.default_rng(seed)` instead of the global RNG.
5. Normalize or guard probabilities if `sum(|ψ|²)` drifts slightly from 1;
   raise or warn if far off.
6. Add tests: same seed → identical counts; Bell only `00`/`11` at large shots.
7. Optional helper: `probabilities(state)` with no sampling.

### Acceptance criteria

- [ ] Seeded runs are identical across two calls
- [ ] Ideal probabilities match `|amp|²`
- [ ] Existing call sites still work, or migration is documented
- [ ] Public exports updated in `fqkit/__init__.py` if needed

---

## Task 3 — Pauli observables and expectation values

**Status:** Missing · **Labels:** `research`, `simulator`

### Why it helps

Unlocks energy estimation, correlation checks, and VQE/QAOA-style workflows
**without** hardware. Users can ask for `⟨ZZ⟩` on a Bell state instead of
only looking at shot histograms.

### How to go about it

1. Add a module such as `fqkit/core/observables.py` (or `pauli.py`).
2. Implement:
   - single-qubit Paulis `X`, `Y`, `Z` (and `I`)
   - Pauli strings / products, e.g. `Z0 Z1`
   - `expectation(state, observable) -> float` as `⟨ψ|O|ψ⟩`
3. Keep the first version dense and exact (full matrix or tensor apply).
4. Analytical tests on Bell `|Φ⁺⟩`:
   - `⟨ZZ⟩ = +1`
   - `⟨XX⟩ = +1`
   - `⟨YY⟩ = −1`
5. Add a short tutorial example. Do **not** build a full VQE optimizer yet.

### Acceptance criteria

- [ ] Bell expectation tests pass
- [ ] Invalid Pauli strings / qubit indices raise clear errors
- [ ] Public export from `fqkit` (`expectation`, Pauli helpers)
- [ ] One docs/tutorial example

---

## Task 4 — Local circuit equivalence tests

**Status:** Missing · **Labels:** `quality`, `tests`

### Why it helps

Gives FQkit an internal truth check when rewrite rules are added later.
Even without an optimizer, equivalence tests catch silent bugs in gate
definitions. Qiskit round-trips in `tests/test_qasm.py` are useful but are
not a substitute for in-library identities.

### How to go about it

1. Compare two circuits by statevector (optionally phase-insensitive).
2. Cover identities first:
   - `H·H ≡ I`
   - `X·X ≡ I`, `CNOT·CNOT ≡ I`
   - `SWAP` twice ≡ identity
3. Optional follow-up: a tiny `cancel_adjacent_inverses` pass — only after
   tests exist.

### Acceptance criteria

- [ ] Identity suite runs in CI without requiring Qiskit
- [ ] Any future optimizer PR must show optimized ≈ original state

---

## Task 5 — Density-matrix simulator and simple noise

**Status:** Missing · **Labels:** `advanced`, `simulator` · **Depends on:** Tasks 1–3 solid

### Why it helps

Ideal statevectors cannot model decoherence. A density-matrix path lets
FQkit teach and research noisy algorithms and provides a reference for
stochastic noise later.

### How to go about it

1. New module, e.g. `fqkit/core/density.py`:
   - `run_density(circuit) -> ρ`
   - apply gates as `ρ → U ρ U†`
2. Validate: `Tr(ρ) ≈ 1`, Hermitian, eigenvalues ≥ 0 (within tolerance).
3. Start with bit-flip, phase-flip, and depolarizing channels.
4. Tests: pure Bell as `|ψ⟩⟨ψ|` matches the statevector outer product;
   after depolarizing, purity drops.
5. Document the memory cost (`4ⁿ`) and recommend small `n`.

**Important:** do not only add random flips to a statevector and claim that
models all quantum noise.

### Acceptance criteria

- [ ] Trace / Hermiticity / positivity tests pass
- [ ] At least one noise model covered by tests
- [ ] Clear API split: ideal `run` vs density / noisy path

---

## Task 6 — Performance and memory benchmarks

**Status:** Missing · **Labels:** `performance`

### Why it helps

Benchmarks decide whether sparse or tensor-network work is worth doing.
Without numbers, collaborators waste time on premature optimization.

### How to go about it

1. Add `benchmarks/` with a script (`time` + `tracemalloc` / `resource`, or
   pytest-benchmark).
2. Measure for several qubit counts (e.g. `n = 8 … 14` until limits):
   - wall time for `run` on a fixed circuit
   - peak memory for the statevector
3. Publish a markdown table (machine, Python, NumPy versions).
4. Optional: compare tensordot apply vs a naive kron baseline.

### Acceptance criteria

- [ ] Reproducible script others can run
- [ ] Table for at least three qubit counts
- [ ] Short note on practical laptop limits for full statevector

---

## Extra tasks (good parallel PRs)

### A. Missing gates: I, X, Y, Z, S, T

Matches textbook algorithms. Mirror `Hadamard` in `gate.py`; add matrix and
one-qubit state tests.

### B. `probabilities(state)` helper

Ideal probabilities without shots. Useful for plots, docs, and debugging
expectations.

### C. Immutable parameter binding

Today binding may mutate circuits. Prefer returning a bound copy and leaving
the original unbound.

### D. Single-qubit / partial Z-measurement

Clarifies collapse and `Result` design before noise work.

### E. Simulator correctness docs page

One Bell example that covers gates, entanglement, norm, and sampling — under
`website/src/content/` or tutorials.

---

## Filing an issue

Use the **Simulator task** issue template. Pick the task id, link this doc,
and checklist the acceptance criteria you will own.
