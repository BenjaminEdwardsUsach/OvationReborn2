#%%  
import numpy as np
from .segment_utils import split_cycle_segment
from .candidate_utils import detect_b2i_candidate
from .io_utils import save_cycle_info
from .plot_utils import plot_cycle

def procesar_ciclos(pares_extremos, tiempo_final, tiempo_final_dict,
                    sc_lat, sc_geo,
                    flujos_filtrado, ion_diff_filtrado,
                    energy_edges, main_folder):
    """
    Orquesta el procesamiento de cada ciclo:
      1) Divide en segmentos
      2) Detecta candidatos B2I
      3) Guarda info JSON
      4) Genera y guarda plot con spectrogramas y flujos
    """
    for idx, par in enumerate(pares_extremos):
        # 1) Segmentación
        segments = split_cycle_segment(
            par, tiempo_final, tiempo_final_dict,
            flujos_filtrado, sc_lat, sc_geo
        )

        # 2) Detección de candidatos B2I
        cand1 = detect_b2i_candidate(
            segments['seg1'], window_avg=2, lookahead=10,
            sliding_window=3, min_flux=10.5
        )
        cand2 = detect_b2i_candidate(
            segments['seg2'], window_avg=2, lookahead=10,
            sliding_window=3, min_flux=10.5
        )

        # 3) Guardar información JSON
        info = {
            'b2i_candidate': {
                'primera_mitad': cand1,
                'segunda_mitad': cand2
            }
        }
        save_cycle_info(info, main_folder, idx)

        # 4) Preparar espectrogramas para cada mitad
        # split_cycle_segment debe proporcionar en segments['segX']['indices'] 
        # el array de índices temporales para cada mitad.
        spec1 = ion_diff_filtrado[segments['seg1']['indices'], :].T
        spec2 = ion_diff_filtrado[segments['seg2']['indices'], :].T

        # 5) Generar y guardar la figura
        plot_cycle(
            segments['seg1'],   # dict con 'time','flux','coords_aacgm','coords_geo'
            segments['seg2'],
            cand1,
            cand2,
            spec1,
            spec2,
            energy_edges,
            main_folder,
            idx
        )
