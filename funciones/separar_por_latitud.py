def separar_por_latitud(SC_AACGM_LAT, tiempo_final):
    """Separa datos según latitud en rangos específicos de manera vectorizada"""
    if len(SC_AACGM_LAT) != len(tiempo_final):
        raise ValueError("Las listas deben tener el mismo largo.")
    
    # Crear máscara booleana para latitudes de interés
    mask = ((-75 < SC_AACGM_LAT) & (SC_AACGM_LAT < -50)) | ((50 < SC_AACGM_LAT) & (SC_AACGM_LAT < 75))
    
    # Listas ajustadas
    adjust_SC_AACGM_LAT = SC_AACGM_LAT[mask].tolist()
    adjust_tiempo_final = [t for i, t in enumerate(tiempo_final) if mask[i]]
    
    # Listas otras latitudes
    other_SC_AACGM_LAT = SC_AACGM_LAT[~mask].tolist()
    other_tiempo_final = [t for i, t in enumerate(tiempo_final) if not mask[i]]
    
    # Puntos de transición
    transitions = []
    prev_mask = False
    for i, lat in enumerate(SC_AACGM_LAT):
        current_mask = mask[i]
        if current_mask != prev_mask:
            transitions.append((lat, tiempo_final[i]))
        prev_mask = current_mask
    
    return adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, transitions