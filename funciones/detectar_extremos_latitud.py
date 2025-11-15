import numpy as np

def detectar_extremos_latitud(adjust_SC_AACGM_LAT, adjust_tiempo_final):
    """Detecta cambios de signo en latitud - MÁS SENSIBLE"""
    extremos = []
    
    if len(adjust_SC_AACGM_LAT) < 2:
        return extremos
    
    # Agregar primer punto
    extremos.append((adjust_tiempo_final[0], adjust_SC_AACGM_LAT[0]))
    
    # Buscar cruces por cero con criterio más sensible
    for i in range(1, len(adjust_SC_AACGM_LAT) - 1):
        lat_prev = adjust_SC_AACGM_LAT[i-1]
        lat_curr = adjust_SC_AACGM_LAT[i]
        lat_next = adjust_SC_AACGM_LAT[i+1]
        
        # CRITERIO MÁS SENSIBLE: Cualquier cruce por cero
        if lat_prev * lat_curr <= 0:
            # Encontrar el punto exacto del cruce
            if abs(lat_curr) < abs(lat_prev):
                extremos.append((adjust_tiempo_final[i], lat_curr))
            else:
                extremos.append((adjust_tiempo_final[i-1], lat_prev))
    
    # Agregar último punto
    extremos.append((adjust_tiempo_final[-1], adjust_SC_AACGM_LAT[-1]))
    
    print(f"🔍 Extremos detectados: {len(extremos)}")
    
    # Filtrar extremos duplicados o muy cercanos (menos estricto)
    extremos_filtrados = []
    tiempo_min_diff = np.timedelta64(5, 's')  # Solo 5 segundos de separación mínima
    
    for i, extremo in enumerate(extremos):
        if i == 0:
            extremos_filtrados.append(extremo)
        else:
            t_prev = extremos_filtrados[-1][0]
            t_curr = extremo[0]
            if t_curr - t_prev > tiempo_min_diff:
                extremos_filtrados.append(extremo)
            else:
                # Si están muy cercanos, mantener el que tenga mayor latitud absoluta
                lat_prev = extremos_filtrados[-1][1]
                lat_curr = extremo[1]
                if abs(lat_curr) > abs(lat_prev):
                    extremos_filtrados[-1] = extremo
    
    print(f"🔍 Extremos después de filtrado: {len(extremos_filtrados)}")
    
    # Mostrar información de extremos
    for i, (t, lat) in enumerate(extremos_filtrados):
        print(f"   Extremo {i}: t={t}, lat={lat:.2f}°")
    
    return extremos_filtrados