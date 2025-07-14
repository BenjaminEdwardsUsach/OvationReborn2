import numpy as np

def compute_energy_edges(energies):
    """
    Calcula los bordes de energía a partir de un array de energías ordenadas.
    """
    if len(energies) < 2:
        raise ValueError("El array de energías debe tener al menos dos elementos")
    return np.concatenate(([energies[0] - (energies[1] - energies[0]) / 2],
                           (energies[:-1] + energies[1:]) / 2,
                           [energies[-1] + (energies[-1] - energies[-2]) / 2]))
