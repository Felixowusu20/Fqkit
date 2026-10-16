"""Task 5 — density-matrix simulator and Kraus noise.

Run:
    pytest tests/test_density.py -v
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Hadamard,
    CNOT,
    X,
    run,
    run_density,
    to_density,
    Noise,
    purity,
    trace,
    entropy,
    is_physical,
    expectation,
    pauli,
    probabilities,
    measure_all,
)


ATOL = 1e-10


def bell_circuit():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    return qc


# --- pure-state agreement with statevector engine -------------------------

def test_run_density_matches_outer_product_of_run():
    qc = bell_circuit()
    rho = run_density(qc)
    psi = run(qc)
    assert np.allclose(rho, to_density(psi), atol=ATOL)
    assert is_physical(rho)
    assert purity(rho) == pytest.approx(1.0, abs=ATOL)
    assert trace(rho) == pytest.approx(1.0, abs=ATOL)
    assert entropy(rho) == pytest.approx(0.0, abs=1e-8)


def test_bell_expectations_match_on_density():
    rho = run_density(bell_circuit())
    assert expectation(rho, "ZZ") == pytest.approx(1.0, abs=ATOL)
    assert expectation(rho, "XX") == pytest.approx(1.0, abs=ATOL)
    assert expectation(rho, "YY") == pytest.approx(-1.0, abs=ATOL)


# --- Kraus noise is scientifically meaningful -----------------------------

def test_depolarizing_reduces_purity():
    qc = bell_circuit()
    pure = run_density(qc)
    noisy = run_density(qc, noise=Noise.depolarizing(0.2))
    assert is_physical(noisy)
    assert purity(noisy) < purity(pure) - 1e-6
    assert entropy(noisy) > entropy(pure) + 1e-6


def test_bit_flip_on_one_moves_probability():
    # |0> with bit-flip p=1 becomes |1>
    qc = QuantumCircuit(1)
    rho = run_density(qc, noise=Noise.bit_flip(1.0))
    assert probabilities(rho)["1"] == pytest.approx(1.0, abs=ATOL)


def test_phase_flip_preserves_z_populations():
    # Phase flip does not change Z-basis probabilities of |+>
    qc = QuantumCircuit(1)
    qc.add_gate(Hadamard(), [0])
    rho = run_density(qc, noise=Noise.phase_flip(0.4))
    probs = probabilities(rho)
    assert probs["0"] == pytest.approx(0.5, abs=1e-8)
    assert probs["1"] == pytest.approx(0.5, abs=1e-8)


def test_amplitude_damping_relaxes_toward_zero():
    qc = QuantumCircuit(1)
    qc.add_gate(X(), [0])  # |1>
    rho = run_density(qc, noise=Noise.amplitude_damping(1.0))
    assert probabilities(rho)["0"] == pytest.approx(1.0, abs=ATOL)
    assert expectation(rho, "Z") == pytest.approx(1.0, abs=ATOL)


def test_noise_every_gate_differs_from_end_only():
    qc = bell_circuit()
    end = run_density(qc, noise=Noise.depolarizing(0.05), noise_every_gate=False)
    each = run_density(qc, noise=Noise.depolarizing(0.05), noise_every_gate=True)
    # More opportunities to err when noise hits after every gate.
    assert purity(each) < purity(end) + 1e-12


def test_targeted_noise_qubits():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    # Noise only on qubit 1 (idle |0>) with bit_flip p=1 → that qubit becomes |1>
    rho = run_density(qc, noise=Noise.bit_flip(1.0, qubits=[1]))
    # State should be |+⟩⊗|1⟩ → outcomes 01 and 11 only.
    probs = probabilities(rho)
    assert probs["01"] + probs["11"] == pytest.approx(1.0, abs=ATOL)


# --- measurement from density --------------------------------------------

def test_measure_all_accepts_density_and_is_seeded():
    rho = run_density(bell_circuit())
    a = measure_all(rho, shots=500, seed=11)
    b = measure_all(rho, shots=500, seed=11)
    assert a.counts == b.counts
    assert set(a.counts) <= {"00", "11"}


# --- validation -----------------------------------------------------------

def test_noise_rejects_bad_probability():
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        Noise.depolarizing(1.5)


def test_is_physical_rejects_non_hermitian():
    bad = np.array([[1, 2], [0, 0]], dtype=complex)
    assert not is_physical(bad)
