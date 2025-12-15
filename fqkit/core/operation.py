# Operation (Gate + target qubits)
# Why this matters

# A gate alone is abstract.
# An operation is a gate applied to specific qubits.


class Operation:
    def __init__(self, gate, target_qubits):
        self.gate = gate
        self.qubits = target_qubits

    def __repr__(self):
        qubit_str = ', '.join([str(q) for q in self.qubits])
        return f"{self.gate} on ({qubit_str})"