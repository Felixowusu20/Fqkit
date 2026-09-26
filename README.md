# FQkit

FQkit is a lightweight Python framework for building and simulating quantum
circuits. It is designed to be readable and approachable, so beginner quantum
enthusiasts — in Africa and around the world — can learn how a quantum computer
works by reading and hacking on the source.

## Features

- Qubits and parameterized gates (`H`, `RX`, `RY`, `RZ`)
- Multi-qubit gates: `CNOT`, `CZ`, `SWAP`, `Toffoli`
- Circuit construction with `QuantumCircuit`
- Parameter binding for variational circuits
- A statevector simulator that returns the final state
- Measurement with shot-based sampling
- Export to OpenQASM 2.0 — run your circuits on real IBM hardware via Qiskit

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/Felixowusu20/Fqkit.git
cd Fqkit
pip install -e .
```

To run the test suite as well:

```bash
pip install -e ".[dev]"
pytest
```

## Quick start

Build a Bell state — an entangled pair of qubits — and measure it:

```python
from fqkit import QuantumCircuit, Hadamard, CNOT, run, measure_all

qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [0])      # put qubit 0 into superposition
qc.add_gate(CNOT(), [0, 1])       # entangle qubit 1 with qubit 0

state = run(qc)                   # -> array([0.707, 0, 0, 0.707])
counts = measure_all(state, shots=1024)

print("State :", state)
print("Counts:", counts)          # -> {'00': ~512, '11': ~512}
```

## Variational circuits

Gates can take symbolic `Parameter`s that you bind to numbers later — the basis
of variational algorithms like VQE and QAOA:

```python
from fqkit import QuantumCircuit, Hadamard, RX, Parameter, bind_parameters, run, measure_all

theta = Parameter("theta")

qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [0])
qc.add_gate(RX(theta), [1])

bind_parameters(qc, {"theta": 3.14159})

counts = measure_all(run(qc), shots=1024)
print(counts)
```

## Export to OpenQASM — run on real hardware

Any circuit can be exported to OpenQASM 2.0, the open standard that Qiskit
reads. That means a circuit you build in fqkit can run on a **real quantum
computer** through IBM Quantum's free tier — no hardware of your own needed.
Everything in this pipeline (OpenQASM, Qiskit, the IBM free tier) costs nothing.

```python
from fqkit import QuantumCircuit, Hadamard, CNOT

qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [0])
qc.add_gate(CNOT(), [0, 1])

print(qc.to_qasm())          # or: to_qasm(qc)
```

```
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
```

### Load it in Qiskit (free)

`pip install qiskit` (free and open source), then:

```python
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.quantum_info import Statevector

qiskit_qc = QiskitCircuit.from_qasm_str(qc.to_qasm(measure=False))
print(Statevector.from_instruction(qiskit_qc).probabilities_dict())
# {'00': 0.5, '11': 0.5}
```

### Run on a real IBM Quantum backend (free tier)

```python
# 1. Create a free account at https://quantum.cloud.ibm.com
# 2. pip install qiskit-ibm-runtime, then save your token once:
#      from qiskit_ibm_runtime import QiskitRuntimeService
#      QiskitRuntimeService.save_account(channel="ibm_quantum", token="<YOUR_TOKEN>")
# 3. Run the exported circuit on the least-busy real device:
#      from qiskit import transpile
#      service = QiskitRuntimeService()
#      backend = service.least_busy(operational=True, simulator=False)
#      job = backend.run(transpile(qiskit_qc, backend), shots=1024)
#      print(job.result().get_counts())
```

> **Bit order:** fqkit treats qubit 0 as the most significant bit, while Qiskit
> prints measured bitstrings least-significant-bit first. The circuit and its
> correlations are identical — only the printed string may look reversed.

## Project layout

```
fqkit/
  core/
    qubit.py              # Qubit: an index into Hilbert space
    parameter.py          # Parameter: a symbolic variable
    gate.py               # Gate + H, RX, RY, RZ, CNOT, CZ, SWAP, Toffoli
    operation.py          # Operation: a gate applied to specific qubits
    circuit.py            # QuantumCircuit: an ordered list of operations
    parameter_binding.py  # bind_parameters: substitute symbols -> numbers
    simulator.py          # run: apply gates to a statevector
    measurement.py        # measure_all: sample |amplitude|^2
    qasm.py               # to_qasm: export circuits to OpenQASM 2.0
```

## Convention

FQkit uses **big-endian** qubit ordering: qubit 0 is the most significant bit
of the state-vector index, and the first qubit passed to a multi-qubit gate is
its most significant qubit (for `CNOT`, the control).

## Testing

FQkit ships with a `pytest` suite covering the simulator, every gate, parameter
binding, measurement, input validation, and the OpenQASM export — including
round-trip tests that load an exported circuit into Qiskit and check that the
statevectors match fqkit's own simulator.

```bash
pip install -e ".[dev]"   # installs pytest
pytest -v                 # 29 tests
```

The Qiskit round-trip tests are skipped automatically if Qiskit is not
installed. Install it (free) with `pip install qiskit` to run those too.

| Test file | Covers |
|---|---|
| `tests/test_fqkit.py` | Single- and multi-qubit gates, entanglement (Bell states), reversed and non-adjacent controls, parameter binding, unbound-parameter errors, measurement statistics, and input validation |
| `tests/test_qasm.py` | OpenQASM string output, gate-name mapping, error handling, and Qiskit round-trip equivalence |
