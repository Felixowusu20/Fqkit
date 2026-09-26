"""Tests for the OpenQASM 2.0 export bridge (fqkit -> Qiskit)."""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Gate,
    Parameter,
    Hadamard,
    RX,
    RY,
    RZ,
    CNOT,
    CZ,
    SWAP,
    Toffoli,
    bind_parameters,
    run,
    to_qasm,
)


# --- string structure -----------------------------------------------------

def test_bell_qasm_string():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    qasm = qc.to_qasm()

    assert "OPENQASM 2.0;" in qasm
    assert 'include "qelib1.inc";' in qasm
    assert "qreg q[2];" in qasm
    assert "creg c[2];" in qasm
    assert "h q[0];" in qasm
    assert "cx q[0], q[1];" in qasm
    assert "measure q -> c;" in qasm


def test_measure_false_omits_classical_bits():
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    qasm = to_qasm(qc, measure=False)
    assert "creg" not in qasm
    assert "measure" not in qasm


def test_all_gate_names_map():
    theta = Parameter("t")
    qc = QuantumCircuit(3)
    qc.add_gate(RX(theta), [0])
    bind_parameters(qc, {"t": 0.5})
    qc.add_gate(RY(0.25), [1])
    qc.add_gate(RZ(0.75), [2])
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CZ(), [0, 1])
    qc.add_gate(SWAP(), [1, 2])
    qc.add_gate(CNOT(), [0, 2])
    qc.add_gate(Toffoli(), [0, 1, 2])

    qasm = qc.to_qasm(measure=False)
    for token in ["rx(0.5)", "ry(0.25)", "rz(0.75)", "h ", "cz ", "swap ", "cx ", "ccx "]:
        assert token in qasm


# --- error handling -------------------------------------------------------

def test_unbound_parameter_raises():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RX(theta), [0])
    with pytest.raises(ValueError, match="unbound parameter"):
        qc.to_qasm()


def test_unknown_gate_raises():
    qc = QuantumCircuit(1)
    qc.add_gate(Gate("MyCustomGate", 1, matrix=[[1, 0], [0, 1]]), [0])
    with pytest.raises(ValueError, match="no OpenQASM"):
        qc.to_qasm()


# --- round-trip against Qiskit --------------------------------------------

def _reverse_index_bits(k, n):
    """Reverse the n-bit representation of k (big-endian <-> little-endian)."""
    r = 0
    for _ in range(n):
        r = (r << 1) | (k & 1)
        k >>= 1
    return r


def _assert_matches_qiskit(qc):
    """Export to QASM, simulate in Qiskit, and compare statevectors."""
    qiskit = pytest.importorskip("qiskit", reason="Qiskit not installed")
    from qiskit import QuantumCircuit as QiskitCircuit
    from qiskit.quantum_info import Statevector

    qiskit_qc = QiskitCircuit.from_qasm_str(qc.to_qasm(measure=False))
    qiskit_state = Statevector.from_instruction(qiskit_qc).data

    n = qc.num_qubits
    fqkit_state = run(qc)
    reordered = np.array([qiskit_state[_reverse_index_bits(m, n)] for m in range(2 ** n)])

    assert np.allclose(fqkit_state, reordered, atol=1e-8)


def test_roundtrip_bell():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    _assert_matches_qiskit(qc)


def test_roundtrip_parameterized():
    theta = Parameter("theta")
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(RX(theta), [1])
    qc.add_gate(RY(theta), [0])
    bind_parameters(qc, {"theta": 1.234})
    _assert_matches_qiskit(qc)


def test_roundtrip_three_qubit_mixed():
    qc = QuantumCircuit(3)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 2])     # non-adjacent
    qc.add_gate(RY(0.7), [1])
    qc.add_gate(CZ(), [1, 2])
    qc.add_gate(SWAP(), [0, 1])
    qc.add_gate(Toffoli(), [2, 1, 0])   # reversed control/target order
    _assert_matches_qiskit(qc)
