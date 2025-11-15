import numpy as np

def agrupar_extremos(extremos):
    """Agrupa extremos en pares - MÁS FLEXIBLE"""
    if len(extremos) < 2:
        print("⚠️  No hay suficientes extremos para formar pares")
        return []
    
    # Ordenar por tiempo
    extremos_ordenados = sorted(extremos, key=lambda x: x[0])
    
    # Formar pares de manera más flexible
    pares_extremos = []
    i = 0
    
    while i < len(extremos_ordenados) - 1:
        current = extremos_ordenados[i]
        next_extremo = extremos_ordenados[i + 1]
        
        lat_current = current[1]
        lat_next = next_extremo[1]
        
        # CRITERIO MÁS FLEXIBLE: Permitir pares con mismo signo
        if lat_current * lat_next < 0:  # Signos opuestos (ideal)
            pares_extremos.append([current, next_extremo])
            i += 2
        else:
            # Buscar el siguiente extremo con signo opuesto en un rango más amplio
            found = False
            search_range = min(i + 10, len(extremos_ordenados))  # Rango más amplio
            for j in range(i + 2, search_range):
                if extremos_ordenados[j][1] * lat_current < 0:
                    pares_extremos.append([current, extremos_ordenados[j]])
                    i = j + 1
                    found = True
                    break
            
            if not found:
                # Si no encontramos signo opuesto, formar par con el siguiente extremo
                pares_extremos.append([current, next_extremo])
                i += 2
    
    print(f"🔍 Pares de extremos formados: {len(pares_extremos)}")
    
    # Mostrar información de los pares
    for idx, par in enumerate(pares_extremos):
        t1, lat1 = par[0]
        t2, lat2 = par[1]
        duration = t2 - t1
        print(f"   Par {idx}: Lat {lat1:.1f}° → {lat2:.1f}°, Duración: {duration}")
    
    return pares_extremos