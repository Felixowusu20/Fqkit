"""Hardware submission, with the vendor SDKs replaced by fakes."""

import importlib.util

import pytest

from fqkit import CNOT, Hadamard, Parameter, QuantumCircuit, RX, bind_parameters
from fqkit.hardware import backends, get_job, providers, submit
from fqkit.hardware.braket import counts_from_braket_result, resolve_device
from fqkit.hardware.errors import ProviderNotInstalled, UnknownMachine
from fqkit.hardware.ibm import counts_from_ibm_result
from fqkit.hardware.job import normalize_status, to_fqkit_counts
from fqkit.hardware.qasm3 import to_qasm3


def bell():
    qc = QuantumCircuit(2)
    qc.add_gate(Hadamard(), [0])
    qc.add_gate(CNOT(), [0, 1])
    return qc


def test_qasm3_bell_uses_braket_gate_names():
    text = to_qasm3(bell())
    assert text.startswith("OPENQASM 3.0;")
    assert "bit[2] c;" in text
    assert "qubit[2] q;" in text
    assert "h q[0];" in text
    assert "cnot q[0], q[1];" in text
    assert "c = measure q;" in text


def test_qasm3_rejects_unbound_parameter():
    qc = QuantumCircuit(1)
    qc.add_gate(RX(Parameter("theta")), [0])
    with pytest.raises(ValueError, match="unbound parameter"):
        to_qasm3(qc)


def test_qasm3_writes_a_bound_angle():
    qc = QuantumCircuit(1)
    qc.add_gate(RX(Parameter("theta")), [0])
    bind_parameters(qc, {"theta": 0.5})
    assert "rx(0.5) q[0];" in to_qasm3(qc)


def test_vendor_bitstrings_are_flipped_into_fqkit_order():
    # Vendor qubit 0 is on the right. FQkit qubit 0 is on the left.
    assert to_fqkit_counts({"01": 3, "10": 1}, 2) == {"10": 3, "01": 1}


def test_status_words_match_across_vendors():
    assert normalize_status("DONE") == "COMPLETED"
    assert normalize_status("COMPLETED") == "COMPLETED"
    assert normalize_status("QUEUED") == "QUEUED"
    assert normalize_status("ERROR") == "FAILED"

    class Status:
        name = "RUNNING"

    assert normalize_status(Status()) == "RUNNING"


def test_providers_lists_machines_without_contacting_them():
    names = [row["name"] for row in providers()]
    assert names == ["ibm", "ionq", "rigetti", "iqm", "aqt"]
    ibm = providers()[0]
    assert ibm["installed"] is _installed("qiskit_ibm_runtime")
    assert "fqkit[ibm]" in ibm["install"]
    assert providers()[1]["installed"] is _installed("braket.aws")
    assert "Amazon Braket" == providers()[1]["via"]


def test_backends_for_a_braket_machine_is_its_arn():
    listed = backends("ionq")
    assert any(item.startswith("arn:aws:braket:") and "ionq" in item for item in listed)
    assert backends("ibm") == ["least_busy"]
    assert backends("braket")[0].startswith("ionq:")


def test_unknown_machine_names_the_choices():
    with pytest.raises(UnknownMachine, match="ionq"):
        submit(bell(), "quantinuum")


def test_shots_must_be_positive():
    with pytest.raises(ValueError, match="shots"):
        submit(bell(), "ibm", shots=0)


def test_submit_ibm_uses_runtime_sampler(monkeypatch):
    seen = {}

    class Device:
        name = "ibm_fez"

    class Account:
        def least_busy(self, operational, simulator):
            seen["least_busy"] = (operational, simulator)
            return Device()

        def backend(self, name):
            seen["named"] = name
            return Device()

    class VendorJob:
        def job_id(self):
            return "job-123"

        def status(self):
            return "QUEUED"

        def result(self):
            return _ibm_result({"01": 4, "10": 6})

        def cancel(self):
            seen["cancelled"] = True

    class Sampler:
        def __init__(self, mode):
            seen["mode"] = mode

        def run(self, circuits, shots=None):
            seen["shots"] = shots
            seen["qasm"] = circuits[0]["qasm"]
            return VendorJob()

    class QiskitCircuit:
        @staticmethod
        def from_qasm_str(text):
            return {"qasm": text}

    def pass_manager(backend, optimization_level):
        seen["opt"] = optimization_level

        class PM:
            def run(self, circuit):
                return circuit

        return PM()

    monkeypatch.setattr(
        "fqkit.hardware.ibm._import_ibm",
        lambda: (QiskitCircuit, pass_manager, Account, Sampler),
    )

    job = submit(bell(), "ibm", shots=128, service=Account())
    assert job.job_id == "job-123"
    assert job.backend == "ibm_fez"
    assert job.status() == "QUEUED"
    assert seen["shots"] == 128
    assert seen["least_busy"] == (True, False)
    assert "h q[0];" in seen["qasm"]
    assert "cx q[0], q[1];" in seen["qasm"]
    assert job.counts() == {"10": 4, "01": 6}
    job.cancel()
    assert seen["cancelled"] is True

    submit(bell(), "ibm", backend="ibm_torino", shots=8, service=Account())
    assert seen["named"] == "ibm_torino"


