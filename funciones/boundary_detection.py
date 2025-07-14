import numpy as np
from scipy.stats import pearsonr
from scipy.ndimage import uniform_filter1d

def detect_b1e(segment, energy_channels, low_energy_range=(32, 47), 
               min_jump=2.0, high_flux_jump=1.6, high_flux_thresh=8.0, 
               very_high_flux=8.25, background_window=10, max_attempts=5, energy_step=5):
    """
    Boundary 1e con detección iterativa
    Devuelve: (idx, time, lat, params, deviation)
    """
    original_range = low_energy_range
    current_range = low_energy_range
    deviation = 0

    for attempt in range(max_attempts):
        # Convertir a arrays de NumPy para operaciones vectorizadas
        lat = np.asarray(segment['lat'])
        ele_diff_flux = np.asarray(segment['ele_diff_flux'])
        
        # Verificar consistencia de dimensiones
        n_energy_channels = len(energy_channels)
        n_data_channels = ele_diff_flux.shape[1]
        
        if n_energy_channels != n_data_channels:
            if n_energy_channels > n_data_channels:
                energy_channels_adj = energy_channels[:n_data_channels]
            else:
                padded_energy = np.zeros(n_data_channels)
                padded_energy[:n_energy_channels] = energy_channels
                energy_channels_adj = padded_energy
        else:
            energy_channels_adj = energy_channels
        
        # 1. Determinar canales de energía a usar
        low_mask = (energy_channels_adj >= current_range[0]) & (energy_channels_adj <= current_range[1])

        # 2. Calcular flujo parcial integrado
        partial_flux = np.sum(ele_diff_flux[:, low_mask], axis=1)
        log_flux = np.log10(partial_flux + 1e-10)

        
        # 3. Manejo de fotoelectrones (vectorizado)
        high_mask = energy_channels_adj > 68
        if np.any(high_mask):
            high_flux = np.mean(ele_diff_flux[:, high_mask], axis=1)
            photoelectron_mask = (high_flux < 0.1 * partial_flux) & (lat < 60)
            if np.any(photoelectron_mask):
                clean_mask = (energy_channels_adj > 100) & (energy_channels_adj < 145)
                if np.any(clean_mask):
                    low_mask = clean_mask
                    partial_flux = np.sum(ele_diff_flux[:, low_mask], axis=1)
                    log_flux = np.log10(partial_flux + 1e-10)
        
        # 4. Calcular fondo (promedio ecuatorial)
        background = np.mean(log_flux[:background_window])
        
        # 5. Detectar límite con ventana deslizante
        n = len(log_flux)
        
        # Precalcular promedios móviles
        prev_avg = uniform_filter1d(log_flux, size=3, origin=-1)[:n-3]
        next_avg = uniform_filter1d(log_flux, size=3, origin=1)[2:n-1]
        
        # Condiciones de detección
        jump_factors = np.full(n-3, min_jump)
        high_flux_mask = log_flux[3:-3] >= high_flux_thresh
        jump_factors[:len(high_flux_mask)][high_flux_mask] = high_flux_jump  # Asegura coincidencia de tamaños
        
        cond1 = log_flux[3:-3] >= very_high_flux
        cond2 = (next_avg > prev_avg * jump_factors) & (next_avg > background + 0.3)
        cond3 = np.all([log_flux[i:i+3] > background for i in range(3, n-3)], axis=1)
        
        # Encontrar el primer punto que cumpla las condiciones
        core_cond2 = cond2[3:]     # ahora core_cond2.shape == cond1.shape == cond3.shape
        detection_points = np.where(cond1 | (core_cond2 & cond3))[0]
        if detection_points.size > 0:
            idx = detection_points[0] + 3
            return (
                idx, 
                segment['time'][idx], 
                segment['lat'][idx],
                {'low_energy_range': current_range},
                deviation
            )
        
        # Expandir rango para siguiente intento
        current_range = (max(0, current_range[0]-energy_step), current_range[1]+energy_step)
        deviation += energy_step * 2  # Sumamos 5 en cada dirección
        
    return None, None, None, {'low_energy_range': current_range}, deviation

