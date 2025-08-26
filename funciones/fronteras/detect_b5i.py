import numpy as np
from .funciones_auxiliares.detect_b5 import detect_b5

def detect_b5i(segment_data):
    """
    Detecta la frontera b5i (borde polar del óvalo auroral para iones)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o valores None si no se detecta
    """
    result = detect_b5(segment_data, 'flux_ion', 9.7)
    if result is None:
        return {'index': None, 'time': None, 'lat': None}
    return result