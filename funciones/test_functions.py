# Import necessary libraries
import pytest
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock, mock_open
import datetime

# Import the functions to be tested
from .agrupar_extremos import agrupar_extremos
from .compute_energy_edges import compute_energy_edges
from .convert_to_serializable import convert_to_serializable
from .clean_local_outliers import clean_local_outliers
from .crear_carpetas import crear_carpetas
from .detectar_b2i_sliding_vec import detectar_b2i_sliding_vec
from .candidate_utils import detect_b2i_candidate
from .cargar_datos_cdf import cargar_datos_cdf
from .detectar_extremos_latitud import detectar_extremos_latitud
from .filtrar_canales import filtrar_canales
from .io_utils import save_cycle_info
from .integrar_flujo_diferencial import integrar_flujo_diferencial
from .load_variable import load_variable
from .procesar_ciclos import procesar_ciclos
from .plot_utils import plot_cycle
from .moving_average import moving_average
from .segment_utils import split_cycle_segment
from .separar_por_latitud import separar_por_latitud

# Tests for agrupar_extremos.py

def test_agrupar_extremos_even_list():
    """Test grouping with an even number of elemments."""
    data = [1, 2, 3, 4, 5, 6]
    expected = [[1, 2], [3, 4], [5, 6]]
    assert agrupar_extremos(data) == expected

def test_agrupar_extremos_odd_list():
    """Test grouping with an odd number of elements."""
    data = [1, 2, 3, 4, 5]
    expected = [[1, 2], [3, 4], [5]]
    assert agrupar_extremos(data) == expected

def test_agrupar_extremos_empty_list():
    """Test grouping with an empty list."""
    data = []
    expected = []
    assert agrupar_extremos(data) == expected

def test_agrupar_extremos_single_element():
    """Test grouping with a single element."""
    data = [1]
    expected = [[1]]
    assert agrupar_extremos(data) == expected

# Tests for compute_energy_edges.py

def test_compute_energy_edges_basic():
    """Tests the basic functionality of compute_energy_edges."""
    energies = np.array([10., 20., 30.])
    expected = np.array([5., 15., 25., 35.])
    np.testing.assert_allclose(compute_energy_edges(energies), expected)

def test_compute_energy_edges_uneven_spacing():
    """Tests with unevenly spaced energies."""
    energies = np.array([10., 30., 60.])
    # (10-(30-10)/2, (10+30)/2, (30+60)/2, (60+(60-30)/2
    expected = np.array([0., 20., 45., 75.])
    np.testing.assert_allclose(compute_energy_edges(energies), expected)

def test_compute_energy_edges_raises_error_for_short_array():
    """Tests that a ValueError is raised for arrays with less than two elements."""
    with pytest.raises(ValueError, match="El array de energías debe tener al menos dos elementos"):
        compute_energy_edges(np.array([10.]))
    with pytest.raises(ValueError, match="El array de energías debe tener al menos dos elementos"):
        compute_energy_edges(np.array([]))

# Tests for convert_to_serializable.py

def test_convert_to_serializable_datetime64():
    """Tests conversion of np.datetime64."""
    dt = np.datetime64('2023-10-27T10:00:00')
    assert convert_to_serializable(dt) == '2023-10-27T10:00:00.000000'

def test_convert_to_serializable_ndarray():
    """Tests conversion of np.ndarray."""
    arr = np.array([1, 2], [3, 4])
    assert convert_to_serializable(arr) == [[1, 2], [3, 4]]

def test_convert_to_serializable_numpy_ints():
    """Tests conversion of numpy integers."""
    assert isinstance(convert_to_serializable(np.int32(42)), int)
    assert isinstance(convert_to_serializable(np.int64(42)), int)

def test_convert_to_serializable_numpy_floats():
    """Tests conversion of numpy floats."""
    assert isinstance(convert_to_serializable(np.float32(3.14)), float)
    assert isinstance(convert_to_serializable(np.float64(3.14)), float)

def test_convert_to_serializable_raises_error_for_unsupported_type():
    """Tests that a TypeError is raised for unsupported types."""
    with pytest.raises(TypeError, match="is not JSON serializable"):
        convert_to_serializable({1, 2, 3})

# Tests for clean_local_outliers.py

def test_clean_local_outliners_removes_outliners():
    """Tests that a clear outliner is replaced by the median."""
    data = np.array([10, 12, 11, 15, 100, 13])
    median = 12.5 # Median of [10, 12, 11, 15, 13]
    expexted = np.array([10, 12, 11, 15, median, 13])
    np.testing.assert_array_equal(clean_local_outliers(data), expexted)

