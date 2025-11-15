import numpy as np
from .funciones_auxiliares.thresholds import PAPER_THRESHOLDS

def validate_segment_data(segment, required_keys):
    """Valida que el segmento tenga los datos necesarios"""
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

def detect_b3(segment, energy_channels):
    """
    Boundaries 3a,b (electron acceleration events) - VERSIÓN CORREGIDA CON UMBRALES
    """
    thresholds = PAPER_THRESHOLDS.get('b3a', {})
    
    # Validación de datos
    required_keys = ['ele_diff_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        print(f"   ⚠️ b3: {msg}")
        return {
            'b3a': {'index': None, 'time': None, 'lat': None, 'deviation': 0},
            'b3b': {'index': None, 'time': None, 'lat': None, 'deviation': 0}
        }
    
    spectra = segment['ele_diff_flux']
    acceleration_indices = []
    
    # Usar umbrales del paper
    peak_ratio = thresholds.get('min_peak_ratio', 5)
    drop_ratio = thresholds.get('drop_ratio', 10)
    min_flux_threshold = thresholds.get('min_flux', 1e-10)
    
    for i, spectrum in enumerate(spectra):
        if spectrum is None or len(spectrum) == 0 or np.nanmax(spectrum) <= min_flux_threshold:
            continue
            
        try:
            max_idx = np.nanargmax(spectrum)
            max_val = spectrum[max_idx]
            
            # Verificar que el máximo sea significativo
            if max_val <= min_flux_threshold:
                continue
                
            # Criterio 1: Pico monoenergético (5x mayor que cualquier otro canal)
            other_vals = np.delete(spectrum, max_idx)
            if len(other_vals) > 0 and max_val > peak_ratio * np.nanmax(other_vals):
                acceleration_indices.append(i)
                continue
                
            # Criterio 2: Caída brusca sobre el pico (factor 10)
            if (max_idx < len(spectrum) - 1 and 
                max_val > drop_ratio * spectrum[max_idx + 1]):
                acceleration_indices.append(i)
                
        except (ValueError, IndexError):
            continue
    
    if not acceleration_indices:
        return {
            'b3a': {'index': None, 'time': None, 'lat': None, 'deviation': 0},
            'b3b': {'index': None, 'time': None, 'lat': None, 'deviation': 0}
        }
    
    # b3a: más ecuatorial, b3b: más polar
    b3a_idx = min(acceleration_indices)
    b3b_idx = max(acceleration_indices)
    
    return {
        'b3a': {'index': b3a_idx, 'time': segment['time'][b3a_idx], 
                'lat': segment['lat'][b3a_idx], 'deviation': 0},
        'b3b': {'index': b3b_idx, 'time': segment['time'][b3b_idx], 
                'lat': segment['lat'][b3b_idx], 'deviation': 0}
    }