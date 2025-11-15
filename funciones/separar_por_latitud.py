import numpy as np

def separar_por_latitud(SC_AACGM_LAT, tiempo_final):
    """Separa datos según latitud en rangos específicos - MÁS INCLUSIVO"""
    if len(SC_AACGM_LAT) != len(tiempo_final):
        raise ValueError("Las listas deben tener el mismo largo.")
    
    # RANGO MÁS AMPLIO: Incluir más latitudes
    mask = ((-80 < SC_AACGM_LAT) & (SC_AACGM_LAT < -40)) | ((40 < SC_AACGM_LAT) & (SC_AACGM_LAT < 80))
    
    # Aplicar filtro menos restrictivo
    mask_clean = clean_latitude_mask(mask, min_consecutive=2)  # Solo 2 puntos consecutivos
    
    # Listas ajustadas
    adjust_SC_AACGM_LAT = SC_AACGM_LAT[mask_clean].tolist()
    adjust_tiempo_final = [t for i, t in enumerate(tiempo_final) if mask_clean[i]]
    
    # Listas otras latitudes
    other_SC_AACGM_LAT = SC_AACGM_LAT[~mask_clean].tolist()
    other_tiempo_final = [t for i, t in enumerate(tiempo_final) if not mask_clean[i]]
    
    print(f"🔍 Datos en zona auroral: {len(adjust_SC_AACGM_LAT)} de {len(SC_AACGM_LAT)} puntos")
    
    # Puntos de transición
    transitions = find_clean_transitions(mask_clean, SC_AACGM_LAT, tiempo_final)
    
    return adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, transitions

def clean_latitude_mask(mask, min_consecutive=2):
    """Limpia la máscara para requerir secuencias mínimas de puntos - MENOS ESTRICTO"""
    cleaned_mask = mask.copy()
    n = len(mask)
    
    i = 0
    while i < n:
        if mask[i]:
            # Encontrar secuencia consecutiva
            j = i
            while j < n and mask[j]:
                j += 1
            sequence_length = j - i
            
            # Si la secuencia es muy corta, eliminarla
            if sequence_length < min_consecutive:
                cleaned_mask[i:j] = False
            
            i = j
        else:
            i += 1
    
    return cleaned_mask

def find_clean_transitions(mask, latitudes, times):
    """Encuentra transiciones limpias entre zonas"""
    transitions = []
    prev_mask = False
    
    for i, (lat, time, current_mask) in enumerate(zip(latitudes, times, mask)):
        if current_mask != prev_mask:
            transitions.append((lat, time))
            prev_mask = current_mask
    
    print(f"🔍 Transiciones encontradas: {len(transitions)}")
    return transitions