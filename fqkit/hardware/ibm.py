"""Submit a circuit to IBM Quantum through Qiskit Runtime.

The SDK is imported only when a job is sent. A normal `import fqkit`
does not load it.
"""

from fqkit.hardware.errors import ProviderNotInstalled
from fqkit.hardware.job import HardwareJob


def _import_ibm():
    try:
        from qiskit import QuantumCircuit as QiskitCircuit
        try:
            from qiskit.transpiler.preset_passmanagers import (
                generate_preset_pass_manager,
            )
        except ImportError:
            from qiskit.transpiler import generate_preset_pass_manager
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    except ImportError as exc:
        raise ProviderNotInstalled("ibm", "ibm") from exc
    return QiskitCircuit, generate_preset_pass_manager, QiskitRuntimeService, Sampler


def counts_from_ibm_result(result):
    """Pull measurement counts out of a SamplerV2 result."""
    pub = result[0]
    data = pub.data
    names = []
    if hasattr(data, "__iter__") and not isinstance(data, (str, bytes)):
        names = list(data)
    for name in names:
        value = data[name]
        if hasattr(value, "get_counts"):
            return value.get_counts()
    for name in dir(data):
        if name.startswith("_"):
            continue
        value = getattr(data, name, None)
        if hasattr(value, "get_counts"):
            return value.get_counts()
    raise RuntimeError("IBM returned a result with no measurement counts.")


def _service(Service, *, service, token, channel, instance):
    if service is not None:
        return service
    kwargs = {}
    if token is not None:
        kwargs["token"] = token
    if channel is not None:
        kwargs["channel"] = channel
    if instance is not None:
        kwargs["instance"] = instance
    return Service(**kwargs)


def _backend_name(device):
    name = getattr(device, "name", None)
    if callable(name):
        name = name()
    return str(name or device)


class IBMProvider:
    """Qiskit Runtime Sampler against a real IBM backend."""

    def list_backends(self, *, service=None, token=None, channel=None, instance=None):
        _, _, Service, _ = _import_ibm()
        account = _service(
            Service, service=service, token=token, channel=channel, instance=instance
        )
        devices = account.backends(operational=True, simulator=False)
        return [_backend_name(device) for device in devices]

    def submit(
        self,
        circuit,
        *,
        backend=None,
        shots=1024,
        service=None,
        token=None,
        channel=None,
        instance=None,
    ):
        QiskitCircuit, pass_manager, Service, Sampler = _import_ibm()
        account = _service(
            Service, service=service, token=token, channel=channel, instance=instance
        )
        if backend is None or backend == "least_busy":
            device = account.least_busy(operational=True, simulator=False)
        else:
            device = account.backend(backend)

        qiskit_qc = QiskitCircuit.from_qasm_str(circuit.to_qasm(measure=True))
        isa = pass_manager(backend=device, optimization_level=1).run(qiskit_qc)
        sampler = Sampler(mode=device)
        vendor_job = sampler.run([isa], shots=shots)
        name = _backend_name(device)
        return HardwareJob(
            machine="ibm",
            provider="ibm",
            backend=name,
            job_id=vendor_job.job_id(),
            shots=shots,
            num_qubits=circuit.num_qubits,
            read_status=vendor_job.status,
            read_counts=lambda: counts_from_ibm_result(vendor_job.result()),
            cancel=vendor_job.cancel,
        )

    def reconnect(self, job_id, *, service=None, token=None, channel=None, instance=None, num_qubits=None):
        _, _, Service, _ = _import_ibm()
        account = _service(
            Service, service=service, token=token, channel=channel, instance=instance
        )
        vendor_job = account.job(job_id)
        device = vendor_job.backend() if callable(getattr(vendor_job, "backend", None)) else None
        return HardwareJob(
            machine="ibm",
            provider="ibm",
            backend=_backend_name(device) if device is not None else "ibm",
            job_id=job_id,
            shots=None,
            num_qubits=num_qubits,
            read_status=vendor_job.status,
            read_counts=lambda: counts_from_ibm_result(vendor_job.result()),
            cancel=getattr(vendor_job, "cancel", None),
        )
