from .funciones_auxiliares.has_monoenergetic_peak import has_monoenergetic_peak

def detect_b3a(segment_data, channel_energies):
    """
    Detecta la frontera b3a (evento de aceleración de electrones más ecuatorial)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        channel_energies (array): Energías de los canales
    
    Returns:
        dict: Diccionario con 'index', 'time' y 'lat' o valores None si no se detecta
    """
    ele_diff_flux = segment_data['ele_diff_flux']
    n = ele_diff_flux.shape[0]
    
    # Buscar desde el inicio hacia el polo
    for i in range(n):
        if has_monoenergetic_peak(ele_diff_flux[i], channel_energies):
            return {
                'index': i,
                'time': segment_data['time'][i],
                'lat': segment_data['lat'][i]
            }
    
    return {'index': None, 'time': None, 'lat': None}