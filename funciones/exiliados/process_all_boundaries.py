def process_all_boundaries(segment, energy_channels):
    """
    Procesa todas las fronteras en orden
    """
    results = {}
    
    # Detectar fronteras en orden de dependencia
    results['b1e'] = detect_b1e(segment, energy_channels)
    results['b1i'] = detect_b1e(segment, energy_channels, particle='ion')
    
    results['b2e'] = detect_b2e(segment, results['b1e'])
    results['b2i'] = detect_b2i(segment, energy_channels)
    
    results['b3a'], results['b3b'] = detect_b3(segment, energy_channels)
    
    results['b4s'] = detect_b4s(segment, results['b2e'], results['b2i'])
    
    results['b5e'] = detect_b5(segment, 'electron')
    results['b5i'] = detect_b5(segment, 'ion')
    
    results['b6'] = detect_b6(segment, results['b5e'])
    
    return results