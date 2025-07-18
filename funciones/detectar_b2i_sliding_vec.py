import numpy as np
from .moving_average import moving_average

def detectar_b2i_sliding_vec(flux, window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5):
    """
        Detecta el índice candidato para el límite b2i en una serie de flujos integrados.
    
        args:
        flux: array-like
            Flujo de energía diferencial integrado.
        window_avg: int
            Tamaño de la ventana para el promedio móvil inicial.
        lookahead: int
            Número de puntos a considerar para el cálculo del máximo deslizante.
        sliding_window: int
            Tamaño de la ventana para el promedio móvil deslizante.
        min_flux: float
            Valor mínimo de flujo para considerar un candidato válido.
    Returns:
        int or None
            Índice del candidato para el límite b2i, o None si no se encuentra un candidato válido.
    """
    valid_range = len(flux) - (lookahead + window_avg) + 1
    if valid_range < 1:
        return None


    candidate_avgs = moving_average(flux, n=window_avg)[:valid_range]
    max_sliding = np.zeros(valid_range)
    for i in range(valid_range):
        segment = flux[i + window_avg : i + window_avg + lookahead]
        sliding_avgs = moving_average(segment, n=sliding_window)
        max_sliding[i] = np.max(sliding_avgs)

    diff = candidate_avgs - max_sliding
    valid_candidates = np.where((candidate_avgs >= min_flux) & (diff > 0))[0]
    if len(valid_candidates) == 0:
        return None

    best_candidate = valid_candidates[np.argmax(diff[valid_candidates])]
    return best_candidate
