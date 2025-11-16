import numpy as np

def split_cycle_segment(par, tiempo_final, tiempo_final_dict, flujos, sc_lat, sc_geo):
    """
    Divide un ciclo (par de instantes) en segmentos - CON DIRECCIÓN CORREGIDA
    """
    # Manejo de pares incompletos
    if len(par) == 1:
        par = (par[0], tiempo_final[-1])

    # Obtener índices de forma segura
    t0 = par[0][0] if isinstance(par[0], (tuple, list)) else par[0]
    t1 = par[1][0] if isinstance(par[1], (tuple, list)) else par[1]

    i0 = tiempo_final_dict.get(t0)
    i1 = tiempo_final_dict.get(t1)
    
    if i0 is None or i1 is None:
        return create_empty_segments()

    # Asegurar límites y orden
    N = len(tiempo_final)
    i0 = int(max(0, min(i0, N-1)))
    i1 = int(max(0, min(i1, N-1)))
    
    if i1 <= i0:
        i0, i1 = i1, i0

    # Extraer subarrays
    flux = flujos[i0:i1+1]
    times = tiempo_final[i0:i1+1]
    sc_geo_arr = np.asarray(sc_geo, float)

    # Construir coordenadas
    coords_a = []
    coords_g = []
    tiempo_arr = np.array(tiempo_final)
    
    for t in times:
        idx = tiempo_final_dict.get(t)
        if idx is None:
            diffs = np.abs(tiempo_arr - t)
            idx = int(np.argmin(diffs))
        idx = int(max(0, min(idx, len(sc_lat)-1)))
        coords_a.append(sc_lat[idx])
        coords_g.append(sc_geo_arr[idx])

    coords_a = np.array(coords_a)
    coords_g = np.array(coords_g)

    if len(coords_g) == 0:
        return create_empty_segments()
    
    # DETERMINAR DIRECCIÓN DEL SEGMENTO
    lat_inicial = coords_g[0]
    lat_final = coords_g[-1]
    
    direccion_original = "ecuador-polo" if abs(lat_inicial) < abs(lat_final) else "polo-ecuador"
    
    # Encontrar máximo absoluto de latitud geocéntrica
    max_idx = int(np.argmax(np.abs(coords_g)))

    def build(start, end, reverse=False, direccion=""):
        start = int(start)
        end = int(end)
        
        if start >= end:
            return create_empty_segment()
            
        idxs = np.arange(i0 + start, i0 + end, dtype=np.int32)
        sub_flux = flux[start:end]
        sub_time = times[start:end]
        sub_ca = coords_a[start:end]
        sub_cg = coords_g[start:end]
        
        return {
            'flux': sub_flux,
            'time': sub_time,
            'coords_aacgm': sub_ca,
            'coords_geo': sub_cg,
            'indices': idxs,
            'direccion_original': direccion_original,
            'direccion_procesamiento': direccion
        }

    def build_for_processing(start, end, reverse=False, direccion=""):
        """Versión para procesamiento que sí invierte cuando es necesario"""
        start = int(start)
        end = int(end)
        
        if start >= end:
            return create_empty_segment()
            
        idxs = np.arange(i0 + start, i0 + end, dtype=np.int32)
        sub_flux = flux[start:end]
        sub_time = times[start:end]
        sub_ca = coords_a[start:end]
        sub_cg = coords_g[start:end]
        
        if reverse:
            idxs = idxs[::-1].astype(np.int32)
            sub_flux = sub_flux[::-1]
            sub_time = sub_time[::-1]
            sub_ca = sub_ca[::-1]
            sub_cg = sub_cg[::-1]
            
        return {
            'flux': sub_flux,
            'time': sub_time,
            'coords_aacgm': sub_ca,
            'coords_geo': sub_cg,
            'indices': idxs,
            'direccion_original': direccion_original,
            'direccion_procesamiento': direccion
        }


    
    if direccion_original == "ecuador-polo":
        # Segmento ya está en dirección correcta
        seg1_original = build(0, max_idx, reverse=False, direccion="ecuador-polo")
        seg2_original = build(max_idx, len(flux), reverse=False, direccion="polo-ecuador")
        
        # Para procesamiento: seg1 ya está bien, seg2 necesita invertirse
        seg1_processing = build_for_processing(0, max_idx, reverse=False, direccion="ecuador-polo")
        seg2_processing = build_for_processing(max_idx, len(flux), reverse=True, direccion="ecuador-polo")
    else:
        # Segmento está en dirección polo-ecuador
        seg1_original = build(0, max_idx, reverse=False, direccion="polo-ecuador")
        seg2_original = build(max_idx, len(flux), reverse=False, direccion="ecuador-polo")
        
        # Para procesamiento: ambos segmentos necesitan invertirse
        seg1_processing = build_for_processing(0, max_idx, reverse=True, direccion="ecuador-polo")
        seg2_processing = build_for_processing(max_idx, len(flux), reverse=False, direccion="ecuador-polo")

    return {
        'seg1_original': seg1_original,
        'seg2_original': seg2_original,
        'seg1_processing': seg1_processing,
        'seg2_processing': seg2_processing,
        'direccion_original': direccion_original
    }

def create_empty_segment():
    """Crea un segmento vacío con información de dirección"""
    return {
        'flux': np.array([]),
        'time': np.array([]), 
        'coords_aacgm': np.array([]),
        'coords_geo': np.array([]),
        'indices': np.array([], dtype=np.int32),
        'direccion_original': "desconocida",
        'direccion_procesamiento': "desconocida"
    }

def create_empty_segments():
    """Crea todos los segmentos vacíos"""
    empty = create_empty_segment()
    return {
        'seg1_original': empty,
        'seg2_original': empty,
        'seg1_processing': empty,
        'seg2_processing': empty,
        'direccion_original': "desconocida"
    }