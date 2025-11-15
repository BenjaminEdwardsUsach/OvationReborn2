# safe_utils.py
import numpy as np

def safe_statistics(array, default_value=0):
    """Calcula estadísticas de forma segura para arrays que pueden estar vacíos"""
    if array is None or array.size == 0:
        return default_value, default_value, 0
    
    valid_data = array[~np.isnan(array)]
    if valid_data.size == 0:
        return default_value, default_value, 0
    
    return np.min(valid_data), np.max(valid_data), valid_data.size

def safe_min_max(array, default_min=0, default_max=0):
    """Calcula min y max de forma segura"""
    if array is None or array.size == 0:
        return default_min, default_max
    
    valid_data = array[~np.isnan(array)]
    if valid_data.size == 0:
        return default_min, default_max
    
    return np.min(valid_data), np.max(valid_data)