"""
ejemplo_integracion_clean_log.py - Ejemplo de cómo integrar limpieza de log en OvationRebron23.py

Este archivo muestra cómo añadir la funcionalidad de limpiar valores negativos en log
al procesamiento principal.
"""

import numpy as np
import sys
import os

# Simular estructura del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'funciones'))

from clean_log_values import (
    clean_negative_log_values,
    print_cleaning_report,
    print_log_scale_reference
)


# ============================================================================
# EJEMPLO 1: Integración Básica en OvationRebron23.py
# ============================================================================

def procesar_datos_dmsp_con_limpeza(archivo_cdf, limpiar_log_negativos=False, 
                                    threshold=0.0, directorio_salida="results"):
    """
    Versión modificada de procesar_datos_dmsp que opcionalmente limpia valores
    negativos en escala logarítmica.
    
    Parámetros adicionales:
    ----------------------
    limpiar_log_negativos : bool
        Si True, reemplaza valores log < threshold con NaN
    threshold : float
        Umbral para filtrado (defecto: 0.0, equivalente a flujo < 1)
    """
    
    print("\n" + "="*70)
    print("PROCESAMIENTO DE DATOS DMSP CON LIMPIEZA DE LOG")
    print("="*70)
    
    # Simular datos procesados (como en OvationRebron23.py)
    print("\nSimulando cálculo de flujos en escala logarítmica...")
    
    # Flujos totales (originales, sin log)
    flujos_iones_totales = np.array([0.5, 0.05, 2.0, 0.001, 100, 0.1])
    flujos_elec_totales = np.array([2.0, 0.02, 50, 1000, 0.5, 0.01])
    
    # Calcular logaritmos (como hace el código actual)
    flujos_iones_log = np.log10(flujos_iones_totales + 1e-10)
    flujos_elec_log = np.log10(flujos_elec_totales + 1e-10)
    
    print(f"\nFlujos de Iones originales: {flujos_iones_totales}")
    print(f"Flujos de Iones en log:     {flujos_iones_log}")
    print(f"\nFlujos de Electrones originales: {flujos_elec_totales}")
    print(f"Flujos de Electrones en log:     {flujos_elec_log}")
    
    # NUEVA FEATURE: Limpiar valores negativos si se solicita
    if limpiar_log_negativos:
        print(f"\n{'─'*70}")
        print("APLICANDO LIMPIEZA DE VALORES NEGATIVOS")
        print(f"{'─'*70}")
        print(f"Umbral: {threshold} → Flujo mínimo = 10^{threshold} eV/cm²/ster/s")
        
        flujos_iones_log_original = flujos_iones_log.copy()
        flujos_elec_log_original = flujos_elec_log.copy()
        
        flujos_iones_log = clean_negative_log_values(
            flujos_iones_log, 
            replace_with_nan=True, 
            threshold=threshold
        )
        flujos_elec_log = clean_negative_log_values(
            flujos_elec_log, 
            replace_with_nan=True, 
            threshold=threshold
        )
        
        print(f"\nFlujos de Iones después de limpiar:     {flujos_iones_log}")
        print(f"Flujos de Electrones después de limpiar: {flujos_elec_log}")
        
        # Mostrar reporte
        print_cleaning_report(flujos_iones_log_original, flujos_iones_log, "Flujos de Iones")
        print_cleaning_report(flujos_elec_log_original, flujos_elec_log, "Flujos de Electrones")
    
    else:
        print("\n(Limpieza desactivada)")
    
    # El resto del procesamiento continúa con los flujos limpios o sin limpiar
    print(f"\n{'─'*70}")
    print("CONTINUANDO CON PROCESAMIENTO NORMAL...")
    print(f"{'─'*70}")
    print("Los flujos se pasarían a procesar_ciclos() como siempre")
    print(f"{'─'*70}\n")
    
    return {
        'flujos_iones_log': flujos_iones_log,
        'flujos_elec_log': flujos_elec_log,
        'limpeza_aplicada': limpiar_log_negativos
    }


# ============================================================================
# EJEMPLO 2: Uso en main_app.py (Streamlit)
# ============================================================================

