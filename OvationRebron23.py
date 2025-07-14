#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#%%
import os
import sys
import numpy as np
import funciones as ov

def main(cdf_file):
    """Script principal con detección completa de fronteras"""
    # 1. Cargar datos
    datos = ov.cargar_datos_cdf(cdf_file)
    tiempo_final = datos["tiempo_final"]
    ele_total_energy = datos["ELE_TOTAL_ENERGY_FLUX"]
    CHANNEL_ENERGIES = datos["CHANNEL_ENERGIES"]
    tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}
    
    # 2. Calcular energía promedio de electrones si no existe
    if 'ELE_AVG_ENERGY' not in datos:
        ele_avg_energy = np.zeros(len(tiempo_final))
        for i in range(len(datos['ELE_DIFF_ENERGY_FLUX'])):
            flux = datos['ELE_DIFF_ENERGY_FLUX'][i]
            valid_mask = flux > 0
            if np.any(valid_mask):
                weighted_energy = np.sum(flux[valid_mask] * datos['CHANNEL_ENERGIES'][valid_mask])
                total_flux = np.sum(flux[valid_mask])
                ele_avg_energy[i] = weighted_energy / total_flux
        datos['ELE_AVG_ENERGY'] = ele_avg_energy
    
    # 3. Filtrar canales
    CHANNEL_ENERGIES_f, ELE_DIFF_ENERGY_FLUX_f, ION_DIFF_ENERGY_FLUX_f, delta = ov.filtrar_canales(
        datos['CHANNEL_ENERGIES'],
        datos['ELE_DIFF_ENERGY_FLUX'],
        datos['ION_DIFF_ENERGY_FLUX'],
        low=30,
        high=30000
    )
    
    # 4. Integrar flujo de iones
    flujos_iones = ov.integrar_flujo_diferencial(
        ION_DIFF_ENERGY_FLUX_f,
        delta,
        canal1=0,
        canal2=6
    )
    
    # Integrar flujo de electrones
    flujos_elec = ov.integrar_flujo_diferencial(
        ELE_DIFF_ENERGY_FLUX_f,
        delta,
        canal1=0,
        canal2=6
    )

    # 5. Separar por latitud
    adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, comparador = ov.separar_por_latitud(
        datos['SC_AACGM_LAT'],
        tiempo_final
    )
    
    # 6. Detectar extremos
    extremos = ov.detectar_extremos_latitud(
        adjust_SC_AACGM_LAT,
        adjust_tiempo_final
    )
    
    # 7. Agrupar extremos
    pares_extremos = ov.agrupar_extremos(extremos)
    
    # 8. Crear carpeta principal
    main_folder = ov.crear_carpetas(cdf_file)
    
    # 9. Calcular bordes de energía
    energy_edges = ov.compute_energy_edges(CHANNEL_ENERGIES)
    
    # 10. Procesar ciclos con todas las fronteras
    ov.procesar_ciclos(
        pares_extremos,
        tiempo_final,
        tiempo_final_dict,
        datos['SC_AACGM_LAT'],
        datos['SC_GEOCENTRIC_LAT'],
        flujos_iones,
        flujos_elec,         # 6: flujo total de electrones
        ele_total_energy,         # 7: energía total de electrones
        ELE_DIFF_ENERGY_FLUX_f,   # 8: flujo diferencial de electrones
        datos['ELE_AVG_ENERGY'],  # 9: energía promedio de electrones
        ION_DIFF_ENERGY_FLUX_f,   # 10: flujo diferencial de iones
        CHANNEL_ENERGIES_f,
        energy_edges,
        main_folder
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python OvationRebron2.0.py <ruta_al_archivo.cdf>")
        sys.exit(1)
    
    cdf_path = sys.argv[1]
    if not os.path.isfile(cdf_path):
        print(f"Error: No se encontró el archivo CDF en '{cdf_path}'")
        sys.exit(1)
    
    main(cdf_path)