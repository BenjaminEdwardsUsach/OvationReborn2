def seleccionar_segmentos_validos(pares_extremos, adjust_SC_AACGM_LAT, adjust_tiempo_final, comparador, tol=1):
    """
    Selecciona segmentos válidos basados en tolerancia y número mínimo de puntos.
    """
    valid_data = []
    others = []
    for par in pares_extremos:
        t_in = par[0][0]
        t_out = par[1][0]
        count = 0
        for (lat, t) in comparador:
            if (t >= t_in - tol) and (t <= t_out + tol) and (lat != 0):
                count += 1
        try:
            idx_out = adjust_tiempo_final.index(t_out)
        except ValueError:
            idx_out = None
        if idx_out is not None and idx_out < len(adjust_tiempo_final) - 1:
            t_next = adjust_tiempo_final[idx_out + 1]
            if (t_next - t_out) <= tol:
                count += 1
        if count >= 3:
            valid_data.append(par)
        else:
            others.append(par)
    return valid_data, others