def ejemplo_streamlit_integration():
    """
    Código de ejemplo para integrar en main_app.py
    """
    
    codigo_ejemplo = '''
import streamlit as st

# En la sección de configuración del sidebar
st.sidebar.header("🧪 Ambiente de Prueba")

# Añadir checkbox para activar limpieza
limpiar_log = st.sidebar.checkbox(
    "Limpiar valores negativos en log",
    value=False,
    help="Reemplaza valores log < 0 con NaN para visualización más clara"
)

# Opcional: slider para ajustar umbral
if limpiar_log:
    umbral = st.sidebar.slider(
        "Umbral de filtrado",
        min_value=-3.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="Valores de log menores que este se excluyen (NaN)"
    )
else:
    umbral = None

# Pasar al procesamiento
try:
    resultados = ovation.procesar_datos_dmsp(
        archivo_cdf,
        limpiar_log_negativos=limpiar_log,
        threshold=umbral if umbral else 0.0
    )
    st.success("✅ Procesamiento completado")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    '''
    
    return codigo_ejemplo


# ============================================================================
# EJEMPLO 3: Modificación de OvationRebron23.py
# ============================================================================

def codigo_modificacion_ovation():
    """
    Muestra el código necesario para modificar OvationRebron23.py
    """
    
    codigo = '''
# En el inicio del archivo, añadir:
from funciones.clean_log_values import (
    clean_negative_log_values,
    print_cleaning_report
)

# En la función procesar_datos_dmsp, después de calcular los logs:

# Línea actual (no cambiar):
flujos_iones_log = np.log10(flujos_iones_totales + 1e-10)
flujos_elec_log = np.log10(flujos_elec_totales + 1e-10)

# Añadir estas líneas (nuevas):
# ─────────────────────────────────────
# FEATURE: Limpiar valores negativos en log (ambiente de prueba)
LIMPIAR_LOG_NEGATIVOS = False  # ← Cambiar a True para activar
THRESHOLD_LOG = 0.0            # ← Ajustar según necesidad

if LIMPIAR_LOG_NEGATIVOS:
    flujos_iones_log = clean_negative_log_values(
        flujos_iones_log,
        replace_with_nan=True,
        threshold=THRESHOLD_LOG
    )
    flujos_elec_log = clean_negative_log_values(
        flujos_elec_log,
        replace_with_nan=True,
        threshold=THRESHOLD_LOG
    )
    if DEBUG_MODE:  # Si existe modo debug
        print_cleaning_report(flujos_iones_log, flujos_iones_log, "Iones")
        print_cleaning_report(flujos_elec_log, flujos_elec_log, "Electrones")
# ─────────────────────────────────────

# El resto sigue normalmente:
flujos_iones_b2i = ov.integrar_flujo_diferencial(...)
    '''
    
    return codigo


# ============================================================================
# EJEMPLO 4: Comparación de Resultados
# ============================================================================

def demo_comparacion_visual():
    """
    Demuestra la diferencia visual entre limpiar y no limpiar
    """
    
    print("\n" + "="*70)
    print("COMPARACIÓN VISUAL: CON vs SIN LIMPIEZA")
    print("="*70)
    
    # Datos de ejemplo
    tiempos = np.arange(20)
    flujos_sin_limpiar = np.random.normal(0.5, 1.5, 20)  # Puede tener negativos en log
    flujos_log = np.log10(flujos_sin_limpiar + 1e-10)
    flujos_limpios = clean_negative_log_values(flujos_log, replace_with_nan=True, threshold=0.0)
    
    print("\n📊 GRÁFICO SIMULADO - SIN LIMPIEZA:")
    print(f"{'Tiempo':<8} {'Flujo (log)':<15} {'Visualización':<30}")
    print("─" * 53)
    
    for t, f in zip(tiempos[:10], flujos_log[:10]):
        bar = "█" * max(0, int((f + 5) * 3))
        print(f"{t:<8} {f:>7.2f}        {bar:<30}")
    
    print("\n📊 GRÁFICO SIMULADO - CON LIMPIEZA (log >= 0):")
    print(f"{'Tiempo':<8} {'Flujo (log)':<15} {'Visualización':<30}")
    print("─" * 53)
    
    for t, f in zip(tiempos[:10], flujos_limpios[:10]):
        if np.isnan(f):
            bar = "N/A (NaN)"
            f_str = "NaN"
        else:
            bar = "█" * max(0, int(f * 3))
            f_str = f"{f:.2f}"
        print(f"{t:<8} {f_str:>7}        {bar:<30}")
    
    stats_original = np.sum(flujos_log < 0)
    stats_limpio = np.sum(np.isnan(flujos_limpios))
    
    print(f"\n{'─'*70}")
    print(f"Valores negativos en original: {stats_original}")
    print(f"Valores convertidos a NaN:     {stats_limpio}")
    print(f"{'─'*70}\n")


