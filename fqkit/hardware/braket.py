"""Submit a circuit to IonQ, Rigetti, IQM, or AQT through Amazon Braket.

Braket compiles the OpenQASM 3 program onto the selected device. The SDK
is imported only when a job is sent.
"""

from fqkit.hardware.errors import ProviderNotInstalled, UnknownMachine
from fqkit.hardware.job import HardwareJob
from fqkit.hardware.machines import BRAKET_MACHINES
from fqkit.hardware.qasm3 import to_qasm3


def _import_braket():
    try:
        from braket.aws import AwsDevice, AwsQuantumTask
        from braket.ir.openqasm import Program
    except ImportError as exc:
        raise ProviderNotInstalled("braket", "braket") from exc
    return AwsDevice, AwsQuantumTask, Program


def resolve_device(machine, backend=None):
    """Return (arn, machine_name) for a Braket machine or an explicit ARN."""
    if isinstance(backend, str) and backend.startswith("arn:"):
        name = machine if machine in BRAKET_MACHINES else "braket"
        return backend, name
    if machine == "braket":
        if backend in BRAKET_MACHINES:
            return BRAKET_MACHINES[backend]["arn"], backend
        known = ", ".join(BRAKET_MACHINES)
        raise UnknownMachine(
            f"Choose a Braket machine ({known}) or pass a device ARN as backend."
        )
    if machine in BRAKET_MACHINES:
        return BRAKET_MACHINES[machine]["arn"], machine
    known = ", ".join(("ibm",) + tuple(BRAKET_MACHINES))
    raise UnknownMachine(f"Unknown machine '{machine}'. Choose one of: {known}.")


def counts_from_braket_result(result):
    counts = getattr(result, "measurement_counts", None)
    if counts is None:
        raise RuntimeError("Braket returned a result with no measurement counts.")
    return dict(counts)


class BraketProvider:
    """Amazon Braket device.run for the named QPU."""

    def submit(self, circuit, machine, *, backend=None, shots=1024, s3_location=None):
        AwsDevice, _, Program = _import_braket()
        arn, name = resolve_device(machine, backend)
        device = AwsDevice(arn)
        program = Program(source=to_qasm3(circuit))
        kwargs = {"shots": shots}
        if s3_location is not None:
            kwargs["s3_destination_folder"] = s3_location
        task = device.run(program, **kwargs)
        task_id = task.id if not callable(getattr(task, "id", None)) else task.id()
        return HardwareJob(
            machine=name,
            provider="braket",
            backend=arn,
            job_id=str(task_id),
            shots=shots,
            num_qubits=circuit.num_qubits,
            read_status=task.state,
            read_counts=lambda: counts_from_braket_result(task.result()),
            cancel=task.cancel,
        )

    def reconnect(self, job_id, *, machine="braket", num_qubits=None):
        _, AwsQuantumTask, _ = _import_braket()
        task = AwsQuantumTask(arn=job_id)
        return HardwareJob(
            machine=machine,
            provider="braket",
            backend=job_id,
            job_id=job_id,
            shots=None,
            num_qubits=num_qubits,
            read_status=task.state,
            read_counts=lambda: counts_from_braket_result(task.result()),
            cancel=getattr(task, "cancel", None),
        )

    def list_live(self):
        """Return online gate-model device ARNs from the caller's AWS account."""
        AwsDevice, _, _ = _import_braket()
        devices = AwsDevice.get_devices(statuses=["ONLINE"])
        found = []
        for device in devices:
            arn = getattr(device, "arn", "")
            if "/qpu/" in arn and "quera" not in arn:
                found.append(arn)
        return found
