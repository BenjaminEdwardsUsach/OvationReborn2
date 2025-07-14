import numpy as np
def split_cycle_segment(par, tiempo_final, tiempo_final_dict, flujos, sc_lat, sc_geo):
    """
    Divide un ciclo (par de instantes) en dos segmentos:
      - seg1: desde inicio hasta lat_max_abs
      - seg2: desde lat_max_abs hasta final, invertido
    Devuelve:
      ({'seg1': {..., 'indices': idx1},
        'seg2': {..., 'indices': idx2}},
       coords_a_list,
       coords_g_list)
    donde cada segX dict contiene:
      - 'flux', 'time', 'coords_aacgm', 'coords_geo', 'indices'
    """
    # Manejo de pares incompletos: si solo hay un extremo, emparejar con fin
    if len(par) == 1:
        # Tomar el último timestamp disponible
        par = (par[0], tiempo_final[-1])

    # Índices en la serie global: par[i] puede ser (timestamp, otro)
    t0 = par[0][0] if isinstance(par[0], (tuple, list)) else par[0]
    t1 = par[1][0] if isinstance(par[1], (tuple, list)) else par[1]

    # Obtener índices i0, i1 de forma segura
    i0 = tiempo_final_dict.get(t0)
    i1 = tiempo_final_dict.get(t1)
    if i0 is None or i1 is None:
        raise ValueError(f"Timestamps {t0} o {t1} no encontrados en tiempo_final.")
    # Asegurar límites
    N = len(tiempo_final)
    i0 = max(0, min(i0, N-1))
    i1 = max(0, min(i1, N-1))
    if i1 < i0:
        i0, i1 = i1, i0  # invertir si necesario

    # Extraer subarrays
    flux = flujos[i0:i1+1]
    times = tiempo_final[i0:i1+1]
    sc_geo_arr = np.asarray(sc_geo, float)

        # Construir coordenadas AACGM y GEO buscando índice más cercano si falla
    coords_a = []
    coords_g = []
    # preconvertir tiempos a array para cálculo de diferencias
    tiempo_arr = np.array(tiempo_final)
    # Asegurar longitudes para clamping
    M = len(sc_lat)
    for t in times:
        idx = tiempo_final_dict.get(t)
        if idx is None:
            # buscar índice de tiempo más cercano
            diffs = np.abs(tiempo_arr - t)
            idx = int(np.argmin(diffs))
        # clamp para evitar fuera de rango
        idx = max(0, min(idx, M-1))
        coords_a.append(sc_lat[idx])
        coords_g.append(sc_geo_arr[idx])

    # Índice del máximo absoluto de coords_g
    max_idx = int(np.argmax(np.abs(coords_g)))

    def build(start, end, reverse=False):
        idxs = np.arange(i0 + start, i0 + end)
        sub_flux = flux[start:end]
        sub_time = times[start:end]
        sub_ca = coords_a[start:end]
        sub_cg = coords_g[start:end]
        if reverse:
            idxs = idxs[::-1]
            sub_flux = sub_flux[::-1]
        return {
            'flux': sub_flux,
            'time': sub_time,
            'coords_aacgm': sub_ca,
            'coords_geo': sub_cg,
            'indices': idxs
        }

        # Construir segmentos
    seg1 = build(0, max_idx, reverse=False)
    # Para seg2, build sin invertir time, luego invertimos sólo flux y coords
    seg2 = build(max_idx, len(flux), reverse=True)

    coords_a = np.array(coords_a)
    coords_g = np.array(coords_g)

    # Caso especial: si el máximo está al inicio, usar mismo segmento (invertido)
    if max_idx == 0:
        seg1 = seg2.copy()
        

    return {'seg1': seg1, 'seg2': seg2}
