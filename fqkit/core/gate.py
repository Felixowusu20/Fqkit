# Gates (unitary operators)
# A gate is a unitary matrix: U such that U†U = I.
# Some gates are parameterized.

# BASE GATE CLASS

class Gate:
    def __init__(self ,name:str ,num_qubits:int ,matrix = None ,params = None):
        self.name = name
        self.num_qubits = num_qubits
        self.matrix = matrix
        self.params = params or []

    def __repr__(self):
        if self.params:
            params = ', '.join([str(p) for p in self.params])
            return f"{self.name}({params})"
        else:
            return f"{self.name}"
        


# Single-qubit gates -------------------------------------------------------
# Each factory returns a Gate with a unitary matrix U (U†U = I). 

def Identity():
    """Do-nothing gate. Matrix is the 2x2 identity."""
    return Gate(name="I", num_qubits=1, matrix=[[1, 0], [0, 1]])


def Hadamard():
    s = 1 / 2**0.5
    return Gate(name="H", num_qubits=1, matrix=[[s, s], [s, -s]])


def X():
    """Pauli X (bit flip): |0> <-> |1>."""
    return Gate(name="X", num_qubits=1, matrix=[[0, 1], [1, 0]])


def Y():
    """Pauli Y."""
    return Gate(name="Y", num_qubits=1, matrix=[[0, -1j], [1j, 0]])


def Z():
    """Pauli Z (phase flip): |1> -> -|1>."""
    return Gate(name="Z", num_qubits=1, matrix=[[1, 0], [0, -1]])


def S():
    """Phase gate S = diag(1, i). S² = Z."""
    return Gate(name="S", num_qubits=1, matrix=[[1, 0], [0, 1j]])


def T():
    """T gate = diag(1, exp(i π/4)). T² = S."""
    return Gate(
        name="T",
        num_qubits=1,
        matrix=[[1, 0], [0, (1 + 1j) / 2**0.5]],
    )


# Parameterized rotations store the angle; the matrix is built in simulator.py.

def RX(theta):
    return Gate(name="RX", num_qubits=1, params=[theta])


def RY(theta):
    return Gate(name="RY", num_qubits=1, params=[theta])


def RZ(theta):
    return Gate(name="RZ", num_qubits=1, params=[theta])


# Multi-qubit gates --------------------------------------------------------

def CNOT():
    return Gate(
        name="CNOT",
        num_qubits=2,
        matrix=[
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
    )


def CZ():
    return Gate(
        name="CZ",
        num_qubits=2,
        matrix=[
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1],
        ],
    )


def SWAP():
    return Gate(
        name="SWAP",
        num_qubits=2,
        matrix=[
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
        ],
    )


def Toffoli():
    return Gate(
        name="Toffoli",
        num_qubits=3,
        matrix=[
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 1, 0],
        ],
    )
