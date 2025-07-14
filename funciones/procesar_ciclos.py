import numpy as np
from .segment_utils import split_cycle_segment
from .io_utils import save_cycle_info
from .plot_utils import plot_cycle
from .boundary_detection import detect_all_boundaries

def procesar_ciclos(pares_extremos, tiempo_final, tiempo_final_dict, sc_lat, sc_geo,
                    flujos_iones, flujos_elec, ele_total_energy, ele_diff_flux,
                    ele_avg_energy, ion_diff_filtrado, channel_energies, energy_edges, 
                    main_folder, fronteras=None):
    """
    Procesamiento completo de ciclos con todas las fronteras
    """
    # Convertir datos a arrays NumPy para eficiencia
    flujos_iones = np.asarray(flujos_iones)
    flujos_elec = np.asarray(flujos_elec)
    ion_diff_filtrado = np.asarray(ion_diff_filtrado)
    ele_diff_flux = np.asarray(ele_diff_flux)
    ele_avg_energy = np.asarray(ele_avg_energy)
    
    for idx, par in enumerate(pares_extremos):
        # 1) Segmentación
        segments = split_cycle_segment(
            par, tiempo_final, tiempo_final_dict,
            flujos_iones, sc_lat, sc_geo
        )
        
        # 2) Preparar datos para detección de fronteras
        seg1_data = {
            'time': segments['seg1']['time'],
            'coords_aacgm': segments['seg1']['coords_aacgm'],   # <-- añadido
            'lat': segments['seg1']['coords_aacgm'],            # puedes mantener lat también
            'ele_diff_flux': ele_diff_flux[segments['seg1']['indices']],
            'ion_diff_flux': ion_diff_filtrado[segments['seg1']['indices']],
            'ion_energy_flux': flujos_iones[segments['seg1']['indices']],  # <-- añadido
            'flux_ion': flujos_iones[segments['seg1']['indices']],
            'ele_energy_flux': ele_total_energy[segments['seg1']['indices']],
            'flux_ele': flujos_elec[segments['seg1']['indices']],
            'ele_avg_energy': ele_avg_energy[segments['seg1']['indices']]
        }
        
        seg2_data = {
            'time': segments['seg2']['time'],
            'coords_aacgm': segments['seg2']['coords_aacgm'],   # <-- añadido
            'lat': segments['seg2']['coords_aacgm'],
            'ele_diff_flux': ele_diff_flux[segments['seg2']['indices']],
            'ion_diff_flux': ion_diff_filtrado[segments['seg2']['indices']],
            'ion_energy_flux': flujos_iones[segments['seg2']['indices']],  # <-- añadido
            'flux_ion': flujos_iones[segments['seg2']['indices']],
            'ele_energy_flux': ele_total_energy[segments['seg2']['indices']],
            'flux_ele': flujos_elec[segments['seg2']['indices']],
            'ele_avg_energy': ele_avg_energy[segments['seg2']['indices']]
        }
        
        # 3) Detectar todas las fronteras
        boundaries_seg1 = detect_all_boundaries(seg1_data, channel_energies,fronteras=fronteras)
        boundaries_seg2 = detect_all_boundaries(seg2_data, channel_energies, fronteras=fronteras)
        
        # 4) Guardar información
        info = {
            'boundaries': {
                'primera_mitad': boundaries_seg1,
                'segunda_mitad': boundaries_seg2
            }
        }
        save_cycle_info(info, main_folder, idx)
        
        # 5) Preparar espectrogramas
        spec1_ion = ion_diff_filtrado[segments['seg1']['indices'], :].T
        spec2_ion = ion_diff_filtrado[segments['seg2']['indices'], :].T
        spec1_ele = ele_diff_flux[segments['seg1']['indices'], :].T
        spec2_ele = ele_diff_flux[segments['seg2']['indices'], :].T
        


        # 6) Generar gráfico con todas las fronteras
        plot_cycle(
            seg1_data,                # <-- aquí usar seg1_data, no segments['seg1']
            seg2_data,                # <-- aquí usar seg2_data
            boundaries_seg1,
            boundaries_seg2,
            spec1_ion, spec2_ion,
            spec1_ele, spec2_ele,
            energy_edges,
            main_folder,
            idx
        )
