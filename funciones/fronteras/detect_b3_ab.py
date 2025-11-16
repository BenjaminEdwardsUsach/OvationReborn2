import numpy as np

def validate_segment_data(segment, required_keys):
    """Función de validación consistente con otros scripts"""
    for key in required_keys:
        if key not in segment:
            return False, f"Falta clave: {key}"
        if segment[key] is None or len(segment[key]) == 0:
            return False, f"Datos vacíos: {key}"
    
    base_length = len(segment['time'])
    for key in required_keys:
        if len(segment[key]) != base_length:
            return False, f"Longitud inconsistente: {key}"
    
    return True, "OK"

def detect_b3(segment, energy_channels):
    """
    Boundaries 3a,b (electron acceleration events) - CORREGIDO SEGÚN PAPER p.5
    """
    # Validación de datos usando función consistente
    required_keys = ['ele_diff_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        return {
            'b3a': {'index': None, 'time': None, 'lat': None, 'deviation': 0},
            'b3b': {'index': None, 'time': None, 'lat': None, 'deviation': 0}
        }
    
    spectra = segment['ele_diff_flux']
    times = segment['time']
    lats = segment['lat']
    
    acceleration_indices = []
    
    # Umbrales exactos del paper Newell et al. 1996
    PEAK_RATIO = 5.0    # "single channel with differential energy flux 5 times larger"
    DROP_RATIO = 10.0   # "sharp drop by at least a factor of 10"
    
    for i, spectrum in enumerate(spectra):
        # Validación más robusta del espectro
        if spectrum is None or len(spectrum) == 0:
            continue
            
        try:
            # Limpiar NaN y asegurar valores positivos
            clean_spectrum = np.nan_to_num(spectrum, nan=0.0, posinf=0.0, neginf=0.0)
            clean_spectrum = np.maximum(clean_spectrum, 0.0)
            
            # Verificar que haya datos significativos
            if np.max(clean_spectrum) <= 1e-10:
                continue
            
            max_idx = np.argmax(clean_spectrum)
            max_val = clean_spectrum[max_idx]
            
            # Criterio 1: Pico monoenergético (5x mayor que cualquier otro canal)
            other_vals = np.delete(clean_spectrum, max_idx)
            other_max = np.max(other_vals) if len(other_vals) > 0 else 0.0
            
            if other_max > 0 and max_val / other_max >= PEAK_RATIO:
                acceleration_indices.append(i)
                continue
                
            # Criterio 2: Caída brusca sobre el pico (factor 10)
            if max_idx < len(clean_spectrum) - 1:
                next_val = clean_spectrum[max_idx + 1]
                if next_val > 0 and max_val / next_val >= DROP_RATIO:
                    acceleration_indices.append(i)
                    
        except (ValueError, IndexError, RuntimeError):
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
        'b3a': {
            'index': b3a_idx, 
            'time': times[b3a_idx], 
            'lat': lats[b3a_idx], 
            'deviation': 0
        },
        'b3b': {
            'index': b3b_idx, 
            'time': times[b3b_idx], 
            'lat': lats[b3b_idx], 
            'deviation': 0
        }
    }