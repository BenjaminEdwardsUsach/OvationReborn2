import numpy as np

def calcular_min_tolerable(segment_flux, factor=0.1):
    """
    Calcula un umbral mínimo tolerable a partir de un segmento de flujo.
    """
    segment_flux = np.array(segment_flux)
    background = np.percentile(segment_flux, 85)
    peak = np.percentile(segment_flux, 90)
    umbral = background + factor * (peak - background)
    print(f"Background: {background:.3f}, Peak: {peak:.3f}, Threshold: {umbral:.3f}")
    return umbral
