# detect_b2i.py - Frontera de isotropía de iones (b2i)
# Basado en Newell et al. (1996), "Morphology of nightside precipitation"
# Unidades: flujo energético en eV/cm²/ster/s (escala logarítmica)

import numpy as np
from scipy.ndimage import uniform_filter1d
from .funciones_auxiliares.thresholds import PAPER_THRESHOLDS
from .validators import validate_segment_data

def detect_b2i(segment, energy_channels):
    """
    Detecta la frontera b2i (ion isotropy boundary).
    
    La b2i marca el límite interior de la precipitación de iones,
    donde el flujo de iones de 3-30 keV alcanza un máximo pronunciado
    antes de disminuir hacia el polo.
    
    Parámetros
    ----------
    segment : dict
        Diccionario con datos del segmento. Debe contener:
        - 'ion_energy_flux_b2i' (recomendado): flujo integrado de iones 3-30 keV
          (calculado externamente con integrar_flujo_diferencial)
        - O bien 'ion_diff_flux': flujo diferencial para calcularlo sobre la marcha
        - 'time', 'lat'
    energy_channels : array
        Energías centrales de los canales [eV]
    
    Retorna
    -------
    dict
        Diccionario con 'index', 'time', 'lat', 'deviation' 
        o valores None si no se detecta.
    """
    thresholds = PAPER_THRESHOLDS['b2i']
    default = {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    
    # Validar datos mínimos
    required_keys = ['time', 'lat']
    valid, msg = validate_segment_data(segment, required_keys)
    if not valid:
        return default
    
    # 1. Obtener flujo de iones en banda 3-30 keV
    if 'ion_energy_flux_b2i' in segment and len(segment['ion_energy_flux_b2i']) > 0:
        # Usar valor preintegrado (más eficiente y consistente)
        partial_flux = np.asarray(segment['ion_energy_flux_b2i'], dtype=np.float64)
    elif 'ion_diff_flux' in segment and len(segment['ion_diff_flux']) > 0:
        # Calcular sobre la marcha (fallback)
        energy_mask = (energy_channels >= thresholds['min_energy']) & \
                      (energy_channels <= thresholds['max_energy'])
        if not np.any(energy_mask):
            return default
        partial_flux = np.sum(segment['ion_diff_flux'][:, energy_mask], axis=1)
    else:
        return default
    
    # 2. Limpiar valores inválidos
    partial_flux = np.nan_to_num(partial_flux, nan=0.0, posinf=0.0, neginf=0.0)
    if np.all(partial_flux <= 0):
        return default
    
    # 3. Escala logarítmica
    log_flux = np.log10(partial_flux + 1e-10)
    
    # 4. Suavizado de 2 segundos (como en el paper)
    smoothed_flux = uniform_filter1d(log_flux, size=thresholds['avg_window'])
    
    n = len(smoothed_flux)
    if n < thresholds['lookahead'] + 3:
        return default
    
    # 5. Buscar máximos locales (candidatos)
    candidates = []
    for i in range(2, n - thresholds['lookahead']):
        current = smoothed_flux[i]
        # Umbral mínimo de flujo (log10)
        if current < thresholds['min_flux']:
            continue
        # Verificar que sea máximo respecto a los siguientes 'lookahead' segundos
        future_max = np.max(smoothed_flux[i+1 : i+1+thresholds['lookahead']])
        if current >= future_max:
            candidates.append(i)
    
    # 6. Filtrar eventos tipo "nose" (ver paper, pág. 5)
    #    Un "nose event" es cuando hay un máximo mayor más hacia el polo.
    valid_candidates = []
    for idx, cand in enumerate(candidates):
        is_nose = False
        for later_cand in candidates[idx+1:]:
            if smoothed_flux[later_cand] > smoothed_flux[cand]:
                is_nose = True
                break
        if not is_nose:
            valid_candidates.append(cand)
    
    # 7. Seleccionar el candidato más ecuatorial (el primero en la lista)
    if valid_candidates:
        best = valid_candidates[0]
        return {
            'index': best,
            'time': segment['time'][best],
            'lat': segment['lat'][best],
            'deviation': 0,
            'params': {'flux_log': smoothed_flux[best]}
        }
    
    return default