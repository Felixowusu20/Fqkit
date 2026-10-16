#!/usr/bin/env python3
"""FQkit engine benchmark — machine specs first, then how far you can go.

Run from the repo root:
    PYTHONPATH=. python benchmarks/bench_fqkit.py
    PYTHONPATH=. python benchmarks/bench_fqkit.py --quick
    PYTHONPATH=. python benchmarks/bench_fqkit.py --save

What you get
------------
1. A clear table of this laptop's specs (CPU, RAM, Python, NumPy, …)
2. Statevector timings / memory vs qubit count
3. Density-matrix timings / memory vs qubit count (smaller n; costs 4^n)
4. A short “how far can this machine go?” summary
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time
import tracemalloc
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Prefer the repo checkout over an older pip install.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fqkit import (  # noqa: E402
    CNOT,
    Hadamard,
    QuantumCircuit,
    RX,
    __version__ as FQKIT_VERSION,
    run,
    run_density,
)


# ---------------------------------------------------------------------------
# Pretty tables
# ---------------------------------------------------------------------------

def _table(headers, rows) -> str:
    """Render a simple box table that stays readable in any terminal."""
    str_rows = [[str(c) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(cells):
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    rule = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    lines = [rule, fmt(headers), rule.replace("-", "=")]
    for row in str_rows:
        lines.append(fmt(row))
    lines.append(rule)
    return "\n".join(lines)


def _section(title: str) -> str:
    bar = "=" * 64
    return f"\n{bar}\n {title}\n{bar}\n"


# ---------------------------------------------------------------------------
# Machine specs
# ---------------------------------------------------------------------------

def _cpu_name() -> str:
    system = platform.system()
    if system == "Darwin":
        try:
            import subprocess

            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True
            ).strip()
            if out:
                return out
        except Exception:
            pass
    if system == "Linux":
        try:
            for line in Path("/proc/cpuinfo").read_text().splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
    return platform.processor() or platform.machine() or "unknown"


def _ram_gb() -> str:
    system = platform.system()
    try:
        if system == "Darwin":
            import subprocess

            pages = int(
                subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            )
            return f"{pages / (1024 ** 3):.1f} GB"
        if system == "Linux":
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return f"{kb / (1024 ** 2):.1f} GB"
    except Exception:
        pass
    return "unknown"


def collect_specs() -> list[tuple[str, str]]:
    return [
        ("Time (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        ("OS", f"{platform.system()} {platform.release()}"),
        ("Machine", platform.machine()),
        ("Processor", _cpu_name()),
        ("CPU cores (logical)", str(os.cpu_count() or "unknown")),
        ("RAM (total)", _ram_gb()),
        ("Python", platform.python_version()),
        ("NumPy", np.__version__),
        ("FQkit", FQKIT_VERSION),
        ("Working directory", str(Path.cwd())),
    ]


# ---------------------------------------------------------------------------
# Circuits + timing
# ---------------------------------------------------------------------------

def make_circuit(n: int, depth: int = 3) -> QuantumCircuit:
    """Deterministic layered circuit (H + RX + nearest-neighbor CNOT)."""
    qc = QuantumCircuit(n)
    for layer in range(depth):
        for q in range(n):
            qc.add_gate(Hadamard(), [q])
            qc.add_gate(RX(0.1 * (layer + 1) * (q + 1)), [q])
        for q in range(n - 1):
            qc.add_gate(CNOT(), [q, q + 1])
    return qc


@dataclass
class BenchRow:
    n: int
    dimension: str
    time_ms: str
    peak_mib: str
    status: str
    note: str = ""


def _time_and_memory(fn, repeats: int):
    """Return (best_seconds, peak_mib)."""
    best = None
    peak = 0.0
    for _ in range(repeats):
        tracemalloc.start()
        t0 = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - t0
        _, traced_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak = max(peak, traced_peak / (1024 ** 2))
        best = elapsed if best is None else min(best, elapsed)
    return best, peak


def bench_statevector(qubit_counts, depth: int, repeats: int, time_limit: float):
    rows = []
    practical_n = 0
    for n in qubit_counts:
        dim = 2 ** n
        qc = make_circuit(n, depth=depth)

        def job(circuit=qc):
            return run(circuit)

        try:
            # Warm-up (imports / BLAS) outside the timed window for n small.
            if n <= 10:
                job()
            seconds, peak_mib = _time_and_memory(job, repeats=repeats)
            status = "ok"
            note = ""
            if seconds > time_limit:
                status = "slow"
                note = f">{time_limit:.1f}s comfort target"
            else:
                practical_n = n
            rows.append(
                BenchRow(
                    n=n,
                    dimension=f"2^{n} = {dim}",
                    time_ms=f"{seconds * 1000:.2f}",
                    peak_mib=f"{peak_mib:.2f}",
                    status=status,
                    note=note,
                )
            )
            if seconds > time_limit * 3:
                break
        except MemoryError:
            rows.append(
                BenchRow(n, f"2^{n} = {dim}", "—", "—", "oom", "MemoryError")
            )
            break
        except Exception as exc:  # pragma: no cover - defensive
            rows.append(
                BenchRow(n, f"2^{n} = {dim}", "—", "—", "error", type(exc).__name__)
            )
            break
    return rows, practical_n


def bench_density(qubit_counts, depth: int, repeats: int, time_limit: float):
    rows = []
    practical_n = 0
    for n in qubit_counts:
        dim = 4 ** n
        qc = make_circuit(n, depth=depth)

        def job(circuit=qc):
            return run_density(circuit)

        try:
            if n <= 5:
                job()
            seconds, peak_mib = _time_and_memory(job, repeats=repeats)
            status = "ok"
            note = ""
            if seconds > time_limit:
                status = "slow"
                note = f">{time_limit:.1f}s comfort target"
            else:
                practical_n = n
            rows.append(
                BenchRow(
                    n=n,
                    dimension=f"4^{n} = {dim}",
                    time_ms=f"{seconds * 1000:.2f}",
                    peak_mib=f"{peak_mib:.2f}",
                    status=status,
                    note=note,
                )
            )
            if seconds > time_limit * 3:
                break
        except MemoryError:
            rows.append(
                BenchRow(n, f"4^{n} = {dim}", "—", "—", "oom", "MemoryError")
            )
            break
        except Exception as exc:  # pragma: no cover
            rows.append(
                BenchRow(n, f"4^{n} = {dim}", "—", "—", "error", type(exc).__name__)
            )
            break
    return rows, practical_n


def rows_to_cells(rows: list[BenchRow]):
    return [
        [r.n, r.dimension, r.time_ms, r.peak_mib, r.status, r.note or ""]
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(quick: bool = False) -> str:
    if quick:
        sv_ns = list(range(6, 11))
        dm_ns = list(range(2, 6))
        depth = 2
        repeats = 1
        limit = 1.0
    else:
        sv_ns = list(range(8, 15))
        dm_ns = list(range(3, 9))
        depth = 3
        repeats = 2
        limit = 2.0

    parts = []
    parts.append(_section("FQkit engine benchmark"))
    parts.append(
        "This report first shows your machine, then how far the classical\n"
        "simulator can go on that machine (time + peak traced memory).\n"
    )

    # 1. Specs
    parts.append(_section("1. Your laptop / machine specs"))
    specs = collect_specs()
    parts.append(_table(["Field", "Value"], specs))
    parts.append("")

    # 2. Statevector
    parts.append(_section("2. Statevector engine  —  run(circuit)"))
    parts.append(
        f"Circuit: depth={depth} layers of H + RX + nearest-neighbor CNOT.\n"
        f"Repeats per size: {repeats} (best time kept). "
        f"Comfort target: ≤ {limit:.1f}s.\n"
    )
    sv_rows, sv_practical = bench_statevector(sv_ns, depth, repeats, limit)
    parts.append(
        _table(
            ["qubits n", "amplitudes", "time (ms)", "peak MiB", "status", "note"],
            rows_to_cells(sv_rows),
        )
    )
    parts.append("")

    # 3. Density
    parts.append(_section("3. Density-matrix engine  —  run_density(circuit)"))
    parts.append(
        "Density matrices store 4^n complex entries (much heavier than 2^n).\n"
        "Expect comfortable n to be smaller than for statevector.\n"
    )
    dm_rows, dm_practical = bench_density(dm_ns, depth, repeats, limit)
    parts.append(
        _table(
            ["qubits n", "matrix size", "time (ms)", "peak MiB", "status", "note"],
            rows_to_cells(dm_rows),
        )
    )
    parts.append("")

    # 4. Guidance
    parts.append(_section("4. How far can this machine go?"))
    parts.append(
        _table(
            ["Engine", "Comfortable up to (this run)", "Why"],
            [
                [
                    "Statevector run()",
                    f"n ≈ {sv_practical}" if sv_practical else "n < tested range",
                    "needs 2^n amplitudes",
                ],
                [
                    "Density run_density()",
                    f"n ≈ {dm_practical}" if dm_practical else "n < tested range",
                    "needs 4^n matrix entries",
                ],
            ],
        )
    )
    parts.append(
        "\nTips\n"
        "----\n"
        "* status=ok and time under the comfort target → fine for interactive research.\n"
        "* status=slow → still correct, but better for batch jobs.\n"
        "* status=oom → this machine ran out of memory at that size.\n"
        "* Use statevector for ideal algorithms; density when you need Kraus noise.\n"
        "* Re-run after big engine changes to catch performance regressions.\n"
    )
    return "\n".join(parts), specs, sv_rows, dm_rows, sv_practical, dm_practical


def to_markdown(text_report: str, specs, sv_rows, dm_rows, sv_practical, dm_practical) -> str:
    lines = [
        "# FQkit benchmark results",
        "",
        "Generated by `python benchmarks/bench_fqkit.py --save`.",
        "",
        "## 1. Machine specs",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for field, value in specs:
        lines.append(f"| {field} | {value} |")

    lines += [
        "",
        "## 2. Statevector (`run`)",
        "",
        "| qubits n | amplitudes | time (ms) | peak MiB | status | note |",
        "|---:|---|---:|---:|---|---|",
    ]
    for r in sv_rows:
        lines.append(
            f"| {r.n} | {r.dimension} | {r.time_ms} | {r.peak_mib} | {r.status} | {r.note} |"
        )

    lines += [
        "",
        "## 3. Density matrix (`run_density`)",
        "",
        "| qubits n | matrix size | time (ms) | peak MiB | status | note |",
        "|---:|---|---:|---:|---|---|",
    ]
    for r in dm_rows:
        lines.append(
            f"| {r.n} | {r.dimension} | {r.time_ms} | {r.peak_mib} | {r.status} | {r.note} |"
        )

    lines += [
        "",
        "## 4. How far on this machine?",
        "",
        f"- Statevector comfortable up to about **n = {sv_practical}**",
        f"- Density-matrix comfortable up to about **n = {dm_practical}**",
        "",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark the FQkit classical engines.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Smaller qubit range (faster smoke run).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Write benchmarks/RESULTS.md with this run.",
    )
    args = parser.parse_args(argv)

    report, specs, sv_rows, dm_rows, sv_n, dm_n = build_report(quick=args.quick)
    print(report)

    if args.save:
        out = Path(__file__).resolve().parent / "RESULTS.md"
        out.write_text(
            to_markdown(report, specs, sv_rows, dm_rows, sv_n, dm_n), encoding="utf-8"
        )
        print(f"\nSaved markdown tables to: {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
