# Changelog

All notable changes to FQkit are documented in this file.

## [Unreleased]

## [0.1.3] - 2026-10-06

### Added
- The package page credits Felix Owusu and Dr. Addo Dorcas Attuabea.
- The `fqkit` command prints the FQKIT mark with the authors' first names, Felix and Dorcas.

## [0.1.2] - 2026-10-06

### Added
- `draw` and `plot` paint a circuit and its probabilities with Matplotlib.
  Qubit 0 is the top wire. `qc.draw()` is the same picture.
- The package page links to the website at https://fqkit.vercel.app/.

## [0.1.1] - 2026-10-06

### Added
- MIT license and package metadata so this version can be installed from PyPI.
- **Hardware jobs.** `fqkit.hardware.submit` sends a circuit to IBM Quantum
  through Qiskit Runtime, or to IonQ, Rigetti, IQM, and AQT through Amazon
  Braket. The caller picks the machine by name, checks `job.status()`, and
  reads `job.counts()` in fqkit bit order. The vendor SDKs are optional extras
  (`fqkit[ibm]`, `fqkit[braket]`, `fqkit[hardware]`), so the core install
  still depends only on NumPy.

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
