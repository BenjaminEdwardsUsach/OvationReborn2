import numpy as np

def detect_b5(segment_data, flux_key, min_flux):
    """
    Función auxiliar para detectar las fronteras b5e y b5i
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        flux_key (str): Clave del flujo a usar ('flux_ele' o 'flux_ion')
        min_flux (float): Valor mínimo de flujo para considerar como óvalo
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o valores None si no se detecta
    """
    flux = segment_data[flux_key]
    n = len(flux)
    
    for i in range(12, n-12):
        prev_avg = np.mean(flux[i-12:i])
        next_avg = np.mean(flux[i+1:i+13])
        
        # Verificar caída por factor de 4 (en espacio lineal)
        linear_drop = 10**prev_avg / 10**next_avg
        if linear_drop >= 4.0:
            # Doble verificación: los próximos 30 segundos deben mantenerse bajos
            if i + 35 < n:
                future_avg = np.mean(flux[i+1:i+36])
                if future_avg < min_flux:
                    return {
                        'index': i,
                        'time': segment_data['time'][i],
                        'lat': segment_data['lat'][i]
                    }
    
    return {'index': None, 'time': None, 'lat': None}