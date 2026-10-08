# FQkit

```text
-------------------------------------------
|                                         |
|                        /\               |
|                       /  \              |
|                     / /\ \              |
|                    / /  \ \             |
|                  / /    \ \             |
|                 / /______\ \            |
|              /_/          \_\           |
|                                         |
|  ███████╗ ██████╗ ██╗  ██╗██╗████████╗  |
|  ██╔════╝██╔═══██╗██║ ██╔╝██║╚══██╔══╝  |
|   █████╗  ██║   ██║█████╔╝ ██║   ██║    |
|   ██╔══╝  ██║▄▄ ██║██╔═██╗ ██║   ██║    |
|   ██║     ╚██████╔╝██║  ██╗██║   ██║    |
|   ╚═╝      ╚══▀▀═╝ ╚═╝  ╚═╝╚═╝   ╚═╝    |
|                                         |
|         Felix            Dorcas         |
|                                         |
-------------------------------------------
```

FQkit is a Python package for building and simulating quantum circuits. The
library is written in Python. NumPy does the arithmetic, and Matplotlib draws
the circuits and the probability graphs.

Authors: Felix Owusu and Dr. Addo Dorcas Attuabea.

Website: <https://fqkit.vercel.app/>

## Features

- Qubits and parameterized gates (`H`, `RX`, `RY`, `RZ`)
- Multi-qubit gates: `CNOT`, `CZ`, `SWAP`, `Toffoli`
- Circuit construction with `QuantumCircuit`
- Parameter binding for variational circuits
- A statevector simulator that returns the final state
- Measurement with shot-based sampling
- `draw` and `plot` for circuit pictures and probability graphs
- Export to OpenQASM 2.0: run your circuits on real IBM hardware via Qiskit

## Installation

```bash
pip install fqkit
fqkit
```

FQkit needs Python 3.9 or newer. NumPy and Matplotlib are installed with it.
The `fqkit` command prints the mark above, with the authors' first names underneath.

To work on the source, clone the repository and install it in editable mode:

```bash
git clone https://github.com/Felixowusu20/Fqkit.git
cd Fqkit
pip install -e ".[dev]"
pytest
```

## Quick start

Build a Bell state, an entangled pair of qubits, and measure it:

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

## Draw a circuit

`draw` paints the wires with Matplotlib. Qubit 0 is the top wire. `plot`
paints the probabilities, or the shot counts.

```python
from fqkit import QuantumCircuit, Hadamard, CNOT, draw, plot, run, measure_all
import matplotlib.pyplot as plt

qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [0])
qc.add_gate(CNOT(), [0, 1])

draw(qc)                 # or qc.draw()
plt.show()

plot(run(qc))            # one bar per basis state
plt.show()
```

`draw(qc, filename="circuit.png")` saves the picture instead of opening a window.

## Variational circuits

Gates can take symbolic `Parameter`s that you bind to numbers later: the basis
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

## Export to OpenQASM: run on real hardware

Any circuit can be exported to OpenQASM 2.0, the open standard that Qiskit
reads. That means a circuit you build in fqkit can run on a **real quantum
computer** through IBM Quantum's free tier: no hardware of your own needed.
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

### Run on real hardware

`run()` stays on your computer. Hardware jobs go through `fqkit.hardware`,
which calls the vendor SDK, waits on the queue, and returns counts in fqkit
bit order (qubit 0 on the left). The vendor packages are optional, so a normal
install still depends only on NumPy.

```bash
pip install "fqkit[ibm]"       # IBM Quantum, through Qiskit Runtime
pip install "fqkit[braket]"    # IonQ, Rigetti, IQM, and AQT, through Amazon Braket
pip install "fqkit[hardware]"  # both
```

```python
from fqkit.hardware import providers, submit

providers()                    # ibm, ionq, rigetti, iqm, aqt

job = submit(qc, "ibm", shots=1024)
print(job.job_id, job.status())   # QUEUED, RUNNING, COMPLETED, CANCELLED, FAILED
print(job.counts())               # waits for the device

job = submit(qc, "ionq", shots=100)
job = submit(qc, "rigetti", shots=100)
```

IBM needs a free account at https://quantum.cloud.ibm.com. Save the token once
with `QiskitRuntimeService.save_account`, or pass `token=` to `submit`. With
no backend name, fqkit picks the least busy real device. Pass
`backend="ibm_..."` to choose one, or `backends("ibm", live=True)` to list
the devices that are up.

IonQ, Rigetti, IQM, and AQT are one Amazon Braket account. Those QPU tasks are
billed by AWS. `submit(qc, "ionq")` targets IonQ Forte-1. Pass `backend=` as a
full device ARN when you need a different chip. `job.status()` returns
immediately. `job.counts()` blocks until the machine finishes. `get_job(machine,
job_id)` reconnects to a job you already submitted.

The lessons in the browser keep using the local simulator. A hardware token
stays in your own Python process.

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
  hardware/
    ibm.py                # IBM Quantum via Qiskit Runtime
    braket.py             # IonQ, Rigetti, IQM, AQT via Amazon Braket
```

## Convention

FQkit uses **big-endian** qubit ordering: qubit 0 is the most significant bit
of the state-vector index, and the first qubit passed to a multi-qubit gate is
its most significant qubit (for `CNOT`, the control).

## Testing

FQkit ships with a `pytest` suite covering the simulator, every gate, parameter
binding, measurement, input validation, and the OpenQASM export, including
round-trip tests that load an exported circuit into Qiskit and check that the
statevectors match fqkit's own simulator.

```bash
pip install -e ".[dev]"   # installs pytest
pytest -v                 # 46 tests
```

The Qiskit round-trip tests are skipped automatically if Qiskit is not
installed. Install it (free) with `pip install qiskit` to run those too.

| Test file | Covers |
|---|---|
| `tests/test_fqkit.py` | Single- and multi-qubit gates, entanglement (Bell states), reversed and non-adjacent controls, parameter binding, unbound-parameter errors, measurement statistics, and input validation |
| `tests/test_qasm.py` | OpenQASM string output, gate-name mapping, error handling, and Qiskit round-trip equivalence |
| `tests/test_hardware.py` | Machine selection, OpenQASM 3 for Braket, Runtime and Braket submission with stand-in SDKs, job status, and bit order |
