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
    #reorganizar de manera más eficiente
    for i, elem in enumerate(SC_AACGM_LAT):
        if (-75 < elem < -50) or (50 < elem < 75):
            adjust_SC_AACGM_LAT.append(elem)
            adjust_tiempo_final.append(tiempo_final[i])
            if not flag:
                comparador.append((elem, tiempo_final[i]))
            flag = True
        else:
            if flag:
                comparador.append((elem, tiempo_final[i]))
            flag = False
            other_SC_AACGM_LAT.append(elem)
            other_tiempo_final.append(tiempo_final[i])
    return adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, comparador