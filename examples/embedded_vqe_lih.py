"""One-shot DMET Embedded-VQE for LiH (H-atom fragment) on FQkit.

Requires:
    pip install -e ".[chemistry]"

Run:
    PYTHONPATH=. python examples/embedded_vqe_lih.py
"""

from fqkit.vqe import run_embedded_vqe


def main():
    geometry = [
        ("Li", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 1.6)),
    ]

    print("Building DMET impurity (H fragment) → FQkit Hamiltonian...")
    out = run_embedded_vqe(
        geometry,
        fragment_atoms="H",
        basis="sto-3g",
        run_casci=True,
        run_fci=True,
        layers=3,
        maxiter=400,
        seed=0,
    )
    emb = out.embedding
    assert emb is not None

    print(f"  fragment AOs : {emb.fragment_ao}")
    print(f"  n_cas / bath : {emb.n_cas} / {emb.n_bath}")
    print(f"  qubits       : {emb.n_qubits}")
    print(f"  Pauli terms  : {emb.n_terms}")
    print(f"  HF energy    : {emb.hf_energy:.8f} Ha")
    print(f"  CASCI (imp.) : {emb.casci_energy:.8f} Ha")
    print(f"  FCI (full)   : {emb.fci_energy:.8f} Ha")
    print(f"  VQE energy   : {out.energy:.8f} Ha")
    print(f"  |VQE−CASCI|  : {abs(out.energy - emb.casci_energy):.6f} Ha")
    print(f"  |CASCI−FCI|  : {abs(emb.casci_energy - emb.fci_energy):.6f} Ha")


if __name__ == "__main__":
    main()
