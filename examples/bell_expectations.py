"""Small research-style demo for Task 3 (Pauli expectation values).

Run from the repo root:
    python examples/bell_expectations.py
"""

from fqkit import (
    QuantumCircuit,
    Hadamard,
    CNOT,
    run,
    pauli,
    Hamiltonian,
    expectation,
)


def main():
    # Bell state |Φ+> = (|00> + |11>)/√2
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    state = run(qc)

    print("⟨ZZ⟩ =", expectation(state, pauli("ZZ")))  # +1
    print("⟨XX⟩ =", expectation(state, "XX"))         # +1
    print("⟨YY⟩ =", expectation(state, "YY"))         # -1

    # Toy Hamiltonian — the same pattern used in VQE energy evaluation
    H = Hamiltonian(("ZZ", 0.5), ("XX", 0.25))
    print("⟨H⟩  =", expectation(state, H))            # 0.75


if __name__ == "__main__":
    main()
