from fqkit.core.operation import Operation
from fqkit.core.qubit import Qubit
from fqkit.core.qasm import to_qasm as _to_qasm

class QuantumCircuit:
    def __init__(self , num_qubits:int):
        if num_qubits <= 0:
            raise ValueError("A circuit needs at least one qubit.")
        self.num_qubits = num_qubits
        self.qubits = [Qubit(i) for i in range(num_qubits)]
        self.operations = []

    def add_gate(self, gate, target_qubits):
        # Convert Qubit objects to indices automatically
        target_qubits = [q.index if isinstance(q, Qubit) else q for q in target_qubits]

        if len(target_qubits) != gate.num_qubits:
            raise ValueError(f"Gate {gate.name} requires {gate.num_qubits} qubits, "
                             f"but {len(target_qubits)} were provided.")
        if min(target_qubits) < 0:
            raise ValueError("Target qubit index cannot be negative")
        if max(target_qubits) >= self.num_qubits:
            raise ValueError("Target qubit index exceeds circuit size")
        if len(set(target_qubits)) != len(target_qubits):
            raise ValueError(f"Gate {gate.name} was given a repeated target qubit: "
                             f"{target_qubits}")

        op = Operation(gate, target_qubits)
        self.operations.append(op)

    def to_qasm(self, measure=True):
        """Return this circuit as an OpenQASM 2.0 string.

        See fqkit.core.qasm.to_qasm for details.
        """
        return _to_qasm(self, measure=measure)

    def __repr__(self):
        op_str = '\n'.join([str(op) for op in self.operations])
        return f"QuantumCircuit({self.num_qubits}, [\n{op_str}\n])"
