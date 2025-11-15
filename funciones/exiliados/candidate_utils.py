import numpy as np
from .clean_local_outliers import clean_local_outliers
from .detectar_b2i_sliding_vec import detectar_b2i_sliding_vec

def detect_b2i_candidate(segment, threshold_percentile=85, **kwargs):
    """
    Para un segmento con keys 'flux' y 'time':
      - limpia outliers
      - calcula umbral en percentil
      - selecciona índices sobre umbral
      - detecta candidato b2i con sliding window
    Retorna dict con:
      't_candidate', 'flux_candidate', 'flux_recorted', 'time_recorted'
    """
    flux = np.array(segment['flux'])
    times = segment['time']
    if len(flux) < 2:
        return {
            't_candidate': times[0],
            'flux_candidate': float(flux[0]),
            'flux_recorted': flux,
            'time_recorted': times
        }

    cleaned = clean_local_outliers(flux)
    umbral = np.percentile(cleaned, threshold_percentile)
    idxs = np.where(flux >= umbral)[0]
    if idxs.size == 0:
        idxs = np.arange(len(flux))

    rec_flux = flux[idxs]
    rec_time = [times[i] for i in idxs]

    raw_idx = detectar_b2i_sliding_vec(rec_flux, **kwargs)
    if raw_idx is None:
        raw_idx = 0
    local_idx = idxs[raw_idx]

    return {
        't_candidate': rec_time[raw_idx],
        'flux_candidate': float(flux[local_idx]),
        'flux_recorted': rec_flux,
        'time_recorted': rec_time
    }
