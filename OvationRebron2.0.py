#%% IMPORTS Y CONFIGURACIÓN INICIAL
import cdflib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator
import json
import os  # Para manejo de archivos y carpetas

# Nota: Se debe tener cuidado con la ordenación de CHANNEL_ENERGIES (ascendente o descendente)
# para que el cálculo de 'delta' (ancho de los canales) tenga sentido.

#%% FUNCIONES DE UTILIDAD
#guardaer un solo resultado para probar algoritsmnos y guardar funciones en otro archivo

def detectar_b2i_sliding_vec(flux, window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5):
    """
    Detecta el índice candidato para el límite b2i en una serie de flujos integrados.
    """
    flux = np.asarray(flux, dtype=float)
    n = len(flux)
    valid_range = n - (lookahead + window_avg) + 1
    if valid_range < 1:
        return None

    # Promedio móvil para los candidatos
    kernel_avg = np.ones(window_avg) / window_avg
    candidate_avgs = np.convolve(flux, kernel_avg, mode='valid')[:valid_range]

    # Vectorizar el cálculo del máximo promedio móvil en la ventana lookahead
    max_sliding = np.empty(valid_range)
    kernel_slide = np.ones(sliding_window) / sliding_window
    for i in range(valid_range):
        segment = flux[i + window_avg : i + window_avg + lookahead]
        if len(segment) < sliding_window:
            max_sliding[i] = -np.inf  # No hay suficientes datos
        else:
            sliding_avgs = np.convolve(segment, kernel_slide, mode='valid')
            max_sliding[i] = np.max(sliding_avgs)

    diff = candidate_avgs - max_sliding
    valid_candidates = np.where((candidate_avgs >= min_flux) & (diff > 0))[0]
    if len(valid_candidates) == 0:
        return None

    best_candidate = valid_candidates[np.argmax(diff[valid_candidates])]
    return best_candidate


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

def clean_local_outliers(data, threshold=3): #Aún no se prueba que funcione
    """
    Reemplaza en 'data' los valores que se desvían más de 'threshold' veces la mediana absoluta de la desviación (MAD) por la mediana.
    """
    data = np.array(data)
    median_val = np.median(data)
    mad = np.median(np.abs(data - median_val))
    if mad == 0:
        mad = np.mean(np.abs(data - median_val))
    cleaned_data = np.where(np.abs(data - median_val) > threshold * mad, median_val, data)
    return cleaned_data

def compute_time_edges(time_array):
    """
    Calcula los bordes de tiempo a partir de un array de tiempos para su uso en pcolormesh.
    """
    time_num = mdates.date2num(time_array)
    if len(time_num) > 1:
        dt = np.diff(time_num)
        return np.concatenate(([time_num[0] - dt[0]/2],
                               (time_num[:-1] + time_num[1:]) / 2,
                               [time_num[-1] + dt[-1]/2]))
    else:
        return np.array([time_num[0] - 0.005, time_num[0] + 0.005])

def compute_energy_edges(energies):
    """
    Calcula los bordes de energía a partir de un array de energías ordenadas.
    Devuelve un array de tamaño len(energies) + 1 con los bordes de cada canal.
    """
    energies = np.asarray(energies, dtype=float)
    if energies.ndim != 1 or len(energies) < 2:
        raise ValueError("El array de energías debe ser unidimensional y tener al menos dos elementos")
    
    # Calcula los bordes intermedios como el promedio entre energías adyacentes
    edges = (energies[:-1] + energies[1:]) / 2
    # Calcula el borde inferior y superior
    lower = energies[0] - (energies[1] - energies[0]) / 2
    upper = energies[-1] + (energies[-1] - energies[-2]) / 2
    # Une todos los bordes en un solo array
    return np.concatenate(([lower], edges, [upper]))

def calcular_min_tolerable(segment_flux, factor=0.1): #aún no se prueba que funcione
    """
    Calcula un umbral mínimo tolerable a partir de un segmento de flujo.
    """
    segment_flux = np.array(segment_flux)
    background = np.percentile(segment_flux, 85)
    peak = np.percentile(segment_flux, 90)
    umbral = background + factor * (peak - background)
    print(f"Background: {background:.3f}, Peak: {peak:.3f}, Threshold: {umbral:.3f}")
    return umbral

