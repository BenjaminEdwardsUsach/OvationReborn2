import numpy as np
import matplotlib.dates as mdates

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
