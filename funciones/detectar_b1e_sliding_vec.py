import numpy as np
from scipy.ndimage import uniform_filter1d

def detect_b1e(segment, energy_channels, low_energy_range=(32, 47), 
               min_jump=2.0, high_flux_jump=1.6, high_flux_thresh=8.0, 
               very_high_flux=8.25, background_window=10):
    """
    Detecta Boundary 1e (zero-energy electron boundary)
    
    Args:
        segment: dict con keys 'time', 'lat', 'ele_diff_flux'
        energy_channels: array de energías de los canales
        low_energy_range: tupla (E_min, E_max) para flujo parcial
        min_jump: factor mínimo de salto para detección
        high_flux_jump: factor de salto cuando flujo es alto
        high_flux_thresh: umbral para considerar flujo alto
        very_high_flux: umbral para detección directa
        background_window: ventana para cálculo de fondo
        
    Returns:
        Índice del segmento donde se detecta b1e, o None
    """
    # 1. Determinar canales de energía a usar
    low_idx = np.where((energy_channels >= low_energy_range[0]) & 
                       (energy_channels <= low_energy_range[1]))[0]
    
    if len(low_idx) == 0:
        return None
    
    # 2. Calcular flujo parcial integrado
    partial_flux = np.sum(segment['ele_diff_flux'][:, low_idx], axis=1)
    log_flux = np.log10(partial_flux)
    
    # 3. Detectar fotoelectrones (caída brusca >68 eV)
    high_e_idx = np.where(energy_channels > 68)[0]
    if len(high_e_idx) > 0:
        high_flux = np.mean(segment['ele_diff_flux'][:, high_e_idx], axis=1)
        photoelectron_mask = (high_flux < 0.1 * partial_flux) & (segment['lat'] < 60)
        if np.any(photoelectron_mask):
            # Ajustar rango de energía si hay fotoelectrones
            clean_channels = energy_channels[energy_channels > 100]
            if len(clean_channels) > 1:
                new_low = clean_channels[0]
                new_high = clean_channels[1]
                low_idx = np.where((energy_channels >= new_low) & 
                                   (energy_channels <= new_high))[0]
                partial_flux = np.sum(segment['ele_diff_flux'][:, low_idx], axis=1)
                log_flux = np.log10(partial_flux)
    
    # 4. Calcular fondo (promedio ecuatorial)
    background = np.mean(log_flux[:background_window])
    
    # 5. Detectar límite moviéndose de sur a norte
    n = len(log_flux)
    for i in range(3, n-3):
        prev_avg = np.mean(log_flux[i-3:i])
        next_avg = np.mean(log_flux[i:i+3])
        
        # Verificar si el flujo es muy alto
        if log_flux[i] >= very_high_flux:
            return i
        
        # Determinar factor de salto requerido
        required_jump = high_flux_jump if log_flux[i] >= high_flux_thresh else min_jump
        
        # Verificar salto significativo
        if (next_avg > prev_avg * required_jump and 
            next_avg > background + 0.3):  # 0.3 en log ≈ 2x
            # Doble verificación: asegurar que no es ruido
            if np.all(log_flux[i:i+3] > background):
                return i
    
    return None