from fqkit.core.operation import Operation
from fqkit.core.qubit import Qubit

class QuantumCircuit:
    def __init__(self , num_qubits:int):
        self.num_qubits = num_qubits
        self.qubits = [Qubit(i) for i in range(num_qubits)]
        self.operations = []

    def add_gate(self, gate, target_qubits):
        # Convert Qubit objects to indices automatically
        target_qubits = [q.index if isinstance(q, Qubit) else q for q in target_qubits]

        if len(target_qubits) != gate.num_qubits:
            raise ValueError(f"Gate {gate.name} requires {gate.num_qubits} qubits, "
                             f"but {len(target_qubits)} were provided.")
        if max(target_qubits) >= self.num_qubits:
            raise ValueError("Target qubit index exceeds circuit size")

        op = Operation(gate, target_qubits)
        self.operations.append(op)
        print(f"Added {op} to the circuit.")

    def __repr__(self):
        op_str = '\n'.join([str(op) for op in self.operations])
        return f"QuantumCircuit({self.num_qubits}, [\n{op_str}\n])"
