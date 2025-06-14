import os
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator

from .clean_local_outliers import clean_local_outliers
from .detectar_b2i_sliding_vec import detectar_b2i_sliding_vec
from .compute_time_edges import compute_time_edges
from .compute_energy_edges import compute_energy_edges
from .convert_to_serializable import convert_to_serializable

def procesar_ciclos(pares_extremos, tiempo_final, tiempo_final_dict, SC_AACGM_LAT, SC_GEOCENTRIC_LAT, flujos_iones_filtrado, ION_DIFF_ENERGY_FLUX_filtrado, CHANNEL_ENERGIES, main_folder):
    """
    Procesa cada ciclo válido, detecta candidatos b2i y genera gráficas y archivos de información.
    """
    info_pasadas = []
    contador = 0
    delta_t = tiempo_final[1] - tiempo_final[0]
    print(delta_t)

    for par in pares_extremos:
        idx_start = tiempo_final_dict[par[0][0]]
        idx_end = tiempo_final_dict[par[1][0]]

        segmento_flux = flujos_iones_filtrado[idx_start: idx_end + 1]
        segmento_time = tiempo_final[idx_start: idx_end + 1]

        coords_SC_AACGM = [SC_AACGM_LAT[tiempo_final_dict[t]] for t in segmento_time]
        coords_SC_GEOCENTRIC = [SC_GEOCENTRIC_LAT[tiempo_final_dict[t]] for t in segmento_time]

        max_lat_index = max(range(len(coords_SC_GEOCENTRIC)), key=lambda i: abs(coords_SC_GEOCENTRIC[i]))
        if max_lat_index == 0:
            segmento_flux_1 = segmento_flux.copy()
            segmento_time_1 = segmento_time.copy()
            segmento_flux_2 = segmento_flux.copy()
            segmento_time_2 = segmento_time
            coords_first = coords_SC_AACGM
            coords_geo_first = coords_SC_GEOCENTRIC
            coords_second = coords_SC_AACGM
            coords_geo_second = coords_SC_GEOCENTRIC
        else:
            segmento_flux_1 = segmento_flux[:max_lat_index]
            segmento_time_1 = segmento_time[:max_lat_index]
            segmento_flux_2 = segmento_flux[max_lat_index:][::-1]
            segmento_time_2 = segmento_time[max_lat_index:]
            coords_first = coords_SC_AACGM[:max_lat_index]
            coords_geo_first = coords_SC_GEOCENTRIC[:max_lat_index]
            coords_second = coords_SC_AACGM[max_lat_index:]
            coords_geo_second = coords_SC_GEOCENTRIC[max_lat_index:]

        if len(segmento_flux_1) < 2:
            candidate_index_recorte = 0
            t_candidate_1 = segmento_time_1[0]
            flux_candidate_1 = segmento_flux_1[0]
            flujo_recortado_1 = segmento_flux_1
            tiempo_recortado_1 = segmento_time_1
        else:
            segmento_flux_cleaned_1 = clean_local_outliers(segmento_flux_1, threshold=3)
            umbral_recorte_1 = np.percentile(segmento_flux_cleaned_1, 85)
            idx_recorte_1 = np.where(segmento_flux_1 >= umbral_recorte_1)[0]
            if idx_recorte_1.size == 0:
                idx_recorte_1 = np.arange(len(segmento_flux_1))
            flujo_recortado_1 = segmento_flux_1[idx_recorte_1]
            tiempo_recortado_1 = segmento_time_1[idx_recorte_1]
            candidate_index_recorte = detectar_b2i_sliding_vec(flujo_recortado_1, window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5)
            if candidate_index_recorte is None:
                candidate_index_recorte = 0
            candidate_local_1 = idx_recorte_1[candidate_index_recorte]
            t_candidate_1 = segmento_time_1[candidate_local_1]
            flux_candidate_1 = segmento_flux_1[candidate_local_1]

        # Segunda mitad
        if len(segmento_flux_2) < 2:
            candidate_index_recorte_2 = 0
            t_candidate_2 = segmento_time_2[0]
            flux_candidate_2 = segmento_flux_2[0]
            flujo_recortado_2 = segmento_flux_2
            tiempo_recortado_2 = segmento_time_2
        else:
            segmento_flux_cleaned_2 = clean_local_outliers(segmento_flux_2, threshold=3)
            umbral_recorte_2 = np.percentile(segmento_flux_cleaned_2, 85)
            idx_recorte_2 = np.where(segmento_flux_2 >= umbral_recorte_2)[0]
            if idx_recorte_2.size == 0:
                idx_recorte_2 = np.arange(len(segmento_flux_2))
            flujo_recortado_2 = segmento_flux_2[idx_recorte_2]
            tiempo_recortado_2 = segmento_time_2[idx_recorte_2]

            candidate_index_recorte_2 = detectar_b2i_sliding_vec(flujo_recortado_2, window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5)
            if candidate_index_recorte_2 is None:
                candidate_index_recorte_2 = 0
            t_candidate_2 = tiempo_recortado_2[candidate_index_recorte_2]
            flux_candidate_2 = flujo_recortado_2[candidate_index_recorte_2]

        info_pasada = {
            "b2i_candidate": {
                "primera_mitad": {
                    "candidate_time": str(t_candidate_1),
                    "candidate_flux": flux_candidate_1,
                    "recortado_time": [str(tiempo_recortado_1[0]), str(tiempo_recortado_1[-1])],
                    "coordinates": {
                        "SC_AACGM": (coords_first[0], coords_first[-1]),
                        "SC_GEOCENTRIC": (coords_geo_first[0], coords_geo_first[-1])
                    }
                },
                "segunda_mitad": {
                    "candidate_time": str(t_candidate_2),
                    "candidate_flux": flux_candidate_2,
                    "recortado_time": [str(tiempo_recortado_2[0]), str(tiempo_recortado_2[-1])],
                    "coordinates": {
                        "SC_AACGM": (coords_second[0], coords_second[-1]),
                        "SC_GEOCENTRIC": (coords_geo_second[0], coords_geo_second[-1])
                    }
                }
            }
        }

        cycle_folder = os.path.join(main_folder, f"cycle_{contador}")
        if not os.path.exists(cycle_folder):
            os.makedirs(cycle_folder)

        info_filename = os.path.join(cycle_folder, f"info_{contador}.txt")
        with open(info_filename, 'w') as file:
            file.write(json.dumps(info_pasada, indent=4, default=convert_to_serializable))

        if max_lat_index == 0:
            indices_first = range(idx_start, idx_end + 1)
            indices_second = indices_first
        else:
            indices_first = range(idx_start, idx_start + max_lat_index)
            indices_second = range(idx_start + max_lat_index, idx_end + 1)

        time_segment_first = [tiempo_final[i] for i in indices_first]
        data_ion_first = ION_DIFF_ENERGY_FLUX_filtrado[indices_first, :].T
        time_edges_first = compute_time_edges(time_segment_first)
        flux_segment_first = segmento_flux_1

        time_segment_second = [tiempo_final[i] for i in indices_second]
        data_ion_second = ION_DIFF_ENERGY_FLUX_filtrado[indices_second, :].T
        data_ion_second_invertido = data_ion_second[:, ::-1]
        time_edges_second = compute_time_edges(time_segment_second)
        flux_segment_second = segmento_flux_2

        date_format = mdates.DateFormatter('%H:%M:%S')
        energy_edges = compute_energy_edges(CHANNEL_ENERGIES)

        fig, axs = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
        ax_spec_left = axs[0, 0]
        ax_flux_left = axs[1, 0]
        ax_spec_right = axs[0, 1]
        ax_flux_right = axs[1, 1]

        X_left, Y_left = np.meshgrid(time_edges_first, energy_edges)
        c1 = ax_spec_left.pcolormesh(X_left, Y_left, data_ion_first,
                                     norm=plt.matplotlib.colors.LogNorm(), shading='auto')
        ax_spec_left.set_yscale('log')
        ax_spec_left.set_title("Spectrogram - ION_DIFF_ENERGY_FLUX (Primera mitad)")
        ax_spec_left.set_ylabel("Energy (eV)")
        ax_spec_left.xaxis_date()
        ax_spec_left.xaxis.set_major_formatter(date_format)
        fig.colorbar(c1, ax=ax_spec_left, label="Flux (arb. units)")

        ax_flux_left.scatter(time_segment_first, flux_segment_first, label="Integrated Flux (ION_DIFF)")
        ax_flux_left.set_ylabel("Integrated Flux (eV)")
        ax_flux_left.set_title(f"Cycle {contador}: ION_DIFF (Primera mitad)\nCandidate: {t_candidate_1}, Flux: {flux_candidate_1:.3f}")
        ax_flux_left.axvline(t_candidate_1, color='red', linestyle='--', label=f"Candidate: {t_candidate_1}")
        ax_flux_left.legend()
        ax_flux_left.grid(True)
        ax_flux_left.xaxis_date()
        ax_flux_left.xaxis.set_major_formatter(date_format)

        tick_locs_left = ax_flux_left.get_xticks()
        seg_time_num_left = mdates.date2num(time_segment_first)
        new_labels_left = []
        for i, loc in enumerate(tick_locs_left):
            dt_tick = mdates.num2date(loc)
            idx = min(range(len(seg_time_num_left)), key=lambda j: abs(seg_time_num_left[j] - loc))
            if i == 0:
                label = dt_tick.strftime('UT: %H:%M:%S') + "\nAACGM: {:.1f}, \nGEO: {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
            else:
                label = dt_tick.strftime('%H:%M:%S') + "\n {:.1f}, \n {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
            new_labels_left.append(label)
        ax_flux_left.xaxis.set_major_locator(FixedLocator(tick_locs_left))
        ax_flux_left.set_xticklabels(new_labels_left, rotation=0, ha='center')

        X_right, Y_right = np.meshgrid(time_edges_second, energy_edges)
        c2 = ax_spec_right.pcolormesh(X_right, Y_right, data_ion_second_invertido,
                                      norm=plt.matplotlib.colors.LogNorm(), shading='auto')
        ax_spec_right.set_yscale('log')
        ax_spec_right.set_title("Spectrogram - ION_DIFF_ENERGY_FLUX (Segunda mitad, invertida)")
        ax_spec_right.set_ylabel("Energy (eV)")
        ax_spec_right.xaxis_date()
        ax_spec_right.xaxis.set_major_formatter(date_format)
        fig.colorbar(c2, ax=ax_spec_right, label="Flux (arb. units)")

        ax_flux_right.plot(time_segment_second, flux_segment_second, 'b-', label="Integrated Flux (ION_DIFF)")
        ax_flux_right.set_ylabel("Integrated Flux (eV)")
        ax_flux_right.set_title(f"Cycle {contador}: ION_DIFF (Segunda mitad, invertida)\nCandidate: {t_candidate_2}, Flux: {flux_candidate_2:.3f}")
        ax_flux_right.axvline(t_candidate_2, color='red', linestyle='--', label=f"Candidate: {t_candidate_2}")
        ax_flux_right.legend()
        ax_flux_right.grid(True)
        ax_flux_right.xaxis_date()
        ax_flux_right.xaxis.set_major_formatter(date_format)

        tick_locs_right = ax_flux_right.get_xticks()
        seg_time_num_right = mdates.date2num(time_segment_second)
        new_labels_right = []
        for i, loc in enumerate(tick_locs_right):
            dt_tick = mdates.num2date(loc)
            idx = min(range(len(seg_time_num_right)), key=lambda j: abs(seg_time_num_right[j] - loc))
            if i == 0:
                label = dt_tick.strftime('UT: %H:%M:%S') + "\nAACGM: {:.1f}, \nGEO: {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
            else:
                label = dt_tick.strftime('%H:%M:%S') + "\n {:.1f}, \n {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
            new_labels_right.append(label)
        ax_flux_right.xaxis.set_major_locator(FixedLocator(tick_locs_right))
        ax_flux_right.set_xticklabels(new_labels_right, rotation=0, ha='center')

        image_filename = os.path.join(main_folder, f"cycle{contador}.png")
        plt.savefig(image_filename, format='png')
        plt.close(fig)

        contador += 1
