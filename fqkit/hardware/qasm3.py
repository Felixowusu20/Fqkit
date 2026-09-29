"""OpenQASM 3.0 text for vendors that do not accept OpenQASM 2.0.

Amazon Braket is the consumer. IBM keeps using QuantumCircuit.to_qasm(),
which is OpenQASM 2.0.
"""

from fqkit.core.parameter import Parameter


_GATES = {
    "H": ("h", False),
    "CNOT": ("cnot", False),
    "CZ": ("cz", False),
    "SWAP": ("swap", False),
    "Toffoli": ("ccnot", False),
    "RX": ("rx", True),
    "RY": ("ry", True),
    "RZ": ("rz", True),
}


def to_qasm3(circuit):
    """Serialize a circuit to OpenQASM 3.0, including a full measurement."""
    n = circuit.num_qubits
    lines = [
        "OPENQASM 3.0;",
        f"bit[{n}] c;",
        f"qubit[{n}] q;",
    ]
    for op in circuit.operations:
        gate = op.gate
        if gate.name not in _GATES:
            raise ValueError(
                f"Gate '{gate.name}' has no OpenQASM 3.0 equivalent in fqkit."
            )
        name, parameterized = _GATES[gate.name]
        targets = ", ".join(f"q[{i}]" for i in op.qubits)
        if parameterized:
            if not gate.params:
                raise ValueError(f"Gate '{gate.name}' requires a parameter.")
            value = gate.params[0]
            if isinstance(value, Parameter):
                raise ValueError(
                    f"Gate '{gate.name}' has an unbound parameter "
                    f"'{value.name}'. Bind it before sending the circuit."
                )
            lines.append(f"{name}({value}) {targets};")
        else:
            lines.append(f"{name} {targets};")
    lines.append("c = measure q;")
    return "\n".join(lines) + "\n"
