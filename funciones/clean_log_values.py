"""
clean_log_values.py - Funciones para limpiar y filtrar valores negativos en escala logarítmica

Este módulo proporciona herramientas para trabajar con valores en escala logarítmica,
reemplazando valores negativos con NaN o aplicando umbrales.
"""

import numpy as np


def clean_negative_log_values(log_values, replace_with_nan=True, threshold=0.0):
    """
    Limpia valores negativos en escala logarítmica.
    
    Parámetros:
    -----------
    log_values : array - Valores en escala logarítmica (log10)
    replace_with_nan : bool - Si True, reemplaza con NaN; si False, usa el threshold
    threshold : float - Valor mínimo permitido (por defecto 0.0, que corresponde a flujo=1)
    
    Retorna:
    --------
    array - Valores limpios con NaN donde corresponda
    
    Notas:
    ------
    - log10(x) < 0 cuando 0 < x < 1
    - log10(1) = 0
    - log10(10) = 1
    - Los valores negativos corresponden a flujos muy bajos
    """
    log_values = np.asarray(log_values, dtype=float)
    result = log_values.copy()
    
    if replace_with_nan:
        # Reemplazar valores negativos con NaN
        result[result < threshold] = np.nan
    else:
        # Reemplazar valores menores al threshold con el threshold
        result[result < threshold] = threshold
    
    return result


def clean_log_array_2d(log_array, replace_with_nan=True, threshold=0.0):
    """
    Limpia una matriz 2D de valores en escala logarítmica.
    Útil para datos de tiempo x energía.
    
    Parámetros:
    -----------
    log_array : array 2D - Matriz de valores en log (tiempo x energía)
    replace_with_nan : bool - Si True, reemplaza con NaN
    threshold : float - Valor mínimo permitido
    
    Retorna:
    --------
    array 2D - Matriz limpida
    """
    log_array = np.asarray(log_array, dtype=float)
    result = log_array.copy()
    
    if replace_with_nan:
        result[result < threshold] = np.nan
    else:
        result[result < threshold] = threshold
    
    return result


def get_statistics_before_after(original_log, cleaned_log):
    """
    Calcula estadísticas antes y después de la limpieza.
    
    Parámetros:
    -----------
    original_log : array - Valores originales en log
    cleaned_log : array - Valores limpios en log
    
    Retorna:
    --------
    dict - Estadísticas de la limpieza
    """
    original_array = np.asarray(original_log, dtype=float).flatten()
    cleaned_array = np.asarray(cleaned_log, dtype=float).flatten()
    
    # Contar valores negativos en original
    negative_count = np.sum(original_array < 0)
    total_count = len(original_array)
    
    # Contar NaN en limpio
    nan_count = np.sum(np.isnan(cleaned_array))
    valid_count = np.sum(~np.isnan(cleaned_array))
    
    stats = {
        'original_negative_values': int(negative_count),
        'original_total_values': int(total_count),
        'percentage_negative': float(100 * negative_count / total_count) if total_count > 0 else 0,
        'cleaned_nan_values': int(nan_count),
        'cleaned_valid_values': int(valid_count),
        'original_min': float(np.nanmin(original_array)) if len(original_array) > 0 else np.nan,
        'original_max': float(np.nanmax(original_array)) if len(original_array) > 0 else np.nan,
        'cleaned_min': float(np.nanmin(cleaned_array)) if valid_count > 0 else np.nan,
        'cleaned_max': float(np.nanmax(cleaned_array)) if valid_count > 0 else np.nan,
    }
    
    return stats


def print_cleaning_report(original_log, cleaned_log, name="Flujo"):
    """
    Imprime un reporte detallado de la limpieza.
    
    Parámetros:
    -----------
    original_log : array - Valores originales
    cleaned_log : array - Valores limpios
    name : str - Nombre del dataset para el reporte
    """
    stats = get_statistics_before_after(original_log, cleaned_log)
    
    print(f"\n{'='*60}")
    print(f"REPORTE DE LIMPIEZA - {name}")
    print(f"{'='*60}")
    print(f"\nDATOS ORIGINALES (escala logarítmica):")
    print(f"  • Total de valores: {stats['original_total_values']:,}")
    print(f"  • Valores negativos: {stats['original_negative_values']:,} ({stats['percentage_negative']:.2f}%)")
    print(f"  • Rango: [{stats['original_min']:.2f}, {stats['original_max']:.2f}]")
    
    print(f"\nDATOS DESPUÉS DE LIMPIEZA:")
    print(f"  • Valores válidos: {stats['cleaned_valid_values']:,}")
    print(f"  • Valores NaN: {stats['cleaned_nan_values']:,}")
    print(f"  • Rango: [{stats['cleaned_min']:.2f}, {stats['cleaned_max']:.2f}]")
    
    print(f"\nINTERPRETACIÓN:")
    print(f"  • Valores log < 0 → Flujo < 1 eV/cm²/ster/s (excluidos de visualización)")
    print(f"  • Valores log ≥ 0 → Flujo ≥ 1 eV/cm²/ster/s (mostrados)")
    print(f"{'='*60}\n")


# Valores de referencia para interpretar escala logarítmica
LOG_SCALE_REFERENCE = {
    'log': 'log10(flujo)',
    'flujo_min': 1e-10,
    'flujo_max': 1e+6,
    'references': [
        ('log = -10', 'flujo = 1e-10 eV/cm²/ster/s (muy débil)'),
        ('log = -5', 'flujo = 1e-5 eV/cm²/ster/s (débil)'),
        ('log = 0', 'flujo = 1 eV/cm²/ster/s (umbral típico)'),
        ('log = 2', 'flujo = 100 eV/cm²/ster/s (alto)'),
        ('log = 4', 'flujo = 10,000 eV/cm²/ster/s (muy alto)'),
    ]
}


def print_log_scale_reference():
    """Imprime una tabla de referencia para interpretar valores en escala logarítmica."""
    print(f"\n{'='*70}")
    print("TABLA DE REFERENCIA - ESCALA LOGARÍTMICA")
    print(f"{'='*70}")
    print(f"\nDefinición: {LOG_SCALE_REFERENCE['log']}\n")
    
    for log_val, flujo_desc in LOG_SCALE_REFERENCE['references']:
        print(f"  {log_val:15} → {flujo_desc}")
    
    print(f"\n{'='*70}\n")
