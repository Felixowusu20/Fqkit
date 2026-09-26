# Changelog

All notable changes to FQkit are documented in this file.

## [0.1.0] - 2026-09-26

### Fixed
- **Multi-qubit gates now work.** Gate application in the simulator was
  rewritten to use tensor contraction (`apply_gate`), so `CNOT`, `CZ`, `SWAP`,
  and `Toffoli` produce correct results for any qubit ordering — including
  reversed and non-adjacent targets. Previously every multi-qubit gate crashed
  with a matrix-dimension error, so entanglement was impossible.
- Unbound parameters now raise a clear `ValueError` naming the parameter,
  instead of a confusing NumPy error.
- Removed the debug `print` that fired on every `add_gate` call.

### Added
- **OpenQASM 2.0 export** — `to_qasm(circuit)` and the convenience method
  `QuantumCircuit.to_qasm(measure=True)`. fqkit circuits can now be loaded into
  Qiskit and run on real IBM Quantum hardware (free tier). Verified with
  round-trip tests that compare fqkit and Qiskit statevectors.
- **Top-level public API** — `from fqkit import QuantumCircuit, Hadamard, CNOT,
  RX, RY, RZ, CZ, SWAP, Toffoli, Parameter, Qubit, bind_parameters, run,
  measure_all, to_qasm`.
- **Packaging** — `pyproject.toml`, so the project is `pip install`-able
  (`pip install -e .`).
- **Test suite** — `tests/` with 29 `pytest` tests covering gates, entanglement,
  parameters, measurement, validation, and the Qiskit round-trip.
- Input validation in `QuantumCircuit.add_gate` for negative and duplicate
  target qubits, and a guard against zero/negative qubit counts.
- `.gitignore`; removed previously committed `__pycache__` artifacts.

### Changed
- README rewritten with working installation, quick-start, variational-circuit,
  OpenQASM/hardware, convention, and testing documentation.
