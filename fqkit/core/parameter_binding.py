
from fqkit.core.parameter import Parameter

def bind_parameters(circuit, param_values: dict):
    for op in circuit.operations:      # <-- iterating over Operation objects
        if op.gate.params:             # <-- accessing the gate's parameters
            new_params = []
            for p in op.gate.params:
                if isinstance(p, Parameter) and p.name in param_values:
                    new_params.append(param_values[p.name])
                else:
                    new_params.append(p)
            op.gate.params = new_params
