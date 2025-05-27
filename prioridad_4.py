# PRIORIDAD 4

def load_variable(cdf, varname):
    """
    Carga una variable del archivo CDF aplicando filtros de VALIDMIN y VALIDMAX.
    """
    attrs = cdf.varattsget(varname)
    raw = cdf.varget(varname)
    if 'VALIDMIN' in attrs and 'VALIDMAX' in attrs:
        valid_min = attrs['VALIDMIN']
        valid_max = attrs['VALIDMAX']
        mask = (raw >= valid_min) & (raw <= valid_max)
        return raw[mask]