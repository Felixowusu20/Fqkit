"""Demo: ideal vs noisy Bell state (Task 5).

Run:
    PYTHONPATH=. python examples/noisy_bell.py
"""

from fqkit import (
    QuantumCircuit,
    Hadamard,
    CNOT,
    run_density,
    Noise,
    purity,
    entropy,
    expectation,
    is_physical,
)


def main():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])

    ideal = run_density(qc)
    noisy = run_density(qc, noise=Noise.depolarizing(0.1))

    print("ideal physical?", is_physical(ideal))
    print("noisy physical?", is_physical(noisy))
    print()
    print(f"purity  ideal={purity(ideal):.6f}  noisy={purity(noisy):.6f}")
    print(f"entropy ideal={entropy(ideal):.6f}  noisy={entropy(noisy):.6f}")
    print(f"⟨ZZ⟩    ideal={expectation(ideal, 'ZZ'):.6f}  noisy={expectation(noisy, 'ZZ'):.6f}")
    print(f"⟨XX⟩    ideal={expectation(ideal, 'XX'):.6f}  noisy={expectation(noisy, 'XX'):.6f}")


if __name__ == "__main__":
    main()
