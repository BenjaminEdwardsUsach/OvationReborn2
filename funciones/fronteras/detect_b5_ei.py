# [file name]: detect_b5_ei.py
import numpy as np

def detect_b5(segment, particle_type='electron'):
    """
    Boundaries 5e/5i - CORREGIDO SEGÚN PAPER p.6
    """
    if particle_type == 'electron':
        name = 'b5e'
        lookahead = 35  # Paper: 35s para electrones
        min_flux_threshold = 10.5  # Paper: "below about 9.7 for ions or 10.5 for electrons"
    else:
        name = 'b5i' 
        lookahead = 30  # Paper: 30s para iones
        min_flux_threshold = 9.7
    
    # Buscar flujo disponible
    flux_key = 'ele_energy_flux' if particle_type == 'electron' else 'ion_energy_flux'
    if flux_key not in segment or len(segment[flux_key]) == 0:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    flux = segment[flux_key]
    times = segment['time']
    lats = segment['lat']
    
    # Convertir a log10
    log_flux = np.log10(np.maximum(flux, 1e-10))
    
    n = len(log_flux)
    window = 12  # Paper: "previous 12 s" vs "succeeding 12 s"
    
    if n < window * 2 + lookahead:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Buscar caída de factor 4 (en escala log: log10(4) ≈ 0.602)
    required_drop = np.log10(4.0)
    
    for i in range(window, n - window - lookahead):
        prev_avg = np.mean(log_flux[i-window:i])
        next_avg = np.mean(log_flux[i:i+window])
        
        drop_magnitude = prev_avg - next_avg
        
        if drop_magnitude >= required_drop:
            # Verificar que permanezca bajo (paper p.6)
            future_fluxes = log_flux[i:min(n, i+lookahead)]
            future_avg = np.mean(future_fluxes)
            
            if future_avg < min_flux_threshold:
                return {
                    'index': i, 
                    'time': times[i], 
                    'lat': lats[i], 
                    'deviation': 0,
                    'drop_magnitude': drop_magnitude
                }
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}