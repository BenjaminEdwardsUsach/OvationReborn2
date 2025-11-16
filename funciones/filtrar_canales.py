import numpy as np

def filtrar_canales(CHANNEL_ENERGIES, ELE_DIFF_ENERGY_FLUX, ION_DIFF_ENERGY_FLUX, low=30, high=30000):
    """
    Filtra canales de energía entre 'low' y 'high'
    """
    # CHANNEL_ENERGIES está en orden DESCENDENTE: [30000, 20400, ..., 30]
    mask_chan = (CHANNEL_ENERGIES >= low) & (CHANNEL_ENERGIES <= high)
    
    # Aplicar máscara - mantener orden descendente
    CHANNEL_ENERGIES_f = CHANNEL_ENERGIES[mask_chan]
    ELE_DIFF_ENERGY_FLUX_f = ELE_DIFF_ENERGY_FLUX[:, mask_chan]
    ION_DIFF_ENERGY_FLUX_f = ION_DIFF_ENERGY_FLUX[:, mask_chan]

    # CALCULAR DELTA EN ORDEN DESCENDENTE
    # Para energías descendentes: delta[i] = energy_edges[i] - energy_edges[i+1]
    energy_edges = np.zeros(len(CHANNEL_ENERGIES_f) + 1)
    
    # Calcular bordes entre canales
    for i in range(len(CHANNEL_ENERGIES_f) - 1):
        energy_edges[i+1] = (CHANNEL_ENERGIES_f[i] + CHANNEL_ENERGIES_f[i+1]) / 2
    
    # Bordes extremos
    energy_edges[0] = CHANNEL_ENERGIES_f[0] + (CHANNEL_ENERGIES_f[0] - energy_edges[1])
    energy_edges[-1] = CHANNEL_ENERGIES_f[-1] - (energy_edges[-2] - CHANNEL_ENERGIES_f[-1])
    
    # Delta es la diferencia entre bordes consecutivos (positivo porque orden descendente)
    delta = energy_edges[:-1] - energy_edges[1:]
    
    # Verificar que delta sea positivo
    if np.any(delta <= 0):
        delta = np.abs(delta)

    return CHANNEL_ENERGIES_f, ELE_DIFF_ENERGY_FLUX_f, ION_DIFF_ENERGY_FLUX_f, delta