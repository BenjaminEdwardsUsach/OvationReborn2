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

    # Energías de los canales [eV] - 30 eV a 30 keV
    CHANNEL_ENERGIES      = load_variable(archivo, 'CHANNEL_ENERGIES')
    # Flujo diferencial de electrones [eV/cm²/ΔeV/ster/s]
    ELE_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ELE_DIFF_ENERGY_FLUX')
    # Flujo energético total de electrones [eV/cm²/ster/s]
    ELE_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ELE_TOTAL_ENERGY_FLUX')
    # Flujo diferencial de iones [eV/cm²/ΔeV/ster/s]
    ION_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ION_DIFF_ENERGY_FLUX')
    # Flujo energético total de iones [eV/cm²/ster/s]
    ION_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ION_TOTAL_ENERGY_FLUX')
    # Latitud AACGM (coordenadas geomagnéticas) [grados]
    SC_AACGM_LAT          = load_variable(archivo, 'SC_AACGM_LAT')
    # Latitud geocéntrica (coordenadas geográficas) [grados]
    SC_GEOCENTRIC_LAT     = load_variable(archivo, 'SC_GEOCENTRIC_LAT')
    # Longitud AACGM (coordenadas geomagnéticas) [grados]
    SC_AACGM_LON          = load_variable(archivo, 'SC_AACGM_LON')

    return {
        "tiempo_final": tiempo_final,
        "tiempo_final_dict": tiempo_final_dict,
        "CHANNEL_ENERGIES": CHANNEL_ENERGIES,  # [eV] - Energías de los canales
        "ELE_DIFF_ENERGY_FLUX": ELE_DIFF_ENERGY_FLUX,  # [eV/cm²/ΔeV/ster/s] - Flujo diferencial de electrones
        "ELE_TOTAL_ENERGY_FLUX": ELE_TOTAL_ENERGY_FLUX,  # [eV/cm²/ster/s] - Flujo energético total de electrones
        "ION_DIFF_ENERGY_FLUX": ION_DIFF_ENERGY_FLUX,  # [eV/cm²/ΔeV/ster/s] - Flujo diferencial de iones
        "ION_TOTAL_ENERGY_FLUX": ION_TOTAL_ENERGY_FLUX,  # [eV/cm²/ster/s] - Flujo energético total de iones
        "SC_AACGM_LAT": SC_AACGM_LAT,  # [grados] - Latitud geomagnética AACGM
        "SC_GEOCENTRIC_LAT": SC_GEOCENTRIC_LAT,  # [grados] - Latitud geocéntrica
        "SC_AACGM_LON": SC_AACGM_LON,  # [grados] - Longitud geomagnética AACGM
        "tiempo": tiempo  # [ms] según definición en CDF
    }
    