# ============================================================================
# MAIN - Ejecutar Ejemplos
# ============================================================================

def main():
    """Ejecuta todos los ejemplos de integración"""
    
    print("\n" + "="*70)
    print("EJEMPLOS DE INTEGRACIÓN - LIMPIEZA DE VALORES NEGATIVOS EN LOG")
    print("="*70)
    
    # Mostrar tabla de referencia
    print_log_scale_reference()
    
    # Ejemplo 1: Integración básica
    print("\n" + "="*70)
    print("EJEMPLO 1: INTEGRACIÓN BÁSICA")
    print("="*70)
    
    print("\n▶ SIN LIMPIAR:")
    resultado1 = procesar_datos_dmsp_con_limpeza("dummy.cdf", limpiar_log_negativos=False)
    
    print("\n" + "─"*70)
    print("\n▶ CON LIMPIAR (threshold=0.0):")
    resultado2 = procesar_datos_dmsp_con_limpeza("dummy.cdf", limpiar_log_negativos=True, threshold=0.0)
    
    print("\n" + "─"*70)
    print("\n▶ CON LIMPIAR (threshold=-1.0, más permisivo):")
    resultado3 = procesar_datos_dmsp_con_limpeza("dummy.cdf", limpiar_log_negativos=True, threshold=-1.0)
    
    # Ejemplo 2: Código para Streamlit
    print("\n" + "="*70)
    print("EJEMPLO 2: INTEGRACIÓN EN main_app.py (STREAMLIT)")
    print("="*70)
    print("\nCódigo a añadir:")
    print(ejemplo_streamlit_integration())
    
    # Ejemplo 3: Modificación de OvationRebron23.py
    print("\n" + "="*70)
    print("EJEMPLO 3: MODIFICACIÓN DE OvationRebron23.py")
    print("="*70)
    print("\nCódigo a añadir:")
    print(codigo_modificacion_ovation())
    
    # Ejemplo 4: Comparación visual
    demo_comparacion_visual()
    
    # Summary
    print("\n" + "="*70)
    print("RESUMEN DE INTEGRACIÓN")
    print("="*70)
    print("""
OPCIONES DE INTEGRACIÓN:

1. ✅ RECOMENDADO PARA INICIO: Cambiar bandera en OvationRebron23.py
   - Archivo: OvationRebron23.py
   - Línea: LIMPIAR_LOG_NEGATIVOS = True/False
   - Fácil activar/desactivar

2. ✅ CON INTERFAZ GRÁFICA: Añadir checkbox en main_app.py
   - Archivo: main_app.py
   - Ubicación: sidebar → sección 🧪 Ambiente de Prueba
   - Permite cambiar en tiempo real en la UI

3. ✅ PARA ANÁLISIS: Llamar función específica
   - Usar: clean_negative_log_values(flujos_log, threshold=X)
   - Más control y flexibilidad

PARÁMETROS RECOMENDADOS:

• threshold = 0.0  (por defecto)
  → Excluye flujos < 1 eV/cm²/ster/s
  → Limpieza fuerte, mejor visualización

• threshold = -1.0
  → Excluye flujos < 0.1 eV/cm²/ster/s
  → Más datos, menos limpio

• threshold = -2.0
  → Excluye flujos < 0.01 eV/cm²/ster/s
  → Casi todo incluido, poco filtrado
    """)
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
