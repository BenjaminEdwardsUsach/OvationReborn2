import numpy as np

def filtrar_canales(CHANNEL_ENERGIES, ELE_DIFF_ENERGY_FLUX, ION_DIFF_ENERGY_FLUX, low=30, high=30000):
    """
    Filtra canales de energía entre 'low' y 'high'
    
    Parámetros:
    -----------
    CHANNEL_ENERGIES : array - Energías de los canales [eV]
    ELE_DIFF_ENERGY_FLUX : array - Flujo diferencial de electrones [eV/cm²/ΔeV/ster/s]
    ION_DIFF_ENERGY_FLUX : array - Flujo diferencial de iones [eV/cm²/ΔeV/ster/s]
    low, high : float - Rango de energía a filtrar [eV]
    
    Retorna:
    --------
    CHANNEL_ENERGIES_f : array - Energías filtradas [eV]
    ELE_DIFF_ENERGY_FLUX_f : array - Flujo diferencial filtrado [eV/cm²/ΔeV/ster/s]
    ION_DIFF_ENERGY_FLUX_f : array - Flujo diferencial filtrado [eV/cm²/ΔeV/ster/s]
    delta : array - Ancho de los canales filtrados [eV]
    """
    # CHANNEL_ENERGIES está en orden DESCENDENTE: [30000, 20400, ..., 30]
    mask_chan = (CHANNEL_ENERGIES >= low) & (CHANNEL_ENERGIES <= high)
    
    # Aplicar máscara - mantener orden descendente
    # Las unidades se preservan en los espectros diferenciales
    CHANNEL_ENERGIES_f = CHANNEL_ENERGIES[mask_chan]
    ELE_DIFF_ENERGY_FLUX_f = ELE_DIFF_ENERGY_FLUX[:, mask_chan]  # [eV/cm²/ΔeV/ster/s]
    ION_DIFF_ENERGY_FLUX_f = ION_DIFF_ENERGY_FLUX[:, mask_chan]  # [eV/cm²/ΔeV/ster/s]

    # CALCULAR DELTA EN ORDEN DESCENDENTE
    # Para energías descendentes: delta[i] = energy_edges[i] - energy_edges[i+1]
    # El resultado delta está en [eV] - representa el ancho de cada canal de energía
    energy_edges = np.zeros(len(CHANNEL_ENERGIES_f) + 1)
    
    # Calcular bordes entre canales
    for i in range(len(CHANNEL_ENERGIES_f) - 1):
        energy_edges[i+1] = (CHANNEL_ENERGIES_f[i] + CHANNEL_ENERGIES_f[i+1]) / 2
    
    # Bordes extremos
    energy_edges[0] = CHANNEL_ENERGIES_f[0] + (CHANNEL_ENERGIES_f[0] - energy_edges[1])
    energy_edges[-1] = CHANNEL_ENERGIES_f[-1] - (energy_edges[-2] - CHANNEL_ENERGIES_f[-1])
    
    # Delta es la diferencia entre bordes consecutivos (positivo porque orden descendente)
    # delta en [eV] - se usa para integración: integral = sum(flujo_diferencial * delta)
    delta = energy_edges[:-1] - energy_edges[1:]
    
    # Verificar que delta sea positivo
    if np.any(delta <= 0):
        delta = np.abs(delta)

    return CHANNEL_ENERGIES_f, ELE_DIFF_ENERGY_FLUX_f, ION_DIFF_ENERGY_FLUX_f, delta