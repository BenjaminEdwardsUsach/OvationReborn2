# procesar_ciclos.py - VERSIÓN CORREGIDA
import numpy as np
from .segment_utils import split_cycle_segment
from .io_utils import save_cycle_info
from .plot_utils import plot_cycle, plot_polar_cycle
from .boundary_detection import detect_all_boundaries

def procesar_ciclos(pares_extremos, tiempo_final, tiempo_final_dict, sc_lat, sc_geo,
                    flujos_iones_log, flujos_elec_log, flujos_iones_b2i_log,
                    ele_total_energy, ele_diff_flux, ele_avg_energy, 
                    ion_diff_filtrado, channel_energies, energy_edges, 
                    main_folder, fronteras=None):
    
    print(f"🔄 Iniciando procesamiento de {len(pares_extremos)} ciclos")
    
    # Convertir datos a arrays NumPy
    flujos_iones_log = np.asarray(flujos_iones_log)
    flujos_elec_log = np.asarray(flujos_elec_log)
    flujos_iones_b2i_log = np.asarray(flujos_iones_b2i_log)
    ion_diff_filtrado = np.asarray(ion_diff_filtrado)
    ele_diff_flux = np.asarray(ele_diff_flux)
    ele_avg_energy = np.asarray(ele_avg_energy)
    
    print(f"✅ Flujos recibidos:")
    print(f"   - Iones log: [{np.nanmin(flujos_iones_log):.2f}, {np.nanmax(flujos_iones_log):.2f}]")
    print(f"   - Electrones log: [{np.nanmin(flujos_elec_log):.2f}, {np.nanmax(flujos_elec_log):.2f}]")
    print(f"   - Iones b2i log: [{np.nanmin(flujos_iones_b2i_log):.2f}, {np.nanmax(flujos_iones_b2i_log):.2f}]")
    
    for idx, par in enumerate(pares_extremos):
        print(f"\n🔁 Procesando ciclo {idx}/{len(pares_extremos)-1}")
        
        try:
            # 1) Segmentación - ✅ CORREGIDO: usar flujos_iones_log en lugar de flujos_iones
            segments = split_cycle_segment(
                par, tiempo_final, tiempo_final_dict,
                flujos_iones_log, sc_lat, sc_geo  # ✅ CAMBIADO: flujos_iones_log
            )
            
            seg1_orig_len = len(segments['seg1_original']['time'])
            seg2_orig_len = len(segments['seg2_original']['time'])
            direccion_original = segments.get('direccion_original', 'desconocida')
            
            print(f"   Segmentos originales: seg1={seg1_orig_len}, seg2={seg2_orig_len}, dirección={direccion_original}")
            
            # Verificar si hay datos para procesar
            if seg1_orig_len == 0 and seg2_orig_len == 0:
                print(f"   ⚠️  Ciclo {idx} sin datos, saltando...")
                continue

            # 2) Preparar datos para procesamiento
            def prepare_segment_data(segment, segment_type):
                """Prepara datos para un segmento - CON MANEJO DE ERRORES"""
                indices = segment['indices']
                
                if len(indices) == 0:
                    print(f"   ⚠️  Segmento {segment_type} está vacío")
                    return create_empty_segment_data(segment_type)
                
                try:
                    segment_data = {
                        'time': segment['time'],
                        'coords_aacgm': segment['coords_aacgm'],
                        'lat': segment['coords_aacgm'],
                        'ele_diff_flux': ele_diff_flux[indices],
                        'ion_diff_flux': ion_diff_filtrado[indices],
                        'ion_energy_flux': flujos_iones_log[indices],
                        'ion_energy_flux_b2i': flujos_iones_b2i_log[indices],  # ✅ FLUJO B2I
                        'flux_ion': flujos_iones_log[indices],
                        'ele_energy_flux': flujos_elec_log[indices],
                        'flux_ele': flujos_elec_log[indices],
                        'ele_avg_energy': ele_avg_energy[indices],
                        'energy_edges': energy_edges,
                        'direccion': segment.get('direccion_procesamiento', 'desconocida'),
                        'segment_type': segment_type
                    }
                    
                    # Diagnóstico seguro
                    if len(indices) > 0:
                        print(f"   🔍 Segmento {segment_type}:")
                        ion_flux_data = segment_data['ion_energy_flux']
                        ion_b2i_data = segment_data['ion_energy_flux_b2i']
                        
                        if ion_flux_data.size > 0:
                            valid_ion = ion_flux_data[~np.isnan(ion_flux_data)]
                            if valid_ion.size > 0:
                                print(f"      - ion_energy_flux (log): [{np.min(valid_ion):.2f}, {np.max(valid_ion):.2f}]")
                        
                        if ion_b2i_data.size > 0:
                            valid_b2i = ion_b2i_data[~np.isnan(ion_b2i_data)]
                            if valid_b2i.size > 0:
                                print(f"      - ion_energy_flux_b2i (log): [{np.min(valid_b2i):.2f}, {np.max(valid_b2i):.2f}]")
                    
                    return segment_data
                    
                except Exception as e:
                    print(f"   ❌ Error preparando segmento {segment_type}: {e}")
                    return create_empty_segment_data(segment_type)

            def create_empty_segment_data(segment_type):
                """Crea estructura de datos vacía"""
                return {
                    'time': np.array([]),
                    'coords_aacgm': np.array([]),
                    'lat': np.array([]),
                    'ele_diff_flux': np.array([]),
                    'ion_diff_flux': np.array([]),
                    'ion_energy_flux': np.array([]),
                    'ion_energy_flux_b2i': np.array([]),  # ✅ B2I vacío
                    'flux_ion': np.array([]),
                    'ele_energy_flux': np.array([]),
                    'flux_ele': np.array([]),
                    'ele_avg_energy': np.array([]),
                    'energy_edges': energy_edges,
                    'direccion': "desconocida",
                    'segment_type': segment_type
                }

            # Preparar segmentos
            seg1_processing_data = prepare_segment_data(segments['seg1_processing'], 'seg1')
            seg2_processing_data = prepare_segment_data(segments['seg2_processing'], 'seg2')
            seg1_original_data = prepare_segment_data(segments['seg1_original'], 'seg1')
            seg2_original_data = prepare_segment_data(segments['seg2_original'], 'seg2')

            # 3) Detectar fronteras - CON MANEJO DE ERRORES
            boundaries_seg1 = {}
            boundaries_seg2 = {}
            
            try:
                if len(seg1_processing_data['time']) > 0:
                    boundaries_seg1 = detect_all_boundaries(seg1_processing_data, channel_energies, fronteras=fronteras)
                else:
                    print(f"   ⚠️  Segmento 1 vacío, omitiendo detección de fronteras")
            except Exception as e:
                print(f"   ❌ Error detectando fronteras en segmento 1: {e}")
                boundaries_seg1 = {}
                
            try:
                if len(seg2_processing_data['time']) > 0:
                    boundaries_seg2 = detect_all_boundaries(seg2_processing_data, channel_energies, fronteras=fronteras)
                else:
                    print(f"   ⚠️  Segmento 2 vacío, omitiendo detección de fronteras")
            except Exception as e:
                print(f"   ❌ Error detectando fronteras en segmento 2: {e}")
                boundaries_seg2 = {}

            # 4) Ajustar índices de fronteras
            def safe_adjust_boundary(boundaries, processing_segment, original_segment):
                """Ajusta índices de forma segura"""
                adjusted = {}
                
                if (len(processing_segment['time']) == 0 or 
                    len(original_segment['time']) == 0):
                    return adjusted
                    
                for b_name, b_data in boundaries.items():
                    if b_data and b_data['index'] is not None:
                        try:
                            proc_len = len(processing_segment['time'])
                            orig_len = len(original_segment['time'])
                            
                            if processing_segment['direccion'] != original_segment['direccion']:
                                original_idx = proc_len - 1 - b_data['index']
                            else:
                                original_idx = b_data['index']
                            
                            original_idx = max(0, min(original_idx, orig_len - 1))
                            
                            adjusted[b_name] = {
                                'index': original_idx,
                                'time': original_segment['time'][original_idx],
                                'lat': original_segment['lat'][original_idx],
                                'deviation': b_data.get('deviation', 0),
                                'params': b_data.get('params', {})
                            }
                        except Exception as e:
                            print(f"   ⚠️  Error ajustando frontera {b_name}: {e}")
                            adjusted[b_name] = None
                    else:
                        adjusted[b_name] = b_data
                return adjusted

            boundaries_seg1_adj = safe_adjust_boundary(boundaries_seg1, seg1_processing_data, seg1_original_data)
            boundaries_seg2_adj = safe_adjust_boundary(boundaries_seg2, seg2_processing_data, seg2_original_data)

            # 5) Guardar información
            info = {
                'boundaries': {
                    'primera_mitad': boundaries_seg1_adj,
                    'segunda_mitad': boundaries_seg2_adj
                },
                'direccion_original': direccion_original,
                'segment_info': {
                    'seg1_processing_direction': seg1_processing_data['direccion'],
                    'seg2_processing_direction': seg2_processing_data['direccion'],
                    'seg1_original_direction': seg1_original_data['direccion'],
                    'seg2_original_direction': seg2_original_data['direccion']
                }
            }
            save_cycle_info(info, main_folder, idx)
            
            # 6) Preparar espectrogramas (usando datos originales para visualización)
            def prepare_spectrograms(segment):
                """Prepara espectrogramas asegurando dimensiones compatibles"""
                if len(segment['indices']) > 0:
                    try:
                        # Obtener datos
                        spec_ion = ion_diff_filtrado[segment['indices'], :].T
                        spec_ele = ele_diff_flux[segment['indices'], :].T
                        
                        # DIAGNÓSTICO: Verificar dimensiones
                        print(f"🔍 Preparando espectrogramas:")
                        print(f"   - Iones: {spec_ion.shape} (energías × tiempo)")
                        print(f"   - Electrones: {spec_ele.shape} (energías × tiempo)")
                        print(f"   - Segmento tiempo: {len(segment['time'])} puntos")
                        
                        # Asegurar que no hay NaN
                        spec_ion = np.nan_to_num(spec_ion, nan=1e-10)
                        spec_ele = np.nan_to_num(spec_ele, nan=1e-10)
                        
                        return spec_ion, spec_ele
                        
                    except Exception as e:
                        print(f"❌ Error preparando espectrogramas: {e}")
                        return np.array([]), np.array([])
                else:
                    return np.array([]), np.array([])
            
            spec1_ion, spec1_ele = prepare_spectrograms(segments['seg1_original'])
            spec2_ion, spec2_ele = prepare_spectrograms(segments['seg2_original'])

            # 7) Generar gráfico normal
            try:
                plot_cycle(
                    seg1_original_data,
                    seg2_original_data,
                    boundaries_seg1_adj,
                    boundaries_seg2_adj,
                    spec1_ion, spec2_ion,
                    spec1_ele, spec2_ele,
                    energy_edges,
                    main_folder,
                    idx
                )
                print(f"   ✅ Gráfico del ciclo {idx} generado correctamente")
            except Exception as e:
                print(f"   ❌ Error generando gráfico del ciclo {idx}: {e}")

            # ✅ 8) GENERAR GRÁFICO POLAR
            try:
                plot_polar_cycle(
                    seg1_original_data,
                    seg2_original_data,
                    boundaries_seg1_adj,
                    boundaries_seg2_adj,
                    spec1_ion, spec2_ion,
                    spec1_ele, spec2_ele,
                    energy_edges,
                    main_folder,
                    idx
                )
                print(f"   ✅ Gráfico POLAR del ciclo {idx} generado correctamente")
            except Exception as e:
                print(f"   ❌ Error generando gráfico POLAR del ciclo {idx}: {e}")
            
            print(f"   ✅ Ciclo {idx} procesado correctamente")
            
        except Exception as e:
            print(f"   ❌ ERROR PROCESANDO CICLO {idx}: {e}")
            continue
    
    print(f"🎉 Procesamiento completado: {len(pares_extremos)} ciclos")