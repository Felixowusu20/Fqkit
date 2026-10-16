"""Hardware-efficient ansatz circuits for VQE (FQkit only)."""

from __future__ import annotations

from fqkit.core.circuit import QuantumCircuit
from fqkit.core.gate import CNOT, RY, RZ
from fqkit.core.parameter import Parameter


def hardware_efficient_ansatz(
    n_qubits: int,
    layers: int = 2,
    *,
    prefix: str = "θ",
) -> tuple[QuantumCircuit, list[str]]:
    """
    Build a layered RY–RZ + nearest-neighbor CNOT ansatz.

    Returns
    -------
    circuit : QuantumCircuit
        Template with unbound :class:`~fqkit.Parameter` angles.
    param_names : list[str]
        Parameter names in the order the optimizer should use.
    """
    if n_qubits < 1:
        raise ValueError("n_qubits must be >= 1.")
    if layers < 1:
        raise ValueError("layers must be >= 1.")

    qc = QuantumCircuit(n_qubits)
    names: list[str] = []
    k = 0

    for _layer in range(layers):
        for q in range(n_qubits):
            name_y = f"{prefix}{k}"
            k += 1
            name_z = f"{prefix}{k}"
            k += 1
            names.extend([name_y, name_z])
            qc.add_gate(RY(Parameter(name_y)), [q])
            qc.add_gate(RZ(Parameter(name_z)), [q])
        for q in range(n_qubits - 1):
            qc.add_gate(CNOT(), [q, q + 1])

    return qc, names
