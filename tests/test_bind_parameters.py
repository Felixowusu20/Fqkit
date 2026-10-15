"""Extra C — immutable parameter binding."""

import numpy as np
import pytest

from fqkit import Parameter, QuantumCircuit, RX, bind_parameters, run
from fqkit.core.parameter import Parameter as Param


def test_bind_returns_new_circuit_and_leaves_template():
    theta = Parameter("theta")
    template = QuantumCircuit(1)
    template.add_gate(RX(theta), [0])

    bound = bind_parameters(template, {"theta": np.pi})

    assert bound is not template
    # Template still unbound — run must fail.
    with pytest.raises(ValueError, match="unbound parameter"):
        run(template)
    # Bound circuit runs.
    state = run(bound)
    assert np.allclose(np.abs(state) ** 2, [0, 1])


def test_bind_inplace_mutates_when_requested():
    theta = Parameter("theta")
    qc = QuantumCircuit(1)
    qc.add_gate(RX(theta), [0])
    out = bind_parameters(qc, {"theta": np.pi}, inplace=True)
    assert out is qc
    assert np.allclose(np.abs(run(qc)) ** 2, [0, 1])


def test_bind_does_not_share_mutable_param_list():
    theta = Parameter("theta")
    template = QuantumCircuit(1)
    template.add_gate(RX(theta), [0])
    bound = bind_parameters(template, {"theta": 0.3})
    # Changing the bound gate params must not touch the template.
    bound.operations[0].gate.params[0] = 9.9
    assert isinstance(template.operations[0].gate.params[0], Param)
    assert template.operations[0].gate.params[0].name == "theta"
