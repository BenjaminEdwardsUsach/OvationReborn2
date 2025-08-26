import os

def crear_carpetas(cdf_file):
    """
    Crea carpeta principal basada en nombre de archivo CDF.
    """
    cdf_basename = os.path.splitext(os.path.basename(cdf_file))[0]
    if not os.path.exists(cdf_basename):
        os.makedirs(cdf_basename)
    return cdf_basename
