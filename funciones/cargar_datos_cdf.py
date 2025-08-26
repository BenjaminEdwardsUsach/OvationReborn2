import cdflib
from .load_variable import load_variable

def cargar_datos_cdf(cdf_file):
    """
    Carga variables de un archivo CDF y retorna un diccionario con los datos necesarios.
    """
    archivo = cdflib.CDF(cdf_file)
    tiempo = load_variable(archivo, 'Epoch')
    tiempo_final = [t for t in cdflib.cdfepoch.to_datetime(tiempo)
                    if t.astype('datetime64[Y]').astype(int) + 1970 < 2030]
    tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}

    CHANNEL_ENERGIES      = load_variable(archivo, 'CHANNEL_ENERGIES')
    ELE_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ELE_DIFF_ENERGY_FLUX')
    ELE_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ELE_TOTAL_ENERGY_FLUX')
    ION_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ION_DIFF_ENERGY_FLUX')
    ION_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ION_TOTAL_ENERGY_FLUX')
    SC_AACGM_LAT          = load_variable(archivo, 'SC_AACGM_LAT')
    SC_GEOCENTRIC_LAT     = load_variable(archivo, 'SC_GEOCENTRIC_LAT')

    return {
        "tiempo_final": tiempo_final,
        "tiempo_final_dict": tiempo_final_dict,
        "CHANNEL_ENERGIES": CHANNEL_ENERGIES,
        "ELE_DIFF_ENERGY_FLUX": ELE_DIFF_ENERGY_FLUX,
        "ELE_TOTAL_ENERGY_FLUX": ELE_TOTAL_ENERGY_FLUX,
        "ION_DIFF_ENERGY_FLUX": ION_DIFF_ENERGY_FLUX,
        "ION_TOTAL_ENERGY_FLUX": ION_TOTAL_ENERGY_FLUX,
        "SC_AACGM_LAT": SC_AACGM_LAT,
        "SC_GEOCENTRIC_LAT": SC_GEOCENTRIC_LAT
    }
    