# unit_validation.py
import numpy as np

def validate_flux_units(segment, expected_scale='log10'):
    """
    Valida que los flujos estén en la escala correcta
    """
    warnings = []
    
    # Verificar electrones
    if 'ele_energy_flux' in segment:
        max_flux = np.max(segment['ele_energy_flux'])
        if expected_scale == 'log10' and max_flux > 100:  # Valores muy altos sugieren escala lineal
            warnings.append("ADVERTENCIA: ele_energy_flux parece estar en escala lineal, debería ser log10")
    
    # Verificar iones
    if 'ion_energy_flux' in segment:
        max_flux = np.max(segment['ion_energy_flux'])
        if expected_scale == 'log10' and max_flux > 100:
            warnings.append("ADVERTENCIA: ion_energy_flux parece estar en escala lineal, debería ser log10")
    
    return warnings

def convert_to_log10(flux_array):
    """
    Convierte flujos a escala log10 si es necesario
    """
    if np.max(flux_array) > 50:  # Probablemente está en escala lineal
        return np.log10(flux_array + 1e-10)
    return flux_array