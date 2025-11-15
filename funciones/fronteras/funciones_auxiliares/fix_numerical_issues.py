# fix_numerical_issues.py
import numpy as np

def safe_log10(flux_array, epsilon=1e-15):
    """
    Calcula log10 de forma segura, evitando valores no positivos
    """
    flux_array = np.asarray(flux_array, dtype=np.float64)
    
    # Reemplazar valores no positivos con epsilon
    safe_flux = np.where(flux_array <= 0, epsilon, flux_array)
    
    # Calcular log10 de forma segura
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.log10(safe_flux)
    
    # Reemplazar infinitos y NaN con valores muy bajos
    result = np.nan_to_num(result, nan=-15.0, posinf=15.0, neginf=-15.0)
    
    return result

def safe_power_ratio(log_numerator, log_denominator, max_exponent=50):
    """
    Calcula 10^a / 10^b de forma segura trabajando en escala logarítmica
    Evita overflow/underflow
    """
    log_numerator = np.asarray(log_numerator, dtype=np.float64)
    log_denominator = np.asarray(log_denominator, dtype=np.float64)
    
    # Calcular diferencia en escala logarítmica
    log_ratio = log_numerator - log_denominator
    
    # Limitar exponentes muy grandes/pequeños
    log_ratio = np.clip(log_ratio, -max_exponent, max_exponent)
    
    # Convertir a lineal de forma segura
    with np.errstate(over='ignore', under='ignore', invalid='ignore'):
        ratio = 10 ** log_ratio
        ratio = np.nan_to_num(ratio, nan=1.0, posinf=1000.0, neginf=0.0)
    
    return ratio

def safe_ratio(numerator, denominator, default=1.0):
    """
    Calcula una ratio de forma segura, evitando división por cero
    """
    numerator = np.asarray(numerator, dtype=np.float64)
    denominator = np.asarray(denominator, dtype=np.float64)
    
    # Calcular ratio con manejo de división por cero
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.divide(numerator, denominator)
        ratio = np.where(denominator == 0, default, ratio)
        ratio = np.nan_to_num(ratio, nan=default, posinf=1000.0, neginf=0.0)
    
    return ratio