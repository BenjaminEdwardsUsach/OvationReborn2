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

def detect_b5(segment, particle_type='electron'):
    """
    Boundaries 5e/5i - VERSIÓN CORREGIDA CON ESCALA LOGARÍTMICA
    """
    if particle_type == 'electron':
        thresholds = PAPER_THRESHOLDS['b5e']
        flux_candidates = ['ele_energy_flux', 'flux_ele', 'ele_total_energy']
        name = 'b5e'
    else:
        thresholds = PAPER_THRESHOLDS['b5i'] 
        flux_candidates = ['ion_energy_flux', 'flux_ion', 'ion_total_energy']
        name = 'b5i'
    
    # Buscar flujo disponible
    flux = None
    used_key = None
    for key in flux_candidates:
        if key in segment:
            data = segment[key]
            if data is not None and len(data) > 0 and not np.all(np.isnan(data)):
                flux = data
                used_key = key
                break
    
    if flux is None:
        print(f"   ⚠️ {name}: No se encontró flujo para {particle_type}")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # ✅ CORRECCIÓN CRÍTICA: Convertir a log10 ANTES de calcular diferencias
    log_flux = np.log10(np.maximum(flux, 1e-10))
    
    # Diagnóstico detallado
    print(f"   🔍 {name}: Flujo {particle_type} (log10) - " +
          f"rango: [{np.min(log_flux):.2f}, {np.max(log_flux):.2f}], " +
          f"umbral: {np.log10(thresholds['min_flux']):.2f}")
    
    n = len(log_flux)
    if n < thresholds['window'] * 2 + thresholds['lookahead']:
        print(f"   ⚠️ {name}: Segmento muy corto ({n} puntos)")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Algoritmo de detección - TODO en escala logarítmica
    window = thresholds['window']
    log_drop = np.log10(thresholds['drop_factor'])  # log10(4) ≈ 0.602
    log_min_flux = np.log10(thresholds['min_flux'])
    
    for i in range(window, n - window - thresholds['lookahead']):
        prev_avg = np.mean(log_flux[i-window:i])
        next_avg = np.mean(log_flux[i:i+window])
        
        drop_magnitude = prev_avg - next_avg
        
        # Verificar caída de factor 4 (en escala logarítmica)
        if drop_magnitude >= log_drop and prev_avg > log_min_flux:
            # Verificar que en el futuro permanezca bajo
            look_end = min(i + thresholds['lookahead'], n)
            future_fluxes = log_flux[i:look_end]
            
            if not np.any(future_fluxes > log_min_flux):
                print(f"   ✅ {name}: Detectado en índice {i}, " +
                      f"drop: {drop_magnitude:.3f} (requerido: {log_drop:.3f})")
                return {'index': i, 'time': segment['time'][i], 
                        'lat': segment['lat'][i], 'deviation': 0}
    
    print(f"   ❌ {name}: No se detectó caída suficiente")
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}