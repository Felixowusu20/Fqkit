"""Errors raised by the hardware job layer."""


class ProviderNotInstalled(ImportError):
    """The vendor SDK for a machine is not installed."""

    def __init__(self, machine, extra):
        self.machine = machine
        self.extra = extra
        super().__init__(
            f"The SDK for '{machine}' is not installed. "
            f'Install it with: pip install "fqkit[{extra}]"'
        )


class UnknownMachine(ValueError):
    """The caller named a machine fqkit does not know how to submit to."""
