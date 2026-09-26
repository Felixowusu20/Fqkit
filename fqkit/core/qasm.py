"""OpenQASM 2.0 export.

Serializing an fqkit circuit to OpenQASM text lets it be loaded into other
tools — most notably Qiskit — and run on real quantum hardware (for example
IBM Quantum's free tier), not just simulated locally.

Example
-------
    from fqkit import QuantumCircuit, Hadamard, CNOT
    from fqkit.core.qasm import to_qasm

    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    print(to_qasm(qc))
"""

from fqkit.core.parameter import Parameter


# fqkit gate name -> (OpenQASM gate name, is_parameterized)
# All of these are provided by the standard "qelib1.inc" library.
_QASM_GATES = {
    "H":       ("h",    False),
    "CNOT":    ("cx",   False),
    "CZ":      ("cz",   False),
    "SWAP":    ("swap", False),
    "Toffoli": ("ccx",  False),
    "RX":      ("rx",   True),
    "RY":      ("ry",   True),
    "RZ":      ("rz",   True),
}


def to_qasm(circuit, measure=True):
    """
    Serialize a QuantumCircuit to an OpenQASM 2.0 string.

    Parameters
    ----------
    circuit : QuantumCircuit
        The circuit to export.
    measure : bool
        If True (default), append a measurement of every qubit into a
        matching classical register so the program is directly runnable on
        hardware. Use False to export the unitary part only.

    Notes
    -----
    Gate-to-qubit semantics (which qubit is control/target, which angle is
    applied where) are preserved exactly. fqkit uses big-endian qubit
    ordering while Qiskit reports measured bitstrings little-endian, so an
    output bitstring may look reversed compared with fqkit's own
    measure_all — the physical correlations are identical.
    """
    n = circuit.num_qubits

    lines = [
        "OPENQASM 2.0;",
        'include "qelib1.inc";',
        f"qreg q[{n}];",
    ]
    if measure:
        lines.append(f"creg c[{n}];")

    for op in circuit.operations:
        gate = op.gate

        if gate.name not in _QASM_GATES:
            raise ValueError(
                f"Gate '{gate.name}' has no OpenQASM 2.0 equivalent in fqkit."
            )

        qasm_name, is_param = _QASM_GATES[gate.name]
        targets = ", ".join(f"q[{i}]" for i in op.qubits)

        if is_param:
            if not gate.params:
                raise ValueError(f"Gate '{gate.name}' requires a parameter.")
            value = gate.params[0]
            if isinstance(value, Parameter):
                raise ValueError(
                    f"Gate '{gate.name}' has an unbound parameter "
                    f"'{value.name}'. Bind it before exporting to OpenQASM."
                )
            lines.append(f"{qasm_name}({value}) {targets};")
        else:
            lines.append(f"{qasm_name} {targets};")

    if measure:
        lines.append("measure q -> c;")

    return "\n".join(lines) + "\n"
