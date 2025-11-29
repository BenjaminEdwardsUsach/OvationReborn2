import os
from datetime import datetime

def crear_carpetas(cdf_file, directorio_base="results"):
    """
    Crea carpeta principal basada en nombre de archivo CDF con timestamp.
    
    Args:
        cdf_file (str): Ruta al archivo CDF
        directorio_base (str): Directorio base donde crear los resultados
        
    Returns:
        str: Ruta a la carpeta principal creada
    """
    # Crear directorio base si no existe
    os.makedirs(directorio_base, exist_ok=True)
    
    # Crear nombre único con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cdf_basename = os.path.splitext(os.path.basename(cdf_file))[0]
    carpeta_principal = os.path.join(directorio_base, f"{cdf_basename}_{timestamp}")
    
    # Crear carpeta principal
    if not os.path.exists(carpeta_principal):
        os.makedirs(carpeta_principal)
    
    print(f"Carpeta de resultados creada: {carpeta_principal}")
    return carpeta_principal