def test_clean_local_outliners_no_outliners():
    """Tests that data with no outliners remains unchanged."""
    data = np.array([10, 12, 11, 15, 13, 14])
    np.testing.assert_array_equal(clean_local_outliers(data), data)

def test_clean_local_outliners_zero_mad():
    """Tests the case where the Median Absolute Deviation is zero."""
    data = np.array([5, 5, 5, 100, 5, 5])
    expected = np.array([5, 5, 5, 5, 5, 5])
    np.testing.assert_array_equal(clean_local_outliers(data), expected)

# Tests for crear_carpetas.py

@patch('os.makedirs')
@patch('os.path.exists')
def test_crear_carpetas_if_not_exists(mock_exists, mock_makedirs):
    """Tests folder creation when the folder does not exist."""
    mock_exists.return_value = False
    cdf_file = "/path/to/my_data_file.cdf"
    expected_name = "my_data_file"
    result = crear_carpetas(cdf_file)
    mock_exists.assert_called_once_with(expected_name)
    mock_makedirs.assert_called_once_with(expected_name)
    assert result == expected_name

@patch('os.makedirs')
@patch('os.path.exists')
def test_crear_carpetas_if_exists(mock_exists, mock_makedirs):
    """Tests that no folder is created if it already exists."""
    mock_exists.return_value = True
    cdf_file = "another_file.cdf"
    expected_name = "another_file"
    result = crear_carpetas(cdf_file)
    mock_exists.assert_called_once_with(expected_name)
    mock_makedirs.assert_not_called()
    assert result == expected_name

# Tests for detectar_b2i_sliding_vec.py

def test_detectar_b2i_sliding_vec_finds_candidate():
    """Tests a case where a valid candidate should be found."""
    data = np.array([12, 15, 30, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]) # Should detect a peak at index 2
    result = detectar_b2i_sliding_vec(flux=data, window_avg=2, lookahead=5, min_flux=10.5) # Should find the point where the local average is higher, a good canidate is index 1
    assert result is not None
    assert result == 1 # best_candidate (average of 15 and 30)

def test_detectar_b2i_sliding_vec_no_valid_candidate():
    """Tests a case where no valid candidate should be found."""
    data = np.array([1, 2, 8, 3, 4, 2, 1, 1, 1, 1, 1, 1, 1])
    result = detectar_b2i_sliding_vec(flux=data, min_flux=10.5)
    assert result is None

def test_detectar_b2i_sliding_vec_short_flux():
    """Tests that it returns None if the flux is too short."""
    data = np.array([10, 20, 30])
    result = detectar_b2i_sliding_vec(flux=data, lookahead=10)
    assert result is None

# Tests for candidate_utils.py

@patch('Funciones.candidate_utils.detectar_b2i_sliding_vec')
def test_detect_b2i_candidate_basic(mock_detectar_b2i):
    """Tess the main workflow of detecting a B2I candidate."""
    mock_detectar_b2i.return_value = 1 # Assuming index 1 is the candidate
    times = [np.datetime64(f'2023-01-01T00:00:0{i}') for i in range(7)]
    flux_data = np.array([10, 12, 500, 18, 25, 20, 15])
    segment = {'time': times, 'flux': flux_data}
    result = detect_b2i_candidate(segment=segment)
    assert 't_candidate' in result
    assert 'flux_candidate' in result
    mock_detectar_b2i.assert_called_once()
    assert result['flux_candidate'] > 0

def test_detect_b2i_candidate_short_input():
    """Tests function with a short input data."""
    time = [np.datetime64('2023-01-01T00:00:00')]
    flux = [100.0]
    segment = {'time': time, 'flux': flux}
    result = detect_b2i_candidate(segment=segment)
    assert result['t_candidate'] == time[0]
    assert result['flux_candidate'] == 100.0
    np.testing.assert_array_equal(result['flux_recorted'], flux)

# Tests for cargar_datos_cdf.py

