"""Send an fqkit circuit to a real quantum computer.

The simulator in fqkit.run stays local. This module is the hardware path.
Vendor SDKs are optional. Install the one you need:

    pip install "fqkit[ibm]"       # IBM Quantum, through Qiskit Runtime
    pip install "fqkit[braket]"    # IonQ, Rigetti, IQM, and AQT
    pip install "fqkit[hardware]"  # both

Pick a machine by name:

    from fqkit.hardware import submit, providers

    providers()
    job = submit(qc, "ibm", shots=1024)
    job.status()          # QUEUED, RUNNING, COMPLETED, CANCELLED, or FAILED
    job.counts()          # waits, then bitstrings in fqkit order

    job = submit(qc, "ionq", shots=100)
    job = submit(qc, "rigetti", shots=100)

IBM uses the token saved by QiskitRuntimeService.save_account. Pass token=
to submit() if you have not saved one. Braket machines use your AWS
credentials and the Amazon Braket service, which bills QPU tasks.

Quantinuum is not wired in. It uses a separate account system, and its
SDK is not part of these two extras.
"""

import importlib.util

from fqkit.hardware.braket import BraketProvider, resolve_device
from fqkit.hardware.errors import ProviderNotInstalled, UnknownMachine
from fqkit.hardware.ibm import IBMProvider
from fqkit.hardware.job import HardwareJob
from fqkit.hardware.machines import BRAKET_MACHINES, MACHINE_NAMES

__all__ = [
    "HardwareJob",
    "ProviderNotInstalled",
    "UnknownMachine",
    "backends",
    "get_job",
    "providers",
    "submit",
]


def _sdk_installed(*modules):
    for name in modules:
        try:
            if importlib.util.find_spec(name) is None:
                return False
        except ModuleNotFoundError:
            return False
    return True


def providers():
    """List the machines a caller can pass to submit().

    `installed` is False until that machine's extra is installed. The
    list itself does not contact IBM or AWS.
    """
    ibm_ready = _sdk_installed("qiskit", "qiskit_ibm_runtime")
    braket_ready = _sdk_installed("braket.aws", "braket.ir.openqasm")
    rows = [
        {
            "name": "ibm",
            "label": "IBM Quantum",
            "via": "Qiskit Runtime",
            "installed": ibm_ready,
            "install": 'pip install "fqkit[ibm]"',
        }
    ]
    for name, info in BRAKET_MACHINES.items():
        rows.append(
            {
                "name": name,
                "label": info["label"],
                "via": "Amazon Braket",
                "installed": braket_ready,
                "install": 'pip install "fqkit[braket]"',
                "backend": info["arn"],
            }
        )
    return rows


def backends(machine="ibm", *, live=False, **auth):
    """Return backend names for one machine.

    live=False uses the built-in list and does not contact a vendor.
    live=True asks the account: IBM devices that are up, or online
    Braket QPUs. That call needs credentials.
    """
    if machine == "ibm":
        if not live:
            return ["least_busy"]
        return IBMProvider().list_backends(
            service=auth.get("service"),
            token=auth.get("token"),
            channel=auth.get("channel"),
            instance=auth.get("instance"),
        )
    if machine == "braket":
        if live:
            return BraketProvider().list_live()
        return [
            f"{name}: {info['label']}" for name, info in BRAKET_MACHINES.items()
        ]
    arn, name = resolve_device(machine, auth.get("backend"))
    if name in BRAKET_MACHINES:
        return [BRAKET_MACHINES[name]["label"], arn]
    return [arn]


def submit(circuit, machine, *, backend=None, shots=1024, **auth):
    """Submit a circuit to a named machine and return a HardwareJob.

    machine is one of ibm, ionq, rigetti, iqm, aqt.
    backend overrides the device: an IBM device name, or a Braket ARN.
    shots is how many times the device measures the circuit.
    auth may include token, channel, and instance for IBM, or
    s3_location for Braket.
    """
    if machine not in MACHINE_NAMES and machine != "braket":
        known = ", ".join(MACHINE_NAMES)
        raise UnknownMachine(f"Unknown machine '{machine}'. Choose one of: {known}.")
    if shots < 1:
        raise ValueError("shots must be at least 1.")

    if machine == "ibm":
        return IBMProvider().submit(
            circuit,
            backend=backend,
            shots=shots,
            service=auth.get("service"),
            token=auth.get("token"),
            channel=auth.get("channel"),
            instance=auth.get("instance"),
        )
    return BraketProvider().submit(
        circuit,
        machine,
        backend=backend,
        shots=shots,
        s3_location=auth.get("s3_location"),
    )


def get_job(machine, job_id, **auth):
    """Reconnect to a job that was already submitted.

    For IBM, job_id is the Runtime job id. For a Braket machine, job_id
    is the task ARN. Pass num_qubits= if you already know the width.
    Otherwise counts() infers it from the returned bitstrings.
    """
    num_qubits = auth.get("num_qubits")
    if machine == "ibm":
        return IBMProvider().reconnect(
            job_id,
            service=auth.get("service"),
            token=auth.get("token"),
            channel=auth.get("channel"),
            instance=auth.get("instance"),
            num_qubits=num_qubits,
        )
    if machine in BRAKET_MACHINES or machine == "braket":
        return BraketProvider().reconnect(
            job_id, machine=machine, num_qubits=num_qubits
        )
    known = ", ".join(MACHINE_NAMES)
    raise UnknownMachine(f"Unknown machine '{machine}'. Choose one of: {known}.")
