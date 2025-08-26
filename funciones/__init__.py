# funciones/__init__.py

# — Funciones de carga y filtrado —
from .cargar_datos_cdf import cargar_datos_cdf
from .load_variable import load_variable

# — Funciones de procesamiento de canales —
from .filtrar_canales import filtrar_canales
from .integrar_flujo_diferencial import integrar_flujo_diferencial

# — Funciones de latitud y segmentos —
from .separar_por_latitud import separar_por_latitud
from .detectar_extremos_latitud import detectar_extremos_latitud
from .agrupar_extremos import agrupar_extremos

# — Funciones auxiliares —
from .crear_carpetas import crear_carpetas

# — Funciones de cálculo interno —
#from .moving_average import moving_average
#from .detectar_b2i_sliding_vec import detectar_b2i_sliding_vec
from .convert_to_serializable import convert_to_serializable
#from .clean_local_outliers import clean_local_outliers

from .compute_energy_edges import compute_energy_edges


# — Función principal que genera los ciclos (gráficas, JSON, etc.) —
from .procesar_ciclos import procesar_ciclos


from .io_utils import save_cycle_info
from .plot_utils import plot_cycle
from .procesar_ciclos import procesar_ciclos
