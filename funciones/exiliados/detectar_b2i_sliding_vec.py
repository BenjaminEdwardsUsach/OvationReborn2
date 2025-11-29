    
    if not valid_candidates:
        return None
    
    return valid_candidates[np.argmax(flux[valid_candidates])]