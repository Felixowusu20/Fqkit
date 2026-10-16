"""Build FQkit Hamiltonians from molecular geometry (PySCF + OpenFermion)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from fqkit.core.observables import Hamiltonian
from fqkit.vqe._deps import require_chemistry

Geometry = Sequence[Tuple[str, Tuple[float, float, float]]]


@dataclass(frozen=True)
class MoleculeInfo:
    """Metadata returned with a mapped molecular Hamiltonian."""

    n_qubits: int
    n_electrons: int
    basis: str
    charge: int
    multiplicity: int
    hf_energy: Optional[float] = None
    fci_energy: Optional[float] = None
    n_terms: int = 0
    active: bool = False


def qubit_operator_to_hamiltonian(qubit_op, n_qubits: int) -> Hamiltonian:
    """
    Convert an OpenFermion ``QubitOperator`` into an FQkit ``Hamiltonian``.

    OpenFermion qubit index ``0`` becomes the **leftmost** Pauli letter, matching
    FQkit's qubit-0 = MSB convention.
    """
    terms = []
    for op, coeff in qubit_op.terms.items():
        label = ["I"] * n_qubits
        for index, pauli in op:
            if index < 0 or index >= n_qubits:
                raise ValueError(
                    f"Pauli acts on qubit {index}, but n_qubits={n_qubits}."
                )
            label[index] = pauli
        terms.append(("".join(label), complex(coeff)))
    if not terms:
        raise ValueError("QubitOperator has no terms.")
    return Hamiltonian(*terms)


def molecule_hamiltonian(
    geometry: Geometry,
    *,
    basis: str = "sto-3g",
    charge: int = 0,
    multiplicity: int = 1,
    run_fci: bool = True,
    occupied_indices: Optional[Sequence[int]] = None,
    active_indices: Optional[Sequence[int]] = None,
) -> tuple[Hamiltonian, MoleculeInfo]:
    """
    Map a molecule to an FQkit Pauli Hamiltonian.

    Pipeline: **PySCF** (integrals) → **OpenFermion** (fermions) →
    Jordan–Wigner → :class:`~fqkit.Hamiltonian`.

    Parameters
    ----------
    geometry
        List of ``(element, (x, y, z))`` with coordinates in Ångström.
    basis
        Gaussian basis name (e.g. ``\"sto-3g\"``, ``\"6-31g\"``).
    charge, multiplicity
        Molecular charge and spin multiplicity.
    run_fci
        If True, also compute the FCI energy (small systems only) for reference.
    occupied_indices, active_indices
        Optional active-space selection (OpenFermion). When set, the returned
        Hamiltonian acts on the active orbitals only — the first step toward
        embedded / fragment VQE.

    Returns
    -------
    hamiltonian : Hamiltonian
        Qubit operator ready for :func:`fqkit.expectation` / :func:`run_vqe`.
    info : MoleculeInfo
        Sizes and reference energies.
    """
    chem = require_chemistry()
    MolecularData = chem["MolecularData"]
    run_pyscf = chem["run_pyscf"]
    get_fermion_operator = chem["get_fermion_operator"]
    jordan_wigner = chem["jordan_wigner"]

    geometry = [(str(atom), tuple(float(x) for x in xyz)) for atom, xyz in geometry]

    molecule = MolecularData(
        geometry=geometry,
        basis=basis,
        multiplicity=int(multiplicity),
        charge=int(charge),
    )
    molecule = run_pyscf(
        molecule,
        run_scf=True,
        run_mp2=False,
        run_cisd=False,
        run_ccsd=False,
        run_fci=bool(run_fci),
    )

    active = occupied_indices is not None or active_indices is not None
    if active:
        if occupied_indices is None or active_indices is None:
            raise ValueError(
                "Active-space mapping requires both occupied_indices and "
                "active_indices."
            )
        molecular_hamiltonian = molecule.get_molecular_hamiltonian(
            occupied_indices=list(occupied_indices),
            active_indices=list(active_indices),
        )
        n_qubits = 2 * len(active_indices)
    else:
        molecular_hamiltonian = molecule.get_molecular_hamiltonian()
        n_qubits = molecule.n_qubits

    fermion_op = get_fermion_operator(molecular_hamiltonian)
    qubit_op = jordan_wigner(fermion_op)
    hamiltonian = qubit_operator_to_hamiltonian(qubit_op, n_qubits)

    info = MoleculeInfo(
        n_qubits=n_qubits,
        n_electrons=int(molecule.n_electrons),
        basis=basis,
        charge=int(charge),
        multiplicity=int(multiplicity),
        hf_energy=None if molecule.hf_energy is None else float(molecule.hf_energy),
        fci_energy=None if molecule.fci_energy is None else float(molecule.fci_energy),
        n_terms=len(hamiltonian.terms),
        active=active,
    )
    return hamiltonian, info