def detect_b2e(segment, b1e_idx, window=3, lookahead=9, 
               low_flux_thresh=11.0, energy_thresh=1000):
    """
    Boundary 2e - Mantenemos simple pero con interfaz consistente
    Devuelve: (idx, time, lat, params, deviation)
    """
    # Código existente de detección...
    if b1e_idx is None or b1e_idx >= len(segment['ele_avg_energy']) - window - lookahead:
        return None, None, None, {}, float('inf')
    
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
            # Devolvemos el índice encontrado
            return i, segment['time'][i], segment['lat'][i], {}, 0.0
    
    return None, None, None, {}, float('inf')

def detect_b2i(segment, energy_channels, min_energy=3000, max_energy=30000,
               window_avg=2, lookahead=10, min_flux=10.5, max_attempts=5, energy_step=500):
    """
    Boundary 2i con detección iterativa
    Devuelve: (idx, time, lat, params, deviation)
    """
    original_min = min_energy
    original_max = max_energy
    deviation = 0

    for attempt in range(max_attempts):
        # Código existente de detección usando min_energy y max_energy actuales
        energy_mask = (energy_channels >= min_energy) & (energy_channels <= max_energy)
        if not np.any(energy_mask):
            print(f"Intento {attempt+1}: Sin canales en rango {min_energy}-{max_energy} keV")
            # Expandir rango para siguiente intento
            min_energy = max(0, min_energy - energy_step)
            max_energy += energy_step
            deviation += energy_step * 2
            continue
        
        partial_flux = np.sum(segment['ion_diff_flux'][:, energy_mask], axis=1)
        log_flux = np.log10(partial_flux + 1e-10)
        print(f"b2i (intento {attempt+1}): logf min/max =", log_flux.min(), log_flux.max())
        smoothed_flux = uniform_filter1d(log_flux, size=window_avg)
        n = len(smoothed_flux)
        
        # Detectar máximos locales
        maxima = (smoothed_flux[1:-1] > smoothed_flux[:-2]) & (smoothed_flux[1:-1] > smoothed_flux[2:])
        maxima_indices = np.where(maxima)[0] + 1
        valid_maxima = maxima_indices[(smoothed_flux[maxima_indices] >= np.log10(min_flux)) & 
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
            return (
                best_candidate, 
                segment['time'][best_candidate], 
                segment['lat'][best_candidate],
                {'min_energy': min_energy, 'max_energy': max_energy},
                deviation
            )
        
        # Expandir rango para siguiente intento
        min_energy = max(0, min_energy - energy_step)
        max_energy += energy_step
        deviation += energy_step * 2
        
    return None, None, None, {'min_energy': min_energy, 'max_energy': max_energy}, deviation

def detect_b3(segment, energy_channels, min_peak_ratio=5, min_drop_ratio=10,
              max_attempts=5, ratio_step=0.5):
    """
    Boundaries 3a/3b con detección iterativa
    Devuelve: (b3a_idx, b3a_time, b3a_lat, b3b_idx, b3b_time, b3b_lat, params, deviation)
    """
    original_peak = min_peak_ratio
    original_drop = min_drop_ratio
    deviation = 0

    for attempt in range(max_attempts):
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
        
        if acceleration_indices:
            b3a_idx = np.min(acceleration_indices)
            b3b_idx = np.max(acceleration_indices)
            return (
                b3a_idx, segment['time'][b3a_idx], segment['lat'][b3a_idx],
                b3b_idx, segment['time'][b3b_idx], segment['lat'][b3b_idx],
                {'min_peak_ratio': min_peak_ratio, 'min_drop_ratio': min_drop_ratio},
                deviation
            )
        
        # Relajar umbrales para siguiente intento
        min_peak_ratio = max(1.0, min_peak_ratio - ratio_step)
        min_drop_ratio = max(1.0, min_drop_ratio - ratio_step)
        deviation += ratio_step * 2
        
    return (None, None, None, None, None, None, 
            {'min_peak_ratio': min_peak_ratio, 'min_drop_ratio': min_drop_ratio}, 
            deviation)

def detect_b4s(segment, b2e_idx, b2i_idx, min_corr=0.6, sum_threshold=4.0, 
               subvisual_thresh=10.7, n_corr=5, n_sum=7, max_attempts=3, corr_step=0.1):
    """
    Boundary 4s con detección iterativa
    Devuelve: (idx, time, lat, params, deviation)
    """
    original_corr = min_corr
    deviation = 0

    for attempt in range(max_attempts):
        start_idx = max(b2e_idx or 0, b2i_idx or 0) + 1
        n_spectra = len(segment['ele_diff_flux'])
        
        if start_idx >= n_spectra - n_corr - n_sum:
            print("Índices de B2e o B2i no válidos o fuera de rango.")
            # Continuar para ajustar parámetros
            min_corr = max(0.1, min_corr - corr_step)
            deviation += corr_step
            continue
        
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
                    if avg_corr[j] > min_corr:  # Corregido: sin logaritmo
                        return j, segment['time'][j], segment['lat'][j], {'min_corr': min_corr}, deviation
        
        # Relajar umbral para siguiente intento
        min_corr = max(0.1, min_corr - corr_step)
        deviation += corr_step
        
    return None, None, None, {'min_corr': min_corr}, deviation

def detect_b5(segment, particle_type='electron', window=12, drop_factor=4,
              min_flux_e=10.5, min_flux_i=9.7, lookahead_e=30, lookahead_i=35,
              max_attempts=3, drop_step=0.5):
    """
    Boundary 5e/5i con detección iterativa
    Devuelve: (idx, time, lat, params, deviation)
    """
    original_drop = drop_factor
    deviation = 0

    for attempt in range(max_attempts):
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
        half = window // 2
        prev_avg = uniform_filter1d(flux, size=window, origin=-half)[:n-window]
        next_avg = uniform_filter1d(flux, size=window, origin=half-1)[window:]

        # Detectar caídas significativas
        drop_mask = (prev_avg - next_avg) >= log_drop
        candidate_indices = np.where(drop_mask)[0]
        
        for i in candidate_indices:
            start = i + window
            end = min(start + lookahead, n)
            
            if not np.any(flux[start:end] > min_flux):
                idx = i + window//2
                return idx, segment['time'][idx], segment['lat'][idx], {'drop_factor': drop_factor}, deviation
        
        # Relajar umbral para siguiente intento
        drop_factor = max(1.5, drop_factor - drop_step)
        deviation += drop_step
        
    return None, None, None, {'drop_factor': drop_factor}, deviation

def detect_b6(segment, b5e_idx, min_flux_e=10.4, min_flux_i=9.6, 
              max_energy=500, min_flux_physical=10.0, max_attempts=3, flux_step=0.1):
    """
    Boundary 6 con detección iterativa
    Devuelve: (idx, time, lat, params, deviation)
    """
    original_flux_e = min_flux_e
    original_flux_i = min_flux_i
    deviation = 0

    for attempt in range(max_attempts):
        if b5e_idx is None or b5e_idx >= len(segment['ele_energy_flux']) - 1:
            print("Índice de B5e no válido o fuera de rango.")
            # Relajar umbrales para siguiente intento
            min_flux_e = max(8.0, min_flux_e - flux_step)
            min_flux_i = max(8.0, min_flux_i - flux_step)
            deviation += flux_step * 2
            continue
        
        je = segment['ele_energy_flux']
        ji = segment['ion_energy_flux']
        avg_e = segment['ele_avg_energy']
        
        # Caso 1: Encuentro con lluvia polar
        polar_rain_mask = (ji < min_flux_i - 1.0) & (je > min_flux_e - 0.5)
        polar_rain_indices = np.where(polar_rain_mask)[0]
        if polar_rain_indices.size > 0:
            idx = polar_rain_indices[0]
            return idx, segment['time'][idx], segment['lat'][idx], {'min_flux_e': min_flux_e, 'min_flux_i': min_flux_i}, deviation
        
        # Caso 2: Caída por debajo de umbrales
        low_flux_mask = (je < min_flux_e) & (ji < min_flux_i)
        physical_flux_mask = (je > min_flux_physical) & (avg_e < max_energy)
        valid_mask = low_flux_mask & ~physical_flux_mask
        
        valid_indices = np.where(valid_mask)[0]
        if valid_indices.size > 0:
            idx = valid_indices[0]
            return idx, segment['time'][idx], segment['lat'][idx], {'min_flux_e': min_flux_e, 'min_flux_i': min_flux_i}, deviation
        
        # Relajar umbrales para siguiente intento
        min_flux_e = max(8.0, min_flux_e - flux_step)
        min_flux_i = max(8.0, min_flux_i - flux_step)
        deviation += flux_step * 2
        
    return None, None, None, {'min_flux_e': min_flux_e, 'min_flux_i': min_flux_i}, deviation

def detect_all_boundaries(segment, energy_channels):
    """
    Detecta todas las fronteras en orden con dependencias adecuadas
    """
    # Convertir todas las listas a arrays NumPy para operaciones vectorizadas
    segment = {
        'time': segment['time'],
        'lat': np.asarray(segment['lat']),
        'ele_diff_flux': np.asarray(segment['ele_diff_flux']),
        'ion_diff_flux': np.asarray(segment['ion_diff_flux']),
        'ion_energy_flux': np.asarray(segment['flux_ion']),
        'ele_energy_flux': np.asarray(segment['flux_ele']),
        'ele_avg_energy': np.asarray(segment['ele_avg_energy'])
    }
    
    results = {}
    
    # B1e - Límite de convección de energía cero
    b1e_idx, b1e_time, b1e_lat, b1e_params, b1e_dev = detect_b1e(segment, energy_channels)
    results['b1e'] = {
        'index': b1e_idx, 'time': b1e_time, 'lat': b1e_lat,
        'params': b1e_params, 'deviation': b1e_dev
    }
    
    # B2e - Inicio de la lámina de plasma
    b2e_idx, b2e_time, b2e_lat, b2e_params, b2e_dev = detect_b2e(segment, b1e_idx)
    results['b2e'] = {
        'index': b2e_idx, 'time': b2e_time, 'lat': b2e_lat,
        'params': b2e_params, 'deviation': b2e_dev
    }
    
    # B2i - Frontera de isotropía de iones
    b2i_idx, b2i_time, b2i_lat, b2i_params, b2i_dev = detect_b2i(segment, energy_channels)
    results['b2i'] = {
        'index': b2i_idx, 'time': b2i_time, 'lat': b2i_lat,
        'params': b2i_params, 'deviation': b2i_dev
    }
    
    # B3a/B3b - Eventos de aceleración de electrones
    b3a_idx, b3a_time, b3a_lat, b3b_idx, b3b_time, b3b_lat, b3_params, b3_dev = detect_b3(segment, energy_channels)
    results['b3a'] = {
        'index': b3a_idx, 'time': b3a_time, 'lat': b3a_lat,
        'params': b3_params, 'deviation': b3_dev
    }
    results['b3b'] = {
        'index': b3b_idx, 'time': b3b_time, 'lat': b3b_lat,
        'params': b3_params, 'deviation': b3_dev
    }
    
    # B4s - Transición estructurada/no estructurada
    b4s_idx, b4s_time, b4s_lat, b4s_params, b4s_dev = detect_b4s(segment, b2e_idx, b2i_idx)
    results['b4s'] = {
        'index': b4s_idx, 'time': b4s_time, 'lat': b4s_lat,
        'params': b4s_params, 'deviation': b4s_dev
    }
    
    # B5e/B5i - Borde polar del óvalo auroral
    b5e_idx, b5e_time, b5e_lat, b5e_params, b5e_dev = detect_b5(segment, 'electron')
    results['b5e'] = {
        'index': b5e_idx, 'time': b5e_time, 'lat': b5e_lat,
        'params': b5e_params, 'deviation': b5e_dev
    }
    
    b5i_idx, b5i_time, b5i_lat, b5i_params, b5i_dev = detect_b5(segment, 'ion')
    results['b5i'] = {
        'index': b5i_idx, 'time': b5i_time, 'lat': b5i_lat,
        'params': b5i_params, 'deviation': b5i_dev
    }
    
    # B6 - Límite de llovizna subvisual
    b6_idx, b6_time, b6_lat, b6_params, b6_dev = detect_b6(segment, b5e_idx)
    results['b6'] = {
        'index': b6_idx, 'time': b6_time, 'lat': b6_lat,
        'params': b6_params, 'deviation': b6_dev
    }
    
    return results