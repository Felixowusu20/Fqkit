# # # from fqkit.core.gate import Hadamard as H, RX as RY
# # # from fqkit.core.circuit import QuantumCircuit
# # # from fqkit.core.parameter import Parameter



# # # theta1 = Parameter("theta1")
# # # theta2 = Parameter("theta2")


# # # qc = QuantumCircuit(2)
# # # qc.add_gate(H(), [qc.qubits[0]])
# # # qc.add_gate(RY(theta1), [qc.qubits[1]])
# # # qc.add_gate(RY(theta2), [qc.qubits[0]])


# # # print(qc)



# # # testing the modules i have created


# # # test qubit
# # from fqkit.core.qubit import Qubit

# # print(Qubit(0) , Qubit(1))

# # # parameters

# # from fqkit.core.parameter import Parameter

# # theta = Parameter("theta")
# # phi = Parameter("phi")

# # print(theta , phi)


# # print("||||||||||")


# # # test gate
# # from fqkit.core.gate import  Gate , Hadamard , RX   
# # h_gate = Gate("H" , 1)
# # rx_gate = RX("Rx")
# # Cz_gate = Gate("CZ" , 2)
# # ry_gate = Gate("RY" , 1 , params = [phi])
# # swap_gate = Gate("SWAP" , 2)
# # toffoli_gate = Gate("Toffoli" , 3)
# # Cnot_gate = Gate("CNOT" , 2)

# # print(h_gate)
# # print(rx_gate)
# # print(Cnot_gate)
# # print(Cz_gate)
# # print(ry_gate)
# # print(swap_gate)
# # print(toffoli_gate)

# # print(h_gate)
# # print(rx_gate)


# # let build a circuit with parameterized gates

# from fqkit.core.circuit import QuantumCircuit
# from fqkit.core.parameter import Parameter
# from fqkit.core.gate import  Hadamard , RX
# from fqkit.core.qubit import Qubit
# from fqkit.core.parameter_binding import bind_parameters



# theta = Parameter("theta")
# qc = QuantumCircuit(2)
# qc.add_gate(Hadamard(), [Qubit(0)])
# qc.add_gate(RX(theta), [Qubit(1)])
# binding_params = {"theta": 3.14}
# bind_parameters(qc, binding_params)
# print(qc)




from fqkit.core.simulator import run
from fqkit.core.circuit import QuantumCircuit
from fqkit.core.gate import  Hadamard , RX
from fqkit.core.qubit import Qubit
from fqkit.core.parameter_binding import bind_parameters
from fqkit.core.parameter import Parameter
from fqkit.core.measurement import measure_all

theta = Parameter("theta")
qc = QuantumCircuit(2)
qc.add_gate(Hadamard(), [Qubit(0)])
qc.add_gate(RX(theta), [Qubit(1)])
binding_params = {"theta": 3.14}
bind_parameters(qc, binding_params)
print(qc)




state = run(qc)
count = measure_all(state , shots=1024)
print(count)

#
print(state)