from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from funciones.compute_energy_edges import compute_energy_edges


def _time_edges(tiempos):
    fechas = []
    for tiempo in tiempos:
        if isinstance(tiempo, np.datetime64):
            fechas.append(tiempo.astype("datetime64[ms]").astype(datetime))
        elif isinstance(tiempo, datetime):
            fechas.append(tiempo)
        else:
            fechas.append(datetime.fromisoformat(str(tiempo)))

    fechas_num = mdates.date2num(fechas)
    if len(fechas_num) == 1:
        half_step = 0.5 / 86400
        return np.array([fechas_num[0] - half_step, fechas_num[0] + half_step])

    if np.any(np.diff(fechas_num) <= 0):
        raise ValueError("Los tiempos del archivo deben estar ordenados y no repetirse.")

    edges = np.empty(len(fechas_num) + 1)
    edges[1:-1] = (fechas_num[:-1] + fechas_num[1:]) / 2
    edges[0] = fechas_num[0] - (fechas_num[1] - fechas_num[0]) / 2
    edges[-1] = fechas_num[-1] + (fechas_num[-1] - fechas_num[-2]) / 2
    return edges


def _graficar_espectrograma(
    tiempos,
    energias,
    flujo,
    tiempo_local,
    particula,
    energia_minima,
    mlt_inicio,
    mlt_fin,
    candidatos,
):
    tiempos = np.asarray(tiempos)
    energias = np.asarray(energias, dtype=float).reshape(-1)
    flujo = np.asarray(flujo, dtype=float)
    tiempo_local = np.asarray(tiempo_local, dtype=float).reshape(-1)

    if flujo.ndim != 2:
        raise ValueError(f"El flujo de {particula} debe ser una matriz de tiempo por canal.")

    cantidad_tiempos = min(len(tiempos), flujo.shape[0])
    cantidad_canales = min(len(energias), flujo.shape[1])
    cantidad_mlt = min(cantidad_tiempos, len(tiempo_local))
    if cantidad_mlt == 0:
        raise ValueError("El archivo no contiene datos válidos de tiempo local magnético.")

    mascara_energia = energias[:cantidad_canales] >= energia_minima
    if mascara_energia.sum() < 2:
        raise ValueError(
            f"Se necesitan al menos dos canales de energía desde {energia_minima:g} eV."
        )
    mascara_mlt = (
        np.isfinite(tiempo_local[:cantidad_mlt])
        & (tiempo_local[:cantidad_mlt] >= mlt_inicio)
        & (tiempo_local[:cantidad_mlt] < mlt_fin)
    )
    if not np.any(mascara_mlt):
        raise ValueError(f"No hay registros dentro del intervalo MLT {mlt_inicio}–{mlt_fin}.")

    if cantidad_tiempos == 0:
        raise ValueError(f"No hay datos suficientes para graficar el espectro de {particula}.")

    tiempos = tiempos[:cantidad_tiempos]
    energias = energias[:cantidad_canales][mascara_energia]
    flujo = flujo[:cantidad_tiempos, :cantidad_canales][:, mascara_energia]
    mascara_mlt_completa = np.zeros(cantidad_tiempos, dtype=bool)
    mascara_mlt_completa[:cantidad_mlt] = mascara_mlt
    valores = np.ma.masked_where(
        ~np.isfinite(flujo)
        | (flujo <= 0)
        | ~mascara_mlt_completa[:, np.newaxis],
        flujo,
    )
    valores_validos = valores.compressed()
    if valores_validos.size == 0:
        raise ValueError(f"No hay flujos positivos válidos para graficar ({particula}).")

    minimo = float(valores_validos.min())
    maximo = float(valores_validos.max())
    if minimo == maximo:
        minimo /= 10
        maximo *= 10

    fig, ax = plt.subplots(figsize=(13, 5), constrained_layout=True)
    imagen = ax.pcolormesh(
        _time_edges(tiempos),
        compute_energy_edges(energias),
        valores.T,
        shading="flat",
        cmap="viridis",
        norm=LogNorm(vmin=minimo, vmax=maximo),
    )
    if particula == "electrones":
        for candidato in candidatos:
            inicio = mdates.date2num(datetime.fromisoformat(candidato["inicio"]))
            fin = mdates.date2num(datetime.fromisoformat(candidato["fin"]))
            ax.axvspan(inicio, fin, color="red", alpha=0.2)
    ax.set_yscale("log")
    ax.set_title(
        f"Espectrograma de {particula} "
        f"(MLT {mlt_inicio:02g}:00–{mlt_fin:02g}:00, "
        f"energía ≥ {energia_minima:g} eV)"
    )
    ax.set_xlabel("Tiempo (UTC)")
    ax.set_ylabel("Energía [eV]")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.colorbar(imagen, ax=ax, label="Flujo diferencial [eV/cm²/ΔeV/ster/s]")
    return fig


def graficar_espectrogramas(
    tiempos,
    energias,
    flujo_electrones,
    flujo_iones,
    tiempo_local,
    energia_minima=200,
    mlt_inicio=12,
    mlt_fin=24,
    candidatos=(),
):
    """Grafica electrones e iones filtrados por MLT y energía, sin guardarlos."""
    return {
        "electrones": _graficar_espectrograma(
            tiempos,
            energias,
            flujo_electrones,
            tiempo_local,
            "electrones",
            energia_minima,
            mlt_inicio,
            mlt_fin,
            candidatos,
        ),
        "iones": _graficar_espectrograma(
            tiempos,
            energias,
            flujo_iones,
            tiempo_local,
            "iones",
            energia_minima,
            mlt_inicio,
            mlt_fin,
            (),
        ),
    }
