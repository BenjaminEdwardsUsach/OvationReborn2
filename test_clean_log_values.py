#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_clean_log_values.py - Script de prueba para limpiar valores negativos en log

Este script demuestra cómo funcionan las funciones de limpieza y filtrado de valores
negativos en escala logarítmica, útil para visualización de datos DMSP.

Uso:
    python test_clean_log_values.py
"""

import numpy as np
import sys
import os

# Añadir la carpeta de funciones al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'funciones'))

from clean_log_values import (
    clean_negative_log_values,
    clean_log_array_2d,
    get_statistics_before_after,
    print_cleaning_report,
    print_log_scale_reference
)


def test_basic_cleaning():
    """Prueba básica de limpieza de valores negativos."""
    print("\n" + "="*70)
    print("PRUEBA 1: Limpieza básica de valores negativos")
    print("="*70)
    
    # Crear datos de ejemplo con valores negativos
    # Simulamos flujos en escala logarítmica
    flujos_originales = np.array([
        -5.5,  # Muy pequeño
        -2.3,  # Pequeño
        -0.5,  # Levemente negativo
        0.0,   # log10(1) = 0
        1.5,   # Normal
        2.8,   # Alto
        3.2,   # Muy alto
    ])
    
    print("\nFlujos originales en escala logarítmica:")
    print(flujos_originales)
    
    # Limpiar
    flujos_limpios = clean_negative_log_values(flujos_originales, replace_with_nan=True, threshold=0.0)
    
    print("\nFlujos después de limpiar (valores < 0 → NaN):")
    print(flujos_limpios)
    
    # Estadísticas
    stats = get_statistics_before_after(flujos_originales, flujos_limpios)
    print(f"\nEstadísticas:")
    print(f"  • Valores negativos eliminados: {stats['original_negative_values']}")
    print(f"  • Valores válidos restantes: {stats['cleaned_valid_values']}")
    print(f"  • Porcentaje eliminado: {stats['percentage_negative']:.1f}%")


def test_2d_array_cleaning():
    """Prueba de limpieza de matriz 2D (típico para datos de tiempo x energía)."""
    print("\n" + "="*70)
    print("PRUEBA 2: Limpieza de matriz 2D (Tiempo x Energía)")
    print("="*70)
    
    # Simular espectrograma en log (3 energías x 5 tiempos)
    # Representa: 3 canales de energía, 5 mediciones en el tiempo
    espectro_original = np.array([
        [-2.1, -1.5, 0.2, 1.3, 2.1],  # Energía 1
        [-0.8, 0.5, 1.2, 1.8, 2.5],   # Energía 2
        [1.2, 1.9, 2.3, 2.7, 3.1],    # Energía 3
    ])
    
    print("\nEspectrograma original (3 canales x 5 tiempos):")
    print("(cada fila es un canal de energía, cada columna es un tiempo)")
    print(espectro_original)
    
    # Limpiar
    espectro_limpio = clean_log_array_2d(espectro_original, replace_with_nan=True, threshold=0.0)
    
    print("\nEspectrograma después de limpiar:")
    print(espectro_limpio)
    
    # Reporte
    print_cleaning_report(espectro_original, espectro_limpio, "Espectrograma 2D")


def test_with_random_data():
    """Prueba con datos aleatorios realistas."""
    print("\n" + "="*70)
    print("PRUEBA 3: Limpieza con datos aleatorios realistas")
    print("="*70)
    
    # Simular 1000 mediciones de flujo
    # Con distribución que incluya valores negativos y positivos
    np.random.seed(42)
    flujos_reales = np.random.normal(loc=0.8, scale=2.0, size=1000)
    
    print(f"\nDatos aleatorios generados:")
    print(f"  • Total de mediciones: {len(flujos_reales)}")
    print(f"  • Rango: [{flujos_reales.min():.2f}, {flujos_reales.max():.2f}]")
    print(f"  • Valores negativos: {np.sum(flujos_reales < 0)}")
    
    # Limpiar
    flujos_limpios = clean_negative_log_values(flujos_reales, replace_with_nan=True, threshold=0.0)
    
    # Generar reporte
    print_cleaning_report(flujos_reales, flujos_limpios, "Datos Aleatorios")


def test_threshold_variations():
    """Prueba con diferentes umbrales de filtrado."""
    print("\n" + "="*70)
    print("PRUEBA 4: Variación de umbrales de filtrado")
    print("="*70)
    
    # Crear datos de ejemplo
    flujos = np.array([-2, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3])
    
    # Probar diferentes umbrales
    umbrales = [0.0, 0.5, 1.0, 1.5]
    
    print(f"\nFlujos originales: {flujos}\n")
    
    for threshold in umbrales:
        limpio = clean_negative_log_values(flujos, replace_with_nan=True, threshold=threshold)
        nan_count = np.sum(np.isnan(limpio))
        valid_count = np.sum(~np.isnan(limpio))
        
        print(f"Umbral = {threshold}:")
        print(f"  Valores mantienidos: {valid_count}, Convertidos a NaN: {nan_count}")
        print(f"  Resultado: {limpio}\n")


def test_real_dmsp_format():
    """Prueba simulando el formato real de datos DMSP."""
    print("\n" + "="*70)
    print("PRUEBA 5: Simulación con formato real DMSP")
    print("="*70)
    
    print("\nSimulando flujos de iones y electrones en escala logarítmica:")
    
    # Simular flujos de iones totales (log)
    flujos_iones_log = np.random.uniform(-3, 3, 100)
    # Simular flujos de electrones totales (log)
    flujos_elec_log = np.random.uniform(-2, 4, 100)
    
    print(f"\nFlujos de Iones (log10):")
    print(f"  • Antes: min={flujos_iones_log.min():.2f}, max={flujos_iones_log.max():.2f}")
    
    flujos_iones_limpio = clean_negative_log_values(flujos_iones_log, replace_with_nan=True)
    print(f"  • Después: min={np.nanmin(flujos_iones_limpio):.2f}, max={np.nanmax(flujos_iones_limpio):.2f}")
    print(f"  • NaN: {np.sum(np.isnan(flujos_iones_limpio))}")
    
    print(f"\nFlujos de Electrones (log10):")
    print(f"  • Antes: min={flujos_elec_log.min():.2f}, max={flujos_elec_log.max():.2f}")
    
    flujos_elec_limpio = clean_negative_log_values(flujos_elec_log, replace_with_nan=True)
    print(f"  • Después: min={np.nanmin(flujos_elec_limpio):.2f}, max={np.nanmax(flujos_elec_limpio):.2f}")
    print(f"  • NaN: {np.sum(np.isnan(flujos_elec_limpio))}")
    
    # Reporte
    print_cleaning_report(flujos_iones_log, flujos_iones_limpio, "Flujos de Iones")
    print_cleaning_report(flujos_elec_log, flujos_elec_limpio, "Flujos de Electrones")


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "="*70)
    print("AMBIENTE DE PRUEBA - LIMPIEZA DE VALORES NEGATIVOS EN LOG")
    print("="*70)
    
    # Mostrar tabla de referencia
    print_log_scale_reference()
    
    # Ejecutar pruebas
    test_basic_cleaning()
    test_2d_array_cleaning()
    test_with_random_data()
    test_threshold_variations()
    test_real_dmsp_format()
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print("""
Las funciones de limpieza permiten:

1. REEMPLAZAR valores negativos con NaN
   → Útil para excluir datos de muy baja intensidad
   
2. APLICAR umbrales
   → Filtrar datos por debajo de un valor mínimo
   
3. OBTENER ESTADÍSTICAS
   → Cuantificar cuántos datos se afectan
   
RECOMENDACIÓN:
✓ Usar replace_with_nan=True para visualización (excluye puntos inválidos)
✓ Usar threshold=-1.0 para flujos débiles (10^-1 eV/cm²/ster/s)
✓ Usar threshold=0.0 para excluir flujos menores a 1 eV/cm²/ster/s

Para integrar en el código principal:
1. Importar: from funciones.clean_log_values import clean_negative_log_values
2. Usar después de calcular logs: flujos_limpio = clean_negative_log_values(flujos_log)
3. Pasar al procesamiento: procesar_ciclos(..., flujos_limpio, ...)
    """)
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
