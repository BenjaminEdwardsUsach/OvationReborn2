def is_polar_rain(segment_data, index):
    """
    Determina si el espectro en el índice dado corresponde a lluvia polar
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        index (int): Índice a verificar
    
    Returns:
        bool: True si es lluvia polar, False en caso contrario
    """
    # La lluvia polar tiene electrones no estructurados y sin iones
    ele_flux = segment_data['flux_ele'][index]
    ion_flux = segment_data['flux_ion'][index]
    
    # Verificar flujos bajos de iones y electrones no estructurados
    if ion_flux < 9.0 and ele_flux < 10.0:
        # Verificar estructura (usando correlación)
        ele_diff_flux = segment_data['ele_diff_flux']
        if index > 0 and index < len(ele_diff_flux) - 1:
            r, _ = pearsonr(ele_diff_flux[index], ele_diff_flux[index-1])
            if r > 0.6:  # Alta correlación = no estructurado
                return True
    
    return False