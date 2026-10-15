# FQkit benchmarks

Measure **your machine** first, then see how far the classical engines go.

## Run

From the repository root:

```bash
PYTHONPATH=. python benchmarks/bench_fqkit.py
```

Faster smoke run:

```bash
PYTHONPATH=. python benchmarks/bench_fqkit.py --quick
```

Save markdown tables to `benchmarks/RESULTS.md`:

```bash
PYTHONPATH=. python benchmarks/bench_fqkit.py --save
```

## What the report shows

1. **Laptop / machine specs** — OS, CPU, RAM, Python, NumPy, FQkit version  
2. **Statevector table** — time and peak memory for `run()` as `n` grows (`2^n`)  
3. **Density-matrix table** — same for `run_density()` (`4^n`, smaller `n`)  
4. **How far can you go?** — comfortable qubit counts on *this* machine  

This is Task 6 of the simulator roadmap: honest scaling data before any sparse / tensor-network work.
