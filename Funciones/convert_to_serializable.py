import numpy as np

def convert_to_serializable(obj):
    """
    Convierte objetos de tipos especiales (por ejemplo, numpy) a tipos que puedan ser serializados en JSON.
    """
    if isinstance(obj, np.datetime64):
        return str(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
