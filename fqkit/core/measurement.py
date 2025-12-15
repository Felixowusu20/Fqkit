# fqkit/core/measurement.py
import numpy as np

def measure_all(state_vector, shots=1024):
    """
    Simulate measurements of all qubits.
    
    Parameters
    ----------
    state_vector : np.array
        The final state vector of the circuit
    shots : int
        Number of measurement repetitions

    Returns
    -------
    counts : dict
        Dictionary mapping bitstrings to counts
    """
    num_qubits = int(np.log2(len(state_vector)))
    probabilities = np.abs(state_vector)**2
    outcomes = list(range(len(probabilities)))

    # Sample measurement outcomes
    samples = np.random.choice(outcomes, size=shots, p=probabilities)

    counts = {}
    for s in samples:
        # Convert integer to binary string with leading zeros
        bitstring = format(s, f"0{num_qubits}b")
        counts[bitstring] = counts.get(bitstring, 0) + 1

    return counts
