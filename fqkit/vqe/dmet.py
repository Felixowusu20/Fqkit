"""One-shot interacting-bath DMET → FQkit Pauli Hamiltonian.

Scientific path (standard quantum-chemistry DMET)::

1. RHF mean-field (PySCF) supplies the low-level 1-RDM.
2. Fragment AOs are chosen (atom labels or AO indices).
3. Bath orbitals are built from the environment block of the
   orthogonalized 1-RDM (Schmidt / DMET construction —
   ``pyscf.mcscf.dmet_cas``, Ref. arXiv:1701.07862).
4. The impurity Hamiltonian is the CAS Hamiltonian on
   fragment ⊕ bath with a frozen mean-field core
   (interacting-bath embedding).
5. Spatial integrals → OpenFermion spin-orbitals → Jordan–Wigner
   → :class:`~fqkit.Hamiltonian`.

Exact diagonalization of the mapped qubit ``H`` reproduces the
PySCF CASCI impurity energy (tested). Full-system FCI is recovered
when the fragment+bath spans the whole orbital space (e.g. H₂ with
a one-atom fragment in STO-3G).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple, Union

import numpy as np

from fqkit.core.observables import Hamiltonian
from fqkit.vqe._deps import require_chemistry
from fqkit.vqe.molecule import Geometry, qubit_operator_to_hamiltonian

FragmentSpec = Union[Sequence[str], Sequence[int], str, int]


@dataclass(frozen=True)
class EmbeddingInfo:
    """Metadata for a DMET / active-space embedding."""

    n_qubits: int
    n_cas: int
    n_electrons_cas: int
    n_fragment_ao: int
    n_bath: int
    fragment_ao: Tuple[int, ...]
    basis: str
    charge: int
    multiplicity: int
    hf_energy: float
    casci_energy: Optional[float] = None
    fci_energy: Optional[float] = None
    n_terms: int = 0
    method: str = "dmet-cas"


def _geometry_to_atom_string(geometry: Geometry) -> str:
    lines = []
    for element, xyz in geometry:
        x, y, z = xyz
        lines.append(f"{element} {x} {y} {z}")
    return "; ".join(lines)


def _resolve_fragment_ao(mol, fragment_atoms=None, fragment_ao=None) -> np.ndarray:
    if fragment_ao is not None and fragment_atoms is not None:
        raise ValueError("Pass only one of fragment_atoms or fragment_ao.")
    if fragment_ao is not None:
        bas = np.asarray(list(fragment_ao), dtype=int).reshape(-1)
    elif fragment_atoms is not None:
        if isinstance(fragment_atoms, (str, int)):
            labels = [str(fragment_atoms)]
        else:
            labels = [str(x) for x in fragment_atoms]
        bas = np.asarray(mol.search_ao_label(labels), dtype=int).reshape(-1)
    else:
        raise ValueError("Provide fragment_atoms (e.g. ['H']) or fragment_ao indices.")
    if bas.size == 0:
        raise ValueError(
            "Fragment selection matched no AOs. Check atom labels / AO indices."
        )
    if np.any(bas < 0) or np.any(bas >= mol.nao):
        raise ValueError(f"AO indices out of range for nao={mol.nao}: {bas.tolist()}")
    return np.unique(bas)


def _dmet_cas_orbitals(mf, fragment_ao: np.ndarray, *, threshold: float = 0.05):
    """Return ``(ncas, nelecas, mo_coeff)`` via PySCF DMET-CAS."""
    from pyscf.mcscf import dmet_cas

    # Full-system fragment: no environment → bath construction is undefined.
    if fragment_ao.size == mf.mol.nao:
        ncas = int(mf.mol.nao)
        nelecas = int(mf.mol.nelectron)
        return ncas, nelecas, np.asarray(mf.mo_coeff, dtype=float)

    return dmet_cas.guess_cas(
        mf,
        mf.make_rdm1(),
        fragment_ao,
        threshold=float(threshold),
    )


def _cas_to_interaction_operator(mf, ncas: int, nelecas: int, mo):
    """Build OpenFermion InteractionOperator for the CAS impurity."""
    from pyscf import ao2mo, mcscf
    from openfermion import InteractionOperator
    from openfermion.chem.molecular_data import spinorb_from_spatial

    mc = mcscf.CASCI(mf, ncas, nelecas)
    mc.mo_coeff = mo
    h1eff, ecore = mc.get_h1eff(mo)
    eri = ao2mo.restore(1, mc.get_h2eff(mo), ncas)
    # OpenFermion stores h[p,q,r,s] = (ps|qr) (chemist → OF transpose).
    eri_of = np.asarray(eri.transpose(0, 2, 3, 1), order="C")
    h1, h2 = spinorb_from_spatial(np.asarray(h1eff, float), eri_of)
    return InteractionOperator(float(ecore), h1, 0.5 * h2), mc


def build_embedded_hamiltonian(
    geometry: Geometry,
    *,
    fragment_atoms: Optional[FragmentSpec] = None,
    fragment_ao: Optional[Sequence[int]] = None,
    basis: str = "sto-3g",
    charge: int = 0,
    multiplicity: int = 1,
    bath_threshold: float = 0.05,
    run_casci: bool = True,
    run_fci: bool = False,
) -> Tuple[Hamiltonian, EmbeddingInfo]:
    """
    Construct a one-shot DMET impurity Hamiltonian as an FQkit Pauli sum.

    Parameters
    ----------
    geometry
        ``(element, (x, y, z))`` list in Ångström.
    fragment_atoms
        Atom label(s) defining the impurity (e.g. ``\"H\"`` or ``[\"H\"]``).
    fragment_ao
        Explicit 0-based AO indices for the fragment (alternative to atoms).
    bath_threshold
        DMET entanglement cutoff passed to ``pyscf.mcscf.dmet_cas``.
    run_casci
        If True, store the exact CASCI impurity energy for validation.
    run_fci
        If True, also compute full-system FCI (small molecules only).

    Returns
    -------
    hamiltonian, info
        Qubit Hamiltonian on ``2 * n_cas`` qubits and embedding metadata.
    """
    require_chemistry()
    from pyscf import gto, scf, fci
    from openfermion import get_fermion_operator, jordan_wigner

    geometry = [(str(atom), tuple(float(x) for x in xyz)) for atom, xyz in geometry]
    mol = gto.M(
        atom=_geometry_to_atom_string(geometry),
        basis=basis,
        charge=int(charge),
        spin=int(multiplicity) - 1,
        unit="Angstrom",
        verbose=0,
    )
    mf = scf.RHF(mol).run()
    hf_energy = float(mf.e_tot)

    frag = _resolve_fragment_ao(mol, fragment_atoms=fragment_atoms, fragment_ao=fragment_ao)
    ncas, nelecas, mo = _dmet_cas_orbitals(mf, frag, threshold=bath_threshold)
    ncas = int(ncas)
    nelecas = int(nelecas)
    n_imp = int(frag.size)
    n_bath = max(ncas - n_imp, 0)

    interaction_op, mc = _cas_to_interaction_operator(mf, ncas, nelecas, mo)
    fermion_op = get_fermion_operator(interaction_op)
    qubit_op = jordan_wigner(fermion_op)
    n_qubits = 2 * ncas
    hamiltonian = qubit_operator_to_hamiltonian(qubit_op, n_qubits)

    casci_energy = None
    if run_casci:
        casci_energy = float(mc.kernel()[0])

    fci_energy = None
    if run_fci:
        fci_energy = float(fci.FCI(mf).kernel()[0])

    info = EmbeddingInfo(
        n_qubits=n_qubits,
        n_cas=ncas,
        n_electrons_cas=nelecas,
        n_fragment_ao=n_imp,
        n_bath=n_bath,
        fragment_ao=tuple(int(i) for i in frag.tolist()),
        basis=basis,
        charge=int(charge),
        multiplicity=int(multiplicity),
        hf_energy=hf_energy,
        casci_energy=casci_energy,
        fci_energy=fci_energy,
        n_terms=len(hamiltonian.terms),
        method="dmet-cas",
    )
    return hamiltonian, info
