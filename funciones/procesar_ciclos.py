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
    
    # Convertir datos a arrays NumPy
    flujos_iones_log = np.asarray(flujos_iones_log)
    flujos_elec_log = np.asarray(flujos_elec_log)
    flujos_iones_b2i_log = np.asarray(flujos_iones_b2i_log)
    ion_diff_filtrado = np.asarray(ion_diff_filtrado)
    ele_diff_flux = np.asarray(ele_diff_flux)
    ele_avg_energy = np.asarray(ele_avg_energy)

    # Crear diccionario con datos globales para pasar a las funciones
    global_data = {
        'ele_diff_flux': ele_diff_flux,
        'ion_diff_flux': ion_diff_filtrado,
        'flux_ion': flujos_iones_log,
        'flux_ele': flujos_elec_log,
        'ion_energy_flux_b2i': flujos_iones_b2i_log,
        'ele_energy_flux': flujos_elec_log,  # Usar mismo que flux_ele por ahora
        'ion_energy_flux': flujos_iones_log,  # Usar mismo que flux_ion por ahora
        'ele_avg_energy': ele_avg_energy
    }
    
    for idx, par in enumerate(pares_extremos):
        try:
            # 1) Segmentación 
            segments = split_cycle_segment(
                par, tiempo_final, tiempo_final_dict,
                flujos_iones_log, sc_lat, sc_geo  
            )
            
            seg1_orig_len = len(segments['seg1_original']['time'])
            seg2_orig_len = len(segments['seg2_original']['time'])
            direccion_original = segments.get('direccion_original', 'desconocida')
            
            # Verificar si hay datos para procesar
            if seg1_orig_len == 0 and seg2_orig_len == 0:
                continue

            def prepare_segment_data(segment, segment_type, global_data):
                """Prepara datos para un segmento - VERSIÓN COMPLETA CORREGIDA"""
                indices = segment['indices']
                
                if len(indices) == 0:
                    return create_empty_segment_data(segment_type)
                
                # Extraer datos del segmento usando los índices
                segment_data = {
                    'time': segment['time'],
                    'coords_aacgm': segment['coords_aacgm'],
                    'lat': segment['coords_geo'],
                    'indices': indices,
                    'direccion': segment.get('direccion_procesamiento', 'desconocida'),
                    'segment_type': segment_type
                }
                
                # Añadir datos de flujos desde los arrays globales
                if len(indices) > 0:
                    try:
                        # Usar los índices para extraer datos correspondientes
                        valid_indices = indices[indices < len(global_data['flux_ion'])]
                        
                        segment_data.update({
                            'ele_diff_flux': global_data['ele_diff_flux'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'ion_diff_flux': global_data['ion_diff_flux'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'flux_ion': global_data['flux_ion'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'flux_ele': global_data['flux_ele'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'ion_energy_flux_b2i': global_data['ion_energy_flux_b2i'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'ele_energy_flux': global_data['ele_energy_flux'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'ion_energy_flux': global_data['ion_energy_flux'][valid_indices] if len(valid_indices) > 0 else np.array([]),
                            'ele_avg_energy': global_data['ele_avg_energy'][valid_indices] if len(valid_indices) > 0 else np.array([])
                        })
                    except Exception as e:
                        print(f"Error preparando datos del segmento {segment_type}: {e}")
                        return create_empty_segment_data(segment_type)
                
                return segment_data

            def create_empty_segment_data(segment_type):
                """Crea estructura de datos vacía"""
                return {
                    'time': np.array([]),
                    'coords_aacgm': np.array([]),
                    'lat': np.array([]),
                    'ele_diff_flux': np.array([]),
                    'ion_diff_flux': np.array([]),
                    'ion_energy_flux': np.array([]),
                    'ion_energy_flux_b2i': np.array([]),  
                    'flux_ion': np.array([]),
                    'ele_energy_flux': np.array([]),
                    'flux_ele': np.array([]),
                    'ele_avg_energy': np.array([]),
                    'energy_edges': energy_edges,
                    'direccion': "desconocida",
                    'segment_type': segment_type
                }

            # Preparar segmentos CON el parámetro global_data
            seg1_processing_data = prepare_segment_data(segments['seg1_processing'], 'seg1', global_data)
            seg2_processing_data = prepare_segment_data(segments['seg2_processing'], 'seg2', global_data)
            seg1_original_data = prepare_segment_data(segments['seg1_original'], 'seg1', global_data)
            seg2_original_data = prepare_segment_data(segments['seg2_original'], 'seg2', global_data)

            # 3) Detectar fronteras 
            boundaries_seg1 = {}
            boundaries_seg2 = {}
            
            try:
                if len(seg1_processing_data['time']) > 0:
                    boundaries_seg1 = detect_all_boundaries(seg1_processing_data, channel_energies, fronteras=fronteras)
            except Exception as e:
                print(f"Error detectando fronteras en segmento 1 del ciclo {idx}: {e}")
                boundaries_seg1 = {}
                
            try:
                if len(seg2_processing_data['time']) > 0:
                    boundaries_seg2 = detect_all_boundaries(seg2_processing_data, channel_energies, fronteras=fronteras)
            except Exception as e:
                print(f"Error detectando fronteras en segmento 2 del ciclo {idx}: {e}")
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
                            print(f"Error ajustando índice para {b_name}: {e}")
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
                    'seg1_processing_direction': seg1_processing_data.get('direccion', 'desconocida'),
                    'seg2_processing_direction': seg2_processing_data.get('direccion', 'desconocida'),
                    'seg1_original_direction': seg1_original_data.get('direccion', 'desconocida'),
                    'seg2_original_direction': seg2_original_data.get('direccion', 'desconocida')
                }
            }
            save_cycle_info(info, main_folder, idx)
            
            # 6) Preparar espectrogramas (usando datos originales para visualización)
            def prepare_spectrograms(segment):
                """Prepara espectrogramas asegurando dimensiones compatibles"""
                if len(segment['indices']) > 0:
                    try:
                        # Obtener datos usando índices válidos
                        valid_indices = segment['indices']
                        valid_indices = valid_indices[valid_indices < ion_diff_filtrado.shape[0]]
                        valid_indices = valid_indices[valid_indices < ele_diff_flux.shape[0]]
                        
                        if len(valid_indices) == 0:
                            return np.array([]), np.array([])
                            
                        spec_ion = ion_diff_filtrado[valid_indices, :].T
                        spec_ele = ele_diff_flux[valid_indices, :].T
                        
                        # Asegurar que no hay NaN
                        spec_ion = np.nan_to_num(spec_ion, nan=1e-10)
                        spec_ele = np.nan_to_num(spec_ele, nan=1e-10)
                        
                        return spec_ion, spec_ele
                        
                    except Exception as e:
                        print(f"Error preparando espectrogramas: {e}")
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
            except Exception as e:
                print(f"Error generando gráfico normal del ciclo {idx}: {e}")

            # GENERAR GRÁFICO POLAR
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

            except Exception as e:
                print(f"Error generando gráfico POLAR del ciclo {idx}: {e}")
            
        except Exception as e:
            print(f"Error procesando ciclo {idx}: {e}")
            continue