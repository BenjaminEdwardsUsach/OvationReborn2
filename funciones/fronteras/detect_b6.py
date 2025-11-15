import numpy as np
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

def detect_b6(segment, b5e_idx):
    """
    Boundary 6 (subvisual drizzle edge) - VERSIÓN CORREGIDA
    """
    thresholds = PAPER_THRESHOLDS['b6']
    
    # Validar datos del segmento
    required_keys = ['ele_energy_flux', 'ion_energy_flux', 'time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        print(f"   ⚠️ b6: {msg}")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Obtener b5e_idx de forma segura
    actual_b5e_idx = safe_get_index(b5e_idx)
    
    if actual_b5e_idx is None:
        print("   ⚠️ b6: b5e no detectado, no se puede buscar b6")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    if actual_b5e_idx >= len(segment['ele_energy_flux']) - 1:
        print("   ⚠️ b6: b5e_idx al final del segmento")
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    je = segment['ele_energy_flux']
    ji = segment['ion_energy_flux']
    
    # ✅ CORRECCIÓN: Verificar si los flujos están en escala logarítmica
    if np.max(je) > 100:  # Si no están en log, convertirlos
        je = np.log10(np.maximum(je, 1e-10))
        ji = np.log10(np.maximum(ji, 1e-10))
    
    # Diagnóstico
    print(f"   🔍 b6: Flujos en b5e_idx={actual_b5e_idx} - " +
          f"je: {je[actual_b5e_idx]:.2f}, ji: {ji[actual_b5e_idx]:.2f}")
    
    # Buscar desde b5e hacia el polo
    start_idx = actual_b5e_idx + 1
    
    for i in range(start_idx, len(je)):
        # Caso 1: Encuentro con polar rain (no estructurada, sin iones)
        if (ji[i] < thresholds['min_flux_i'] and 
            je[i] > thresholds['min_flux_e'] - 0.5):
            print(f"   ✅ b6: Polar rain detectado en índice {i}")
            return {'index': i, 'time': segment['time'][i], 
                    'lat': segment['lat'][i], 'deviation': 0}
        
        # Caso 2: Caída por debajo de umbrales físicos
        low_flux = (je[i] < thresholds['min_flux_e']) and (ji[i] < thresholds['min_flux_i'])
        
        if low_flux:
            print(f"   ✅ b6: Flujo bajo detectado en índice {i}")
            return {'index': i, 'time': segment['time'][i], 
                    'lat': segment['lat'][i], 'deviation': 0}
    
    print("   ❌ b6: No se detectó")
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}