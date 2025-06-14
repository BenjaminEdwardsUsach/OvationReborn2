import numpy as np

def moving_average(a, n=2):
    """
    Calcula el promedio móvil de un arreglo 'a' utilizando una ventana de tamaño 'n'.
    """
    ret = np.cumsum(a, dtype=float)
    print(f"ret: {ret[:4]} lista: {a[:4]}")
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n
