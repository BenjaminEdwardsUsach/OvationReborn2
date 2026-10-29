#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validar_integracion.py - Verificar que la limpieza de log está integrada correctamente
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'funciones'))


def validar_integracion():
    """Valida que la limpieza funcione correctamente"""
    
    print("\n" + "="*70)
    print("VALIDACIÓN DE INTEGRACIÓN - LIMPIEZA DE LOG")
    print("="*70)
    
    # Crear datos de prueba realistas
    print("\n1️⃣ Creando datos de prueba...")
    
    # Simular flujos sin limpiar (con negativos en log)
    flujos_iones_totales = np.array([0.1, 0.5, 0.05, 2.0, 100, 0.001])
    flujos_elec_totales = np.array([0.05, 0.02, 50, 1000, 0.5, 0.0001])
    flujos_iones_b2i = np.array([0.2, 0.1, 1.5, 30, 0.01, 0.0005])
    
    # Calcular logs (como en OvationRebron23.py línea ~110)
    flujos_iones_log_sin_limpiar = np.log10(flujos_iones_totales + 1e-10)

if __name__ == '__main__':
    try:
        validar_integracion()
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
