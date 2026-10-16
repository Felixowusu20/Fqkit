"""Bind symbolic Parameters to numeric values.

By default binding is **immutable**: the original circuit is left unchanged and
a new bound circuit is returned. That is the safe pattern for VQE / QAOA loops
where you reuse one template circuit with many angles.

    from fqkit import QuantumCircuit, RX, Parameter, bind_parameters, run

    theta = Parameter("theta")
    template = QuantumCircuit(1)
    template.add_gate(RX(theta), [0])

    bound = bind_parameters(template, {"theta": 1.57})
    state = run(bound)
    # template still has the unbound Parameter
"""

from __future__ import annotations

from fqkit.core.circuit import QuantumCircuit
from fqkit.core.gate import Gate
from fqkit.core.parameter import Parameter


def _resolve_params(params, param_values: dict):
    """Replace Parameter entries whose names appear in ``param_values``."""
    new_params = []
    for p in params:
        if isinstance(p, Parameter) and p.name in param_values:
            new_params.append(param_values[p.name])
        else:
            new_params.append(p)
    return new_params


def _copy_gate_with_params(gate, new_params) -> Gate:
    return Gate(
        name=gate.name,
        num_qubits=gate.num_qubits,
        matrix=gate.matrix,
        params=list(new_params),
    )


def bind_parameters(circuit, param_values: dict, *, inplace: bool = False):
    """
    Substitute numeric values for symbolic ``Parameter`` objects.

    Parameters
    ----------
    circuit : QuantumCircuit
        Template circuit (may contain unbound parameters).
    param_values : dict
        Mapping ``{parameter_name: number}``.
    inplace : bool
        If False (default), return a **new** circuit and leave ``circuit``
        unchanged. If True, mutate ``circuit`` and return it (legacy escape
        hatch).

    Returns
    -------
    QuantumCircuit
        Circuit with matching parameters replaced by numbers.
    """
    if not isinstance(param_values, dict):
        raise TypeError("param_values must be a dict of {name: number}.")

    values = dict(param_values)

    if inplace:
        for op in circuit.operations:
            if op.gate.params:
                op.gate.params = _resolve_params(op.gate.params, values)
        return circuit

    bound = QuantumCircuit(circuit.num_qubits)
    for op in circuit.operations:
        gate = op.gate
        if gate.params:
            new_params = _resolve_params(gate.params, values)
            new_gate = _copy_gate_with_params(gate, new_params)
        else:
            new_gate = _copy_gate_with_params(gate, [])
        # Bypass add_gate validation duplication by appending Operation directly
        # after the same checks add_gate would run — use add_gate for consistency.
        bound.add_gate(new_gate, list(op.qubits))
    return bound