@patch('cdflib.CDF')
@patch('Funciones.cargar_datos_cdf.load_variable')
@patch('cdflib.cdfepoch.to_datime')
def test_cargar_datos_cdf(mock_cdf_class, mock_load_variable, mock_to_datime):
    """Tests loading data and dictionary creation."""
    mock_cdf_instance = MagicMock()
    mock_cdf_class.return_value = mock_cdf_instance
    mock_time = np.array([730486., 730487.]) # Epoch exapmles
    mock_energies = np.array([30., 50., 70.])
    mock_flux = np.array([[1., 2., 3.], [4., 5., 6.]])
    
    # Configure side effects
    def load_variable_side_effect(cdf, var_name):
        if var_name == 'Epoch':
            return mock_time
        if var_name == 'CHANNEL_ENERGIES':
            return mock_energies
        return mock_flux
    
    mock_load_variable.side_effect = load_variable_side_effect
    mock_datetimes = [np.datetime64('2000-01-01T00:00:00'), np.datetime64('2000-01-01T00:00:01')]
    mock_to_datime.return_value = mock_datetimes
    result = cargar_datos_cdf('some_file.cdf')
    mock_cdf_class.assert_called_with('some_file.cdf')
    assert mock_load_variable.call_count == 8 # Call for 8 variables
    mock_to_datime.assert_called_with(mock_time)
    assert "tiempo_final" in result
    assert "CHANNEL_ENERGIES" in result
    assert "ELE_DIFF_ENERGY_FLUX" in result
    assert len(result["tiempo_final"]) == 2
    assert result["tiempo_final_dict"][mock_datetimes[0]] == 0
    np.testing.assert_array_equal(result["CHANNEL_ENERGIES"], mock_energies)

# Tests for detectar_extremos_latitud.py

def test_detectar_extremos_latitud_crossing():
    """Tests detection of zero crossing in latitude."""
    lats = [10, 5, -5, -10, -5, 5, 10]
    times = [f"t{i}" for i in range(7)]
    extremos = detectar_extremos_latitud(lats, times)
    # Expected: start, first crossing, second crossing, end
    expected = [
        ('t0', 10),
        ('t1', 5), ('t2', -5),
        ('t4', -5), ('t5', 5),
        ('t6', 10)
    ]
    assert extremos == expected

def test_detectar_extremos_latitud_no_crossing():
    """Tests when latitude does not cross zero."""
    lats = [10, 15, 20, 25]
    times = [f"t{i}" for i in range(4)]
    extremos = detectar_extremos_latitud(lats, times)
    expected = [('t0', 10), ('t3', 25)]
    assert extremos == expected

# Tests for filtrar_canales.py

def test_filtrar_canales_basic():
    """Tests the filtering of energy channels and related flux arrays."""
    energies = np.array([10, 20, 50, 100, 200, 500]) # eV
    ele_flux = np.ones((2, 6))
    ion_flux = np.ones((2, 6))
    ch_f, ele_f, ion_f, delta_f = filtrar_canales(energies, ele_flux, ion_flux, low=30, high=300) # Filter between 30 and 300 eV
    expected_energies = np.array([50, 100, 200])
    np.testing.assert_array_equal(ch_f, expected_energies)
    assert ele_f.shape == (2, 3)
    assert ion_f.shape == (2, 3)
    assert delta_f.shape == (3,)

def test_filtrar_canales_no_channels():
    """Tests the case where no channels are within the specified range."""
    energies = np.array([10, 20, 500, 1000])
    ele_flux = np.ones((2, 4))
    ion_flux = np.ones((2, 4))
    ch_f, ele_f, ion_f, delta_f = filtrar_canales(energies, ele_flux, ion_flux, low=100, high=300)
    assert len(ch_f) == 0
    assert ele_f.shape == (2, 0)
    assert ion_f.shape == (2, 0)
    assert len(delta_f) == 0

# Tests for io_utils.py

@patch('os.makedirs')
@patch('json.dump')
@patch('builtins.open', new_callable=mock_open)
def test_save_cycle_info(mock_json_dump, mock_file_open, mock_makedirs):
    """Tests that info is saved correctly to a JSON file."""
    info = {'key': 'value', 'data': [1, 2, 3]}
    main_folder = 'output_folder'
    cycle = 5
    save_cycle_info(info, main_folder, cycle)
    expected_folder = os.path.join(main_folder, 'cycle_5')
    expected_file = os.path.join(expected_folder, 'info_5.json')
    mock_makedirs.assert_called_once_with(expected_folder, exist_ok=True)
    mock_file_open.assert_called_once_with(expected_file, 'w', encoding='utf-8')
    mock_json_dump.assert_called_once()
    args, kwargs = mock_json_dump.call_args
    assert args[0] == info
    assert kwargs['indent'] == 4

# Tests for integrar_flujo_diferencial.py

