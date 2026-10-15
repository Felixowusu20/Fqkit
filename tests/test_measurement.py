"""Task 2 — seeded measurement and MeasurementResult.

Run:
    pytest tests/test_measurement.py -v
"""

import numpy as np
import pytest

from fqkit import (
    QuantumCircuit,
    Hadamard,
    CNOT,
    run,
    measure_all,
    probabilities,
    MeasurementResult,
)


def bell_state():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    return run(qc)


# --- ideal probabilities (no sampling) ------------------------------------

def test_probabilities_bell_match_born_rule():
    probs = probabilities(bell_state())
    assert probs["00"] == pytest.approx(0.5, abs=1e-12)
    assert probs["11"] == pytest.approx(0.5, abs=1e-12)
    assert probs["01"] == pytest.approx(0.0, abs=1e-12)
    assert probs["10"] == pytest.approx(0.0, abs=1e-12)
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-12)


# --- reproducibility ------------------------------------------------------

def test_same_seed_reproduces_counts():
    state = bell_state()
    a = measure_all(state, shots=2048, seed=42)
    b = measure_all(state, shots=2048, seed=42)
    assert a.counts == b.counts
    assert a.seed == 42
    assert isinstance(a, MeasurementResult)


def test_different_seeds_can_differ():
    state = bell_state()
    a = measure_all(state, shots=512, seed=1)
    b = measure_all(state, shots=512, seed=2)
    # Extremely unlikely to match for 512 Bell shots; allow equality only if
    # TV still proves sampling ran (we mainly check seeds are stored).
    assert a.seed != b.seed
    assert a.shots == b.shots == 512


# --- scientific content of the result -------------------------------------

def test_result_ideal_and_empirical_and_tv():
    result = measure_all(bell_state(), shots=4000, seed=0)
    assert set(result.counts) <= {"00", "11"}
    assert sum(result.values()) == 4000
    assert result.ideal_probabilities["00"] == pytest.approx(0.5)
    assert result.ideal_probabilities["11"] == pytest.approx(0.5)
    # Empirical should be close to 1/2; TV should be small for 4000 shots.
    assert 1700 < result["00"] < 2300
    assert 1700 < result["11"] < 2300
    assert result.total_variation_distance() < 0.08
    assert result.state_norm == pytest.approx(1.0, abs=1e-10)
    assert result.renormalized is False


def test_result_is_dict_compatible():
    result = measure_all(bell_state(), shots=100, seed=3)
    assert dict(result) == result.counts
    assert "00" in result or "11" in result
    assert str(result) == str(result.counts)


def test_most_probable_is_a_seen_bitstring():
    result = measure_all(bell_state(), shots=200, seed=9)
    assert result.most_probable() in result.counts


# --- validation -----------------------------------------------------------

def test_rejects_non_power_of_two_state():
    with pytest.raises(ValueError, match="power of two"):
        measure_all([1, 0, 0], shots=10, seed=0)


def test_rejects_zero_norm_state():
    with pytest.raises(ValueError, match="zero norm"):
        measure_all([0, 0], shots=10, seed=0)


def test_rejects_badly_unnormalized_state():
    with pytest.raises(ValueError, match="not normalized"):
        measure_all([2, 0], shots=10, seed=0)


def test_rejects_invalid_shots():
    with pytest.raises(ValueError, match="shots"):
        measure_all(bell_state(), shots=0, seed=0)


def test_small_norm_drift_is_renormalized():
    # ‖ψ‖² off by ~1e-7 (above default atol=1e-8) — still safe to sample.
    state = bell_state() * np.sqrt(1.0 + 1e-7)
    result = measure_all(state, shots=50, seed=1)
    assert result.renormalized is True
    assert sum(result.values()) == 50
