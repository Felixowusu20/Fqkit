import numpy as np

from fqkit.core.parameter import Parameter


def apply_gate(state, gate_matrix, num_qubits, target_qubits):
    """
    Apply a k-qubit gate to the target qubits of an n-qubit state vector.

    Uses tensor contraction rather than a Kronecker product, so it works for
    any qubit ordering — including non-adjacent and reversed controls/targets
    (e.g. CNOT with control=1, target=0), which a naive kron cannot express.

    Convention: big-endian. Qubit 0 is the most significant bit of the state
    vector index, and target_qubits[0] is the most significant qubit of
    gate_matrix. This matches the ordering of the gate matrices in gate.py.

    Parameters
    ----------
    state         : (2**num_qubits,) complex state vector
    gate_matrix   : (2**k, 2**k) unitary acting on k = len(target_qubits) qubits
    num_qubits    : total number of qubits in the circuit
    target_qubits : list of k qubit indices the gate acts on
    """
    k = len(target_qubits)

    # View the state as a rank-n tensor: axis i corresponds to qubit i.
    state_tensor = state.reshape([2] * num_qubits)

    # View the gate as a rank-2k tensor: the first k axes are the output
    # (row) indices and the last k axes are the input (column) indices.
    gate_tensor = np.asarray(gate_matrix, dtype=complex).reshape([2] * (2 * k))

    # Contract the gate's input axes with the state's target-qubit axes.
    state_tensor = np.tensordot(
        gate_tensor,
        state_tensor,
        axes=(list(range(k, 2 * k)), list(target_qubits)),
    )

    # tensordot leaves the gate's output axes in front; move them back to the
    # positions of the qubits they act on so axis i == qubit i again.
    state_tensor = np.moveaxis(state_tensor, list(range(k)), list(target_qubits))

    return state_tensor.reshape(2 ** num_qubits)


def _gate_matrix(gate):
    """
    Return the numeric unitary matrix for a gate.

    Rotation gates (RX/RY/RZ) store their angle as a parameter instead of a
    matrix, so we build the matrix on demand from the bound value.
    """
    if gate.params:
        for p in gate.params:
            if isinstance(p, Parameter):
                raise ValueError(
                    f"Gate {gate.name} has an unbound parameter '{p.name}'. "
                    f"Call bind_parameters(circuit, {{'{p.name}': value}}) "
                    f"before running the circuit."
                )

        theta = gate.params[0]
        name = gate.name.upper()

        if name == "RX":
            return np.array([
                [np.cos(theta / 2), -1j * np.sin(theta / 2)],
                [-1j * np.sin(theta / 2), np.cos(theta / 2)],
            ], dtype=complex)
        if name == "RY":
            return np.array([
                [np.cos(theta / 2), -np.sin(theta / 2)],
                [np.sin(theta / 2), np.cos(theta / 2)],
            ], dtype=complex)
        if name == "RZ":
            return np.array([
                [np.exp(-1j * theta / 2), 0],
                [0, np.exp(1j * theta / 2)],
            ], dtype=complex)

        raise NotImplementedError(f"Parameterized gate {gate.name} not implemented")

    if gate.matrix is None:
        raise ValueError(f"Gate {gate.name} has no matrix and no parameters.")

    return np.array(gate.matrix, dtype=complex)


def run(circuit):
    """
    Run a QuantumCircuit and return the final state vector.

    The circuit starts in |00...0> and each operation is applied in order.
    """
    num_qubits = circuit.num_qubits

    # Initialize the |0...0> state.
    state = np.zeros(2 ** num_qubits, dtype=complex)
    state[0] = 1.0

    for op in circuit.operations:
        state = apply_gate(state, _gate_matrix(op.gate), num_qubits, op.qubits)

    return state
