"""Pictures of circuits and measurement results.

``draw`` paints the wires and gates. ``plot`` paints probabilities or shot
counts. Both use Matplotlib and return the figure they created.

Qubit 0 is the top wire, matching the rest of fqkit.
"""

import math

from fqkit.core.parameter import Parameter

_BOX = {"H", "RX", "RY", "RZ"}
_LINKED = {"CNOT", "CZ", "SWAP", "Toffoli"}

_INK = "#202124"
_WIRE = "#3c4043"
_BOX_FILL = "#e8f0fe"
_BOX_EDGE = "#1a56c4"
_BOX_TEXT = "#12315c"
_BAR = "#1a56c4"


def _angle_text(value):
    if isinstance(value, Parameter):
        return value.name
    try:
        angle = float(value)
    except (TypeError, ValueError):
        return str(value)
    named = (
        (math.pi, "π"),
        (-math.pi, "-π"),
        (math.pi / 2, "π/2"),
        (-math.pi / 2, "-π/2"),
        (math.pi / 4, "π/4"),
        (-math.pi / 4, "-π/4"),
        (0.0, "0"),
    )
    for target, text in named:
        if abs(angle - target) < 1e-6:
            return text
    return f"{angle:.3g}"


def _gate_text(op):
    if op.gate.params:
        return f"{op.gate.name}({_angle_text(op.gate.params[0])})"
    return op.gate.name


def _wire_y(qubit, num_qubits):
    return float(num_qubits - 1 - int(qubit))


def _layout(circuit):
    columns = []
    x = 0.0
    for op in circuit.operations:
        qubits = [int(q) for q in op.qubits]
        text = _gate_text(op)
        name = op.gate.name
        if name in _LINKED:
            width = 0.72
        else:
            width = max(0.9, 0.16 * len(text) + 0.46)
        columns.append(
            {
                "name": name,
                "text": text,
                "qubits": qubits,
                "x": x,
                "width": width,
                "lo": min(qubits),
                "hi": max(qubits),
            }
        )
        x += width + 0.42
    return columns, x


def _should_show(show, filename, ax):
    if show is not None:
        return show
    if filename is not None or ax is not None:
        return False
    matplotlib = _pyplot()[0]
    return matplotlib.get_backend().lower() != "agg"


def _pyplot():
    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(
            "Drawing needs Matplotlib. Install it with: pip install matplotlib"
        ) from exc
    return matplotlib, plt


def draw(circuit, *, ax=None, filename=None, show=None):
    """Draw ``circuit`` and return the Matplotlib figure.

    Qubit 0 is the top wire. The first qubit of ``CNOT`` and ``CZ`` is the
    control. For ``Toffoli``, the first two qubits are the controls and the
    last qubit is the target.

    Pass ``filename`` to save a picture. Pass ``show=True`` to open a window.
    With no filename and no axes, a window opens unless Matplotlib is using
    a file-only backend. ``matplotlib.pyplot.draw`` refreshes the canvas
    either way.
    """
    _, plt = _pyplot()
    from matplotlib.patches import Circle, FancyBboxPatch

    n = circuit.num_qubits
    columns, x_end = _layout(circuit)
    if x_end == 0:
        x_end = 1.2

    own_figure = ax is None
    if own_figure:
        width = max(4.2, 1.6 + x_end * 0.95)
        height = max(2.2, 0.9 + n * 0.85)
        fig, ax = plt.subplots(figsize=(width, height), dpi=140)
    else:
        fig = ax.figure

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_aspect("equal")
    ax.axis("off")

    y_of = lambda q: _wire_y(q, n)
    x_right = x_end + 0.15
    for q in range(n):
        y = y_of(q)
        ax.plot([-0.05, x_right], [y, y], color=_WIRE, lw=1.6, solid_capstyle="round", zorder=1)
        ax.text(-0.28, y, f"q{q}", ha="right", va="center", color=_INK, fontsize=11, fontfamily="monospace")

    for col in columns:
        center = col["x"] + col["width"] / 2
        name = col["name"]
        if name in _LINKED and col["lo"] != col["hi"]:
            ax.plot(
                [center, center],
                [y_of(col["lo"]), y_of(col["hi"])],
                color=_INK,
                lw=1.5,
                zorder=2,
            )
        if name == "CNOT":
            _control(ax, center, y_of(col["qubits"][0]), Circle)
            _target(ax, center, y_of(col["qubits"][1]), Circle)
        elif name == "CZ":
            for q in col["qubits"]:
                _control(ax, center, y_of(q), Circle)
        elif name == "SWAP":
            for q in col["qubits"]:
                _swap(ax, center, y_of(q))
        elif name == "Toffoli":
            _control(ax, center, y_of(col["qubits"][0]), Circle)
            _control(ax, center, y_of(col["qubits"][1]), Circle)
            _target(ax, center, y_of(col["qubits"][2]), Circle)
        else:
            _box(ax, col["x"], y_of(col["qubits"][0]), col["width"], col["text"], FancyBboxPatch)

    ax.set_xlim(-1.15, x_right + 0.25)
    ax.set_ylim(-0.65, n - 1 + 0.65)
    fig.tight_layout()
    fig.fqkit_columns = columns

    if filename:
        fig.savefig(filename, bbox_inches="tight", dpi=160)
    plt.draw()
    if _should_show(show, filename, None if own_figure else ax):
        plt.show()
    return fig


