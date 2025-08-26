# b1i.py
import numpy as np

def detect_b1i(segment_data, channel_energies):
    """
    Detecta la frontera b1i (límite de convección de energía cero para iones)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        channel_energies (array): Energías de los canales
    
    Returns:
        int: Índice de la frontera b1i o None si no se detecta
    """
    # Obtener datos relevantes
    ion_diff_flux = segment_data['ion_diff_flux']
    
    # Determinar canales de baja energía (32-47 eV)
    low_e_mask = (channel_energies >= 32) & (channel_energies <= 47)
    
    # Calcular flujo parcial de iones en el rango de baja energía
    jip_partial = np.sum(ion_diff_flux[:, low_e_mask], axis=1)
    jip_log = np.log10(jip_partial)
    
    # Buscar el salto en el flujo (factor de 2)
    n = len(jip_log)
    for i in range(3, n-3):
        prev_avg = np.mean(jip_log[i-3:i])
        next_avg = np.mean(jip_log[i+1:i+4])
        
        # Convertir a espacio lineal para calcular el factor
        linear_jump = 10**next_avg / 10**prev_avg
        
        # Verificar condiciones
        if linear_jump > 2.0 or (jip_log[i] > 6.5 and linear_jump > 1.6) or jip_log[i] > 6.9:
            # Doble verificación mirando adelante
            if i + 5 < n and jip_log[i+1] < jip_log[i]:
                continue  # Falso positivo
            return {
            'index': i,
            'time': segment_data['time'][i],
            'lat': segment_data['lat'][i]
        }
    
    return {'index': None, 'time': None, 'lat': None}