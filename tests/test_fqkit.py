"""Test suite for FQkit.

Run with:  python -m pytest   (from the repository root)
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Qubit,
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
    measure_all,
)


def probs(state):
    """Measurement probabilities |amplitude|^2."""
    return np.abs(state) ** 2


# --- single-qubit gates ---------------------------------------------------

def test_hadamard_single_qubit():
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    state = run(qc)
    assert np.allclose(state, np.array([1, 1]) / np.sqrt(2))


def test_ry_pi_prepares_one():
    qc = QuantumCircuit(1)
    qc.add_gate(RY(np.pi), [0])
    assert np.allclose(probs(run(qc)), [0, 1])


def test_rz_phase():
    qc = QuantumCircuit(1)
    qc.add_gate(RY(np.pi), [0])   # |1>
    qc.add_gate(RZ(np.pi), [0])   # RZ(pi)|1> = i|1>
    assert np.allclose(run(qc), [0, 1j])


# --- multi-qubit gates (the previously-broken path) -----------------------

def test_bell_state():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    expected = np.array([1, 0, 0, 1]) / np.sqrt(2)
    assert np.allclose(run(qc), expected)


def test_bell_state_reversed_control():
    # CNOT with the control on qubit 1 and target on qubit 0.
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [1])
    qc.add_gate(CNOT(), [1, 0])
    expected = np.array([1, 0, 0, 1]) / np.sqrt(2)
    assert np.allclose(run(qc), expected)


def test_cnot_flips_target_when_control_set():
    qc = QuantumCircuit(2)
    qc.add_gate(RY(np.pi), [0])   # q0 -> |1>
    qc.add_gate(CNOT(), [0, 1])   # flip q1
    assert np.allclose(probs(run(qc)), [0, 0, 0, 1])   # |11>


def test_cnot_no_flip_when_control_zero():
    qc = QuantumCircuit(2)
    qc.add_gate(CNOT(), [0, 1])
    assert np.allclose(probs(run(qc)), [1, 0, 0, 0])   # stays |00>


def test_cz_phase():
    qc = QuantumCircuit(2)
    qc.add_gate(RY(np.pi), [0])   # q0 -> |1>
    qc.add_gate(RY(np.pi), [1])   # q1 -> |1>
    qc.add_gate(CZ(), [0, 1])     # |11> -> -|11>
    assert np.allclose(run(qc), [0, 0, 0, -1])


def test_swap():
    qc = QuantumCircuit(2)
    qc.add_gate(RY(np.pi), [0])   # |10>
    qc.add_gate(SWAP(), [0, 1])   # -> |01>
    assert np.allclose(probs(run(qc)), [0, 1, 0, 0])


def test_toffoli_flips_when_both_controls_set():
    qc = QuantumCircuit(3)
    qc.add_gate(RY(np.pi), [0])
    qc.add_gate(RY(np.pi), [1])
    qc.add_gate(Toffoli(), [0, 1, 2])
    assert np.allclose(probs(run(qc)), np.eye(8)[7])   # |110> -> |111>


def test_toffoli_no_flip_with_one_control():
    qc = QuantumCircuit(3)
    qc.add_gate(RY(np.pi), [0])   # only q0 = 1
    qc.add_gate(Toffoli(), [0, 1, 2])
    assert np.allclose(probs(run(qc)), np.eye(8)[4])   # stays |100>


def test_three_qubit_cnot_on_non_adjacent_qubits():
    # Entangle q0 and q2 (skipping q1) to exercise arbitrary target ordering.
    qc = QuantumCircuit(3)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 2])
    state = run(qc)
    # (|000> + |101>)/sqrt(2)  -> indices 0 and 5
    expected = np.zeros(8, dtype=complex)
    expected[0] = expected[5] = 1 / np.sqrt(2)
    assert np.allclose(state, expected)


# --- parameters and binding ----------------------------------------------

def test_parameter_binding_rx():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RX(theta), [0])
    bind_parameters(qc, {"theta": np.pi})
    assert np.allclose(probs(run(qc)), [0, 1])   # RX(pi)|0> = -i|1>


def test_unbound_parameter_raises_clear_error():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RX(theta), [0])
    with pytest.raises(ValueError, match="unbound parameter"):
        run(qc)


# --- measurement ----------------------------------------------------------

def test_measure_all_bell_distribution():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    counts = measure_all(run(qc), shots=4000)
    assert set(counts) == {"00", "11"}
    assert sum(counts.values()) == 4000
    assert 1700 < counts["00"] < 2300   # roughly 50/50


# --- Qubit objects accepted as targets ------------------------------------

def test_qubit_objects_accepted():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [Qubit(0)])
    qc.add_gate(CNOT(), [Qubit(0), Qubit(1)])
    assert np.allclose(run(qc), np.array([1, 0, 0, 1]) / np.sqrt(2))


# --- validation -----------------------------------------------------------

def test_wrong_qubit_count():
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError):
        qc.add_gate(CNOT(), [0])


def test_index_out_of_range():
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError):
        qc.add_gate(Hadamard(), [5])


def test_negative_index():
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError):
        qc.add_gate(Hadamard(), [-1])


def test_duplicate_target_qubits():
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError):
        qc.add_gate(CNOT(), [0, 0])


def test_zero_qubits_invalid():
    with pytest.raises(ValueError):
        QuantumCircuit(0)
