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
        


# # let try creating some gates (Hadamard, CNOT, RX)
def Hadamard():
    return Gate(name="H", num_qubits=1, matrix=[[1/2**0.5, 1/2**0.5], [1/2**0.5, -1/2**0.5]])


# def CNOT():
#     return Gate(name="CNOT", num_quibits=2, matrix=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
def RX(theta):
    return Gate(name="RX", num_qubits=1, params=[theta])


def RY(theta):
    return Gate(name="RY", num_qubits=1, params=[theta])


def RZ(theta):
    return Gate(name="RZ", num_qubits=1, params=[theta])
def CNOT():
    return Gate(name="CNOT", num_qubits=2, matrix=[[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


# You can add more gates as needed
# For example, CZ, SWAP, Toffoli, etc.

def CZ():
    return Gate(
        name="CZ", 
        num_qubits=2, 
        matrix=[[1, 0, 0, 0], [0, 1, 0, 0],
                [0, 0, 1, 0], [0, 0, 0, -1]])
def SWAP():
    return Gate(
        name="SWAP",
                 num_qubits=2,
                 matrix=[[1, 0, 0, 0], [0, 0, 1, 0],
                         [0, 1, 0, 0], [0, 0, 0, 1]])    
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
            [0, 0, 0, 0, 0, 0, 1, 0]
        ]
    )