#%% CARGA DE DATOS DEL ARCHIVO CDF
cdf_file = 'dmsp-f16_ssjs_precipitating-electrons-ions_20141231000000_20141231235959_cdaweb.cdf'
archivo = cdflib.CDF(cdf_file)
info = archivo.cdf_info()

tiempo = load_variable(archivo, 'Epoch')
tiempo_final = [t for t in cdflib.cdfepoch.to_datetime(tiempo)
                if t.astype('datetime64[Y]').astype(int) + 1970 < 2030]
tiempo_final_dict = {t: i for i, t in enumerate(tiempo_final)}

CHANNEL_ENERGIES      = load_variable(archivo, 'CHANNEL_ENERGIES')
ELE_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ELE_DIFF_ENERGY_FLUX')
ELE_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ELE_TOTAL_ENERGY_FLUX')
ION_DIFF_ENERGY_FLUX  = load_variable(archivo, 'ION_DIFF_ENERGY_FLUX')
ION_TOTAL_ENERGY_FLUX = load_variable(archivo, 'ION_TOTAL_ENERGY_FLUX')
SC_AACGM_LAT          = load_variable(archivo, 'SC_AACGM_LAT')
SC_GEOCENTRIC_LAT     = load_variable(archivo, 'SC_GEOCENTRIC_LAT')

#%% FILTRADO DE CANALES (30 eV a 30000 eV)
#MOVER PARA SOLO FILTRAR DATOS YA EN EL RANGO
mask_chan = (CHANNEL_ENERGIES >= 30) & (CHANNEL_ENERGIES <= 30000)
CHANNEL_ENERGIES = CHANNEL_ENERGIES[mask_chan]
ELE_DIFF_ENERGY_FLUX = ELE_DIFF_ENERGY_FLUX[:, mask_chan]
ION_DIFF_ENERGY_FLUX = ION_DIFF_ENERGY_FLUX[:, mask_chan]

# Se definen los canales (índices) a integrar
canal1 = 0
canal2 = 6

Ec2 = CHANNEL_ENERGIES[:-3]
Ec1 = CHANNEL_ENERGIES[2:-1]
delta = (Ec2 - Ec1) / 2
Left  = (CHANNEL_ENERGIES[0] - CHANNEL_ENERGIES[1])
Right = (CHANNEL_ENERGIES[-2] - CHANNEL_ENERGIES[-1])
delta = np.insert(delta, 0, Left)
delta = np.append(delta, Right)
delta = np.array(delta)

#%% INTEGRACIÓN DEL FLUJO DIFERENCIAL
flujos_iones = []
for elem in ION_DIFF_ENERGY_FLUX:
    flux_value = np.sum(elem[canal1:canal2] * delta[canal1:canal2])
    flujos_iones.append(flux_value)
flujos_iones = np.array(flujos_iones)

#%% FILTRADO POR OUTLIERS
indices_diff = np.where(~np.isnan(flujos_iones))[0] 
tiempo_final_filtrado = [tiempo_final[i] for i in indices_diff]
flujos_iones_filtrado = flujos_iones[indices_diff]
ION_DIFF_ENERGY_FLUX_filtrado = ION_DIFF_ENERGY_FLUX[indices_diff, :]

tiempo_final_filtrado_dict = {t: i for i, t in enumerate(tiempo_final_filtrado)}

ion_total_clean = np.array([val for val in ION_TOTAL_ENERGY_FLUX if not np.isnan(val)])
indices_total = np.where(~np.isnan(ION_TOTAL_ENERGY_FLUX))[0]
tiempo_total_filtrado = [tiempo_final[i] for i in indices_total]
ion_total_filtrado = ION_TOTAL_ENERGY_FLUX[indices_total]

#%% SEPARACIÓN SEGÚN LATITUD (SC_AACGM_LAT)
adjust_SC_AACGM_LAT = []
other_SC_AACGM_LAT  = []
adjust_tiempo_final = []
other_tiempo_final  = []
comparador = []
flag = False


