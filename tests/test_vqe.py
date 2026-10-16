"""VQE on FQkit (SciPy loop). Chemistry-stack tests skip if extras missing."""

import numpy as np
import pytest

from fqkit import Hamiltonian, RY, Parameter, QuantumCircuit

pytest.importorskip("scipy")


def test_hamiltonian_accepts_single_term_pair():
    H = Hamiltonian(("Z", 1.0))
    assert H.n == 1
    assert len(H.terms) == 1


def test_run_vqe_minimizes_single_qubit_z():
    """⟨Z⟩ on RY(θ)|0⟩ is cos(θ); minimum −1 at θ = π."""
    from fqkit.vqe import run_vqe

    H = Hamiltonian(("Z", 1.0))
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RY(theta), [0])

    result = run_vqe(
        H,
        circuit=qc,
        param_names=["theta"],
        x0=[0.2],
        maxiter=80,
        method="COBYLA",
        seed=0,
    )
    assert result.energy == pytest.approx(-1.0, abs=2e-2)
    assert result.n_qubits == 1


def test_energy_from_params_matches_manual_expectation():
    from fqkit.vqe.optimize import energy_from_params

    H = Hamiltonian(("Z", 1.0))
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RY(theta), [0])
    e = energy_from_params(qc, ["theta"], H, [np.pi])
    assert e == pytest.approx(-1.0, abs=1e-10)


@pytest.mark.chemistry
def test_molecule_hamiltonian_h2_spectrum_matches_fci():
    """OpenFermion JW → FQkit H must reproduce the FCI ground energy exactly."""
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import molecule_hamiltonian

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]
    H, info = molecule_hamiltonian(geometry, basis="sto-3g", run_fci=True)
    assert info.n_qubits == 4
    assert info.fci_energy is not None
    assert info.n_terms > 1

    pauli = {
        "I": np.eye(2, dtype=complex),
        "X": np.array([[0, 1], [1, 0]], dtype=complex),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
        "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    }

    def dense(label: str) -> np.ndarray:
        mats = [pauli[c] for c in label]
        out = mats[0]
        for m in mats[1:]:
            out = np.kron(out, m)
        return out

    mat = sum(coeff * dense(p.label) for p, coeff in H.terms)
    e_min = float(np.min(np.linalg.eigvalsh(mat).real))
    assert e_min == pytest.approx(info.fci_energy, abs=1e-6)


@pytest.mark.chemistry
def test_run_vqe_h2_near_fci():
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import molecule_hamiltonian, run_vqe

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]
    H, info = molecule_hamiltonian(geometry, basis="sto-3g", run_fci=True)
    result = run_vqe(H, layers=3, maxiter=400, seed=0, method="COBYLA")
    assert result.energy < info.hf_energy + 1e-3
    assert result.energy == pytest.approx(info.fci_energy, abs=0.05)


# Embedded-VQE scientific tests live in tests/test_embedded_vqe.py
