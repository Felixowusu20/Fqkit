"""Machines a caller can name in submit().

IonQ, Rigetti, IQM, and AQT are reached through Amazon Braket, so one
optional SDK covers those four. QuEra Aquila is an analog device and cannot
run an fqkit gate circuit, so it is not listed. IBM is a separate SDK.
Device names change. Pass a full ARN as backend= when a name here is retired.
"""

BRAKET_MACHINES = {
    "ionq": {
        "label": "IonQ Forte-1",
        "arn": "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1",
    },
    "rigetti": {
        "label": "Rigetti Ankaa-3",
        "arn": "arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3",
    },
    "iqm": {
        "label": "IQM Garnet",
        "arn": "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet",
    },
    "aqt": {
        "label": "AQT IBEX-Q1",
        "arn": "arn:aws:braket:eu-north-1::device/qpu/aqt/Ibex-Q1",
    },
}

MACHINE_NAMES = ("ibm",) + tuple(BRAKET_MACHINES)