#reorganizar de manera más eficiente
for i, elem in enumerate(SC_AACGM_LAT):
    if (-75 < elem < -50) or (50 < elem < 75):
        adjust_SC_AACGM_LAT.append(elem)
        adjust_tiempo_final.append(tiempo_final[i])
        if not flag:
            comparador.append((elem, tiempo_final[i]))
        flag = True
    else:
        if flag:
            comparador.append((elem, tiempo_final[i]))
        flag = False
        other_SC_AACGM_LAT.append(elem)
        other_tiempo_final.append(tiempo_final[i])

#%% DETECCIÓN DE EXTREMOS EN LATITUD (CAMBIO DE SIGNO)
extremos = []
extremos.append((adjust_tiempo_final[0], adjust_SC_AACGM_LAT[0]))
for i in range(len(adjust_SC_AACGM_LAT) - 1):
    if (adjust_SC_AACGM_LAT[i] > 0 and adjust_SC_AACGM_LAT[i + 1] < 0) or \
       (adjust_SC_AACGM_LAT[i] < 0 and adjust_SC_AACGM_LAT[i + 1] > 0):
        extremos.append((adjust_tiempo_final[i], adjust_SC_AACGM_LAT[i]))
        extremos.append((adjust_tiempo_final[i + 1], adjust_SC_AACGM_LAT[i + 1]))
extremos.append((adjust_tiempo_final[-1], adjust_SC_AACGM_LAT[-1]))

#%% AGRUPACIÓN DE EXTREMOS EN PARES (SEGMENTOS DE INTERÉS)
pares_extremos = [extremos[i:i + 2] for i in range(0, len(extremos), 2)]

#%% SELECCIÓN DE SEGMENTOS VÁLIDOS
tol = 1  # Tolerancia en segundos
valid_data = []
others = []
for par in pares_extremos:
    t_in = par[0][0]
    t_out = par[1][0]
    count = 0
    for (lat, t) in comparador:
        if (t >= t_in - tol) and (t <= t_out + tol) and (lat != 0):
            count += 1
    try:
        idx_out = adjust_tiempo_final.index(t_out)
    except ValueError:
        idx_out = None
    if idx_out is not None and idx_out < len(adjust_tiempo_final) - 1:
        t_next = adjust_tiempo_final[idx_out + 1]
        if (t_next - t_out) <= tol:
            count += 1
    if count >= 3:
        valid_data.append(par)
    else:
        others.append(par)

#%% CREACIÓN DE CARPETAS PARA CADA CICLO
cdf_basename = os.path.splitext(os.path.basename(cdf_file))[0]
main_folder = cdf_basename
if not os.path.exists(main_folder):
    os.makedirs(main_folder)


