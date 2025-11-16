import numpy as np

def agrupar_extremos(extremos):
    """Agrupa extremos en pares - MUCHO MÁS FLEXIBLE"""
    if len(extremos) < 2:
        return []
    
    # Ordenar por tiempo
    extremos_ordenados = sorted(extremos, key=lambda x: x[0])
        
    # Formar pares de manera MUY FLEXIBLE
    pares_extremos = []
    i = 0
    
    while i < len(extremos_ordenados) - 1:
        current = extremos_ordenados[i]
        next_extremo = extremos_ordenados[i + 1]
        
        t_current = current[0]
        t_next = next_extremo[0]

        time_diff = t_next - t_current
        min_time_diff = np.timedelta64(10, 's')  # Mínimo 10 segundos
        
        if time_diff >= min_time_diff:
            pares_extremos.append([current, next_extremo])
            i += 2  # Avanzar 2 posiciones
        else:
            i += 1  # Saltar solo 1 posición
    
    # Si quedó un extremo sin pareja, intentar emparejarlo con el siguiente disponible
    if len(extremos_ordenados) % 2 == 1 and len(extremos_ordenados) > 2:
        ultimo_extremo = extremos_ordenados[-1]
        # Buscar el penúltimo par y extenderlo
        if pares_extremos:
            penultimo_par = pares_extremos[-1]
            nuevo_par = [penultimo_par[0], ultimo_extremo]
            pares_extremos[-1] = nuevo_par
    
    return pares_extremos