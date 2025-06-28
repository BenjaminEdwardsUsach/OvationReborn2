#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#%%
import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator

import funciones as ov

def main(cdf_file):
    """
    Script principal refactorizado para procesar un archivo CDF completo,
    utilizando funciones agrupadas en módulos separados.
    """

    # 1. Cargar todos los datos desde el archivo CDF
    datos = ov.cargar_datos_cdf(cdf_file)
    tiempo_final        = datos["tiempo_final"]
    tiempo_final_dict   =  {t: i for i, t in enumerate(tiempo_final)}
    CHANNEL_ENERGIES    = datos["CHANNEL_ENERGIES"]
    ELE_DIFF_ENERGY_FLUX  = datos["ELE_DIFF_ENERGY_FLUX"]
    ION_DIFF_ENERGY_FLUX  = datos["ION_DIFF_ENERGY_FLUX"]
    SC_AACGM_LAT        = datos["SC_AACGM_LAT"]
    SC_GEOCENTRIC_LAT   = datos["SC_GEOCENTRIC_LAT"]

    print("Datos cargados desde el archivo CDF.")

    # 2. Filtrar los canales de energía y calcular delta
    #    (mantiene índices coherentes en las matrices de flujo)
    CHANNEL_ENERGIES_f, \
    ELE_DIFF_ENERGY_FLUX_f, \
    ION_DIFF_ENERGY_FLUX_f, \
    delta = ov.filtrar_canales(
        CHANNEL_ENERGIES,
        ELE_DIFF_ENERGY_FLUX,
        ION_DIFF_ENERGY_FLUX,
        low=30,
        high=30000
    )
    print("Canales filtrados y delta calculado.")
    # 3. Integrar flujo diferencial de iones usando los canales filtrados
    flujos_iones = ov.integrar_flujo_diferencial(
        ION_DIFF_ENERGY_FLUX_f,
        delta,
        canal1=0,
        canal2=6
    )
    print("Flujo diferencial de iones integrado.")

    energy_edges = ov.compute_energy_edges(CHANNEL_ENERGIES)

    # 5. Separar datos según latitud (ajustados vs. otros) y obtener comparador
    adjust_SC_AACGM_LAT, \
    adjust_tiempo_final, \
    other_SC_AACGM_LAT, \
    other_tiempo_final, \
    comparador = ov.separar_por_latitud(
        SC_AACGM_LAT,
        tiempo_final
    )
    print("Datos separados por latitud ajustada y otros.")
    # 6. Detectar extremos de latitud en la parte ajustada
    extremos = ov.detectar_extremos_latitud(
        adjust_SC_AACGM_LAT,
        adjust_tiempo_final
    )
    
    # 7. Agrupar los extremos en pares (inicio, fin) para cada ciclo
    pares_extremos = ov.agrupar_extremos(extremos)

    # 8. Seleccionar segmentos válidos para procesamiento,
    #    según tolerancia y número mínimo de puntos
    valid_data, otros_data = ov.seleccionar_segmentos_validos(
        pares_extremos,
        adjust_SC_AACGM_LAT,
        adjust_tiempo_final,
        comparador,
        tol=1
    )

    # 9. Crear carpeta principal basada en el nombre del archivo CDF
    main_folder = ov.crear_carpetas(cdf_file)
    print(f"Carpeta principal creada: {main_folder}")

    # 10. Procesar ciclos válidos (generación de gráficas, información JSON, etc.)
    ov.procesar_ciclos(
        pares_extremos,
        tiempo_final,
        tiempo_final_dict,
        adjust_SC_AACGM_LAT,
        SC_GEOCENTRIC_LAT,
        flujos_iones,
        ION_DIFF_ENERGY_FLUX,
        energy_edges,
        main_folder
    )

    print("Procesamiento completado.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python OvationRebron2.0.py <ruta_al_archivo.cdf>")
        sys.exit(1)

    cdf_path = sys.argv[1]
    if not os.path.isfile(cdf_path):
        print(f"Error: No se encontró el archivo CDF en '{cdf_path}'")
        sys.exit(1)

    main(cdf_path)
