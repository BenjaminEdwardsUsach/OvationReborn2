import numpy as np

def clean_local_outliers(data, threshold=3):
    """
    Reemplaza en 'data' los valores que se desvían más de 'threshold' veces la mediana absoluta de la desviación (MAD) por la mediana.
    """
    data = np.array(data)
    median_val = np.median(data)
    mad = np.median(np.abs(data - median_val))
    if mad == 0:
        mad = np.mean(np.abs(data - median_val))
    cleaned_data = np.where(np.abs(data - median_val) > threshold * mad, median_val, data)
    return cleaned_data
