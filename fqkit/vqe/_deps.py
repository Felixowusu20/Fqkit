"""Optional chemistry-stack imports with a clear install message."""


def require_chemistry():
    """
    Import PySCF + OpenFermion + openfermionpyscf + SciPy.

    Returns a namespace-like dict of modules/symbols used by ``fqkit.vqe``.
    """
    missing = []
    try:
        import pyscf  # noqa: F401
    except ImportError:
        missing.append("pyscf")
    try:
        import openfermion
    except ImportError:
        missing.append("openfermion")
        openfermion = None
    try:
        import openfermionpyscf
    except ImportError:
        missing.append("openfermionpyscf")
        openfermionpyscf = None
    try:
        import scipy
        import scipy.optimize
    except ImportError:
        missing.append("scipy")
        scipy = None

    if missing:
        raise ImportError(
            "Chemistry / VQE extras are not installed. Install with:\n"
            '  pip install "fqkit[chemistry]"\n'
            f"Missing: {', '.join(missing)}"
        )

    from openfermion import MolecularData, get_fermion_operator, jordan_wigner
    from openfermion.ops.operators import QubitOperator
    from openfermionpyscf import run_pyscf

    return {
        "MolecularData": MolecularData,
        "get_fermion_operator": get_fermion_operator,
        "jordan_wigner": jordan_wigner,
        "QubitOperator": QubitOperator,
        "run_pyscf": run_pyscf,
        "scipy": scipy,
        "openfermion": openfermion,
    }


def require_scipy():
    try:
        import scipy.optimize
    except ImportError as exc:
        raise ImportError(
            "SciPy is required for run_vqe. Install with:\n"
            '  pip install "fqkit[chemistry]"\n'
            "or: pip install scipy"
        ) from exc
    return scipy.optimize
