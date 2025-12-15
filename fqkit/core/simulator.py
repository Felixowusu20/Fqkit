import numpy as np

def kron_n(gate_matrix, num_qubits, target_qubits):
    """
    Expand a gate to the full circuit using Kronecker product.
    
    gate_matrix : 2x2 (or 2^n x 2^n) numpy array
    num_qubits : total qubits in the circuit
    target_qubits : list of qubit indices the gate acts on
    """
    I = np.eye(2, dtype=complex)
    matrices = []

    for i in range(num_qubits):
        if i in target_qubits:
            matrices.append(gate_matrix)
        else:
            matrices.append(I)

    # Compute the full tensor product
    full_gate = matrices[0]
    for mat in matrices[1:]:
        full_gate = np.kron(full_gate, mat)

    return full_gate


def run(circuit):
    """
    Run a QuantumCircuit and return the final state vector.
    """
    # Initialize |0...0> state
    num_qubits = circuit.num_qubits
    state = np.zeros(2**num_qubits, dtype=complex)
    state[0] = 1.0

    for op in circuit.operations:
        gate = op.gate
        qubits = op.qubits  # Must be integer indices

        # Parameterized gates
        if gate.params:
            theta = gate.params[0]
            if gate.name.upper() == "RX":
                gate_matrix = np.array([
                    [np.cos(theta/2), -1j*np.sin(theta/2)],
                    [-1j*np.sin(theta/2), np.cos(theta/2)]
                ], dtype=complex)
            elif gate.name.upper() == "RY":
                gate_matrix = np.array([
                    [np.cos(theta/2), -np.sin(theta/2)],
                    [np.sin(theta/2), np.cos(theta/2)]
                ], dtype=complex)
            elif gate.name.upper() == "RZ":
                gate_matrix = np.array([
                    [np.exp(-1j*theta/2), 0],
                    [0, np.exp(1j*theta/2)]
                ], dtype=complex)
            else:
                raise NotImplementedError(f"Parameterized gate {gate.name} not implemented")
        else:
            gate_matrix = np.array(gate.matrix, dtype=complex)

        # Expand to full circuit
        full_gate = kron_n(gate_matrix, num_qubits, target_qubits=qubits)

        # Apply the gate
        state = full_gate @ state

    return state
