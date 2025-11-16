import numpy as np

def integrar_flujo_diferencial(diff_flux, delta, canal1=0, canal2=6):
    """
    Integra el flujo diferencial sobre energía 
    """
    flujos_integrados = []

    # Verificar que diff_flux no sea todo NaN
    if np.all(np.isnan(diff_flux)):
        return np.zeros(diff_flux.shape[0])
    
    # Contador de valores negativos
    total_negativos = 0
    
    for i, elem in enumerate(diff_flux):
        # PROTECCIÓN CONTRA VALORES NEGATIVOS Y NaN
        elem_clean = np.nan_to_num(elem, nan=0.0)
        
        # Detectar y contar valores negativos
        if np.any(elem_clean < 0):
            neg_count = np.sum(elem_clean < 0)
            total_negativos += neg_count
        
        # Forzar valores positivos para integración
        elem_positivo = np.maximum(elem_clean, 0)
        
        # Seleccionar canales y multiplicar por delta
        selected_flux = elem_positivo[canal1:canal2]
        selected_delta = delta[canal1:canal2]
        
        # Verificar que no hay NaN en la selección
        if np.any(np.isnan(selected_flux)) or np.any(np.isnan(selected_delta)):
            selected_flux = np.nan_to_num(selected_flux, nan=0.0)
            selected_delta = np.nan_to_num(selected_delta, nan=0.0)
        
        flux_value = np.sum(selected_flux * selected_delta)
        flujos_integrados.append(flux_value)
    
    resultado = np.array(flujos_integrados)
    
    # Reemplazar cualquier NaN residual
    resultado = np.nan_to_num(resultado, nan=1e-10)
    resultado = np.maximum(resultado, 1e-10)
    
    return resultado