#%% BUCLE SOBRE SEGMENTOS VÁLIDOS PARA DETECTAR B2I Y GRAFICAR CICLOS
#(hacer en funciones)
info_pasadas = []
contador = 0
for par in pares_extremos:#solo un rango pequeño
    idx_start = tiempo_final_filtrado_dict[par[0][0]]
    idx_end = tiempo_final_filtrado_dict[par[1][0]]

    # Extraer el segmento completo de flujo y tiempo filtrados
    segmento_flux = flujos_iones_filtrado[idx_start: idx_end + 1]
    segmento_time = tiempo_final_filtrado[idx_start: idx_end + 1]

    # Extraer las coordenadas asociadas usando el diccionario original de tiempos
    coords_SC_AACGM = [SC_AACGM_LAT[tiempo_final_dict[t]] for t in segmento_time]
    coords_SC_GEOCENTRIC = [SC_GEOCENTRIC_LAT[tiempo_final_dict[t]] for t in segmento_time]

    # Determinar el índice donde se alcanza la latitud máxima (valor absoluto)
    max_lat_index = np.argmax([abs(x) for x in coords_SC_GEOCENTRIC])
    
    if max_lat_index == 0:  # Caso especial: si empieza en el polo
        segmento_flux_1 = segmento_flux.copy()
        segmento_time_1 = segmento_time.copy()
        segmento_flux_2 = segmento_flux.copy()
        segmento_time_2 = np.array(segmento_time)
        coords_first = coords_SC_AACGM
        coords_geo_first = coords_SC_GEOCENTRIC
        coords_second = coords_SC_AACGM
        coords_geo_second = coords_SC_GEOCENTRIC
    else:
        segmento_flux_1 = segmento_flux[:max_lat_index]
        segmento_time_1 = segmento_time[:max_lat_index]
        segmento_flux_2 = segmento_flux[max_lat_index:][::-1]
        segmento_time_2 = np.array(segmento_time[max_lat_index:])
        coords_first = coords_SC_AACGM[:max_lat_index]
        coords_geo_first = coords_SC_GEOCENTRIC[:max_lat_index]
        coords_second = coords_SC_AACGM[max_lat_index:]
        coords_geo_second = coords_SC_GEOCENTRIC[max_lat_index:]

    # --------- Detección en la primera mitad ---------
    if len(segmento_flux_1) < 2:
        flujo_recortado_1 = np.array(segmento_flux_1)
        tiempo_recortado_1 = np.array(segmento_time_1)
        candidate_index_recorte = 0
        t_candidate_1 = segmento_time_1[0]
        flux_candidate_1 = segmento_flux_1[0]
    else:
        segmento_flux_cleaned_1 = clean_local_outliers(segmento_flux_1, threshold=3)
        umbral_recorte_1 = np.percentile(segmento_flux_cleaned_1, 85)
        idx_recorte_1 = np.where(segmento_flux_1 >= umbral_recorte_1)[0]
        if idx_recorte_1.size == 0:
            idx_recorte_1 = np.arange(len(segmento_flux_1))
        flujo_recortado_1 = np.array(segmento_flux_1)[idx_recorte_1]
        tiempo_recortado_1 = np.array(segmento_time_1)[idx_recorte_1]
        candidate_index_recorte = detectar_b2i_sliding_vec(flujo_recortado_1,
                                                           window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5)
        if candidate_index_recorte is None:
            candidate_index_recorte = 0
        candidate_local_1 = idx_recorte_1[candidate_index_recorte]
        t_candidate_1 = segmento_time_1[candidate_local_1]
        flux_candidate_1 = segmento_flux_1[candidate_local_1]

    # --------- Detección en la segunda mitad ---------
    if len(segmento_flux_2) < 2:
        candidate_index_recorte_2 = 0
        t_candidate_2 = segmento_time_2[0]
        flux_candidate_2 = segmento_flux_2[0]
        flujo_recortado_2 = np.array(segmento_flux_2)
        tiempo_recortado_2 = np.array(segmento_time_2)
    else:
        segmento_flux_cleaned_2 = clean_local_outliers(segmento_flux_2, threshold=3)
        umbral_recorte_2 = np.percentile(segmento_flux_cleaned_2, 85)
        idx_recorte_2 = np.where(segmento_flux_2 >= umbral_recorte_2)[0]
        if idx_recorte_2.size == 0:
            idx_recorte_2 = np.arange(len(segmento_flux_2))
        flujo_recortado_2 = np.array(segmento_flux_2)[idx_recorte_2]
        tiempo_recortado_2 = np.array(segmento_time_2)[idx_recorte_2]
        
        candidate_index_recorte_2 = detectar_b2i_sliding_vec(flujo_recortado_2,
                                                            window_avg=2, lookahead=10, sliding_window=3, min_flux=10.5)
        if candidate_index_recorte_2 is None:
            candidate_index_recorte_2 = 0
        t_candidate_2 = tiempo_recortado_2[candidate_index_recorte_2]
        flux_candidate_2 = flujo_recortado_2[candidate_index_recorte_2]

    #OPTIMIZAR
    info_pasada = {
        "b2i_candidate": {
            "primera_mitad": {
                "candidate_time": str(t_candidate_1),
                "candidate_flux": flux_candidate_1,
                "recortado_time": [str(tiempo_recortado_1[0]), str(tiempo_recortado_1[-1])],
                "coordinates": {
                    "SC_AACGM": (coords_first[0], coords_first[-1]),
                    "SC_GEOCENTRIC": (coords_geo_first[0], coords_geo_first[-1])
                }
            },
            "segunda_mitad": {
                "candidate_time": str(t_candidate_2),
                "candidate_flux": flux_candidate_2,
                "recortado_time": [str(tiempo_recortado_2[0]), str(tiempo_recortado_2[-1])],
                "coordinates": {
                    "SC_AACGM": (coords_second[0], coords_second[-1]),
                    "SC_GEOCENTRIC": (coords_geo_second[0], coords_geo_second[-1])
                }
            }
        }
    }
    
    cycle_folder = os.path.join(main_folder, f"cycle_{contador}")
    if not os.path.exists(cycle_folder):
        os.makedirs(cycle_folder)
    
    info_filename = os.path.join(cycle_folder, f"info_{contador}.txt")
    with open(info_filename, 'w') as file:
        file.write(json.dumps(info_pasada, indent=4, default=convert_to_serializable))
    
    # --- SINCRONIZACIÓN DE TIEMPOS USANDO ÍNDICES DIRECTOS ---
    # Definimos los índices para la primera y segunda mitad utilizando el segmento filtrado original
    if max_lat_index == 0:
        indices_first = np.arange(idx_start, idx_end + 1)
        indices_second = indices_first  # En este caso se usa el mismo segmento para ambas mitades
    else:
        indices_first = np.arange(idx_start, idx_start + max_lat_index)
        indices_second = np.arange(idx_start + max_lat_index, idx_end + 1)
    
    # Primera mitad: extraer la variable de tiempo y datos para el espectrograma
    time_segment_first = np.array(tiempo_final_filtrado)[indices_first]
    data_ion_first = ION_DIFF_ENERGY_FLUX_filtrado[indices_first, :].T
    time_edges_first = compute_time_edges(time_segment_first)
    # Para la gráfica integrada, usamos el segmento ya definido
    flux_segment_first = np.array(segmento_flux_1)
    
    #ESTA PARTE NO ESTÁ VERIFICADA QUE FUNCIONE BIEN, ES DE PRUEBA
    
    # Segunda mitad: extraer la variable de tiempo y datos para el espectrograma
    time_segment_second = np.array(tiempo_final_filtrado)[indices_second]
    # Invertimos la secuencia para mantener la coherencia con la detección
    time_segment_second_invertido = time_segment_second
    data_ion_second = ION_DIFF_ENERGY_FLUX_filtrado[indices_second, :].T
    data_ion_second_invertido = data_ion_second[:, ::-1]
    time_edges_second = compute_time_edges(time_segment_second_invertido)
    flux_segment_second = np.array(segmento_flux[max_lat_index:])[::-1]

    #////////////////////////////////////////////////////////////////
    
    date_format = mdates.DateFormatter('%H:%M:%S')
    energy_edges = compute_energy_edges(CHANNEL_ENERGIES)

    # --- CREAR FIGURA 2x2 CON SUBPLOTS (ESPECTROGRAMA y FLUJO INTEGRADO) ---
    fig, axs = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
    ax_spec_left = axs[0, 0]
    ax_flux_left = axs[1, 0]
    ax_spec_right = axs[0, 1]
    ax_flux_right = axs[1, 1]
    
    # Espectrograma de la primera mitad
    X_left, Y_left = np.meshgrid(time_edges_first, energy_edges)
    c1 = ax_spec_left.pcolormesh(X_left, Y_left, data_ion_first,
                                 norm=plt.matplotlib.colors.LogNorm(), shading='auto')
    ax_spec_left.set_yscale('log')
    ax_spec_left.set_title("Spectrogram - ION_DIFF_ENERGY_FLUX (Primera mitad)")
    ax_spec_left.set_ylabel("Energy (eV)")
    ax_spec_left.xaxis_date()
    ax_spec_left.xaxis.set_major_formatter(date_format)
    fig.colorbar(c1, ax=ax_spec_left, label="Flux (arb. units)")
    
    # Flujo integrado de la primera mitad
    ax_flux_left.scatter(time_segment_first, flux_segment_first, label="Integrated Flux (ION_DIFF)")
    ax_flux_left.set_ylabel("Integrated Flux (eV)")
    ax_flux_left.set_title(f"Cycle {contador}: ION_DIFF (Primera mitad)\nCandidate: {t_candidate_1}, Flux: {flux_candidate_1:.3f}")
    ax_flux_left.axvline(t_candidate_1, color='red', linestyle='--', label=f"Candidate: {t_candidate_1}")
    ax_flux_left.legend()
    ax_flux_left.grid(True)
    ax_flux_left.xaxis_date()
    ax_flux_left.xaxis.set_major_formatter(date_format)
    
    # Personalización de etiquetas en el eje x para la primera mitad
    tick_locs_left = ax_flux_left.get_xticks()
    seg_time_num_left = mdates.date2num(time_segment_first)
    new_labels_left = []
    for i, loc in enumerate(tick_locs_left):
        dt_tick = mdates.num2date(loc)
        idx = np.argmin(np.abs(seg_time_num_left - loc))
        if i == 0:
            label = dt_tick.strftime('UT: %H:%M:%S') + "\nAACGM: {:.1f}, \nGEO: {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
        else:
            label = dt_tick.strftime('%H:%M:%S') + "\n {:.1f}, \n {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
        new_labels_left.append(label)
    ax_flux_left.xaxis.set_major_locator(FixedLocator(tick_locs_left))
    ax_flux_left.set_xticklabels(new_labels_left, rotation=0, ha='center')
    
    # Espectrograma de la segunda mitad (invertido)
    X_right, Y_right = np.meshgrid(time_edges_second, energy_edges)
    c2 = ax_spec_right.pcolormesh(X_right, Y_right, data_ion_second_invertido,
                                  norm=plt.matplotlib.colors.LogNorm(), shading='auto')
    ax_spec_right.set_yscale('log')
    ax_spec_right.set_title("Spectrogram - ION_DIFF_ENERGY_FLUX (Segunda mitad, invertida)")
    ax_spec_right.set_ylabel("Energy (eV)")
    ax_spec_right.xaxis_date()
    ax_spec_right.xaxis.set_major_formatter(date_format)
    fig.colorbar(c2, ax=ax_spec_right, label="Flux (arb. units)")
    
    # Flujo integrado de la segunda mitad
    ax_flux_right.plot(time_segment_second_invertido, flux_segment_second, 'b-', label="Integrated Flux (ION_DIFF)")
    ax_flux_right.set_ylabel("Integrated Flux (eV)")
    ax_flux_right.set_title(f"Cycle {contador}: ION_DIFF (Segunda mitad, invertida)\nCandidate: {t_candidate_2}, Flux: {flux_candidate_2:.3f}")
    ax_flux_right.axvline(t_candidate_2, color='red', linestyle='--', label=f"Candidate: {t_candidate_2}")
    ax_flux_right.legend()
    ax_flux_right.grid(True)
    ax_flux_right.xaxis_date()
    ax_flux_right.xaxis.set_major_formatter(date_format)
    
    # Personalización de etiquetas en el eje x para la segunda mitad
    tick_locs_right = ax_flux_right.get_xticks()
    seg_time_num_right = mdates.date2num(time_segment_second_invertido)
    new_labels_right = []
    for i, loc in enumerate(tick_locs_right):
        dt_tick = mdates.num2date(loc)
        idx = np.argmin(np.abs(seg_time_num_right - loc))
        if i == 0:
            label = dt_tick.strftime('UT: %H:%M:%S') + "\nAACGM: {:.1f}, \nGEO: {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
        else:
            label = dt_tick.strftime('%H:%M:%S') + "\n {:.1f}, \n {:.1f}".format(coords_SC_AACGM[idx], coords_SC_GEOCENTRIC[idx])
        new_labels_right.append(label)
    ax_flux_right.xaxis.set_major_locator(FixedLocator(tick_locs_right))
    ax_flux_right.set_xticklabels(new_labels_right, rotation=0, ha='center')

    image_filename = os.path.join(cycle_folder, f"cycle{contador}.png")
    plt.savefig(image_filename, format='png')
    plt.close(fig)
    
    contador += 1
