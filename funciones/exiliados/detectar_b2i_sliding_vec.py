def detectar_b2i_sliding_vec(flux, lookahead=10, min_flux=10.5):
    flux = np.asarray(flux)
    n = len(flux)
    
    # Calcular máximos deslizantes vectorizado
    sliding_max = np.zeros(n)
    for i in range(n):
        end = min(i + lookahead, n)
        sliding_max[i] = np.max(flux[i:end]) if i < end else 0
    
    # Encontrar candidatos usando diferencias
    diff = flux - sliding_max
    candidates = np.where((flux >= min_flux) & (diff > 0))[0]
    
    # Manejar "nose events": declive seguido de aumento
    valid_candidates = []
    for i in candidates:
        if i > 0 and flux[i-1] < flux[i] and (i == n-1 or flux[i+1] < flux[i]):
            valid_candidates.append(i)
    
    if not valid_candidates:
        return None
    
    return valid_candidates[np.argmax(flux[valid_candidates])]