def test_get_job_ibm_reconnects(monkeypatch):
    class VendorJob:
        def status(self):
            return "DONE"

        def result(self):
            return _ibm_result({"11": 5})

        def backend(self):
            class Device:
                name = "ibm_fez"

            return Device()

        def cancel(self):
            pass

    class Account:
        def job(self, job_id):
            assert job_id == "job-123"
            return VendorJob()

    monkeypatch.setattr(
        "fqkit.hardware.ibm._import_ibm",
        lambda: (None, None, Account, None),
    )
    job = get_job("ibm", "job-123", service=Account(), num_qubits=2)
    assert job.status() == "COMPLETED"
    assert job.counts() == {"11": 5}


def test_submit_ionq_sends_openqasm3(monkeypatch):
    seen = {}

    class Program:
        def __init__(self, source):
            self.source = source

    class Task:
        id = "arn:aws:braket:task/1"

        def state(self):
            return "RUNNING"

        def result(self):
            class Result:
                measurement_counts = {"01": 2, "10": 9}

            return Result()

        def cancel(self):
            seen["cancelled"] = True

    class Device:
        def __init__(self, arn):
            seen["arn"] = arn

        def run(self, program, shots=None, s3_destination_folder=None):
            seen["source"] = program.source
            seen["shots"] = shots
            seen["s3"] = s3_destination_folder
            return Task()

    monkeypatch.setattr(
        "fqkit.hardware.braket._import_braket",
        lambda: (Device, None, Program),
    )
    job = submit(bell(), "ionq", shots=100, s3_location=("bucket", "prefix"))
    assert job.machine == "ionq"
    assert job.provider == "braket"
    assert job.status() == "RUNNING"
    assert seen["arn"].endswith("ionq/Forte-1")
    assert seen["source"].startswith("OPENQASM 3.0;")
    assert "cnot q[0], q[1];" in seen["source"]
    assert seen["shots"] == 100
    assert seen["s3"] == ("bucket", "prefix")
    assert job.counts() == {"10": 2, "01": 9}


def test_braket_arn_override(monkeypatch):
    seen = {}

    class Program:
        def __init__(self, source):
            self.source = source

    class Task:
        id = "arn:aws:braket:task/2"

        def state(self):
            return "QUEUED"

        def result(self):
            return type("R", (), {"measurement_counts": {}})()

        def cancel(self):
            pass

    class Device:
        def __init__(self, arn):
            seen["arn"] = arn

        def run(self, program, shots=None, s3_destination_folder=None):
            return Task()

    monkeypatch.setattr(
        "fqkit.hardware.braket._import_braket",
        lambda: (Device, None, Program),
    )
    arn = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
    job = submit(bell(), "ionq", backend=arn, shots=10)
    assert seen["arn"] == arn
    assert job.backend == arn


def test_missing_sdk_is_reported(monkeypatch):
    def blocked():
        raise ProviderNotInstalled("ibm", "ibm")

    monkeypatch.setattr("fqkit.hardware.ibm._import_ibm", blocked)
    with pytest.raises(ProviderNotInstalled, match=r'fqkit\[ibm\]'):
        submit(bell(), "ibm")


def test_real_imports_fail_clearly_when_sdks_are_absent():
    from fqkit.hardware.braket import _import_braket
    from fqkit.hardware.ibm import _import_ibm

    if importlib.util.find_spec("qiskit_ibm_runtime") is None:
        with pytest.raises(ProviderNotInstalled, match="ibm"):
            _import_ibm()
    if importlib.util.find_spec("braket") is None:
        with pytest.raises(ProviderNotInstalled, match="braket"):
            _import_braket()


def test_counts_helpers_reject_an_empty_payload():
    with pytest.raises(RuntimeError, match="IBM"):
        counts_from_ibm_result([type("Pub", (), {"data": object()})()])

    class Result:
        measurement_counts = None

    with pytest.raises(RuntimeError, match="Braket"):
        counts_from_braket_result(Result())


def test_resolve_device_rejects_a_bare_braket_name():
    with pytest.raises(UnknownMachine, match="ionq"):
        resolve_device("braket")


def _installed(module):
    try:
        return importlib.util.find_spec(module) is not None
    except ModuleNotFoundError:
        return False


class _Bits:
    def __init__(self, counts):
        self._counts = counts

    def get_counts(self):
        return self._counts


class _Data:
    def __init__(self, counts):
        self._counts = counts

    def __iter__(self):
        yield "c"

    def __getitem__(self, key):
        return _Bits(self._counts)


def _ibm_result(counts):
    pub = type("Pub", (), {"data": _Data(counts)})()
    return [pub]