def plot(data, *, ax=None, filename=None, show=None, title=None):
    """Draw probabilities or shot counts and return the Matplotlib figure.

    A state vector becomes one bar per basis state. A counts dictionary
    becomes one bar per bitstring that was seen. Bit 0 is the leftmost bit.
    """
    import numpy as np

    _, plt = _pyplot()
    array = np.asarray(data) if not isinstance(data, dict) else None
    if isinstance(data, dict):
        labels = sorted(data)
        heights = [data[label] for label in labels]
        ylabel = "Shots"
        default_title = "Counts"
    elif array is not None and array.ndim == 1 and array.size > 0:
        probabilities = np.abs(array.astype(complex)) ** 2
        n = int(round(math.log2(probabilities.size))) if probabilities.size > 1 else 0
        if n > 0 and (1 << n) != probabilities.size:
            raise ValueError("A state vector length must be a power of two.")
        labels = [format(i, f"0{max(n, 1)}b") for i in range(probabilities.size)]
        heights = probabilities.real
        ylabel = "Probability"
        default_title = "Probabilities"
    else:
        raise TypeError("plot expects a state vector or a counts dictionary.")

    own_figure = ax is None
    if own_figure:
        fig, ax = plt.subplots(figsize=(max(4.2, 0.7 * max(len(labels), 1) + 1.5), 3.4), dpi=140)
    else:
        fig = ax.figure

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.bar(labels, heights, color=_BAR, width=0.72, zorder=2)
    ax.set_ylabel(ylabel)
    ax.set_title(title or default_title, loc="left", color=_INK, fontsize=12)
    ax.tick_params(colors=_INK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#dadce0")
    ax.yaxis.grid(True, color="#eceff1", zorder=0)
    ax.set_axisbelow(True)
    fig.tight_layout()

    if filename:
        fig.savefig(filename, bbox_inches="tight", dpi=160)
    plt.draw()
    if _should_show(show, filename, None if own_figure else ax):
        plt.show()
    return fig


def _box(ax, x, y, width, text, FancyBboxPatch):
    patch = FancyBboxPatch(
        (x, y - 0.32),
        width,
        0.64,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        facecolor=_BOX_FILL,
        edgecolor=_BOX_EDGE,
        linewidth=1.4,
        zorder=3,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y,
        text,
        ha="center",
        va="center",
        color=_BOX_TEXT,
        fontsize=10,
        fontfamily="monospace",
        zorder=4,
    )


def _control(ax, x, y, Circle):
    ax.add_patch(Circle((x, y), 0.09, facecolor=_INK, edgecolor=_INK, zorder=4))


def _target(ax, x, y, Circle):
    ax.add_patch(Circle((x, y), 0.2, facecolor="white", edgecolor=_INK, linewidth=1.5, zorder=4))
    ax.plot([x - 0.12, x + 0.12], [y, y], color=_INK, lw=1.4, zorder=5)
    ax.plot([x, x], [y - 0.12, y + 0.12], color=_INK, lw=1.4, zorder=5)


def _swap(ax, x, y):
    arm = 0.14
    ax.plot([x - arm, x + arm], [y - arm, y + arm], color=_INK, lw=1.6, zorder=4)
    ax.plot([x - arm, x + arm], [y + arm, y - arm], color=_INK, lw=1.6, zorder=4)
