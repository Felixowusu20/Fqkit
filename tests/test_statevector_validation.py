"""Task 1 — statevector validation.

These tests answer: do our gates and apply_gate follow the math?

Run from the repo root:
    pytest tests/test_statevector_validation.py -v
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Gate,
    Identity,
    Hadamard,
    X,
    Y,
    Z,
    S,
    T,
    RX,
    RY,
    RZ,
    CNOT,
    CZ,
    SWAP,
    Toffoli,
    run,
    apply_gate,
)
from fqkit.core.simulator import _gate_matrix

# Analytical comparisons use this tight tolerance.
ATOL = 1e-10


def norm(state):
    """‖ψ‖ = sqrt(sum |amp|²). A valid state should be ~1."""
    return np.linalg.norm(state)


def is_unitary(matrix, atol=1e-8):
    """True if U†U ≈ I."""
    U = np.asarray(matrix, dtype=complex)
    n = U.shape[0]
    return np.allclose(U.conj().T @ U, np.eye(n), atol=atol)


# --- 1. Every built-in gate matrix is unitary -----------------------------

# Fixed (non-parameterized) gates: use their stored matrix.
FIXED_GATES = [
    Identity(),
    Hadamard(),
    X(),
    Y(),
    Z(),
    S(),
    T(),
    CNOT(),
    CZ(),
    SWAP(),
    Toffoli(),
]

# Parameterized gates: build the numeric matrix at a concrete angle.
PARAMETERIZED_GATES = [
    RX(0.3),
    RY(-1.2),
    RZ(np.pi / 5),
]


@pytest.mark.parametrize("gate", FIXED_GATES, ids=lambda g: g.name)
def test_fixed_gate_matrix_is_unitary(gate):
    assert is_unitary(gate.matrix)


@pytest.mark.parametrize("gate", PARAMETERIZED_GATES, ids=lambda g: g.name)
def test_parameterized_gate_matrix_is_unitary(gate):
    assert is_unitary(_gate_matrix(gate))


# --- 2. Known analytical states ------------------------------------------

def test_hadamard_prepares_plus():
    """H|0> = |+> = (|0> + |1>)/√2."""
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    expected = np.array([1, 1], dtype=complex) / np.sqrt(2)
    assert np.allclose(run(qc), expected, atol=ATOL)


def test_x_flips_zero_to_one():
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    assert np.allclose(run(qc), [0, 1], atol=ATOL)


def test_z_on_one_adds_minus_sign():
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])  # |1>
    qc.add_gate(Z(), [0])  # -|1>
    assert np.allclose(run(qc), [0, -1], atol=ATOL)


def test_y_on_zero():
    """Y|0> = i|1>."""
    qc = QuantumCircuit(1)
    qc.add_gate(Y(), [0])
    assert np.allclose(run(qc), [0, 1j], atol=ATOL)


def test_s_on_one():
    """S|1> = i|1>."""
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    qc.add_gate(S(), [0])
    assert np.allclose(run(qc), [0, 1j], atol=ATOL)


def test_t_on_one():
    """T|1> = exp(i π/4)|1>."""
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    qc.add_gate(T(), [0])
    expected = np.array([0, np.exp(1j * np.pi / 4)], dtype=complex)
    assert np.allclose(run(qc), expected, atol=ATOL)


def test_identity_leaves_state_unchanged():
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(Identity(), [0])
    expected = np.array([1, 1], dtype=complex) / np.sqrt(2)
    assert np.allclose(run(qc), expected, atol=ATOL)


def test_bell_state_analytical():
    """|Φ+> = (|00> + |11>)/√2."""
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    expected = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    state = run(qc)
    assert np.allclose(state, expected, atol=ATOL)
    assert abs(norm(state) - 1.0) < ATOL


def test_ghz3_analytical():
    """GHZ-3 = (|000> + |111>)/√2."""
    qc = QuantumCircuit(3)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    qc.add_gate(CNOT(), [0, 2])
    expected = np.zeros(8, dtype=complex)
    expected[0] = expected[7] = 1 / np.sqrt(2)
    state = run(qc)
    assert np.allclose(state, expected, atol=ATOL)
    assert abs(norm(state) - 1.0) < ATOL


# --- 3. Norm stays 1 after a longer circuit -------------------------------

def test_norm_preserved_on_small_deep_circuit():
    qc = QuantumCircuit(3)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(X(), [1])
    qc.add_gate(CNOT(), [0, 2])
    qc.add_gate(T(), [0])
    qc.add_gate(S(), [1])
    qc.add_gate(CZ(), [1, 2])
    qc.add_gate(SWAP(), [0, 1])
    qc.add_gate(Hadamard(), [2])
    state = run(qc)
    assert abs(norm(state) - 1.0) < ATOL


# --- 4. apply_gate contract checks ---------------------------------------

def test_apply_gate_rejects_wrong_state_length():
    bad_state = np.array([1, 0, 0], dtype=complex)  # not a power-of-two length for n=2
    with pytest.raises(ValueError, match="State vector length"):
        apply_gate(bad_state, Hadamard().matrix, num_qubits=2, target_qubits=[0])


def test_apply_gate_rejects_wrong_matrix_shape():
    state = np.array([1, 0, 0, 0], dtype=complex)
    # 2x2 matrix cannot act on two target qubits (needs 4x4).
    with pytest.raises(ValueError, match="shape"):
        apply_gate(state, Hadamard().matrix, num_qubits=2, target_qubits=[0, 1])


def test_apply_gate_rejects_non_unitary_matrix():
    state = np.array([1, 0], dtype=complex)
    not_unitary = [[1, 1], [0, 1]]  # upper-triangular, not unitary
    with pytest.raises(ValueError, match="not unitary"):
        apply_gate(state, not_unitary, num_qubits=1, target_qubits=[0])


def test_custom_unitary_gate_still_works():
    """A well-formed custom Gate should still simulate."""
    # Phase gate diag(1, -i) is unitary.
    custom = Gate(name="CustomPhase", num_qubits=1, matrix=[[1, 0], [0, -1j]])
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    qc.add_gate(custom, [0])
    assert np.allclose(run(qc), [0, -1j], atol=ATOL)
