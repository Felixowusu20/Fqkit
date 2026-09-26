"""
FQkit — a lightweight quantum circuit framework for learning and simulation.

Quick start
-----------
    from fqkit import QuantumCircuit, Hadamard, CNOT, run, measure_all

    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])

    state = run(qc)
    counts = measure_all(state, shots=1024)
"""

from fqkit.core import (
    Qubit,
    Parameter,
    Gate,
    Hadamard,
    RX,
    RY,
    RZ,
    CNOT,
    CZ,
    SWAP,
    Toffoli,
    Operation,
    QuantumCircuit,
    bind_parameters,
    run,
    apply_gate,
    measure_all,
    to_qasm,
)

__version__ = "0.1.0"

__all__ = [
    "Qubit",
    "Parameter",
    "Gate",
    "Hadamard",
    "RX",
    "RY",
    "RZ",
    "CNOT",
    "CZ",
    "SWAP",
    "Toffoli",
    "Operation",
    "QuantumCircuit",
    "bind_parameters",
    "run",
    "apply_gate",
    "measure_all",
    "to_qasm",
    "__version__",
]
