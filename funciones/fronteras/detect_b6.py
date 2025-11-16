# [file name]: detect_b6.py
def detect_b6(segment, b5e_idx):
    """
    Boundary 6 (subvisual drizzle edge) - CORREGIDO SEGÚN PAPER p.7
    """
    # Validación de datos
    required_keys = ['ele_energy_flux', 'ion_energy_flux', 'time', 'lat']
    for key in required_keys:
        if key not in segment or len(segment[key]) == 0:
            return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    if b5e_idx is None or b5e_idx >= len(segment['ele_energy_flux']) - 1:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    je = segment['ele_energy_flux']
    ji = segment['ion_energy_flux']
    times = segment['time']
    lats = segment['lat']
    
    MIN_FLUX_E = 10.4  # jE drops below 10.4
    MIN_FLUX_I = 9.6   # jE drops below 9.6
    
    # Buscar desde b5e hacia el polo
    start_idx = b5e_idx + 1
    
    for i in range(start_idx, len(je)):
        current_je = je[i]
        current_ji = ji[i]
        
        # Caso 1: Polar rain (paper: unstructured electrons and no ions)
        if current_ji < MIN_FLUX_I and current_je > MIN_FLUX_E - 0.5:
            return {
                'index': i, 
                'time': times[i], 
                'lat': lats[i], 
                'deviation': 0,
                'reason': 'polar_rain'
            }
        
        # Caso 2: Caída por debajo de umbrales físicos
        if current_je < MIN_FLUX_E and current_ji < MIN_FLUX_I:
            return {
                'index': i, 
                'time': times[i], 
                'lat': lats[i], 
                'deviation': 0,
                'reason': 'low_flux'
            }
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}