# Contributing to FQkit

Thanks for helping improve FQkit. Right now the priority is making the
**classical simulators** mathematically reliable and useful for quantum
research. Hardware work can wait until the ideal simulator is solid.

## Quick start for contributors

```bash
git clone https://github.com/Felixowusu20/Fqkit.git
cd Fqkit
pip install -e ".[dev]"
pytest -v
```

Optional (OpenQASM round-trip tests):

```bash
pip install qiskit
pytest -v
```

## What to work on

Full task write-ups (why, how, acceptance criteria, files):

**[docs/simulator-tasks.md](docs/simulator-tasks.md)**

Suggested order:

1. Statevector validation
2. Measurement v2 (seeds + `Result`)
3. Pauli observables and expectation values
4. Circuit equivalence tests
5. Density-matrix + simple noise
6. Performance benchmarks

Smaller parallel tasks (gates, helpers, docs) are listed at the bottom of
that file.

## How to claim a task

1. Open a new issue with the **Simulator task** template.
2. Choose the task id and say what you will deliver.
3. Wait for a maintainer to confirm (or self-assign if you already have
   write access).
4. Open a PR that links the issue (`Fixes #N`).

Please avoid duplicating work that is already assigned or open as a PR.

## Pull request checklist

- [ ] Tests added or updated (`pytest` passes)
- [ ] Public API changes exported in `fqkit/__init__.py` when needed
- [ ] Short example or docs note for user-facing features
- [ ] Tolerances and random seeds documented when relevant
- [ ] No secrets or large binary media committed by accident

## Code standards for simulator work

- Prefer clear NumPy code over clever micro-optimizations until benchmarks
  exist.
- Keep big-endian qubit ordering (qubit 0 = MSB). See the root README.
- Match existing style in `fqkit/core/` and `tests/`.
- Do not claim noise is “correct” unless a density-matrix or validated
  trajectory method backs it.

## Questions

Open a Discussion or an issue. For simulator roadmap questions, mention
which task id from `docs/simulator-tasks.md` you mean.
