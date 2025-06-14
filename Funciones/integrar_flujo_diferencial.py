import numpy as np

def integrar_flujo_diferencial(ION_DIFF_ENERGY_FLUX, delta, canal1=0, canal2=6):
    """
    Integra el flujo diferencial de iones usando los canales especificados.
    """
    flujos_iones = []
    for elem in ION_DIFF_ENERGY_FLUX:
        flux_value = np.sum(elem[canal1:canal2] * delta[canal1:canal2])
        flujos_iones.append(flux_value)
    return np.array(flujos_iones)
