#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#%%
import os
import sys
import numpy as np
import argparse
import funciones as ov

def main(cdf_file, fronteras=None, inicio=None, fin=None):
    """Script principal con detección completa de fronteras"""
    # 1. Cargar datos
    datos = ov.cargar_datos_cdf(cdf_file)
    tiempo_final = datos["tiempo_final"]
    ele_total_energy = datos["ELE_TOTAL_ENERGY_FLUX"]  # ✅ MANTENER para filtrado posterior
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
        
        # ✅ CORRECCIÓN CRÍTICA: Filtrar ele_total_energy también
        ele_total_energy = datos['ELE_TOTAL_ENERGY_FLUX']
        
        # Actualizar diccionario de tiempo
        tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}
        
        print(f"Datos filtrados: {len(tiempo_final)} puntos temporales")
    
    # 3. Calcular energía promedio de electrones si no existe
    if 'ELE_AVG_ENERGY' not in datos or datos['ELE_AVG_ENERGY'] is None:
        ele_avg_energy = np.zeros(len(tiempo_final))
        for i in range(len(datos['ELE_DIFF_ENERGY_FLUX'])):
            flux = datos['ELE_DIFF_ENERGY_FLUX'][i]
            valid_mask = flux > 0
            if np.any(valid_mask):
                weighted_energy = np.sum(flux[valid_mask] * datos['CHANNEL_ENERGIES'][valid_mask])
                total_flux = np.sum(flux[valid_mask])
                ele_avg_energy[i] = weighted_energy / total_flux
        datos['ELE_AVG_ENERGY'] = ele_avg_energy
    
    # 4. Filtrar canales
    CHANNEL_ENERGIES_f, ELE_DIFF_ENERGY_FLUX_f, ION_DIFF_ENERGY_FLUX_f, delta = ov.filtrar_canales(
        datos['CHANNEL_ENERGIES'],
        datos['ELE_DIFF_ENERGY_FLUX'],
        datos['ION_DIFF_ENERGY_FLUX'],
        low=30,
        high=30000
    )

    print(f"Canales filtrados: {len(CHANNEL_ENERGIES_f)} canales entre {CHANNEL_ENERGIES_f[0]} y {CHANNEL_ENERGIES_f[-1]} eV")
    

    # 5. Integrar flujos con rangos CORRECTOS para orden descendente
    print("🎯 Integrando flujos con rangos CORRECTOS para orden descendente:")

    # Para b2i: iones 3-30 keV (canales 0-6 en orden descendente)
    flujos_iones_b2i = ov.integrar_flujo_diferencial(
        ION_DIFF_ENERGY_FLUX_f,
        delta,
        canal1=0,   # 30000 eV (más energético)
        canal2=7     # 3000 eV (límite inferior de 3 keV)
    )

    # Para electrones: rango completo o específico
    flujos_elec = ov.integrar_flujo_diferencial(
        ELE_DIFF_ENERGY_FLUX_f,
        delta,
        canal1=0,   # 30000 eV
        canal2=19    # 30 eV (todo el rango)
    )

    # Para otras fronteras que necesiten flujo total de iones
    flujos_iones = ov.integrar_flujo_diferencial(
        ION_DIFF_ENERGY_FLUX_f,
        delta, 
        canal1=0,
        canal2=19    # 30 eV (todo el rango)
    )

    # ¡CONVERTIR A ESCALA LOGARÍTMICA! (como espera el paper)
    print("📊 Convirtiendo flujos a escala logarítmica...")
    flujos_iones_log = np.log10(flujos_iones + 1e-10)  # +1e-10 para evitar log(0)
    flujos_elec_log = np.log10(flujos_elec + 1e-10)
    flujos_iones_b2i_log = np.log10(flujos_iones_b2i + 1e-10)

    print(f"✅ Flujos integrados - Iones: {flujos_iones_log.shape}, Electrones: {flujos_elec_log.shape}")
    print(f"   Rangos log - Iones: [{np.min(flujos_iones_log):.2f}, {np.max(flujos_iones_log):.2f}]")
    print(f"   Rangos log - Electrones: [{np.min(flujos_elec_log):.2f}, {np.max(flujos_elec_log):.2f}]")

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
    
    # ✅ CORRECCIÓN CRÍTICA: Calcular energy_edges con CHANNEL_ENERGIES_f (filtrado)
    energy_edges = ov.compute_energy_edges(CHANNEL_ENERGIES_f)

    # En OvationRebron23.py, ANTES de llamar procesar_ciclos:
    print("🔍 VERIFICACIÓN FINAL DE FLUJOS:")
    print(f"   flujos_iones_log: shape={flujos_iones_log.shape}, " +
        f"NaN={np.sum(np.isnan(flujos_iones_log))}, " +
        f"rango=[{np.nanmin(flujos_iones_log):.2f}, {np.nanmax(flujos_iones_log):.2f}]")
    print(f"   flujos_elec_log: shape={flujos_elec_log.shape}, " +
        f"NaN={np.sum(np.isnan(flujos_elec_log))}, " +
        f"rango=[{np.nanmin(flujos_elec_log):.2f}, {np.nanmax(flujos_elec_log):.2f}]")
    print(f"   flujos_iones_b2i_log: shape={flujos_iones_b2i_log.shape}, " +
        f"NaN={np.sum(np.isnan(flujos_iones_b2i_log))}, " +
        f"rango=[{np.nanmin(flujos_iones_b2i_log):.2f}, {np.nanmax(flujos_iones_b2i_log):.2f}]")

    # Verificar consistencia de dimensiones
    if len(tiempo_final) != len(flujos_iones_log):
        print(f"❌ ERROR CRÍTICO: Tiempo ({len(tiempo_final)}) y flujos iones ({len(flujos_iones_log)}) no coinciden")
    if len(tiempo_final) != len(flujos_elec_log):
        print(f"❌ ERROR CRÍTICO: Tiempo ({len(tiempo_final)}) y flujos elec ({len(flujos_elec_log)}) no coinciden")
    if len(tiempo_final) != len(flujos_iones_b2i_log):
        print(f"❌ ERROR CRÍTICO: Tiempo ({len(tiempo_final)}) y flujos b2i ({len(flujos_iones_b2i_log)}) no coinciden")

    # Llamar a procesar_ciclos solo si las verificaciones pasan
    if (len(tiempo_final) == len(flujos_iones_log) == 
        len(flujos_elec_log) == len(flujos_iones_b2i_log)):

        ov.procesar_ciclos(
            pares_extremos,
            tiempo_final,
            tiempo_final_dict,
            datos['SC_AACGM_LAT'],
            datos['SC_GEOCENTRIC_LAT'],
            flujos_iones_log,           # Flujo total iones (log)
            flujos_elec_log,            # Flujo total electrones (log)
            flujos_iones_b2i_log,       # Flujo b2i específico
            ele_total_energy,
            ELE_DIFF_ENERGY_FLUX_f,
            datos['ELE_AVG_ENERGY'],
            ION_DIFF_ENERGY_FLUX_f,
            CHANNEL_ENERGIES_f,
            energy_edges,
            main_folder,
            fronteras=fronteras
        )
                
    else:
        print("❌ ERROR: No se puede procesar ciclos debido a inconsistencias en dimensiones")

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
        print(f"Error: No se encontró el archivo CDF en '{args.cdf_file}'")
        sys.exit(1)
    
    # Procesar argumento de fronteras
    if 'all' in args.fronteras:
        fronteras = None  # None significa todas
    else:
        fronteras = args.fronteras
        print(f"Calculando solo las fronteras: {', '.join(fronteras)}")
    
    main(args.cdf_file, fronteras=fronteras, inicio=args.inicio, fin=args.fin)