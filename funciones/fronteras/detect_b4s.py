# [file name]: detect_b4s.py
import numpy as np
from scipy.stats import pearsonr
import warnings
from scipy.stats import ConstantInputWarning

def safe_pearsonr(x, y):
    """
    Calcula correlación de Pearson de forma segura, manejando arrays constantes
    """
    # Filtrar NaN e infinitos
    mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    # Verificar longitud mínima
    if len(x_clean) < 2 or len(y_clean) < 2:
        return 0.0
        
    # Verificar si los arrays son constantes (sin variabilidad)
    x_std = np.std(x_clean)
    y_std = np.std(y_clean)
    
    if x_std < 1e-10 or y_std < 1e-10:
        return 0.0
    
    # Calcular correlación suprimiendo warnings de arrays constantes
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConstantInputWarning)
            r_value, _ = pearsonr(x_clean, y_clean)
            return r_value if not np.isnan(r_value) else 0.0
    except:
        return 0.0

def detect_b4s(segment, b2e_idx, b2i_idx):
    """
    Boundary 4s (structured/unstructured transition) - CORREGIDO SEGÚN PAPER p.6
    VERSIÓN MEJORADA: Maneja arrays constantes y datos inválidos
    """
    # Validación de datos más robusta
    required_keys = ['ele_diff_flux', 'time', 'lat', 'ele_energy_flux']
    for key in required_keys:
        if key not in segment or len(segment[key]) == 0:
            return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    spectra = segment['ele_diff_flux']
    times = segment['time']
    lats = segment['lat']
    energy_flux = segment['ele_energy_flux']
    
    n = len(spectra)
    
    # Verificar que hay suficientes datos
    if n < 12:
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    start_idx = 0
    if b2e_idx is not None:
        start_idx = max(start_idx, b2e_idx)
    if b2i_idx is not None:
        start_idx = max(start_idx, b2i_idx)
    
    start_idx += 1  # Al menos un punto después
    
    if start_idx >= n - 12:  # Necesitamos espacio para el algoritmo
        return {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # 1. Calcular coeficientes de correlación (paper: 5 espectros anteriores)
    avg_correlations = np.full(n, np.nan)  # Usar full en lugar de zeros para inicializar con NaN
    
    for i in range(5, n):  # Necesitamos al menos 5 puntos anteriores
        current_spectrum = spectra[i]
        correlations = []
        
        for j in range(1, 6):  # 5 espectros anteriores
            if i - j >= 0:
                prev_spectrum = spectra[i - j]
                
                # Usar la función segura de correlación
                r_value = safe_pearsonr(current_spectrum, prev_spectrum)
                
                if r_value != 0.0:  # Solo agregar si es válido
                    correlations.append(r_value)
        
        if correlations:
            avg_corr = np.mean(correlations)
            
            # Suprimir para flujos subvisuales (paper p.6)
            if energy_flux[i] < 10.7:  # 0.25 erg/cm² s
                avg_corr *= 0.5
                
            avg_correlations[i] = avg_corr
    
    # 2. Buscar transición (paper: suma de 7 <r> consecutivos < 4.0)
    b4s_index = None
    
    for i in range(start_idx + 6, n - 6):
        # Calcular suma de 7 correlaciones consecutivas
        window = avg_correlations[i-6:i+1]
        
        # Verificar que no hay NaN en la ventana
        if np.any(np.isnan(window)):
            continue
            
        sum_r = np.sum(window)
        
        if sum_r < 4.0:
            # Encontrar el más poleward con <r> > 0.60 en el grupo final
            for j in range(i, i-7, -1):
                if j < n and not np.isnan(avg_correlations[j]) and avg_correlations[j] > 0.60:
                    b4s_index = j
                    break
                    
            if b4s_index is not None:
                break
    
    if b4s_index is not None and b4s_index < n:
        return {
            'index': b4s_index,
            'time': times[b4s_index],
            'lat': lats[b4s_index],
            'deviation': 0,
            'avg_correlation': avg_correlations[b4s_index] if not np.isnan(avg_correlations[b4s_index]) else 0.0
        }
    
    return {'index': None, 'time': None, 'lat': None, 'deviation': 0}