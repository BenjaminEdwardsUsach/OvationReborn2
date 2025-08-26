import numpy as np
from .funciones_auxiliares.detect_b5 import detect_b5

def detect_b5e(segment_data):
    """
    Detecta la frontera b5e (borde polar del óvalo auroral para electrones)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o valores None si no se detecta
    """
    result = detect_b5(segment_data, 'flux_ele', 10.5)
    if result is None:
        return {'index': None, 'time': None, 'lat': None}
    return result