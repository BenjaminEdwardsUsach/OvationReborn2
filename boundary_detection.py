#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
from scipy import signal
from scipy.stats import pearsonr
from . import fronteras as fb

def detect_all_boundaries(segment_data, channel_energies, fronteras=None):
    """
    Detecta todas las fronteras de precipitación nocturna según Newell et al. (1996)
    
    Args:
        segment_data (dict): Diccionario con datos del segmento
        channel_energies (array): Energías de los canales
        fronteras (list): Lista de fronteras a detectar. Si es None, detecta todas.
    
    Returns:
        dict: Diccionario con todas las fronteras detectadas
    """
    # Si no se especifican fronteras, detectar todas
    if fronteras is None:
        fronteras = ['b1e', 'b1i', 'b2e', 'b2i', 'b3a', 'b3b', 'b4s', 'b5e', 'b5i', 'b6']
    
    boundaries = {}
    default_boundary = {'index': None, 'time': None, 'lat': None}
    
    # Detectar cada frontera solicitada
    if 'b1e' in fronteras:
        result = fb.detect_b1e(segment_data, channel_energies)
        boundaries['b1e'] = result if result is not None else default_boundary
    
    if 'b1i' in fronteras:
        result = fb.detect_b1i(segment_data, channel_energies)
        boundaries['b1i'] = result if result is not None else default_boundary
    
    if 'b2e' in fronteras:
        result = fb.detect_b2e(segment_data, boundaries.get('b1e', None))
        boundaries['b2e'] = result if result is not None else default_boundary
    
    if 'b2i' in fronteras:
        result = fb.detect_b2i(segment_data)
        boundaries['b2i'] = result if result is not None else default_boundary
    
    if 'b3a' in fronteras:
        result = fb.detect_b3a(segment_data, channel_energies)
        boundaries['b3a'] = result if result is not None else default_boundary
    
    if 'b3b' in fronteras:
        result = fb.detect_b3b(segment_data, channel_energies)
        boundaries['b3b'] = result if result is not None else default_boundary
    
    if 'b4s' in fronteras:
        result = fb.detect_b4s(segment_data, boundaries.get('b2e', None), boundaries.get('b2i', None))
        boundaries['b4s'] = result if result is not None else default_boundary
    
    if 'b5e' in fronteras:
        result = fb.detect_b5e(segment_data)
        boundaries['b5e'] = result if result is not None else default_boundary
    
    if 'b5i' in fronteras:
        result = fb.detect_b5i(segment_data)
        boundaries['b5i'] = result if result is not None else default_boundary
    
    if 'b6' in fronteras:
        result = fb.detect_b6(segment_data, boundaries.get('b5e', None), boundaries.get('b5i', None))
        boundaries['b6'] = result if result is not None else default_boundary
    
    return boundaries
