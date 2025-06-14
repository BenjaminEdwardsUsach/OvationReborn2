import numpy as np

def load_variable(cdf, varname):
    """
    Carga una variable de un archivo CDF y aplica un filtrado basado en los atributos
    'VALIDMIN' y 'VALIDMAX', en caso de que existan.
    """
    attrs = cdf.varattsget(varname)
    raw = cdf.varget(varname)
    if 'VALIDMIN' in attrs and 'VALIDMAX' in attrs:
        valid_min = attrs['VALIDMIN']
        valid_max = attrs['VALIDMAX']
        return np.where((raw >= valid_min) & (raw <= valid_max), raw, np.nan)
    return raw
