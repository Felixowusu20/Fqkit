"""A hardware job, in the same shape for every vendor."""


_STATUS = {
    "INITIALIZING": "QUEUED",
    "CREATED": "QUEUED",
    "QUEUED": "QUEUED",
    "VALIDATING": "QUEUED",
    "RUNNING": "RUNNING",
    "COMPLETED": "COMPLETED",
    "DONE": "COMPLETED",
    "CANCELLED": "CANCELLED",
    "CANCELLING": "CANCELLED",
    "ERROR": "FAILED",
    "FAILED": "FAILED",
}


def normalize_status(value):
    """Map a vendor status object onto one word.

    The words are QUEUED, RUNNING, COMPLETED, CANCELLED, and FAILED.
    """
    name = getattr(value, "name", None) or str(value)
    name = name.split(".")[-1].strip().upper()
    return _STATUS.get(name, name)


def to_fqkit_counts(counts, num_qubits):
    """Return counts in fqkit order.

    IBM and Amazon Braket both put qubit 0 on the right of a bitstring.
    FQkit puts qubit 0 on the left, matching measure_all.
    """
    out = {}
    width = num_qubits
    for key, value in dict(counts).items():
        bits = str(key).replace(" ", "")
        if width is None:
            width = len(bits)
        bits = bits.zfill(width)
        if len(bits) != width:
            raise ValueError(
                f"Measurement '{bits}' does not match a {width}-qubit circuit."
            )
        flipped = bits[::-1]
        out[flipped] = out.get(flipped, 0) + int(value)
    return out


class HardwareJob:
    """One submitted circuit.

    status() asks the vendor and returns immediately.
    counts() waits until the device finishes, then returns fqkit bitstrings.
    """

    def __init__(
        self,
        *,
        machine,
        provider,
        backend,
        job_id,
        shots,
        num_qubits,
        read_status,
        read_counts,
        cancel=None,
    ):
        self.machine = machine
        self.provider = provider
        self.backend = backend
        self.job_id = job_id
        self.shots = shots
        self.num_qubits = num_qubits
        self._read_status = read_status
        self._read_counts = read_counts
        self._cancel = cancel

    def status(self):
        return normalize_status(self._read_status())

    def counts(self):
        raw = self._read_counts()
        width = self.num_qubits
        if width is None and raw:
            width = len(str(next(iter(raw))).replace(" ", ""))
        return to_fqkit_counts(raw, width)

    def cancel(self):
        if self._cancel is None:
            raise RuntimeError(
                f"Jobs on '{self.machine}' cannot be cancelled from fqkit."
            )
        self._cancel()

    def __repr__(self):
        return (
            f"HardwareJob(machine={self.machine!r}, backend={self.backend!r}, "
            f"job_id={self.job_id!r})"
        )
