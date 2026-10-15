"""Task 4 — scientifically meaningful circuit equivalence.

Equivalence is checked on **all** computational-basis inputs (unitary check),
not only |0...0>.

Run:
    pytest tests/test_equivalence.py -v
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Identity,
    Hadamard,
    X,
    Y,
    Z,
    S,
    T,
    CNOT,
    CZ,
    SWAP,
    run,
    fidelity,
    states_equivalent,
    circuits_equivalent,
)


# --- pure-state fidelity --------------------------------------------------

def test_fidelity_identical_states_is_one():
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    state = run(qc)
    assert fidelity(state, state) == pytest.approx(1.0)


def test_fidelity_orthogonal_states_is_zero():
    zero = run(QuantumCircuit(1))
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    one = run(qc)
    assert fidelity(zero, one) == pytest.approx(0.0)


def test_states_equivalent_allows_global_phase():
    psi = np.array([1, 0], dtype=complex)
    phi = np.array([1j, 0], dtype=complex)  # e^{iπ/2} |0>
    assert states_equivalent(psi, phi, phase=True)
    assert not states_equivalent(psi, phi, phase=False)


# --- gate identities (real algebraic relations) ---------------------------

def test_hh_equals_identity():
    """H·H = I on one qubit."""
    a = QuantumCircuit(1)
    a.add_gate(Hadamard(), [0])
    a.add_gate(Hadamard(), [0])

    b = QuantumCircuit(1)
    b.add_gate(Identity(), [0])

    assert circuits_equivalent(a, b)
    assert circuits_equivalent(a, QuantumCircuit(1))  # empty ≡ I


def test_xx_yy_zz_are_identity():
    for gate in (X, Y, Z):
        a = QuantumCircuit(1)
        a.add_gate(gate(), [0])
        a.add_gate(gate(), [0])
        assert circuits_equivalent(a, QuantumCircuit(1)), gate.__name__


def test_cnot_twice_is_identity():
    a = QuantumCircuit(2)
    a.add_gate(CNOT(), [0, 1])
    a.add_gate(CNOT(), [0, 1])
    assert circuits_equivalent(a, QuantumCircuit(2))


def test_swap_twice_is_identity():
    a = QuantumCircuit(2)
    a.add_gate(SWAP(), [0, 1])
    a.add_gate(SWAP(), [0, 1])
    assert circuits_equivalent(a, QuantumCircuit(2))


def test_cz_twice_is_identity():
    a = QuantumCircuit(2)
    a.add_gate(CZ(), [0, 1])
    a.add_gate(CZ(), [0, 1])
    assert circuits_equivalent(a, QuantumCircuit(2))


def test_ss_equals_z():
    """S·S = Z."""
    a = QuantumCircuit(1)
    a.add_gate(S(), [0])
    a.add_gate(S(), [0])

    b = QuantumCircuit(1)
    b.add_gate(Z(), [0])

    assert circuits_equivalent(a, b)


def test_tt_equals_s():
    """T·T = S."""
    a = QuantumCircuit(1)
    a.add_gate(T(), [0])
    a.add_gate(T(), [0])

    b = QuantumCircuit(1)
    b.add_gate(S(), [0])

    assert circuits_equivalent(a, b)


# --- negative controls (must NOT be equivalent) ---------------------------

def test_hadamard_not_equivalent_to_identity():
    a = QuantumCircuit(1)
    a.add_gate(Hadamard(), [0])
    assert not circuits_equivalent(a, QuantumCircuit(1))


def test_cnot_not_equivalent_to_empty():
    a = QuantumCircuit(2)
    a.add_gate(CNOT(), [0, 1])
    assert not circuits_equivalent(a, QuantumCircuit(2))


def test_bell_not_equivalent_to_product_hadamards():
    """Entangling circuit ≠ H⊗H."""
    bell = QuantumCircuit(2)
    bell.add_gate(Hadamard(), [0])
    bell.add_gate(CNOT(), [0, 1])

    product = QuantumCircuit(2)
    product.add_gate(Hadamard(), [0])
    product.add_gate(Hadamard(), [1])

    assert not circuits_equivalent(bell, product)


def test_z_agrees_with_identity_on_zero_but_not_as_unitary():
    """Classic trap: Z|0>=|0>, so |0>-only checks would wrongly say Z≡I."""
    z_circuit = QuantumCircuit(1)
    z_circuit.add_gate(Z(), [0])

    # Same output from |0>, but not the same unitary.
    assert states_equivalent(run(z_circuit), run(QuantumCircuit(1)))
    assert not circuits_equivalent(z_circuit, QuantumCircuit(1))


# --- API validation -------------------------------------------------------

def test_circuits_equivalent_rejects_width_mismatch():
    with pytest.raises(ValueError, match="same number of qubits"):
        circuits_equivalent(QuantumCircuit(1), QuantumCircuit(2))


def test_run_with_custom_initial_state():
    """Equivalence engine relies on run(circuit, state=...)."""
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    one = np.array([0, 1], dtype=complex)
    # X|1> = |0>
    assert np.allclose(run(qc, one), [1, 0])
