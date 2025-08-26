# b2i.py
import numpy as np

def detect_b2i(segment_data):
    """
    Detecta la frontera b2i (límite de isotropía de iones)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o valores None si no se detecta
    """
    # Obtener datos relevantes
    ion_energy_flux = segment_data['ion_energy_flux']
    n = len(ion_energy_flux)
    
    # Buscar el máximo en el flujo de energía de iones (3-30 keV)
    max_flux = 0
    max_index = None
    
    for i in range(2, n-10):
        current_avg = np.mean(ion_energy_flux[i-1:i+2])
        
        # Verificar los próximos 10 segundos
        for j in range(0, 10, 3):
            next_avg = np.mean(ion_energy_flux[i+j+1:i+j+4])
            if next_avg > current_avg:
                break
        else:
            # Encontramos un máximo local
            if current_avg > max_flux and current_avg > 10.5:
                max_flux = current_avg
                max_index = i
    
    if max_index is not None:
        return {
            'index': max_index,
            'time': segment_data['time'][max_index],
            'lat': segment_data['lat'][max_index]
        }
    else:
        return {'index': None, 'time': None, 'lat': None}