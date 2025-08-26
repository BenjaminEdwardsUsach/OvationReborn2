# b2e.py
import numpy as np

def detect_b2e(segment_data, b1e_data):
    """
    Detecta la frontera b2e (inicio de la lámina de plasma principal)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        b1e_data (dict): Datos de la frontera b1e con clave 'index'
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o None si no se detecta
    """
    # Extraer índice de b1e si está disponible
    if b1e_data is None or b1e_data['index'] is None:
        return {'index': None, 'time': None, 'lat': None}
    
    b1e_index = b1e_data['index']
    
    # Obtener datos relevantes
    ele_avg_energy = segment_data['ele_avg_energy']
    n = len(ele_avg_energy)
    
    # Empezar desde b1e_index
    for i in range(b1e_index, n-9):
        current_avg = np.mean(ele_avg_energy[i-1:i+2])  # Promedio de 3 segundos
        
        # Verificar los próximos 9 segundos en grupos de 3
        found = True
        for j in range(0, 9, 3):
            next_avg = np.mean(ele_avg_energy[i+j+1:i+j+4])
            if next_avg > current_avg:
                found = False
                break
        
        if found:
            # Verificar que estamos en la lámina de plasma principal
            if segment_data['flux_ele'][i] < 11.0 or (
                segment_data['flux_ele'][i] < 11.5 and ele_avg_energy[i] < 1000):
                # Verificar los próximos 30 segundos
                max_flux = np.max(segment_data['flux_ele'][i:i+30])
                if max_flux > segment_data['flux_ele'][i] + 0.3:  # Factor de 2 en lineal
                    continue
            
            return {
                'index': i,
                'time': segment_data['time'][i],
                'lat': segment_data['lat'][i]
            }
    
    return {'index': None, 'time': None, 'lat': None}