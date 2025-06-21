def separar_por_latitud(SC_AACGM_LAT, tiempo_final):
    """
    Separa datos según latitud en rangos específicos y retorna listas ajustadas y otras listas.
    """
    if len(SC_AACGM_LAT) != len(tiempo_final):
        raise ValueError("Las listas deben tener el mismo largo.")

    adjust_SC_AACGM_LAT = []
    other_SC_AACGM_LAT  = []
    adjust_tiempo_final = []
    other_tiempo_final  = []
    comparador = []
    flag = False

    for lat_elem, t_elem in zip(SC_AACGM_LAT, tiempo_final):
        t_elem_stripped = t_elem.strip()
        if (-75 < lat_elem < -50) or (50 < lat_elem < 75):
            adjust_SC_AACGM_LAT.append(lat_elem)
            adjust_tiempo_final.append(t_elem_stripped)
            if not flag:
                comparador.append((lat_elem, t_elem_stripped))
                flag = True
        else:
            if flag:
                comparador.append((lat_elem, t_elem_stripped))
            flag = False
            other_SC_AACGM_LAT.append(lat_elem)
            other_tiempo_final.append(t_elem_stripped)

    return adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, comparador