def test_integrar_flujo_diferencial():
    """Tests the numerical integration of differential flux."""
    ion_flux = np.array([
        [1, 1, 1, 1, 1, 1, 1],
        [2, 2, 2, 2, 2, 2, 2]
    ])
    delta = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    result = integrar_flujo_diferencial(ion_flux, delta, canal1=1, canal2=5)
    expected = np.array([2.0, 4.0])
    np.testing.assert_allclose(result, expected)
    assert result.shape == (2,)

# Tests for load_variable.py

def test_load_variable_with_valid_range():
    """Tests loading a variable with VALIDMIN/VALIDMAX atributes."""
    mock_cdf = MagicMock()
    mock_cdf.varattsget.return_value = {'VALIDMIN': 10., 'VALIDMAX': 100.}
    mock_cdf.varget.return_value = np.array([5., 10., 50., 100., 105.])
    result = load_variable(mock_cdf, 'test_var')
    expected = np.array([np.nan, 10., 50., 100., np.nan])
    np.testing.assert_array_equal(result, expected)

def test_load_variable_without_valid_range():
    """Tests loading a variable without VALIDMIN/VALIDMAX attributes."""
    mock_cdf = MagicMock()
    mock_cdf.varattsget.return_value = {}
    raw_data = np.array([1, 2, 3])
    mock_cdf.varget.return_value = raw_data
    result = load_variable(mock_cdf, 'test_var')
    np.testing.assert_array_equal(result, raw_data)

# Tests for procesar_ciclos.py

@patch('Funciones.procesar_ciclos.plot_cycle')
@patch('Funciones.procesar_ciclos.save_cycle_info')
@patch('Funciones.procesar_ciclos.detect_b2i_candidate')
@patch('Funciones.procesar_ciclos._split_cycle_segment')
def test_procesar_ciclos(mock_split, mock_detect, mock_save, mock_plot):
    """Tests that procesar_ciclos calls its dependencies correctly."""
    mock_split.return_value = {
        'seg1': {'indices': [0, 1], 'time': [0, 1], 'flux': [0, 1], 'coords_aacgm': [0, 1], 'coords_geo': [0, 1]},
        'seg2': {'indices': [2, 3], 'time': [2, 3], 'flux': [2, 3], 'coords_aacgm': [2, 3], 'coords_geo': [2, 3]}
    }
    mock_detect.side_effect = [
        {'t_candidate': 't1', 'flux_candidate': 1.0}, # For first call
        {'t_candidate': 't2', 'flux_candidate': 2.0} # For second call
    ]
    pares_extremos = [('p1_start', 'p1_end')]
    data = {
        'tiempo_final': [0, 1, 2, 3], 'tiempo_final_dict': {},
        'sc_lat': [], 'sc_geo': [], 'flujos_filtrado': [],
        'ion_diff_filtrado': np.zeros((4,10)), 'energy_edges': [],
        'main_folder': 'test_folder'
    }
    procesar_ciclos(pares_extremos, **data)
    mock_split.assert_called_once()
    assert mock_detect.call_count == 2
    mock_save.assert_called_once()
    saved_info = mock_save.call_args[0][0]
    assert 'primera_mitad' in saved_info['b2i_candidate']
    assert saved_info['b2i_candidate']['primera_mitad']['flux_candidate'] == 1.0
    mock_plot.assert_called_once()

# Tests for plot_cycle.py

@patch('matplotlib.pyplot')
@patch('os.makedirs')
def test_plot_cycle(mock_makedirs, mock_plt):
    """Tests that plotting function calls matplotlib and saves files without errors."""
    seg = {'time': [datetime.datetime.now()], 'flux': [1], 'coords_aacgm': [60], 'coords_geo': [60]}
    cand = {'t_candidate': datetime.datetime.now(), 'flux_candidate': 1.0}
    spec = np.random.rand(10, 1)
    energy_edges = np.logspace(1, 4, 11)
    result_path = plot_cycle(seg1=seg, seg2=seg, cand1=cand, cand2=cand, spec1=spec, spec2=spec, energy_edges=energy_edges, main_folder='out', cycle_index=0)
    expected_folder = os.path.join('out', 'cycle_0')
    expected_path = os.path.join(expected_folder, 'cycle0.png')
    mock_makedirs.assert_called_with(expected_folder, exist_ok=True)
    mock_plt.subplots.assert_called_once()
    mock_plt.savefig.assert_called_with(expected_path)
    mock_plt.close.assert_called_once()
    assert result_path == expected_path

