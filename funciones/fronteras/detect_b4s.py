import numpy as np
import warnings
from scipy.ndimage import uniform_filter1d
from scipy.stats import pearsonr
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

def detect_b4s(segment, b2e_idx, b2i_idx):
    """
    Boundary 4s (structured/unstructured transition) - VERSIÓN CORREGIDA
    """
    thresholds = PAPER_THRESHOLDS['b4s']
    
    # Validar datos del segmento
    required_keys = ['ele_diff_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        print(f"   ⚠️ b4s: {msg}")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Obtener índices de forma segura
    safe_b2e = safe_get_index(b2e_idx)
    safe_b2i = safe_get_index(b2i_idx)
    
    # Debe estar poleward de b2e y b2i
    start_idx = max(safe_b2e or 0, safe_b2i or 0) + 1
    spectra = segment['ele_diff_flux']
    n = len(spectra)
    
    # Verificar que start_idx sea válido
    if start_idx >= n - thresholds['n_corr'] - thresholds['n_sum']:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # 1. Calcular coeficientes de correlación SIN WARNINGS
    corr_matrix = np.full((n, thresholds['n_corr']), np.nan)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        
        for i in range(thresholds['n_corr'], n):
            current_corrs = []
            for j in range(1, thresholds['n_corr'] + 1):
                if i - j >= 0:
                    try:
                        # Manejar arrays constantes explícitamente
                        spec1 = spectra[i]
                        spec2 = spectra[i-j]
                        
                        # Verificar si son constantes
                        if (np.all(spec1 == spec1[0]) and np.all(spec2 == spec2[0])):
                            # Ambos constantes: correlación perfecta si iguales, 0 si diferentes
                            corr_val = 1.0 if np.isclose(spec1[0], spec2[0]) else 0.0
                        elif np.all(spec1 == spec1[0]) or np.all(spec2 == spec2[0]):
                            # Solo uno constante: correlación 0
                            corr_val = 0.0
                        else:
                            # Calcular correlación normal
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", category=RuntimeWarning)
                                corr_val = pearsonr(spec1, spec2)[0]
                                if np.isnan(corr_val):
                                    corr_val = 0.0
                        
                        current_corrs.append(corr_val)
                    except Exception:
                        current_corrs.append(0.0)
            
            if current_corrs:
                corr_matrix[i, :len(current_corrs)] = current_corrs
    
    # 2. Calcular promedio SIN WARNINGS
    avg_corr = np.zeros(n)
    for i in range(n):
        row = corr_matrix[i]
        valid_vals = row[~np.isnan(row)]
        avg_corr[i] = np.mean(valid_vals) if len(valid_vals) > 0 else 0.0
    
    # 3. Aplicar supresión para flujos subvisuales
    if 'ele_energy_flux' in segment:
        subvisual_mask = segment['ele_energy_flux'] < thresholds['subvisual_thresh']
        avg_corr[subvisual_mask] *= 0.5
    
    # 4. Suma móvil de correlaciones
    corr_sum = np.zeros(n)
    for i in range(thresholds['n_sum']-1, n):
        start = max(0, i - thresholds['n_sum'] + 1)
        window = avg_corr[start:i+1]
        corr_sum[i] = np.sum(window) if len(window) > 0 else 0.0
    
    # 5. Buscar transición
    transition_point = None
    for i in range(start_idx + thresholds['n_sum'], n):
        if corr_sum[i] < thresholds['sum_threshold']:
            for j in range(i-1, max(start_idx, i-thresholds['n_sum'])-1, -1):
                if j < len(avg_corr) and avg_corr[j] > thresholds['min_corr']:
                    transition_point = j
                    break
            if transition_point is not None:
                break
    
    if transition_point is not None:
        return {'index': transition_point, 'time': segment['time'][transition_point], 
                'lat': segment['lat'][transition_point], 'deviation': 0}
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}