#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#%%
import os
import sys
import numpy as np
import argparse
import funciones as ov

def main(cdf_file, fronteras=None, inicio=None, fin=None):
    """Script principal CORREGIDO - Preserva espectros diferenciales completos"""
    # 1. Cargar datos
    datos = ov.cargar_datos_cdf(cdf_file)
    tiempo_final = datos["tiempo_final"]
    ele_total_energy = datos["ELE_TOTAL_ENERGY_FLUX"]  
    CHANNEL_ENERGIES = datos["CHANNEL_ENERGIES"]
    tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}
    
    # 2. Filtrar por intervalo de tiempo si se especificó
    if inicio or fin:
        tiempo_np = np.array(tiempo_final)
        mascara_tiempo = np.full_like(tiempo_np, True, dtype=bool)
        
        if inicio:
            mascara_tiempo &= (tiempo_np >= np.datetime64(inicio))
        if fin:
            mascara_tiempo &= (tiempo_np <= np.datetime64(fin))
            
        # Aplicar máscara a todos los datos relevantes
        tiempo_final = tiempo_final[mascara_tiempo]
        datos['SC_AACGM_LAT'] = datos['SC_AACGM_LAT'][mascara_tiempo]
        datos['SC_GEOCENTRIC_LAT'] = datos['SC_GEOCENTRIC_LAT'][mascara_tiempo]
        datos['ELE_DIFF_ENERGY_FLUX'] = datos['ELE_DIFF_ENERGY_FLUX'][mascara_tiempo]
        datos['ION_DIFF_ENERGY_FLUX'] = datos['ION_DIFF_ENERGY_FLUX'][mascara_tiempo]
        datos['ELE_TOTAL_ENERGY_FLUX'] = datos['ELE_TOTAL_ENERGY_FLUX'][mascara_tiempo]
        datos['ELE_AVG_ENERGY'] = datos['ELE_AVG_ENERGY'][mascara_tiempo] if 'ELE_AVG_ENERGY' in datos else None
        
        # Filtrar ele_total_energy también
        ele_total_energy = datos['ELE_TOTAL_ENERGY_FLUX']
        
        # Actualizar diccionario de tiempo
        tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}
    
    # 3. Calcular energía promedio de electrones si no existe
    if 'ELE_AVG_ENERGY' not in datos or datos['ELE_AVG_ENERGY'] is None:
        ele_avg_energy = np.zeros(len(tiempo_final))
        for i in range(len(datos['ELE_DIFF_ENERGY_FLUX'])):
            flux = datos['ELE_DIFF_ENERGY_FLUX'][i]
            valid_mask = flux > 0
            if np.any(valid_mask):
                weighted_energy = np.sum(flux[valid_mask] * datos['CHANNEL_ENERGIES'][valid_mask])
                total_flux = np.sum(flux[valid_mask])
                ele_avg_energy[i] = weighted_energy / total_flux if total_flux > 0 else 0.0
        datos['ELE_AVG_ENERGY'] = ele_avg_energy
    
    # 4. Filtrar canales (pero MANTENER ESPECTROS DIFERENCIALES)
    CHANNEL_ENERGIES_f, ELE_DIFF_ESPECTROS, ION_DIFF_ESPECTROS, delta = ov.filtrar_canales(
        datos['CHANNEL_ENERGIES'],
        datos['ELE_DIFF_ENERGY_FLUX'],
        datos['ION_DIFF_ENERGY_FLUX'],
        low=30,
        high=30000
    )

    # 5. Calcular flujos integrados ESPECÍFICOS solo para lo necesario
    # Para b2i: iones 3-30 keV (canales 0-6 en orden descendente)
    flujos_iones_b2i = ov.integrar_flujo_diferencial(
        ION_DIFF_ESPECTROS,
        delta,
        canal1=0,   # 30000 eV (más energético)
        canal2=7     # 3000 eV (límite inferior de 3 keV)
    )

    # Flujos totales para visualización y algunas fronteras
    flujos_elec_totales = ov.integrar_flujo_diferencial(
        ELE_DIFF_ESPECTROS,
        delta,
        canal1=0,   # 30000 eV
        canal2=19    # 30 eV (todo el rango)
    )

    flujos_iones_totales = ov.integrar_flujo_diferencial(
        ION_DIFF_ESPECTROS,
        delta, 
        canal1=0,
        canal2=19    # 30 eV (todo el rango)
    )

    # ¡CONVERTIR A ESCALA LOGARÍTMICA solo para visualización!
    flujos_iones_log = np.log10(flujos_iones_totales + 1e-10)
    flujos_elec_log = np.log10(flujos_elec_totales + 1e-10)
    flujos_iones_b2i_log = np.log10(flujos_iones_b2i + 1e-10)

    # 6. Separar por latitud
    adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, transitions = ov.separar_por_latitud(
        datos['SC_AACGM_LAT'],
        tiempo_final
    )
    
    # 7. Detectar extremos
    extremos = ov.detectar_extremos_latitud(
        adjust_SC_AACGM_LAT,
        adjust_tiempo_final
    )
    
    # 8. Agrupar extremos
    pares_extremos = ov.agrupar_extremos(extremos)
    
    # 9. Crear carpeta principal
    main_folder = ov.crear_carpetas(cdf_file)
    
    # Calcular energy_edges con CHANNEL_ENERGIES_f 
    energy_edges = ov.compute_energy_edges(CHANNEL_ENERGIES_f)

    # 10. Verificar dimensiones antes de procesar
    if (len(tiempo_final) == len(flujos_iones_log) == 
        len(flujos_elec_log) == len(flujos_iones_b2i_log) ==
        len(ELE_DIFF_ESPECTROS) == len(ION_DIFF_ESPECTROS)):

        ov.procesar_ciclos(
            pares_extremos,
            tiempo_final,
            tiempo_final_dict,
            datos['SC_AACGM_LAT'],
            datos['SC_GEOCENTRIC_LAT'],
            flujos_iones_log,           # Flujo total iones (log) - para visualización
            flujos_elec_log,            # Flujo total electrones (log) - para visualización
            flujos_iones_b2i_log,       # Flujo b2i específico - para frontera b2i
            ele_total_energy,
            ELE_DIFF_ESPECTROS,         # ESPECTROS DIFERENCIALES COMPLETOS - para detección
            datos['ELE_AVG_ENERGY'],
            ION_DIFF_ESPECTROS,         # ESPECTROS DIFERENCIALES COMPLETOS - para detección
            CHANNEL_ENERGIES_f,
            energy_edges,
            main_folder,
            fronteras=fronteras
        )
    else:
        print("ERROR: Dimensiones inconsistentes entre arrays de datos")

if __name__ == "__main__":
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Detector de fronteras aurorales')
    parser.add_argument('cdf_file', help='Ruta al archivo CDF')
    parser.add_argument('--fronteras', nargs='*', default=['all'],
                        help='Lista de fronteras a calcular (b1e,b2e,b2i,b3a,b3b,b4s,b5e,b5i,b6) o "all" para todas')
    parser.add_argument('--inicio', help='Tiempo de inicio en formato ISO (ej: 2014-12-31T12:00:00)')
    parser.add_argument('--fin', help='Tiempo final en formato ISO (ej: 2014-12-31T12:30:00)')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.cdf_file):
        print(f"Error: Archivo {args.cdf_file} no encontrado")
        sys.exit(1)
    
    # Procesar argumento de fronteras
    if 'all' in args.fronteras:
        fronteras = None  # None significa todas
    else:
        fronteras = args.fronteras
    
    main(args.cdf_file, fronteras=fronteras, inicio=args.inicio, fin=args.fin)