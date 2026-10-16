"""VQE on FQkit: chemistry (PySCF) → Paulis (OpenFermion) → FQkit circuits.

Install the optional stack (no PennyLane / Qiskit Nature)::

    pip install fqkit[chemistry]

Quick start — full-molecule VQE
-------------------------------
    from fqkit.vqe import molecule_hamiltonian, run_vqe

    H, info = molecule_hamiltonian(
        [("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 0.74))],
        basis="sto-3g",
    )
    result = run_vqe(H)
    print(result.energy, info.fci_energy)

Embedded-VQE (one-shot DMET)
----------------------------
    from fqkit.vqe import run_embedded_vqe

    out = run_embedded_vqe(
        [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, 1.6))],
        fragment_atoms="H",
        run_fci=True,
    )
    print(out.energy, out.embedding.casci_energy, out.embedding.fci_energy)
"""

from fqkit.vqe.ansatz import hardware_efficient_ansatz
from fqkit.vqe.dmet import EmbeddingInfo, build_embedded_hamiltonian
from fqkit.vqe.embedded import EmbeddedVQEResult, run_embedded_vqe
from fqkit.vqe.molecule import MoleculeInfo, molecule_hamiltonian
from fqkit.vqe.optimize import VQEResult, run_vqe

__all__ = [
    "MoleculeInfo",
    "molecule_hamiltonian",
    "EmbeddingInfo",
    "build_embedded_hamiltonian",
    "hardware_efficient_ansatz",
    "VQEResult",
    "run_vqe",
    "EmbeddedVQEResult",
    "run_embedded_vqe",
]
