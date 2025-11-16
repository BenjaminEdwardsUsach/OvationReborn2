import numpy as np
from scipy.ndimage import uniform_filter1d
from .funciones_auxiliares.thresholds import PAPER_THRESHOLDS

def safe_get_index(boundary_dict):
    """Extrae índice de forma segura de un resultado de frontera"""
    if boundary_dict is None:
        return None
    if isinstance(boundary_dict, dict) and 'index' in boundary_dict:
        return boundary_dict['index']
    if isinstance(boundary_dict, (int, np.integer)):
        return boundary_dict
    return None

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

def detect_b2e(segment, b1e_idx):
    """
    Boundary 2e (start of plasma sheet) - VERSIÓN CORREGIDA
    """
    thresholds = PAPER_THRESHOLDS['b2e']
    
    # Validar datos del segmento
    required_keys = ['ele_avg_energy', 'ele_energy_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Obtener b1e_idx de forma segura
    actual_b1e_idx = safe_get_index(b1e_idx)
    
    if actual_b1e_idx is None:
        start_idx = 3
    else:
        # Verificar que el índice esté dentro de los límites
        if actual_b1e_idx >= len(segment['ele_avg_energy']) - thresholds['lookahead'] - 3:
            start_idx = 3
        else:
            start_idx = actual_b1e_idx + 3
    
    # Suavizar energía promedio
    smoothed_energy = uniform_filter1d(segment['ele_avg_energy'], size=3)
    energy_flux = segment['ele_energy_flux']
    
    n = len(smoothed_energy)
    
    # Buscar desde start_idx hacia el polo
    for i in range(start_idx, n - thresholds['lookahead'] - 2):
        current_energy = smoothed_energy[i]
        
        # Verificar que NO haya aumento en los próximos 9 segundos
        future_energies = smoothed_energy[i+1:i+1+thresholds['lookahead']]
        if len(future_energies) == 0:
            continue
            
        future_max = np.max(future_energies)
        
        if current_energy >= future_max:  # dE/dλ ≤ 0
            flux = energy_flux[i]
            
            # Verificación de flujo bajo
            if flux < thresholds['low_flux_thresh'] or (flux < thresholds['low_flux_thresh'] + 0.5 and 
                                                       segment['ele_avg_energy'][i] < thresholds['energy_thresh']):
                
                # Doble verificación según paper
                check_end = min(i + thresholds['verification_window'], len(energy_flux))
                if check_end <= i:
                    continue
                    
                next_fluxes = energy_flux[i:check_end]
                next_energies = segment['ele_avg_energy'][i:check_end]
                
                higher_flux = next_fluxes > flux + 0.3
                higher_energy = next_energies > segment['ele_avg_energy'][i]
                
                # Si NO hay espectros con flujo y energía mayores, aceptar
                if not np.any(higher_flux & higher_energy):
                    return {'index': i, 'time': segment['time'][i], 'lat': segment['lat'][i], 'deviation': 0}
            else:
                # Flujo suficientemente alto, aceptar directamente
                return {'index': i, 'time': segment['time'][i], 'lat': segment['lat'][i], 'deviation': 0}
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}