import numpy as np

def filtrar_canales(CHANNEL_ENERGIES, ELE_DIFF_ENERGY_FLUX, ION_DIFF_ENERGY_FLUX, low=30, high=30000):
    """
    Filtra canales de energía entre 'low' y 'high' e indice los arrays en consecuencia.
    """
    mask_chan = (CHANNEL_ENERGIES >= low) & (CHANNEL_ENERGIES <= high)
    CHANNEL_ENERGIES_f = CHANNEL_ENERGIES[mask_chan]
    ELE_DIFF_ENERGY_FLUX_f = ELE_DIFF_ENERGY_FLUX[:, mask_chan]
    ION_DIFF_ENERGY_FLUX_f = ION_DIFF_ENERGY_FLUX[:, mask_chan]

    Ec2 = CHANNEL_ENERGIES_f[:-3]
    Ec1 = CHANNEL_ENERGIES_f[2:-1]
    delta = (Ec2 - Ec1) / 2
    Left  = (CHANNEL_ENERGIES_f[0] - CHANNEL_ENERGIES_f[1])
    Right = (CHANNEL_ENERGIES_f[-2] - CHANNEL_ENERGIES_f[-1])
    delta = np.insert(delta, 0, Left)
    delta = np.append(delta, Right)
    delta = np.array(delta)

    return CHANNEL_ENERGIES_f, ELE_DIFF_ENERGY_FLUX_f, ION_DIFF_ENERGY_FLUX_f, delta
