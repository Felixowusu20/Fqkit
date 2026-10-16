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
the circuits and the probability graphs. Optional chemistry extras add molecular
VQE and one-shot DMET Embedded-VQE on the same FQkit engine.

Authors: Felix Owusu and Dr. Addo Dorcas Attuabea.

Website: <https://fqkit.vercel.app/>

## Features

- Qubits and parameterized gates (`H`, `RX`, `RY`, `RZ`, …)
- Multi-qubit gates: `CNOT`, `CZ`, `SWAP`, `Toffoli`
- Circuit construction with `QuantumCircuit`
- Immutable `bind_parameters` for variational circuits (VQE / QAOA)
- Dense statevector simulator with seeded measurement / probability tables
- Pauli strings, Hamiltonians, and exact ⟨O⟩ expectations
- Circuit equivalence checks and density-matrix Kraus noise
- `draw` and `plot` for circuits and probability graphs
- Export to OpenQASM 2.0 / 3; submit via `fqkit.hardware` (IBM, Braket)
- **VQE** (`fqkit[chemistry]`): PySCF + OpenFermion → FQkit ansatz / SciPy loop
- **Embedded-VQE**: one-shot DMET fragment ⊕ bath impurity on FQkit

## Progress

Tracked improvements (newest first). Use this as the README changelog.

| Version / date | What landed |
|---|---|
| **0.1.3+ (2026-10)** | Molecular **VQE** and one-shot **DMET Embedded-VQE**: PySCF/OpenFermion mapping, HEA + SciPy on FQkit; H₂ ↔ FCI and LiH impurity ↔ CASCI validated |
| 0.1.3 | Simulator correctness push: Pauli expectations, equivalence, density noise, immutable bind, partial measure/collapse, probability tables, benchmarks, docs site |
| earlier | Core circuits, statevector engine, OpenQASM export, IBM / Braket hardware extras, learning website |

Roadmap next: DMET correlation-potential self-consistency / multi-fragment μ fitting; richer chemistry ansatze; shot-based VQE on `fqkit.hardware`.

## Installation

```bash
pip install fqkit
fqkit
```

FQkit needs Python 3.9 or newer. NumPy and Matplotlib are installed with it.
The `fqkit` command prints the mark above, with the authors' first names underneath.

Optional stacks:

```bash
pip install "fqkit[chemistry]"   # PySCF + OpenFermion + SciPy → VQE / Embedded-VQE
pip install "fqkit[ibm]"         # IBM Quantum via Qiskit Runtime
pip install "fqkit[braket]"      # IonQ, Rigetti, IQM, AQT via Amazon Braket
pip install "fqkit[hardware]"    # ibm + braket
pip install "fqkit[dev]"         # pytest (+ scipy for local VQE unit tests)
```

To work on the source, clone the repository and install it in editable mode:

```bash
git clone https://github.com/Felixowusu20/Fqkit.git
cd Fqkit
pip install -e ".[dev,chemistry]"
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

template = QuantumCircuit(2)
template.add_gate(Hadamard(), [0])
template.add_gate(RX(theta), [1])

bound = bind_parameters(template, {"theta": 3.14159})  # template stays unbound
print(measure_all(run(bound), shots=1024, seed=1))
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
    measurement.py        # measure_all / collapse / probability tables
    observables.py        # Pauli, Hamiltonian, expectation
    equivalence.py        # circuits_equivalent
    density.py            # density-matrix + Kraus noise
    draw.py               # draw / plot
    qasm.py               # to_qasm: OpenQASM 2.0
  vqe/                    # optional: pip install fqkit[chemistry]
    molecule.py           # PySCF + OpenFermion → FQkit Hamiltonian
    ansatz.py             # hardware-efficient ansatz
    optimize.py           # run_vqe (SciPy + FQkit ⟨H⟩)
    dmet.py               # one-shot DMET fragment ⊕ bath
    embedded.py           # run_embedded_vqe
  hardware/
    ibm.py                # IBM Quantum via Qiskit Runtime
    braket.py             # IonQ, Rigetti, IQM, AQT via Amazon Braket
examples/
  vqe_h2.py               # full-molecule H₂ VQE
  embedded_vqe_lih.py     # DMET Embedded-VQE on LiH
```

## Convention

FQkit uses **big-endian** qubit ordering: qubit 0 is the most significant bit
of the state-vector index, and the first qubit passed to a multi-qubit gate is
its most significant qubit (for `CNOT`, the control). OpenFermion JW terms are
mapped so qubit 0 is the **leftmost** Pauli letter, matching this convention.

