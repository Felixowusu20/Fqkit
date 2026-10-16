"""Demo: prove gate identities with a full unitary equivalence check.

Run:
    PYTHONPATH=. python examples/equivalence_identities.py
"""

from fqkit import (
    QuantumCircuit,
    Hadamard,
    Identity,
    X,
    S,
    Z,
    CNOT,
    circuits_equivalent,
)


def show(name, a, b):
    ok = circuits_equivalent(a, b)
    print(f"{name}: {'equivalent' if ok else 'NOT equivalent'}")


def main():
    hh = QuantumCircuit(1)
    hh.add_gate(Hadamard(), [0])
    hh.add_gate(Hadamard(), [0])
    show("H·H ≡ I", hh, QuantumCircuit(1))

    xx = QuantumCircuit(1)
    xx.add_gate(X(), [0])
    xx.add_gate(X(), [0])
    show("X·X ≡ I", xx, QuantumCircuit(1))

    ss = QuantumCircuit(1)
    ss.add_gate(S(), [0])
    ss.add_gate(S(), [0])
    z = QuantumCircuit(1)
    z.add_gate(Z(), [0])
    show("S·S ≡ Z", ss, z)

    cx2 = QuantumCircuit(2)
    cx2.add_gate(CNOT(), [0, 1])
    cx2.add_gate(CNOT(), [0, 1])
    show("CNOT·CNOT ≡ I", cx2, QuantumCircuit(2))

    # Trap: Z looks like I on |0> only — full check correctly rejects it.
    only_z = QuantumCircuit(1)
    only_z.add_gate(Z(), [0])
    show("Z ≡ I (should be false)", only_z, QuantumCircuit(1))


if __name__ == "__main__":
    main()
