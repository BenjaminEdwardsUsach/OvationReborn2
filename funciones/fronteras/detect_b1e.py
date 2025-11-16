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

def detect_b1e(segment, energy_channels):
    """
    Boundary 1e (zero-energy electron boundary) - VERSIÓN CORREGIDA
    """
    thresholds = PAPER_THRESHOLDS['b1e']
    
    # Validar datos del segmento
    required_keys = ['ele_diff_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        print(f"   ⚠️ b1e: {msg}")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # 1. Determinar canales de energía según condiciones del spacecraft
    # USAR UMBRALES DEL PAPER EN LUGAR DE VALORES FIJOS
    low_mask = (energy_channels >= thresholds.get('low_energy_min', 32)) & (energy_channels <= thresholds.get('low_energy_max', 47))
    
    # Verificar fotoelectrones (raro en nightside)
    high_mask = energy_channels > thresholds.get('high_energy_thresh', 68)
    if np.any(high_mask):
        high_flux = np.mean(segment['ele_diff_flux'][:, high_mask], axis=1)
        photoelectron_mask = (high_flux < 0.1 * np.sum(segment['ele_diff_flux'][:, low_mask], axis=1)) & (segment['lat'] < 60)
        if np.any(photoelectron_mask):
            # Usar canales "limpios" 100-145 eV
            clean_mask = (energy_channels > thresholds.get('clean_energy_min', 100)) & (energy_channels < thresholds.get('clean_energy_max', 145))
            if np.any(clean_mask):
                low_mask = clean_mask
    
    # 2. Calcular flujo parcial
    partial_flux = np.sum(segment['ele_diff_flux'][:, low_mask], axis=1)
    log_flux = np.log10(partial_flux + 1e-10)
    
    n = len(log_flux)
    if n < thresholds['background_window'] + 6:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # 3. Calcular fondo (primeros 10 segundos)
    background = np.mean(log_flux[:thresholds['background_window']])
    
    # 4. Algoritmo principal: comparar 3 anteriores vs 3 siguientes
    for i in range(3, n - 3):
        prev_avg = np.mean(log_flux[i-3:i])    # 3 anteriores
        next_avg = np.mean(log_flux[i:i+3])    # 3 siguientes ← CORREGIR
        
        # Evitar división por cero
        if prev_avg <= 0:
            continue
            
        jump_ratio = next_avg / prev_avg
        
        # Criterio 1: Flujo muy alto (detección directa)
        if log_flux[i] >= thresholds['very_high_flux']:
            return {'index': i, 'time': segment['time'][i], 'lat': segment['lat'][i], 'deviation': 0}
        
        # Criterio 2: Salto significativo sobre fondo
        required_jump = thresholds['min_jump']
        if log_flux[i] >= thresholds['high_flux_thresh']:
            required_jump = thresholds['high_flux_jump']
        
        if (jump_ratio >= required_jump and 
            next_avg > background + 0.3 and
            np.all(log_flux[i:i+3] > background)):
            # Verificación adicional: asegurar que no sea falso positivo
            future_avg = np.mean(log_flux[i:min(i+6, n)])
            if future_avg > background + 0.2:
                return {'index': i, 'time': segment['time'][i], 'lat': segment['lat'][i], 'deviation': 0}
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}