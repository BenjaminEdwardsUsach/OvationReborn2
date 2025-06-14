def detectar_extremos_latitud(adjust_SC_AACGM_LAT, adjust_tiempo_final):
    """
    Detecta cambios de signo en latitud y retorna lista de extremos.
    """
    extremos = []
    extremos.append((adjust_tiempo_final[0], adjust_SC_AACGM_LAT[0]))
    for i in range(len(adjust_SC_AACGM_LAT) - 1):
        if (adjust_SC_AACGM_LAT[i] > 0 and adjust_SC_AACGM_LAT[i + 1] < 0) or            (adjust_SC_AACGM_LAT[i] < 0 and adjust_SC_AACGM_LAT[i + 1] > 0):
            extremos.append((adjust_tiempo_final[i], adjust_SC_AACGM_LAT[i]))
            extremos.append((adjust_tiempo_final[i + 1], adjust_SC_AACGM_LAT[i + 1]))
    extremos.append((adjust_tiempo_final[-1], adjust_SC_AACGM_LAT[-1]))
    return extremos