## VQE and Embedded-VQE (chemistry extras)

Stack choice (kept deliberately lean):

| Layer | Tool |
|---|---|
| Chemistry | PySCF (+ NumPy / SciPy) |
| Mapping | OpenFermion + openfermionpyscf (Jordan–Wigner) |
| Quantum app | **FQkit only** — ansatz, `bind_parameters`, ⟨H⟩, VQE loop |
| Hardware later | `fqkit.hardware` (same circuits → OpenQASM → IBM / Braket) |

No PennyLane or Qiskit Nature on the chemistry path.

### Full-molecule VQE

```bash
pip install -e ".[chemistry]"
PYTHONPATH=. python examples/vqe_h2.py
```

```python
from fqkit.vqe import molecule_hamiltonian, run_vqe

H, info = molecule_hamiltonian(
    [("H", (0, 0, 0)), ("H", (0, 0, 0.7414))],
    basis="sto-3g",
)
result = run_vqe(H, layers=3, maxiter=400, seed=0)
print(result.energy, info.hf_energy, info.fci_energy)
```

Works for any geometry PySCF accepts. Practical limit is statevector size
(~2 × number of spatial orbitals qubits). H₂ / STO-3G is 4 qubits; larger
molecules should use embedding.

**Checks:** mapped `H` spectrum matches FCI; VQE on H₂ lands near FCI with the
default HEA + COBYLA settings used in the example.

### One-shot DMET Embedded-VQE

For correlated / larger systems: pick a fragment, build bath orbitals from the
HF 1-RDM (`pyscf.mcscf.dmet_cas`), form the interacting-bath impurity
Hamiltonian, then run the same FQkit VQE loop.

```python
from fqkit.vqe import run_embedded_vqe

out = run_embedded_vqe(
    [("Li", (0, 0, 0)), ("H", (0, 0, 1.6))],
    fragment_atoms="H",
    run_casci=True,
    run_fci=True,
)
emb = out.embedding
print(out.energy, emb.casci_energy, emb.fci_energy, emb.n_cas, emb.n_bath)
```

```bash
PYTHONPATH=. python examples/embedded_vqe_lih.py
```

**Checks:** qubit `H` ground energy = PySCF CASCI (machine precision); H₂ with a
one-atom fragment recovers full FCI; LiH H-fragment impurity beats HF and sits
near FCI; bath size ≤ fragment size (DMET bound).

Still **one-shot** DMET (no correlation-potential self-consistency yet — see
Progress / roadmap above).

## Benchmarks

See how far the engines go on your laptop (specs table + timing/memory tables):

```bash
PYTHONPATH=. python benchmarks/bench_fqkit.py
```

Details: [benchmarks/README.md](benchmarks/README.md).

## Contributing

We are prioritizing classical-simulator correctness and research usefulness.
See [CONTRIBUTING.md](CONTRIBUTING.md) and the task board in
[docs/simulator-tasks.md](docs/simulator-tasks.md). Use the **Simulator task**
GitHub issue template to claim work.

## Testing

```bash
pip install -e ".[dev,chemistry]"
pytest -v                 # 150+ tests when chemistry extras are present
pytest -m "not chemistry" # skip PySCF / OpenFermion cases
```

Qiskit / hardware round-trips skip automatically if those SDKs are missing.
Chemistry-marked tests skip if `fqkit[chemistry]` is not installed.

| Test file | Covers |
|---|---|
| `tests/test_fqkit.py` | Gates, entanglement, parameter binding, measurement, validation |
| `tests/test_statevector_validation.py` | Analytical statevector / norm / unitary checks |
| `tests/test_observables.py` | Pauli / Hamiltonian expectations |
| `tests/test_equivalence.py` | Circuit equivalence |
| `tests/test_density.py` | Density matrix + Kraus noise |
| `tests/test_measurement.py` | Shots, seeds, probability tables, collapse |
| `tests/test_bind_parameters.py` | Immutable bind |
| `tests/test_qasm.py` | OpenQASM export + Qiskit round-trip |
| `tests/test_hardware.py` | IBM / Braket submit path (stand-in SDKs) |
| `tests/test_vqe.py` | `run_vqe`, H₂ mapping ↔ FCI |
| `tests/test_embedded_vqe.py` | DMET impurity ↔ CASCI / FCI, bath bounds, LiH VQE |
