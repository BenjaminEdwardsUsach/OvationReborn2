import numpy as np

def validate_segment_data(segment, required_keys):
    """
    Valida que el segmento tenga los datos necesarios y longitudes consistentes.
    
    Parámetros:
    -----------
    segment : dict - Diccionario con datos del segmento
    required_keys : list - Lista de claves requeridas
    
    Retorna:
    --------
    tuple (bool, str) - (validez, mensaje)
    """
    for key in required_keys:
        if key not in segment:
            return False, f"Falta clave: {key}"
        if segment[key] is None or len(segment[key]) == 0:
            return False, f"Datos vacíos: {key}"
    
    # Verificar consistencia de longitudes
    base_length = len(segment['time'])
    for key in required_keys:
        if len(segment[key]) != base_length:
            return False, f"Longitud inconsistente: {key}"
    
    return True, "OK"