# Tests for moving_average.py

def test_moving_average_basic():
    """Tests the function with a window size of 2."""
    data = np.array([10, 20, 30, 40, 50])
    expected = np.array([15., 25., 35., 45.])
    np.testing.assert_allclose(moving_average(data, n=2), expected)

def test_moving_aveerage_custom_window():
    """Tests the function with a custom window size of 3."""
    data = np.array([2, 4, 6, 8, 10])
    expected = np.array([4., 6., 8.]) # (2+4+6)/3, (4+6+8)/3, (6+8+10)/3
    np.testing.assert_allclose(moving_average(data, n=3), expected)

# Tests for segment_utils.py

def test_split_cycle_segment():
    """Tests the logic of splitting a cycle into two segments around the max latitude."""
    times = [datetime.datetime(2023, 1, 1, 0, 0, i) for i in range(10)]
    time_dict = {t: i for i, t in enumerate(times)}
    par = (times[1], times[8]) # Process from index 1 to 8
    flujos = np.arange(100, 110)
    sc_lat = np.arange(10)
    sc_geo = [10, 20, 30, 40, -50, 45, 35, 25, 15, 5] # Max index is 5
    result = split_cycle_segment(par=par, tiempo_final=times, tiempo_final_dict=time_dict, flujos=flujos, sc_lat=sc_lat, sc_geo=sc_geo)
    seg1 = result['seg1']
    seg2 = result['seg2']
    # Since there was a segment taken into consideration starting at 1, now the max before 5, is now 4
    assert len(seg1['flux']) == 3
    assert len(seg2['flux']) == 4
    np.testing.assert_array_equal(seg1['flux'], [100, 102, 103])
    assert seg1['time'][0] == times[1]
    assert seg2['time'][0] == times[4]
    assert seg2['time'][-1] == times[7]
    np.testing.assert_array_equal(seg2['flux'], [107, 106, 105, 104])
    assert seg1['coords_geo'] == [25, 35, 45, -50]

# Tests for separar_por_latitud.py

def test_separar_por_latitud_mixed_data():
    """Test with a standard mix of data inside and outside the range."""
    lats =   [80, 60, 70, 40, -40, -60, -80]
    times = ['t0', 't1', 't2', 't3', 't4', 't5', 't6']
    expected_adjust_lats = [60, 70, -60]
    expected_adjust_times = ['t1', 't2', 't5']
    expected_other_lats = [80, 40, -40, -80]
    expected_other_times = ['t0', 't3', 't4', 't6']
    expected_comparador = [(60, 't1'), (40, 't3'), (-60, 't5'), (-80, 't6')] # All values that are over the boundaries
    a_lat, a_t, o_lat, o_t, comp = separar_por_latitud(lats, times)
    assert a_lat == expected_adjust_lats
    assert a_t == expected_adjust_times
    assert o_lat == expected_other_lats
    assert o_t == expected_other_times
    assert comp == expected_comparador

def test_separar_por_latitud_boundary_values():
    """Tests that values on the exact boundaries."""
    lats = [50, 75, -50, -75, 49.9, 75.1]
    times = ['t0', 't1', 't2', 't3', 't4', 't5']
    a_lat, a_t, o_lat, o_t, comp = separar_por_latitud(lats, times)
    assert a_lat == []
    assert a_t == []
    assert o_lat == lats
    assert o_t == times
    assert comp == []

def test_separar_por_latitud_all_values_inside():
    """Tests the case where all latitude values fall within the valid bands."""
    lats = [60, 65, 70]
    times = ['t0', 't1', 't2']
    a_lat, a_t, o_lat, o_t, comp = separar_por_latitud(lats, times)
    assert a_lat == lats
    assert a_t == times
    assert o_lat == []
    assert o_t == []
    assert comp == [(60, 't0')] # (only) The first entry is recorded

def test_separar_por_latitud_empty_input():
    """Tests that the function handles empty lists."""
    a_lat, a_t, o_lat, o_t, comp = separar_por_latitud([], [])
    assert a_lat == []
    assert a_t == []
    assert o_lat == []
    assert o_t == []
    assert comp == []

def test_separar_por_latitud_mismatched_length():
    """Tests that a ValueError is raised if the inputs have different lengths."""
    with pytest.raises(ValueError, match="Las listas deben tener el mismo largo."):
        separar_por_latitud([60, 70], ['t0'])
