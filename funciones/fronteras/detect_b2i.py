# [file name]: detect_b2i.py
import numpy as np
from scipy.ndimage import uniform_filter1d

def detect_b2i(segment, energy_channels):
    """
    Boundary 2i (ion isotropy boundary) - CORREGIDO SEGÚN PAPER p.5
    """
    # Validación de datos
    required_keys = ['ion_diff_flux', 'time', 'lat']
    for key in required_keys:
        if key not in segment or len(segment[key]) == 0:
            return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Máscara para iones 3-30 keV (paper p.5)
    energy_mask = (energy_channels >= 3000) & (energy_channels <= 30000)
    if not np.any(energy_mask):
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Calcular flujo parcial
    partial_flux = np.sum(segment['ion_diff_flux'][:, energy_mask], axis=1)
    
    if np.all(partial_flux <= 0) or np.all(np.isnan(partial_flux)):
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    log_flux = np.log10(partial_flux + 1e-10)
    
    # Suavizado de 2s exacto como paper
    smoothed_flux = uniform_filter1d(log_flux, size=2)
    
    n = len(smoothed_flux)
    
    candidates = []
    
    for i in range(2, n - 10):  # paper: comparar con próximos 10s
        current_val = smoothed_flux[i]
        
        # UMBRAL MÍNIMO: 10.5 (paper p.5)
        if current_val < 10.5:
            continue
            
        # Verificar que sea máximo comparando con próximos 10s
        future_max = np.max(smoothed_flux[i+1:min(n, i+11)])
        if current_val >= future_max:
            candidates.append(i)
    
    # Filtrar eventos "nose" (paper p.5)
    valid_candidates = []
    for i, candidate in enumerate(candidates):
        is_nose_event = False
        
        # Buscar si hay un máximo global más poleward
        for j in range(i+1, len(candidates)):
            if (candidates[j] > candidate and 
                smoothed_flux[candidates[j]] > smoothed_flux[candidate]):
                is_nose_event = True
                break
                
        if not is_nose_event:
            valid_candidates.append(candidate)
    
    if valid_candidates:
        # Tomar el candidato más ecuatorial (menor índice)
        best_candidate = min(valid_candidates)
        return {
            'index': best_candidate, 
            'time': segment['time'][best_candidate], 
            'lat': segment['lat'][best_candidate], 
            'deviation': 0
        }
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}