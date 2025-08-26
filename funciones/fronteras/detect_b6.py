import numpy as np
from .funciones_auxiliares.is_polar_rain import is_polar_rain

def detect_b6(segment_data, b5e_data, b5i_data):
    """
    Detecta la frontera b6 (límite polar de la llovizna subvisual)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        b5e_data (dict): Datos de la frontera b5e con clave 'index'
        b5i_data (dict): Datos de la frontera b5i con clave 'index'
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o None si no se detecta
    """
    # Extraer índice de b5e si está disponible
    if b5e_data is None or b5e_data['index'] is None:
        return None
    
    b5e_index = b5e_data['index']
    
    flux_ele = segment_data['flux_ele']
    flux_ion = segment_data['flux_ion']
    ele_avg_energy = segment_data['ele_avg_energy']
    n = len(flux_ele)
    
    # Empezar desde b5e_index
    for i in range(b5e_index, n):
        # Verificar si encontramos lluvia polar (electrones no estructurados y sin iones)
        # o si el flujo cae por debajo de los umbrales
        if (flux_ele[i] < 10.4 and flux_ion[i] < 9.6) or is_polar_rain(segment_data, i):
            # Verificar que la energía promedio es baja (no ruido)
            if ele_avg_energy[i] < 500:  # eV
                return {
                    'index': i,
                    'time': segment_data['time'][i],
                    'lat': segment_data['lat'][i]
                }
    
    return None