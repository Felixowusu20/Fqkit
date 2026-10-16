"""Scientific tests for one-shot DMET embedded-VQE."""

import numpy as np
import pytest

pytest.importorskip("scipy")

chemistry = pytest.mark.chemistry


def _dense_min_eig(H) -> float:
    pauli = {
        "I": np.eye(2, dtype=complex),
        "X": np.array([[0, 1], [1, 0]], dtype=complex),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
        "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    }

    def dense(label: str) -> np.ndarray:
        out = pauli[label[0]]
        for c in label[1:]:
            out = np.kron(out, pauli[c])
        return out

    mat = sum(coeff * dense(p.label) for p, coeff in H.terms)
    return float(np.min(np.linalg.eigvalsh(mat).real))


@chemistry
def test_dmet_h2_impurity_matches_fci():
    """H₂ / STO-3G with a one-atom fragment recovers the full FCI space."""
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import build_embedded_hamiltonian

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]
    H, info = build_embedded_hamiltonian(
        geometry,
        fragment_ao=[0],
        run_casci=True,
        run_fci=True,
    )
    assert info.n_cas == 2
    assert info.n_electrons_cas == 2
    assert info.n_qubits == 4
    assert info.n_bath >= 1  # environment AO becomes bath
    assert info.casci_energy == pytest.approx(info.fci_energy, abs=1e-8)
    assert _dense_min_eig(H) == pytest.approx(info.casci_energy, abs=1e-8)


@chemistry
def test_dmet_lih_matches_casci_and_beats_hf():
    """LiH H-fragment DMET impurity spectrum equals PySCF CASCI."""
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import build_embedded_hamiltonian

    geometry = [
        ("Li", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 1.6)),
    ]
    H, info = build_embedded_hamiltonian(
        geometry,
        fragment_atoms="H",
        run_casci=True,
        run_fci=True,
    )
    assert info.n_fragment_ao == 1
    assert info.n_cas == 2
    assert info.n_bath == 1
    assert info.n_qubits == 4
    # Mapping correctness: qubit H ground energy == CASCI impurity energy
    assert _dense_min_eig(H) == pytest.approx(info.casci_energy, abs=1e-8)
    # Physically recovers correlation beyond HF, near full FCI
    assert info.casci_energy < info.hf_energy - 1e-3
    assert info.casci_energy == pytest.approx(info.fci_energy, abs=5e-3)


@chemistry
def test_dmet_bath_size_bounded_by_fragment():
    """DMET theorem: number of entangled bath orbitals ≤ fragment size."""
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import build_embedded_hamiltonian

    geometry = [
        ("Li", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 1.6)),
    ]
    _, info = build_embedded_hamiltonian(
        geometry,
        fragment_atoms="H",
        run_casci=False,
        run_fci=False,
    )
    assert info.n_bath <= info.n_fragment_ao
    assert info.n_cas == info.n_fragment_ao + info.n_bath


@chemistry
def test_run_embedded_vqe_h2_near_fci():
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import run_embedded_vqe

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]
    out = run_embedded_vqe(
        geometry,
        fragment_ao=[0],
        run_casci=True,
        run_fci=True,
        layers=3,
        maxiter=400,
        seed=0,
    )
    assert out.embedding is not None
    assert out.energy < out.embedding.hf_energy + 1e-3
    assert out.energy == pytest.approx(out.embedding.fci_energy, abs=0.05)


@chemistry
def test_run_embedded_vqe_lih_near_casci():
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import run_embedded_vqe

    geometry = [
        ("Li", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 1.6)),
    ]
    out = run_embedded_vqe(
        geometry,
        fragment_atoms="H",
        run_casci=True,
        run_fci=False,
        layers=3,
        maxiter=400,
        seed=0,
    )
    assert out.embedding is not None
    assert out.embedding.casci_energy is not None
    assert out.energy < out.embedding.hf_energy + 1e-3
    assert out.energy == pytest.approx(out.embedding.casci_energy, abs=0.05)


@chemistry
def test_legacy_active_space_still_works():
    pytest.importorskip("pyscf")
    pytest.importorskip("openfermion")
    pytest.importorskip("openfermionpyscf")

    from fqkit.vqe import run_embedded_vqe

    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]
    out = run_embedded_vqe(
        geometry,
        occupied_indices=[0],
        active_indices=[0, 1],
        layers=2,
        maxiter=80,
        seed=0,
    )
    assert out.molecule is not None
    assert out.molecule.active
    assert out.hamiltonian.n == 4
    assert np.isfinite(out.energy)
