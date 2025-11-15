import numpy as np

def integrar_flujo_diferencial(diff_flux, delta, canal1=0, canal2=6):
    """
    Integra correctamente el flujo diferencial sobre energía - CORREGIDO PARA ORDEN DESCENDENTE
    """
    # En orden DESCENDENTE, canal1 es más energético que canal2
    # Por ejemplo: canal1=0 (30000 eV), canal2=6 (3000 eV) cubre 30000-3000 eV
    
    flujos_integrados = []
    
    print(f"🔍 Diagnóstico integración (orden descendente):")
    print(f"   diff_flux shape: {diff_flux.shape}")
    print(f"   delta shape: {delta.shape}")
    print(f"   canales: {canal1} a {canal2} (energías más altas a más bajas)")
    
    # Verificar que diff_flux no sea todo NaN
    if np.all(np.isnan(diff_flux)):
        print("❌ ERROR: diff_flux es completamente NaN")
        return np.zeros(diff_flux.shape[0])
    
    # ✅ MEJORA: Contador de valores negativos
    total_negativos = 0
    
    for i, elem in enumerate(diff_flux):
        if i < 3:  # Solo mostrar diagnóstico para primeros puntos
            print(f"   Punto {i}: elem shape {elem.shape}, NaN: {np.sum(np.isnan(elem))}/{len(elem)}")
        
        # PROTECCIÓN CONTRA VALORES NEGATIVOS Y NaN
        elem_clean = np.nan_to_num(elem, nan=0.0)
        
        # ✅ MEJORA: Detectar y contar valores negativos
        if np.any(elem_clean < 0):
            neg_count = np.sum(elem_clean < 0)
            total_negativos += neg_count
            if i < 5:  # Solo mostrar para primeros puntos
                print(f"   ⚠️  Punto {i}: {neg_count} valores negativos")
        
        # Forzar valores positivos para integración
        elem_positivo = np.maximum(elem_clean, 0)
        
        # Seleccionar canales y multiplicar por delta
        selected_flux = elem_positivo[canal1:canal2]
        selected_delta = delta[canal1:canal2]
        
        # Verificar que no hay NaN en la selección
        if np.any(np.isnan(selected_flux)) or np.any(np.isnan(selected_delta)):
            print(f"   ⚠️  Punto {i}: NaN en selected_flux o selected_delta")
            selected_flux = np.nan_to_num(selected_flux, nan=0.0)
            selected_delta = np.nan_to_num(selected_delta, nan=0.0)
        
        flux_value = np.sum(selected_flux * selected_delta)
        flujos_integrados.append(flux_value)
    
    resultado = np.array(flujos_integrados)
    
    # ✅ MEJORA: Reportar total de valores negativos encontrados
    if total_negativos > 0:
        print(f"   ⚠️  Se encontraron {total_negativos} valores negativos en total")
    
    # Reemplazar cualquier NaN residual
    resultado = np.nan_to_num(resultado, nan=1e-10)
    resultado = np.maximum(resultado, 1e-10)
    
    # Estadísticas del resultado
    valid_results = resultado[resultado > 1e-10]
    if len(valid_results) > 0:
        print(f"   ✅ Resultado integración - Min: {np.min(valid_results):.2e}, Max: {np.max(valid_results):.2e}")
        print(f"   Puntos válidos: {len(valid_results)}/{len(resultado)}")
    else:
        print(f"   ⚠️  Resultado integración - TODOS CERO O NaN")
    
    return resultado