# Fqkit
# FQkit  FQkit is a lightweight Python framework for building and simulating quantum circuits, which can be studied by beginner quantum enthusiats


## Features

- Define qubits and parameterized gates (H, RX, RY, RZ)
- Multi-qubit gates: CNOT, CZ, SWAP, Toffoli
- Circuit construction with `QuantumCircuit`
- Parameter binding for variational circuits
- Simulator that returns the state vector
- Measurement with shot-based probabilities


## Installation

Clone the repository:

```bash
git clone https://github.com/Felixowusu20/Fqkit.git
cd FQkit



from fqkit.core.circuit import QuantumCircuit
from fqkit.core.gate import Hadamard, CNOT
from fqkit.core.parameter import Parameter
from fqkit.core.parameter_binding import bind_parameters
from fqkit.core.simulator import run
from fqkit.core.measurement import measure_all

qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [0])
qc.add_gate(CNOT(), [0,1])

state = run(qc)
counts = measure_all(state, shots=1024)
print("State:", state)
print("Counts:", counts)

