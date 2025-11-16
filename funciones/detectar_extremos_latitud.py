import numpy as np

def detectar_extremos_latitud(adjust_SC_AACGM_LAT, adjust_tiempo_final):
    """Detecta cambios de signo en latitud - MÁS SENSIBLE Y CON MÁS PUNTOS"""
    extremos = []
    
    if len(adjust_SC_AACGM_LAT) < 2:
        return extremos
    
    # Agregar primer punto 
    extremos.append((adjust_tiempo_final[0], adjust_SC_AACGM_LAT[0]))

    # Buscar cruces por cero 
    for i in range(1, len(adjust_SC_AACGM_LAT)):
        lat_prev = adjust_SC_AACGM_LAT[i-1]
        lat_curr = adjust_SC_AACGM_LAT[i]
        
        # Cualquier cruce por cero O cambio significativo
        if (lat_prev * lat_curr <= 0) or (abs(lat_curr - lat_prev) > 5.0):  # Umbral de cambio de 5°
            # Encontrar el punto exacto del cruce
            if abs(lat_curr) < abs(lat_prev):
                extremos.append((adjust_tiempo_final[i], lat_curr))
            else:
                extremos.append((adjust_tiempo_final[i-1], lat_prev))
    
    # Agregar último punto 
    extremos.append((adjust_tiempo_final[-1], adjust_SC_AACGM_LAT[-1]))
    
    # Solo eliminar duplicados exactos
    extremos_filtrados = []
    tiempo_min_diff = np.timedelta64(2, 's')  # Reducido a 2 segundos
    
    for i, extremo in enumerate(extremos):
        if i == 0:
            extremos_filtrados.append(extremo)
        else:
            t_prev = extremos_filtrados[-1][0]
            t_curr = extremo[0]
            lat_prev = extremos_filtrados[-1][1]
            lat_curr = extremo[1]
            
            # Solo filtrar si son MUY cercanos y tienen latitud similar
            time_diff = t_curr - t_prev
            lat_diff = abs(lat_curr - lat_prev)
            
            if time_diff > tiempo_min_diff or lat_diff > 1.0:  # 1° de diferencia
                extremos_filtrados.append(extremo)
            else:
                # Si están muy cercanos, mantener el que tenga mayor latitud absoluta
                if abs(lat_curr) > abs(lat_prev):
                    extremos_filtrados[-1] = extremo
    
    return extremos_filtrados