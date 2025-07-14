import numpy as np
from scipy.stats import pearsonr
from scipy.ndimage import uniform_filter1d

def detect_b1e(segment, energy_channels, low_energy_range=(32, 47), 
               min_jump=2.0, high_flux_jump=1.6, high_flux_thresh=8.0, 
               very_high_flux=8.25, background_window=10):
    """
    Detecta Boundary 1e (zero-energy electron boundary) - Optimizada
    
    Args:
        segment: dict con keys 'ele_diff_flux', 'lat', 'time'
        energy_channels: array de energías de los canales
        low_energy_range: tupla (E_min, E_max) para flujo parcial
        min_jump: factor mínimo de salto para detección
        high_flux_jump: factor de salto cuando flujo es alto
        high_flux_thresh: umbral para considerar flujo alto
        very_high_flux: umbral para detección directa
        background_window: ventana para cálculo de fondo
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    # Vectorización de cálculos
    low_mask = (energy_channels >= low_energy_range[0]) & (energy_channels <= low_energy_range[1])
    if not np.any(low_mask):
        return None, None, None
    
    # Cálculo de flujo parcial
    partial_flux = np.sum(segment['ele_diff_flux'][:, low_mask], axis=1)
    log_flux = np.log10(partial_flux + 1e-10)  # Evitar log(0)
    
    # Manejo de fotoelectrones (vectorizado)
    high_mask = energy_channels > 68
    if np.any(high_mask):
        high_flux = np.mean(segment['ele_diff_flux'][:, high_mask], axis=1)
        photoelectron_mask = (high_flux < 0.1 * partial_flux) & (segment['lat'] < 60)
        if np.any(photoelectron_mask):
            clean_mask = (energy_channels > 100) & (energy_channels < 145)
            if np.any(clean_mask):
                low_mask = clean_mask
                partial_flux = np.sum(segment['ele_diff_flux'][:, low_mask], axis=1)
                log_flux = np.log10(partial_flux + 1e-10)
    
    # Cálculo de fondo y detección de salto
    background = np.mean(log_flux[:background_window])
    n = len(log_flux)
    
    # Precalcular promedios móviles
    prev_avg = uniform_filter1d(log_flux, size=3, origin=-1)[:n-3]
    next_avg = uniform_filter1d(log_flux, size=3, origin=1)[2:n-1]
    
    # Condiciones de detección
    jump_factors = np.full(n-3, min_jump)
    high_flux_mask = log_flux[3:-3] >= high_flux_thresh
    jump_factors[high_flux_mask] = high_flux_jump
    
    cond1 = log_flux[3:-3] >= very_high_flux
    cond2 = (next_avg > prev_avg * jump_factors) & (next_avg > background + 0.3)
    cond3 = np.all([log_flux[i:i+3] > background for i in range(3, n-3)], axis=1)
    
    # Encontrar el primer punto que cumpla las condiciones
    detection_points = np.where(cond1 | (cond2 & cond3))[0]
    if detection_points.size > 0:
        idx = detection_points[0] + 3
        return idx, segment['time'][idx], segment['lat'][idx]
    
    return None, None, None

def detect_b2e(segment, b1e_idx, window=3, lookahead=9, 
               low_flux_thresh=11.0, energy_thresh=1000):
    """
    Detecta Boundary 2e (start of plasma sheet) - Optimizada
    
    Args:
        segment: dict con 'ele_avg_energy', 'ele_energy_flux', 'time', 'lat'
        b1e_idx: índice de b1e
        window: tamaño de ventana para promedio
        lookahead: puntos adelante para comparación
        low_flux_thresh: umbral de flujo bajo
        energy_thresh: umbral de energía para verificación
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    if b1e_idx is None or b1e_idx >= len(segment['ele_avg_energy']) - window - lookahead:
        return None, None, None
    
    # Vectorización de cálculos
    smoothed_energy = uniform_filter1d(segment['ele_avg_energy'], size=window)
    n = len(smoothed_energy)
    start_idx = b1e_idx + window
    
    # Buscar punto donde la energía deja de aumentar
    for i in range(start_idx, n - lookahead - 2):
        current_energy = smoothed_energy[i]
        future_energies = smoothed_energy[i+1:i+1+lookahead]
        
        if not np.any(future_energies > current_energy):
            flux = segment['ele_energy_flux'][i]
            if flux < low_flux_thresh or (flux < low_flux_thresh + 0.5 and segment['ele_avg_energy'][i] < energy_thresh):
                # Verificación adicional para flujos bajos
                next_30s = segment['ele_energy_flux'][i:i+30]
                next_energies = segment['ele_avg_energy'][i:i+30]
                higher_flux = next_30s > flux + 0.3
                higher_energy = next_energies > segment['ele_avg_energy'][i]
                if np.any(higher_flux & higher_energy):
                    continue
            return i, segment['time'][i], segment['lat'][i]
    
    return None, None, None

