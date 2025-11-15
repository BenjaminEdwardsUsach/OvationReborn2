import numpy as np
from scipy.ndimage import uniform_filter1d
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

def detect_b2i(segment, energy_channels):
    """
    Boundary 2i (ion isotropy boundary) - VERSIÓN CORREGIDA
    """
    thresholds = PAPER_THRESHOLDS['b2i']
    
    # Validar datos del segmento
    required_keys = ['ion_diff_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        print(f"   ⚠️ b2i: {msg}")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Máscara para iones 3-30 keV
    energy_mask = (energy_channels >= thresholds['min_energy']) & (energy_channels <= thresholds['max_energy'])
    if not np.any(energy_mask):
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Calcular flujo parcial de iones de alta energía
    partial_flux = np.sum(segment['ion_diff_flux'][:, energy_mask], axis=1)
    log_flux = np.log10(partial_flux + 1e-10)
    
    # Suavizado de 2s como especifica el paper
    smoothed_flux = uniform_filter1d(log_flux, size=thresholds['avg_window'])
    
    n = len(smoothed_flux)
    candidates = []
    
    # Buscar máximos locales
    for i in range(thresholds['avg_window'], n - thresholds['lookahead'] - 2):
        current_avg = np.mean(smoothed_flux[i-thresholds['avg_window']:i])
        
        # Verificar que sea mayor o igual que cualquier promedio de 3s en los próximos 10s
        is_maximum = True
        for j in range(i+1, min(i+1+thresholds['lookahead'], n-2)):
            future_avg = np.mean(smoothed_flux[j:j+3])
            if future_avg > current_avg:
                is_maximum = False
                break
        
        if (is_maximum and 
            current_avg >= thresholds['min_flux'] and
            current_avg == np.max(smoothed_flux[max(0,i-5):min(n,i+5)])):
            candidates.append(i)
    
    # Manejar eventos "nose" - descartar máximos aislados
    if candidates:
        # Tomar el candidato más ecuatorial (menor índice)
        best_candidate = min(candidates)
        return {'index': best_candidate, 'time': segment['time'][best_candidate], 
                'lat': segment['lat'][best_candidate], 'deviation': 0}
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}