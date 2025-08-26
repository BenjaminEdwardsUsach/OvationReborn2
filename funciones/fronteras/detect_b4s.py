# b4s.py
import numpy as np
from scipy.stats import pearsonr
import warnings

def detect_b4s(segment_data, b2e_data, b2i_data):
    """
    Detecta la frontera b4s (transición entre precipitación estructurada y no estructurada)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        b2e_data (dict): Datos de la frontera b2e con clave 'index'
        b2i_data (dict): Datos de la frontera b2i con clave 'index'
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o None si no se detecta
    """
    # Extraer índices de b2e y b2i si están disponibles
    if b2e_data is None or b2e_data['index'] is None:
        b2e_index = None
    else:
        b2e_index = b2e_data['index']
        
    if b2i_data is None or b2i_data['index'] is None:
        b2i_index = None
    else:
        b2i_index = b2i_data['index']
    
    if b2e_index is None or b2i_index is None:
        return None
    
    ele_diff_flux = segment_data['ele_diff_flux']
    flux_ele = segment_data['flux_ele']
    n = ele_diff_flux.shape[0]
    
    # Calcular coeficientes de correlación
    corr_coeffs = np.zeros(n)
    for i in range(5, n):
        # Calcular correlación con los 5 espectros anteriores
        corrs = []
        for j in range(1, 6):
            if i - j >= 0:
                with warnings.catch_warnings():
                    warnings.filterwarnings('error')
                    try:
                        r, _ = pearsonr(ele_diff_flux[i], ele_diff_flux[i-j])
                        corrs.append(r)
                    except (RuntimeWarning, ValueError):
                        corrs.append(0.0)  # Set correlation to 0 for constant arrays
        
        # Promedio de coeficientes de correlación
        if corrs:
            avg_corr = np.mean(corrs)
            
            # Suprimir coeficiente si el flujo es bajo (subvisual)
            if flux_ele[i] < 10.7:  # 0.25 erg/cm² s
                avg_corr *= 0.5
                
            corr_coeffs[i] = avg_corr
    
    # Buscar la transición (donde la correlación cae por debajo de 0.6)
    start_idx = max(b2e_index, b2i_index)
    for i in range(start_idx, n-7):
        window_sum = np.sum(corr_coeffs[i:i+7])
        if window_sum < 4.0:
            # Encontrar el espectro más polar con correlación > 0.6
            for j in range(i+6, i-1, -1):
                if j < n and corr_coeffs[j] > 0.6:
                    return {
                        'index': j,
                        'time': segment_data['time'][j],
                        'lat': segment_data['lat'][j]
                    }
            return {
                'index': i,
                'time': segment_data['time'][i],
                'lat': segment_data['lat'][i]
            }
    
    return None