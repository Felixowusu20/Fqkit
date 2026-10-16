"""H₂ VQE on FQkit (PySCF + OpenFermion mapping, FQkit ansatz/optimizer).

Requires:
    pip install -e ".[chemistry]"

Run:
    PYTHONPATH=. python examples/vqe_h2.py
"""

from fqkit.vqe import molecule_hamiltonian, run_vqe


def main():
    geometry = [
        ("H", (0.0, 0.0, 0.0)),
        ("H", (0.0, 0.0, 0.7414)),
    ]

    print("Building H₂ / STO-3G Hamiltonian (PySCF → OpenFermion → FQkit)...")
    H, info = molecule_hamiltonian(geometry, basis="sto-3g", run_fci=True)
    print(f"  qubits     : {info.n_qubits}")
    print(f"  Pauli terms: {info.n_terms}")
    print(f"  HF energy  : {info.hf_energy:.8f} Ha")
    print(f"  FCI energy : {info.fci_energy:.8f} Ha")

    print("\nRunning VQE on the FQkit statevector engine...")
    result = run_vqe(H, layers=3, maxiter=400, seed=0, method="COBYLA")
    print(f"  VQE energy : {result.energy:.8f} Ha")
    print(f"  success    : {result.success}")
    print(f"  evaluations: {result.n_eval}")
    if info.fci_energy is not None:
        print(f"  error vs FCI: {abs(result.energy - info.fci_energy):.6f} Ha")


if __name__ == "__main__":
    main()
