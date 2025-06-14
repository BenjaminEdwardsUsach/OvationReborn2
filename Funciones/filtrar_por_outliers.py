#%%
import numpy as np

def filtrar_por_outliers(flujos_iones, ION_TOTAL_ENERGY_FLUX,ION_DIFF_ENERGY_FLUX, SC_AACGM_LAT, SC_GEOCENTRIC_LAT, tiempo_final):
    """
    Filtra valores NaN de flujos y retorna datos filtrados correspondientes.
    """
    indices_diff = np.where(~np.isnan(flujos_iones))[0]
    tiempo_final_filtrado = [tiempo_final[i] for i in indices_diff]
    flujos_iones_filtrado = flujos_iones[indices_diff]
    ION_DIFF_ENERGY_FLUX_filtrado = ION_DIFF_ENERGY_FLUX[indices_diff, :]

    ion_total_clean = np.array([val for val in ION_TOTAL_ENERGY_FLUX if not np.isnan(val)])
    indices_total = np.where(~np.isnan(ION_TOTAL_ENERGY_FLUX))[0]
    tiempo_total_filtrado = [tiempo_final[i] for i in indices_total]
    ion_total_filtrado = ION_TOTAL_ENERGY_FLUX[indices_total]

    return {
        "tiempo_final_filtrado": tiempo_final_filtrado,
        "flujos_iones_filtrado": flujos_iones_filtrado,
        "ION_DIFF_ENERGY_FLUX_filtrado": ION_DIFF_ENERGY_FLUX_filtrado,
        "SC_AACGM_LAT": SC_AACGM_LAT,
        "SC_GEOCENTRIC_LAT": SC_GEOCENTRIC_LAT,
        "tiempo_total_filtrado": tiempo_total_filtrado,
        "ion_total_filtrado": ion_total_filtrado
    }