def detect_b2i(segment, energy_channels, min_energy=3000, max_energy=30000,
               window_avg=2, lookahead=10, min_flux=10.5):
    """
    Detecta Boundary 2i (ion isotropy boundary) - Optimizada
    
    Args:
        segment: dict con 'ion_diff_flux', 'time', 'lat'
        energy_channels: array de energías
        min_energy: energía mínima para flujo parcial
        max_energy: energía máxima para flujo parcial
        window_avg: ventana para suavizado
        lookahead: puntos adelante para comparación
        min_flux: flujo mínimo para considerar
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    # Vectorización de cálculos
    energy_mask = (energy_channels >= min_energy) & (energy_channels <= max_energy)
    if not np.any(energy_mask):
        return None, None, None
    
    partial_flux = np.sum(segment['ion_diff_flux'][:, energy_mask], axis=1)
    log_flux = np.log10(partial_flux + 1e-10)
    smoothed_flux = uniform_filter1d(log_flux, size=window_avg)
    n = len(smoothed_flux)
    
    # Detectar máximos locales
    maxima = (smoothed_flux[1:-1] > smoothed_flux[:-2]) & (smoothed_flux[1:-1] > smoothed_flux[2:])
    maxima_indices = np.where(maxima)[0] + 1
    valid_maxima = maxima_indices[(smoothed_flux[maxima_indices] >= min_flux) & 
                                 (maxima_indices < n - lookahead - 2)]
    
    # Filtrar máximos que no tienen valores mayores adelante
    candidates = []
    for i in valid_maxima:
        future_max = np.max(smoothed_flux[i+1:i+1+lookahead])
        if smoothed_flux[i] >= future_max:
            candidates.append(i)
    
    # Manejar eventos "nose"
    if candidates:
        best_candidate = candidates[np.argmax(smoothed_flux[candidates])]
        return best_candidate, segment['time'][best_candidate], segment['lat'][best_candidate]
    
    return None, None, None

def detect_b3(segment, energy_channels, min_peak_ratio=5, min_drop_ratio=10):
    """
    Detecta Boundaries 3a y 3b (electron acceleration events) - Optimizada
    
    Args:
        segment: dict con 'ele_diff_flux', 'time', 'lat'
        energy_channels: array de energías
        min_peak_ratio: ratio mínimo para pico monoenergético
        min_drop_ratio: ratio mínimo para caída sobre pico
        
    Returns:
        (b3a_idx, b3a_time, b3a_lat, b3b_idx, b3b_time, b3b_lat) o (None,)*6
    """
    acceleration_indices = []
    spectra = segment['ele_diff_flux']
    
    # Vectorización de detección de eventos
    for i, spectrum in enumerate(spectra):
        max_idx = np.argmax(spectrum)
        max_val = spectrum[max_idx]
        
        # Criterio 1: Pico monoenergético
        if max_val > min_peak_ratio * np.max(np.delete(spectrum, max_idx)):
            acceleration_indices.append(i)
            continue
            
        # Criterio 2: Caída brusca sobre el pico
        if max_idx < len(spectrum) - 1 and max_val > min_drop_ratio * spectrum[max_idx+1]:
            acceleration_indices.append(i)
    
    if not acceleration_indices:
        return (None,)*6
    
    # Encontrar eventos más ecuatorial y polar
    b3a_idx = np.min(acceleration_indices)
    b3b_idx = np.max(acceleration_indices)
    
    return (
        b3a_idx, segment['time'][b3a_idx], segment['lat'][b3a_idx],
        b3b_idx, segment['time'][b3b_idx], segment['lat'][b3b_idx]
    )

def detect_b4s(segment, b2e_idx, b2i_idx, min_corr=0.6, sum_threshold=4.0, 
               subvisual_thresh=10.7, n_corr=5, n_sum=7):
    """
    Detecta Boundary 4s (structured/unstructured transition) - Optimizada
    
    Args:
        segment: dict con 'ele_diff_flux', 'ele_energy_flux', 'time', 'lat'
        b2e_idx: índice de b2e
        b2i_idx: índice de b2i
        min_corr: correlación mínima para considerar estructurado
        sum_threshold: umbral para suma de correlaciones
        subvisual_thresh: umbral de flujo para aurora subvisual
        n_corr: número de correlaciones a calcular
        n_sum: número de puntos para suma móvil
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    start_idx = max(b2e_idx or 0, b2i_idx or 0) + 1
    n_spectra = len(segment['ele_diff_flux'])
    
    if start_idx >= n_spectra - n_corr - n_sum:
        return None, None, None
    
    # Precalcular correlaciones
    corr_matrix = np.zeros((n_spectra, n_corr))
    spectra = segment['ele_diff_flux']
    
    for j in range(1, n_corr+1):
        for i in range(j, n_spectra):
            corr_matrix[i, j-1] = pearsonr(spectra[i], spectra[i-j])[0]
    
    avg_corr = np.mean(corr_matrix, axis=1)
    flux_mask = segment['ele_energy_flux'] < subvisual_thresh
    avg_corr[flux_mask] *= 0.5
    
    # Suma móvil de correlaciones
    corr_sum = uniform_filter1d(avg_corr, size=n_sum, mode='constant', origin=(n_sum-1)//2)
    
    # Detectar transición
    for i in range(start_idx + n_sum, n_spectra):
        if corr_sum[i] < sum_threshold:
            # Buscar hacia atrás el último punto con correlación alta
            for j in range(i, i-n_sum, -1):
                if avg_corr[j] > min_corr:
                    return j, segment['time'][j], segment['lat'][j]
    
    return None, None, None

def detect_b5(segment, particle_type='electron', window=12, drop_factor=4,
              min_flux_e=10.5, min_flux_i=9.7, lookahead_e=30, lookahead_i=35):
    """
    Detecta Boundaries 5e/5i (poleward oval edge) - Optimizada
    
    Args:
        segment: dict con 'ele_energy_flux', 'ion_energy_flux', 'time', 'lat'
        particle_type: 'electron' o 'ion'
        window: tamaño de ventana para promedio
        drop_factor: factor de caída requerido
        min_flux_e: flujo mínimo para electrones fuera del óvalo
        min_flux_i: flujo mínimo para iones fuera del óvalo
        lookahead_e: puntos adelante para verificación (electrones)
        lookahead_i: puntos adelante para verificación (iones)
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    # Seleccionar parámetros según tipo de partícula
    if particle_type == 'electron':
        flux = segment['ele_energy_flux']
        min_flux = min_flux_e
        lookahead = lookahead_e
    else:
        flux = segment['ion_energy_flux']
        min_flux = min_flux_i
        lookahead = lookahead_i
    
    log_drop = np.log10(drop_factor)
    n = len(flux)
    
    # Cálculo de promedios móviles
    prev_avg = uniform_filter1d(flux, size=window, origin=-window//2)[:n-window]
    next_avg = uniform_filter1d(flux, size=window, origin=window//2)[window:]
    
    # Detectar caídas significativas
    drop_mask = (prev_avg - next_avg) >= log_drop
    for i in np.where(drop_mask)[0]:
        start = i + window
        end = min(start + lookahead, n)
        
        if not np.any(flux[start:end] > min_flux):
            return i + window//2, segment['time'][i + window//2], segment['lat'][i + window//2]
    
    return None, None, None

def detect_b6(segment, b5e_idx, min_flux_e=10.4, min_flux_i=9.6, 
              max_energy=500, min_flux_physical=10.0):
    """
    Detecta Boundary 6 (subvisual drizzle edge) - Optimizada
    
    Args:
        segment: dict con 'ele_energy_flux', 'ion_energy_flux', 'ele_avg_energy', 'time', 'lat'
        b5e_idx: índice de b5e
        min_flux_e: umbral de flujo para electrones
        min_flux_i: umbral de flujo para iones
        max_energy: energía máxima para considerar flujo físico
        min_flux_physical: flujo mínimo para considerar físico con baja energía
        
    Returns:
        (índice, tiempo, latitud) del límite detectado o (None, None, None)
    """
    if b5e_idx is None or b5e_idx >= len(segment['ele_energy_flux']) - 1:
        return None, None, None
    
    je = segment['ele_energy_flux']
    ji = segment['ion_energy_flux']
    avg_e = segment['ele_avg_energy']
    
    # Caso 1: Encuentro con lluvia polar
    polar_rain_mask = (ji < min_flux_i - 1.0) & (je > min_flux_e - 0.5)
    polar_rain_indices = np.where(polar_rain_mask)[0]
    if polar_rain_indices.size > 0:
        idx = polar_rain_indices[0]
        return idx, segment['time'][idx], segment['lat'][idx]
    
    # Caso 2: Caída por debajo de umbrales
    low_flux_mask = (je < min_flux_e) & (ji < min_flux_i)
    physical_flux_mask = (je > min_flux_physical) & (avg_e < max_energy)
    valid_mask = low_flux_mask & ~physical_flux_mask
    
    valid_indices = np.where(valid_mask)[0]
    if valid_indices.size > 0:
        idx = valid_indices[0]
        return idx, segment['time'][idx], segment['lat'][idx]
    
    return None, None, None

def detect_all_boundaries(segment, energy_channels):
    """
    Detecta todas las fronteras en orden con dependencias adecuadas
    
    Args:
        segment: dict con todos los datos necesarios
        energy_channels: array de energías de los canales
        
    Returns:
        Dict con todas las fronteras detectadas (cada una con índice, tiempo y latitud)
    """
    results = {}
    
    # B1e - Límite de convección de energía cero
    b1e_idx, b1e_time, b1e_lat = detect_b1e(segment, energy_channels)
    results['b1e'] = {'index': b1e_idx, 'time': b1e_time, 'lat': b1e_lat}
    
    # B2e - Inicio de la lámina de plasma
    b2e_idx, b2e_time, b2e_lat = detect_b2e(segment, b1e_idx)
    results['b2e'] = {'index': b2e_idx, 'time': b2e_time, 'lat': b2e_lat}
    
    # B2i - Frontera de isotropía de iones
    b2i_idx, b2i_time, b2i_lat = detect_b2i(segment, energy_channels)
    results['b2i'] = {'index': b2i_idx, 'time': b2i_time, 'lat': b2i_lat}
    
    # B3a/B3b - Eventos de aceleración de electrones
    b3a_idx, b3a_time, b3a_lat, b3b_idx, b3b_time, b3b_lat = detect_b3(segment, energy_channels)
    results['b3a'] = {'index': b3a_idx, 'time': b3a_time, 'lat': b3a_lat}
    results['b3b'] = {'index': b3b_idx, 'time': b3b_time, 'lat': b3b_lat}
    
    # B4s - Transición estructurada/no estructurada
    b4s_idx, b4s_time, b4s_lat = detect_b4s(segment, b2e_idx, b2i_idx)
    results['b4s'] = {'index': b4s_idx, 'time': b4s_time, 'lat': b4s_lat}
    
    # B5e/B5i - Borde polar del óvalo auroral
    b5e_idx, b5e_time, b5e_lat = detect_b5(segment, 'electron')
    results['b5e'] = {'index': b5e_idx, 'time': b5e_time, 'lat': b5e_lat}
    
    b5i_idx, b5i_time, b5i_lat = detect_b5(segment, 'ion')
    results['b5i'] = {'index': b5i_idx, 'time': b5i_time, 'lat': b5i_lat}
    
    # B6 - Límite de llovizna subvisual
    b6_idx, b6_time, b6_lat = detect_b6(segment, b5e_idx)
    results['b6'] = {'index': b6_idx, 'time': b6_time, 'lat': b6_lat}
    
    return results