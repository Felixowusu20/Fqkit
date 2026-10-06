"""Graphical circuit and probability figures."""

import matplotlib
matplotlib.use("Agg")

import numpy as np

from fqkit import (
    CZ,
    CNOT,
    Hadamard,
    Parameter,
    QuantumCircuit,
    RX,
    SWAP,
    Toffoli,
    draw,
    measure_all,
    plot,
    run,
)


def _bell():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    return qc


def test_draw_returns_a_figure_with_qubit_zero_on_top():
    fig = draw(_bell(), show=False)
    assert fig.axes
    columns = fig.fqkit_columns
    assert [col["name"] for col in columns] == ["H", "CNOT"]
    assert columns[1]["qubits"] == [0, 1]
    # The control sits on qubit 0, which is stored as the higher wire.
    assert columns[0]["qubits"] == [0]


def test_circuit_draw_matches_the_function():
    qc = _bell()
    fig = qc.draw(show=False)
    assert fig.fqkit_columns[1]["name"] == "CNOT"


def test_draw_labels_a_symbolic_angle_and_linked_gates():
    theta = Parameter("theta")
    qc = QuantumCircuit(3)
    qc.add_gate(RX(theta), [1])
    qc.add_gate(CZ(), [0, 1])
    qc.add_gate(SWAP(), [1, 2])
    qc.add_gate(Toffoli(), [0, 1, 2])
    fig = draw(qc, show=False)
    names = [col["name"] for col in fig.fqkit_columns]
    assert names == ["RX", "CZ", "SWAP", "Toffoli"]
    assert fig.fqkit_columns[0]["text"] == "RX(theta)"
    assert fig.fqkit_columns[3]["qubits"] == [0, 1, 2]


def test_draw_saves_a_png(tmp_path):
    path = tmp_path / "bell.png"
    draw(_bell(), filename=str(path), show=False)
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 1000


def test_plot_state_and_counts(tmp_path):
    state = run(_bell())
    state_fig = plot(state, show=False)
    assert state_fig.axes[0].get_ylabel() == "Probability"
    labels = [tick.get_text() for tick in state_fig.axes[0].get_xticklabels()]
    assert labels == ["00", "01", "10", "11"]

    counts = measure_all(state, shots=200)
    counts_fig = plot(counts, filename=str(tmp_path / "counts.png"), show=False)
    assert counts_fig.axes[0].get_ylabel() == "Shots"
    assert (tmp_path / "counts.png").stat().st_size > 1000
    heights = counts_fig.axes[0].patches
    assert len(heights) == len(counts)
    assert np.isclose(sum(bar.get_height() for bar in heights), 200)
