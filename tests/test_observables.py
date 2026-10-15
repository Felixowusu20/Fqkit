"""Task 3 — Pauli observables and expectation values.

Run:
    pytest tests/test_observables.py -v
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Hadamard,
    CNOT,
    X,
    run,
    pauli,
    Pauli,
    Hamiltonian,
    expectation,
)


ATOL = 1e-10


def bell_state():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    return run(qc)


# --- Bell-state analytics (research sanity checks) ------------------------

def test_bell_zz_is_plus_one():
    assert expectation(bell_state(), pauli("ZZ")) == pytest.approx(1.0, abs=ATOL)


def test_bell_xx_is_plus_one():
    assert expectation(bell_state(), "XX") == pytest.approx(1.0, abs=ATOL)


def test_bell_yy_is_minus_one():
    assert expectation(bell_state(), pauli("YY")) == pytest.approx(-1.0, abs=ATOL)


def test_bell_zi_and_iz_are_zero():
    state = bell_state()
    assert expectation(state, "ZI") == pytest.approx(0.0, abs=ATOL)
    assert expectation(state, "IZ") == pytest.approx(0.0, abs=ATOL)


# --- single-qubit Paulis --------------------------------------------------

def test_z_on_zero_and_one():
    zero = run(QuantumCircuit(1))
    assert expectation(zero, "Z") == pytest.approx(1.0, abs=ATOL)

    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])
    one = run(qc)
    assert expectation(one, pauli("Z")) == pytest.approx(-1.0, abs=ATOL)


def test_identity_expectation_is_one():
    assert expectation(bell_state(), "II") == pytest.approx(1.0, abs=ATOL)


# --- Hamiltonian (VQE-style energy) ---------------------------------------

def test_hamiltonian_linear_combination():
    state = bell_state()
    # ⟨0.5 ZZ + 0.25 XX⟩ = 0.5(1) + 0.25(1) = 0.75
    H = Hamiltonian(("ZZ", 0.5), ("XX", 0.25))
    assert expectation(state, H) == pytest.approx(0.75, abs=ATOL)


def test_hamiltonian_from_algebra():
    state = bell_state()
    H = 0.5 * pauli("ZZ") + 0.25 * pauli("XX")
    assert isinstance(H, Hamiltonian)
    assert expectation(state, H) == pytest.approx(0.75, abs=ATOL)


def test_tensor_product_with_matmul():
    zz = pauli("Z") @ pauli("Z")
    assert zz == Pauli("ZZ")
    assert expectation(bell_state(), zz) == pytest.approx(1.0, abs=ATOL)


# --- validation -----------------------------------------------------------

def test_rejects_bad_pauli_letter():
    with pytest.raises(ValueError, match="Invalid Pauli"):
        pauli("ZA")


def test_rejects_qubit_mismatch():
    with pytest.raises(ValueError, match="qubit"):
        expectation(bell_state(), "Z")


def test_rejects_mixed_term_widths():
    with pytest.raises(ValueError, match="same number of qubits"):
        Hamiltonian(("Z", 1.0), ("ZZ", 1.0))


def test_pauli_repr_is_readable():
    assert repr(pauli("XY")) == 'pauli("XY")'
