#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import argparse
import json
from datetime import datetime

# Importar módulo de funciones (asegúrate de que funciones.py esté en el mismo directorio)
try:
    import funciones as ov
except ImportError as e:
    print(f"Error importando funciones: {e}")
    # Crear funciones básicas si no existe el módulo
    ov = None

def procesar_datos_dmsp(archivo_cdf, directorio_salida="results"):
    """
    Función principal que procesa un archivo CDF DMSP
    
    Args:
        archivo_cdf (str): Ruta al archivo CDF
        directorio_salida (str): Directorio para guardar resultados
    
    Returns:
        dict: Información de los resultados
    """
    try:
        # Verificar que el archivo existe
        if not os.path.isfile(archivo_cdf):
            return {
                'estado': 'error',
                'error': f"Archivo no encontrado: {archivo_cdf}",
                'timestamp': datetime.now().isoformat()
            }
        
        # Verificar que el módulo de funciones está disponible
        if ov is None:
            return {
                'estado': 'error',
                'error': "Módulo 'funciones' no disponible",
                'timestamp': datetime.now().isoformat()
            }
        
        # 1. Cargar datos
        datos = ov.cargar_datos_cdf(archivo_cdf)
        tiempo_final = datos["tiempo_final"]
        ele_total_energy = datos["ELE_TOTAL_ENERGY_FLUX"]  
        CHANNEL_ENERGIES = datos["CHANNEL_ENERGIES"]
        tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}
        
        # 2. Calcular energía promedio de electrones si no existe
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
        
        # 3. Filtrar canales (pero MANTENER ESPECTROS DIFERENCIALES)
        CHANNEL_ENERGIES_f, ELE_DIFF_ESPECTROS, ION_DIFF_ESPECTROS, delta = ov.filtrar_canales(
            datos['CHANNEL_ENERGIES'],
            datos['ELE_DIFF_ENERGY_FLUX'],
            datos['ION_DIFF_ENERGY_FLUX'],
            low=30,
            high=30000
        )

        # 4. Calcular flujos integrados ESPECÍFICOS
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

        # Convertir a escala logarítmica solo para visualización
        flujos_iones_log = np.log10(flujos_iones_totales + 1e-10)
        flujos_elec_log = np.log10(flujos_elec_totales + 1e-10)
        flujos_iones_b2i_log = np.log10(flujos_iones_b2i + 1e-10)

        # 5. Separar por latitud
        adjust_SC_AACGM_LAT, adjust_tiempo_final, other_SC_AACGM_LAT, other_tiempo_final, transitions = ov.separar_por_latitud(
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
        
        # 8. Crear carpeta principal usando el directorio de salida
        main_folder = ov.crear_carpetas(archivo_cdf, directorio_base=directorio_salida)
        
        # Calcular energy_edges con CHANNEL_ENERGIES_f 
        energy_edges = ov.compute_energy_edges(CHANNEL_ENERGIES_f)

        # 9. Verificar dimensiones antes de procesar
        if (len(tiempo_final) == len(flujos_iones_log) == 
            len(flujos_elec_log) == len(flujos_iones_b2i_log) ==
            len(ELE_DIFF_ESPECTROS) == len(ION_DIFF_ESPECTROS)):

            # Ejecutar el procesamiento principal
            resultados_procesamiento = ov.procesar_ciclos(
                pares_extremos,
                tiempo_final,
                tiempo_final_dict,
                datos['SC_AACGM_LAT'],
                datos['SC_GEOCENTRIC_LAT'],
                flujos_iones_log,
                flujos_elec_log,
                flujos_iones_b2i_log,
                ele_total_energy,
                ELE_DIFF_ESPECTROS,
                datos['ELE_AVG_ENERGY'],
                ION_DIFF_ESPECTROS,
                CHANNEL_ENERGIES_f,
                energy_edges,
                main_folder,
                fronteras=None  # Procesar todas las fronteras
            )
            
            # Contar ciclos procesados
            numero_ciclos = len(pares_extremos) if pares_extremos else 0
            
            # Estructura de retorno para la aplicación Streamlit
            resultados = {
                'estado': 'completado',
                'archivo_procesado': archivo_cdf,
                'timestamp': datetime.now().isoformat(),
                'ciclos_procesados': numero_ciclos,
                'directorio_resultados': main_folder,
                'limites_detectados': {
                    'b1e': None,  # Estos valores se obtendrían del procesamiento real
                    'b1i': None,
                    'b2e': None,
                    'b2i': None,
                    'b3a': None,
                    'b3b': None,
                    'b4s': None,
                    'b5': None,
                    'b6': None
                },
                'datos_dimensiones': {
                    'puntos_tiempo': len(tiempo_final),
                    'canales_energia': len(CHANNEL_ENERGIES_f),
                    'extremos_detectados': len(extremos)
                }
            }
            
            # Si tenemos resultados del procesamiento, actualizar los límites
            if resultados_procesamiento:
                resultados['limites_detectados'].update(resultados_procesamiento)

            return resultados
            
        else:
            error_msg = "Dimensiones inconsistentes entre arrays de datos"
            return {
                'estado': 'error',
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {
            'estado': 'error',
            'error': str(e),
            'detalles_error': error_details,
            'timestamp': datetime.now().isoformat()
        }


def main(cdf_file, fronteras=None, inicio=None, fin=None):
    """
    Función principal para ejecución por línea de comandos
    """
    try:
        print(f"Procesando archivo: {cdf_file}")
        
        resultados = procesar_datos_dmsp(cdf_file)
        
        if resultados['estado'] == 'completado':
            print(f"Procesamiento completado exitosamente")
            print(f"Ciclos procesados: {resultados['ciclos_procesados']}")
            print(f"Resultados en: {resultados['directorio_resultados']}")
        else:
            print(f"Error en el procesamiento: {resultados['error']}")
            
        return resultados
        
    except Exception as e:
        print(f"Error durante la ejecución: {str(e)}")
        return {
            'estado': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


# Si el archivo se ejecuta directamente (no importado)
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
    
    # Ejecutar procesamiento
    main(args.cdf_file, fronteras=fronteras, inicio=args.inicio, fin=args.fin)