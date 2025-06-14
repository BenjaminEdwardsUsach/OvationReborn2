def agrupar_extremos(extremos):
    """
    Agrupa extremos en pares para definir segmentos de interés.
    """
    return [extremos[i:i + 2] for i in range(0, len(extremos), 2)]
