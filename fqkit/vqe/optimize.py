"""Classical VQE loop: SciPy optimizer + FQkit statevector expectations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

import numpy as np

from fqkit.core.circuit import QuantumCircuit
from fqkit.core.observables import Hamiltonian, expectation
from fqkit.core.parameter_binding import bind_parameters
from fqkit.core.simulator import run
from fqkit.vqe._deps import require_scipy
from fqkit.vqe.ansatz import hardware_efficient_ansatz


@dataclass(frozen=True)
class VQEResult:
    """Outcome of a VQE optimization on the FQkit simulator."""

    energy: float
    params: np.ndarray
    param_names: tuple
    nit: int
    success: bool
    message: str
    n_qubits: int
    n_eval: int


def energy_from_params(
    circuit: QuantumCircuit,
    param_names: Sequence[str],
    hamiltonian: Hamiltonian,
    params: Sequence[float],
) -> float:
    """Evaluate ⟨ψ(θ)|H|ψ(θ)⟩ with an immutable bind + statevector run."""
    values = {name: float(params[i]) for i, name in enumerate(param_names)}
    bound = bind_parameters(circuit, values)
    return float(expectation(run(bound), hamiltonian))


def run_vqe(
    hamiltonian: Hamiltonian,
    circuit: Optional[QuantumCircuit] = None,
    param_names: Optional[Sequence[str]] = None,
    *,
    layers: int = 3,
    x0: Optional[Sequence[float]] = None,
    method: str = "COBYLA",
    maxiter: int = 300,
    seed: Optional[int] = 0,
    callback: Optional[Callable[[np.ndarray, float], None]] = None,
) -> VQEResult:
    """
    Variational Quantum Eigensolver on the FQkit **statevector** engine.

    Parameters
    ----------
    hamiltonian
        Molecule or model Hamiltonian (Pauli sum).
    circuit, param_names
        Optional custom ansatz. If omitted, a hardware-efficient ansatz with
        ``layers`` is built for ``hamiltonian.n`` qubits.
    layers
        Ansatz depth when building the default circuit.
    x0
        Initial angles. Default: small random values from ``seed``.
    method, maxiter
        Passed to ``scipy.optimize.minimize``.
    seed
        RNG seed for default ``x0``.
    callback
        Optional ``callback(params, energy)`` after each evaluation.

    Returns
    -------
    VQEResult
        Best energy and parameters found.

    Notes
    -----
    This path is exact (up to float precision) for small qubit counts. For
    hardware execution later, reuse the same ansatz circuit via OpenQASM /
    ``fqkit.hardware`` and estimate energies from shots.
    """
    optimize = require_scipy()

    n = hamiltonian.n
    if circuit is None:
        circuit, built_names = hardware_efficient_ansatz(n, layers=layers)
        param_names = list(built_names)
    else:
        if param_names is None:
            raise ValueError("param_names is required when passing a custom circuit.")
        param_names = list(param_names)
        if circuit.num_qubits != n:
            raise ValueError(
                f"Ansatz has {circuit.num_qubits} qubits but Hamiltonian acts on {n}."
            )

    n_params = len(param_names)
    if n_params == 0:
        # Constant circuit (rare) — just evaluate once.
        energy = float(expectation(run(circuit), hamiltonian))
        return VQEResult(
            energy=energy,
            params=np.asarray([], dtype=float),
            param_names=tuple(param_names),
            nit=0,
            success=True,
            message="no parameters",
            n_qubits=n,
            n_eval=1,
        )

    rng = np.random.default_rng(seed)
    if x0 is None:
        x0_arr = rng.normal(scale=0.1, size=n_params)
    else:
        x0_arr = np.asarray(list(x0), dtype=float)
        if x0_arr.shape != (n_params,):
            raise ValueError(f"x0 must have length {n_params}, got {x0_arr.shape}.")

    n_eval = 0

    def objective(x):
        nonlocal n_eval
        n_eval += 1
        energy = energy_from_params(circuit, param_names, hamiltonian, x)
        if callback is not None:
            callback(np.asarray(x, dtype=float), energy)
        return energy

    result = optimize.minimize(
        objective,
        x0_arr,
        method=method,
        options={"maxiter": int(maxiter)},
    )

    return VQEResult(
        energy=float(result.fun),
        params=np.asarray(result.x, dtype=float),
        param_names=tuple(param_names),
        nit=int(getattr(result, "nit", 0) or 0),
        success=bool(result.success),
        message=str(result.message),
        n_qubits=n,
        n_eval=n_eval,
    )
