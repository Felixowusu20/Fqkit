"""Embedded-VQE: one-shot DMET impurity solved with FQkit VQE.

Primary path
------------
:func:`run_embedded_vqe` builds a DMET fragment⊕bath Hamiltonian
(:func:`fqkit.vqe.dmet.build_embedded_hamiltonian`) and minimizes it
with :func:`run_vqe`.

Legacy active-space path
------------------------
Passing ``occupied_indices`` + ``active_indices`` still uses OpenFermion's
frozen-core active-space mapping (no DMET bath). Prefer the DMET API for
correlated / larger molecules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from fqkit.core.observables import Hamiltonian
from fqkit.vqe.dmet import EmbeddingInfo, FragmentSpec, build_embedded_hamiltonian
from fqkit.vqe.molecule import Geometry, MoleculeInfo, molecule_hamiltonian
from fqkit.vqe.optimize import VQEResult, run_vqe


@dataclass(frozen=True)
class EmbeddedVQEResult:
    """VQE on an embedded impurity, with classical references."""

    vqe: VQEResult
    hamiltonian: Hamiltonian
    embedding: Optional[EmbeddingInfo] = None
    molecule: Optional[MoleculeInfo] = None

    @property
    def energy(self) -> float:
        return self.vqe.energy


def run_embedded_vqe(
    geometry: Geometry,
    *,
    fragment_atoms: Optional[FragmentSpec] = None,
    fragment_ao: Optional[Sequence[int]] = None,
    occupied_indices: Optional[Sequence[int]] = None,
    active_indices: Optional[Sequence[int]] = None,
    basis: str = "sto-3g",
    charge: int = 0,
    multiplicity: int = 1,
    bath_threshold: float = 0.05,
    run_casci: bool = True,
    run_fci: bool = False,
    layers: int = 3,
    maxiter: int = 400,
    seed: Optional[int] = 0,
    method: str = "COBYLA",
) -> EmbeddedVQEResult:
    """
    Embedded VQE on a molecular fragment.

    **DMET mode** (recommended): pass ``fragment_atoms`` or ``fragment_ao``.
    Builds an interacting-bath impurity Hamiltonian and runs FQkit VQE.

    **Legacy CAS mode**: pass ``occupied_indices`` and ``active_indices``
    for a plain frozen-core active space (no bath construction).

    Parameters
    ----------
    geometry
        Molecular geometry in Ångström.
    fragment_atoms, fragment_ao
        DMET fragment specification.
    occupied_indices, active_indices
        Legacy OpenFermion active-space indices.
    bath_threshold
        DMET bath entanglement cutoff.
    run_casci, run_fci
        Classical references stored on :class:`EmbeddingInfo`.
    layers, maxiter, seed, method
        Passed through to :func:`run_vqe`.

    Returns
    -------
    EmbeddedVQEResult
        VQE outcome, qubit Hamiltonian, and embedding / molecule metadata.
    """
    dmet_requested = fragment_atoms is not None or fragment_ao is not None
    legacy_requested = occupied_indices is not None or active_indices is not None
    if dmet_requested and legacy_requested:
        raise ValueError(
            "Use either DMET fragments (fragment_atoms/fragment_ao) or "
            "legacy occupied_indices/active_indices, not both."
        )
    if not dmet_requested and not legacy_requested:
        raise ValueError(
            "Specify a fragment via fragment_atoms / fragment_ao "
            "(DMET), or occupied_indices + active_indices (legacy CAS)."
        )

    if dmet_requested:
        hamiltonian, emb = build_embedded_hamiltonian(
            geometry,
            fragment_atoms=fragment_atoms,
            fragment_ao=fragment_ao,
            basis=basis,
            charge=charge,
            multiplicity=multiplicity,
            bath_threshold=bath_threshold,
            run_casci=run_casci,
            run_fci=run_fci,
        )
        result = run_vqe(
            hamiltonian,
            layers=layers,
            maxiter=maxiter,
            seed=seed,
            method=method,
        )
        return EmbeddedVQEResult(
            vqe=result,
            hamiltonian=hamiltonian,
            embedding=emb,
            molecule=None,
        )

    # Legacy frozen-core active space
    hamiltonian, info = molecule_hamiltonian(
        geometry,
        basis=basis,
        charge=charge,
        multiplicity=multiplicity,
        run_fci=run_fci,
        occupied_indices=occupied_indices,
        active_indices=active_indices,
    )
    if not info.active:
        raise RuntimeError("Expected an active-space Hamiltonian.")

    result = run_vqe(
        hamiltonian,
        layers=layers,
        maxiter=maxiter,
        seed=seed,
        method=method,
    )
    return EmbeddedVQEResult(
        vqe=result,
        hamiltonian=hamiltonian,
        embedding=None,
        molecule=info,
    )
