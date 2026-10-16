import numpy as np

from fqkit.core.parameter import Parameter

# How close U†U must be to I before we reject a gate matrix.
_UNITARY_ATOL = 1e-8


def _validate_apply_gate_inputs(
    state, gate_matrix, num_qubits, target_qubits, *, check_unitary=True
):
    """
    Check the contracts that make apply_gate mathematically safe.

    - state length must be 2**num_qubits
    - gate matrix must be (2**k, 2**k) for k = len(target_qubits)
    - gate matrix must be unitary (U†U ≈ I) when ``check_unitary`` is True

    Kraus operators used in noise channels are not unitary; density-matrix
    code calls ``apply_gate(..., check_unitary=False)``.
    """
    state = np.asarray(state)
    expected_len = 2 ** num_qubits
    if state.ndim != 1 or state.shape[0] != expected_len:
        raise ValueError(
            f"State vector length must be {expected_len} for {num_qubits} qubits, "
            f"got shape {state.shape}."
        )

    k = len(target_qubits)
    U = np.asarray(gate_matrix, dtype=complex)
    expected_shape = (2 ** k, 2 ** k)
    if U.shape != expected_shape:
        raise ValueError(
            f"Gate matrix for {k} target qubit(s) must have shape {expected_shape}, "
            f"got {U.shape}."
        )

    if check_unitary:
        product = U.conj().T @ U
        if not np.allclose(product, np.eye(2 ** k), atol=_UNITARY_ATOL):
            raise ValueError(
                "Gate matrix is not unitary within tolerance "
                f"{_UNITARY_ATOL} (U†U must equal I)."
            )

    return state, U


def apply_gate(state, gate_matrix, num_qubits, target_qubits, *, check_unitary=True):
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
    gate_matrix   : (2**k, 2**k) matrix acting on k = len(target_qubits) qubits
    num_qubits    : total number of qubits in the circuit
    target_qubits : list of k qubit indices the gate acts on
    check_unitary : bool
        If True (default), require a unitary matrix. Set False for Kraus ops.
    """
    k = len(target_qubits)
    state, U = _validate_apply_gate_inputs(
        state,
        gate_matrix,
        num_qubits,
        target_qubits,
        check_unitary=check_unitary,
    )

    # View the state as a rank-n tensor: axis i corresponds to qubit i.
    state_tensor = state.reshape([2] * num_qubits)

    # View the gate as a rank-2k tensor: the first k axes are the output
    # (row) indices and the last k axes are the input (column) indices.
    gate_tensor = U.reshape([2] * (2 * k))

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


def run(circuit, state=None):
    """
    Run a QuantumCircuit and return the final state vector.

    Parameters
    ----------
    circuit : QuantumCircuit
        Gates are applied in order.
    state : array-like, optional
        Initial statevector of length ``2**n``. If omitted, starts in
        ``|00...0>``. The input array is not modified.
    """
    num_qubits = circuit.num_qubits
    dim = 2 ** num_qubits

    if state is None:
        psi = np.zeros(dim, dtype=complex)
        psi[0] = 1.0
    else:
        psi = np.asarray(state, dtype=complex).reshape(-1).copy()
        if psi.shape[0] != dim:
            raise ValueError(
                f"Initial state length must be {dim} for {num_qubits} qubits, "
                f"got {psi.shape[0]}."
            )

    for op in circuit.operations:
        psi = apply_gate(psi, _gate_matrix(op.gate), num_qubits, op.qubits)

    return psi
