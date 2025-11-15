#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from scipy import signal
from scipy.stats import pearsonr
from . import fronteras as fb

def detect_all_boundaries(segment_data, channel_energies, fronteras=None, hemisphere=None):
    """
    Detecta todas las fronteras de precipitación nocturna - CON MANEJO ROBUSTO DE ERRORES
    """
    # Si no se especifican fronteras, detectar todas
    if fronteras is None:
        fronteras = ['b1e', 'b1i', 'b2e', 'b2i', 'b3a', 'b3b', 'b4s', 'b5e', 'b5i', 'b6']
    
    boundaries = {}
    default_boundary = {'index': None, 'time': None, 'lat': None, 'deviation': 0}
    

    required_keys = {
        'b1e': ['ele_diff_flux'],
        'b1i': ['ion_diff_flux'], 
        'b2e': ['ele_avg_energy', 'ele_energy_flux'],
        'b2i': ['ion_energy_flux_b2i'], 
        'b3a': ['ele_diff_flux'],
        'b3b': ['ele_diff_flux'],
        'b4s': ['ele_diff_flux'],
        'b5e': ['ele_energy_flux', 'flux_ele'],
        'b5i': ['ion_energy_flux', 'flux_ion'],
        'b6': ['ele_energy_flux', 'ion_energy_flux']
    }
    
    print(f"🔍 Verificando datos en segmento:")
    print(f"   Claves disponibles: {list(segment_data.keys())}")
    
    # Función auxiliar para extraer índice de un resultado
    def get_index(boundary_result):
        if boundary_result and boundary_result['index'] is not None:
            return boundary_result['index']
        return None
    
    # Función para verificar datos requeridos
    def check_required_data(frontera):
        if frontera in required_keys:
            for key in required_keys[frontera]:
                if key not in segment_data:
                    print(f"   ❌ {frontera}: Falta clave '{key}'")
                    return False
                data = segment_data[key]
                if data is None or len(data) == 0 or np.all(np.isnan(data)):
                    print(f"   ❌ {frontera}: Datos inválidos en '{key}'")
                    return False
        return True
    
    # Detectar cada frontera solicitada CON MANEJO DE EXCEPCIONES
    for frontera in fronteras:
        try:
            if frontera == 'b1e' and check_required_data('b1e'):
                result = fb.detect_b1e(segment_data, channel_energies)
                boundaries['b1e'] = result if result is not None else default_boundary
            
            elif frontera == 'b1i' and check_required_data('b1i'):
                result = fb.detect_b1i(segment_data, channel_energies)
                boundaries['b1i'] = result if result is not None else default_boundary
            
            elif frontera == 'b2e' and check_required_data('b2e'):
                b1e_index = get_index(boundaries.get('b1e'))
                result = fb.detect_b2e(segment_data, b1e_index)
                boundaries['b2e'] = result if result is not None else default_boundary
            
            elif frontera == 'b2i' and check_required_data('b2i'):
                result = fb.detect_b2i(segment_data, channel_energies)
                boundaries['b2i'] = result if result is not None else default_boundary
            
            elif frontera in ['b3a', 'b3b'] and check_required_data('b3a'):
                result = fb.detect_b3(segment_data, channel_energies)
                if result is not None:
                    boundaries['b3a'] = result.get('b3a', default_boundary)
                    boundaries['b3b'] = result.get('b3b', default_boundary)
                else:
                    boundaries['b3a'] = default_boundary
                    boundaries['b3b'] = default_boundary
            
            elif frontera == 'b4s' and check_required_data('b4s'):
                b2e_index = get_index(boundaries.get('b2e'))
                b2i_index = get_index(boundaries.get('b2i'))
                result = fb.detect_b4s(segment_data, b2e_index, b2i_index)
                boundaries['b4s'] = result if result is not None else default_boundary
            
            elif frontera == 'b5e' and check_required_data('b5e'):
                result = fb.detect_b5(segment_data, particle_type='electron')
                boundaries['b5e'] = result if result is not None else default_boundary
            
            elif frontera == 'b5i' and check_required_data('b5i'):
                result = fb.detect_b5(segment_data, particle_type='ion')
                boundaries['b5i'] = result if result is not None else default_boundary
            
            elif frontera == 'b6' and check_required_data('b6'):
                b5e_index = get_index(boundaries.get('b5e'))
                result = fb.detect_b6(segment_data, b5e_index)
                boundaries['b6'] = result if result is not None else default_boundary
            
            else:
                boundaries[frontera] = default_boundary
                
        except Exception as e:
            print(f"   ⚠️  Error detectando {frontera}: {e}")
            boundaries[frontera] = default_boundary
    
    # Resumen de fronteras detectadas
    detected = [f for f, b in boundaries.items() if b['index'] is not None]
    print(f"   ✅ Fronteras detectadas: {detected}")
    
    return boundaries