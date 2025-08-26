import numpy as np
def has_monoenergetic_peak(spectrum, channel_energies, threshold=5.0):
    """
    Determina si un espectro tiene un pico monoenergético
    
    Args:
        spectrum (array): Espectro de flujo diferencial
        channel_energies (array): Energías de los canales
        threshold (float): Umbral para la detección de picos
    
    Returns:
        bool: True si tiene un pico monoenergético, False en caso contrario
    """
    if np.max(spectrum) <= 0:
        return False
    
    # Encontrar el pico máximo
    max_idx = np.argmax(spectrum)
    max_val = spectrum[max_idx]
    
    # Verificar si es un pico monoenergético
    # Condición 1: Un canal con flujo 5 veces mayor que cualquier otro
    if max_val > threshold * np.max(np.delete(spectrum, max_idx)):
        return True
    
    # Condición 2: Caída abrupta por un factor de 10 por encima del pico espectral
    if max_idx < len(spectrum) - 1:
        drop_factor = spectrum[max_idx] / spectrum[max_idx + 1]
        if drop_factor > 10:
            return True
    
    return False