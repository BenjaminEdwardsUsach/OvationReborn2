            'flux_recorted': flux,
            'time_recorted': times
        }

    cleaned = clean_local_outliers(flux)
    umbral = np.percentile(cleaned, threshold_percentile)
    idxs = np.where(flux >= umbral)[0]
    if idxs.size == 0:
        idxs = np.arange(len(flux))

    rec_flux = flux[idxs]
    rec_time = [times[i] for i in idxs]

    raw_idx = detectar_b2i_sliding_vec(rec_flux, **kwargs)
    if raw_idx is None:
        raw_idx = 0
    local_idx = idxs[raw_idx]

    return {
        't_candidate': rec_time[raw_idx],
        'flux_candidate': float(flux[local_idx]),
        'flux_recorted': rec_flux,
        'time_recorted': rec_time
    }
