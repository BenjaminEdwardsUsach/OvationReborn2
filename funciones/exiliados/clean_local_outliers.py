        start = max(0, i-2)
        end = min(len(data), i+3)
        cleaned_data[i] = np.median(data[start:end])
    
    return cleaned_data