def clean_local_outliers(data, threshold=3.0):
    data = np.asarray(data)
    if len(data) < 3:
        return data
    
    median_val = np.median(data)
    mad = np.median(np.abs(data - median_val))
    
    # Manejar MAD=0 usando desviación estándar
    if mad < 1e-10:
        std = np.std(data)
        mad = std * 0.6745 if std > 0 else 1.0
    
    # Suavizado adaptativo para series temporales
    z_scores = (data - median_val) / mad
    cleaned_data = np.copy(data)
    outlier_mask = np.abs(z_scores) > threshold
    
    # Reemplazar con promedio local en lugar de mediana global
    for i in np.where(outlier_mask)[0]:
        start = max(0, i-2)
        end = min(len(data), i+3)
        cleaned_data[i] = np.median(data[start:end])
    
    return cleaned_data