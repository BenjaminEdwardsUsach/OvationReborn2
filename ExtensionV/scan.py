import os

import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks

from funciones.compute_energy_edges import compute_energy_edges
from funciones.cargar_datos_cdf import cargar_datos_cdf
from .plot_scan import graficar_espectrogramas


def _contiguous_regions(mask):
    padded = np.concatenate(([False], mask, [False])).astype(np.int8)
    changes = np.diff(padded)
    return list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)))


def _orbital_segments(times, latitude, selected):
    """Split selected contiguous data at smoothed AACGM latitude extrema."""
    segments = []
    for start, stop in _contiguous_regions(selected):
        if stop - start < 3:
            continue
        segment_times = times[start:stop].astype("datetime64[ms]")
        cadence = np.diff(segment_times).astype("timedelta64[ms]").astype(float) / 1000
        gaps = np.flatnonzero(cadence > 2.5) + 1
        gap_bounds = np.concatenate(([0], gaps, [stop - start]))

        for gap_start, gap_stop in zip(gap_bounds[:-1], gap_bounds[1:]):
            if gap_stop - gap_start < 3:
                continue
            absolute_start = start + gap_start
            absolute_stop = start + gap_stop
            lat = latitude[absolute_start:absolute_stop]
            smooth_lat = median_filter(lat, size=min(31, len(lat) // 2 * 2 + 1))
            maxima, _ = find_peaks(smooth_lat, prominence=5, distance=300)
            minima, _ = find_peaks(-smooth_lat, prominence=5, distance=300)
            turning_points = np.sort(np.concatenate((maxima, minima)))
            bounds = np.concatenate(([0], turning_points, [len(lat) - 1]))
            bounds = np.unique(bounds)
            for left, right in zip(bounds[:-1], bounds[1:]):
                if right - left >= 60:
                    segments.append((absolute_start + left, absolute_start + right + 1))
    return segments


def _detect_candidates(times, latitude, mlt, electron_flux, energies):
    """Find minute-scale electron enhancements with a local robust baseline."""
    energy_mask = energies >= 200
    if np.count_nonzero(energy_mask) < 2:
        raise ValueError("Se necesitan al menos dos canales de electrones desde 200 eV.")

    energy_widths = np.abs(np.diff(compute_energy_edges(energies)))
    selected_flux = np.asarray(electron_flux, dtype=float)[:, energy_mask]
    signal = np.sum(
        np.where(np.isfinite(selected_flux), np.maximum(selected_flux, 0), 0)
        * energy_widths[energy_mask],
        axis=1,
    )
    selected = (
        np.isfinite(mlt)
        & (mlt >= 12)
        & (mlt < 24)
        & np.isfinite(latitude)
        & np.isfinite(signal)
        & (signal > 0)
    )

    candidates = []
    cycles = []
    for cycle_index, (start, stop) in enumerate(
        _orbital_segments(times, latitude, selected), start=1
    ):
        cycles.append({
            "ciclo": cycle_index,
            "indice_inicio": int(start),
            "indice_fin": int(stop),
            "inicio": str(times[start]),
            "fin": str(times[stop - 1]),
            "latitud_aacgm_min": round(float(np.nanmin(latitude[start:stop])), 2),
            "latitud_aacgm_max": round(float(np.nanmax(latitude[start:stop])), 2),
        })
        segment_signal = signal[start:stop]
        log_signal = np.log10(np.maximum(segment_signal, np.finfo(float).tiny))
        if len(log_signal) < 90:
            continue

        baseline_window = min(301, len(log_signal) if len(log_signal) % 2 else len(log_signal) - 1)
        smooth_signal = median_filter(log_signal, size=5)
        baseline = median_filter(smooth_signal, size=baseline_window, mode="nearest")
        local_mad = median_filter(
            np.abs(smooth_signal - baseline), size=baseline_window, mode="nearest"
        )
        threshold = baseline + np.maximum(0.5, 3 * 1.4826 * local_mad)
        above_baseline = smooth_signal > threshold

        regions = _contiguous_regions(above_baseline)
        merged = []
        for region_start, region_stop in regions:
            if merged and region_start - merged[-1][1] <= 3:
                merged[-1] = (merged[-1][0], region_stop)
            else:
                merged.append((region_start, region_stop))

        for region_start, region_stop in merged:
            duration_seconds = float(
                (times[start + region_stop - 1] - times[start + region_start])
                / np.timedelta64(1, "s")
            ) + 1
            if not 30 <= duration_seconds <= 90:
                continue

            region_slice = slice(start + region_start, start + region_stop)
            peak_index = region_slice.start + int(np.argmax(signal[region_slice]))
            local_slice = slice(max(start, region_slice.start - 120), min(stop, region_slice.stop + 120))
            local_reference = signal[local_slice]
            local_reference = local_reference[
                (np.arange(local_slice.start, local_slice.stop) < region_slice.start)
                | (np.arange(local_slice.start, local_slice.stop) >= region_slice.stop)
            ]
            baseline_flux = float(np.median(local_reference)) if local_reference.size else 0.0
            peak_flux = float(signal[peak_index])
            contrast = peak_flux / baseline_flux if baseline_flux > 0 else float("inf")

            spectrum = np.maximum(electron_flux[region_slice][:, energy_mask], 0)
            valid_spectrum = np.where(np.isfinite(spectrum), spectrum, 0)
            spectral_weight = np.sum(valid_spectrum * energy_widths[energy_mask], axis=1)
            mean_energy = np.divide(
                np.sum(
                    valid_spectrum
                    * energy_widths[energy_mask][np.newaxis, :]
                    * energies[energy_mask][np.newaxis, :],
                    axis=1,
                ),
                spectral_weight,
                out=np.full(len(spectral_weight), np.nan),
                where=spectral_weight > 0,
            )
            valid_energy_indices = np.flatnonzero(np.isfinite(mean_energy))
            if valid_energy_indices.size:
                energy_peak_index = valid_energy_indices[
                    np.argmax(mean_energy[valid_energy_indices])
                ]
                energy_peak = float(mean_energy[energy_peak_index])
                edge_count = max(1, len(mean_energy) // 5)
                edge_energy = float(
                    np.nanmedian(
                        np.concatenate((mean_energy[:edge_count], mean_energy[-edge_count:]))
                    )
                )
            else:
                energy_peak = float("nan")
                edge_energy = float("nan")
            latitudes = latitude[region_slice]

            candidates.append({
                "ciclo": cycle_index,
                "inicio": str(times[region_slice.start]),
                "fin": str(times[region_slice.stop - 1]),
                "duracion_s": round(duration_seconds, 1),
                "latitud_aacgm_min": round(float(np.nanmin(latitudes)), 2),
                "latitud_aacgm_max": round(float(np.nanmax(latitudes)), 2),
                "flujo_pico_ev_cm2_s_sr": peak_flux,
                "contraste_local": round(contrast, 2),
                "energia_media_pico_kev": round(energy_peak / 1000, 2),
                "energia_borde_kev": round(edge_energy / 1000, 2),
                "energia_aumenta_al_centro": bool(
                    np.isfinite(energy_peak)
                    and np.isfinite(edge_energy)
                    and energy_peak > edge_energy
                ),
            })

    return candidates, cycles


def generar_espectrogramas(archivo_cdf):
    """Carga un CDF y genera espectrogramas."""
    if not os.path.isfile(archivo_cdf):
        raise FileNotFoundError(f"No se encontró el archivo CDF: {archivo_cdf}")

    datos = cargar_datos_cdf(archivo_cdf)
    tiempos = datos["tiempo_final"]
    energias = datos["CHANNEL_ENERGIES"]
    tiempo_local = datos["SC_AACGM_LTIME"]
    if tiempo_local is None:
        raise ValueError(
            "El CDF no incluye SC_AACGM_LTIME; no es posible filtrar por MLT."
        )

    latitud = np.asarray(datos["SC_AACGM_LAT"], dtype=float)
    tiempo_local = np.asarray(tiempo_local, dtype=float)
    electrones = np.asarray(datos["ELE_DIFF_ENERGY_FLUX"], dtype=float)
    energias = np.asarray(energias, dtype=float)
    candidatos, ciclos = _detect_candidates(
        np.asarray(tiempos),
        latitud,
        tiempo_local,
        electrones,
        energias,
    )

    return {
        "puntos_totales": len(tiempos),
        "puntos_mlt": int(((tiempo_local >= 12) & (tiempo_local < 24)).sum()),
        "canales": int((energias >= 30).sum()),
        "candidatos": candidatos,
        "ciclos": ciclos,
        "datos_grafico": {
            "tiempos": np.asarray(tiempos),
            "energias": energias,
            "electrones": electrones,
            "iones": np.asarray(datos["ION_DIFF_ENERGY_FLUX"], dtype=float),
            "mlt": tiempo_local,
        },
        "energia_minima_ev": 200,
        "energia_minima_grafico_ev": 30,
        "mlt_inicio": 12,
        "mlt_fin": 24,
        "archivo": archivo_cdf,
    }


def graficar_ciclo(resultado_scan, ciclo):
    """Genera espectrogramas limitados a una pasada/ciclo seleccionada."""
    datos = resultado_scan["datos_grafico"]
    start = ciclo["indice_inicio"]
    stop = ciclo["indice_fin"]
    candidatos = [
        candidato
        for candidato in resultado_scan["candidatos"]
        if candidato["ciclo"] == ciclo["ciclo"]
    ]
    return graficar_espectrogramas(
        datos["tiempos"][start:stop],
        datos["energias"],
        datos["electrones"][start:stop],
        datos["iones"][start:stop],
        datos["mlt"][start:stop],
        candidatos=candidatos,
        energia_minima=resultado_scan["energia_minima_grafico_ev"],
        mlt_inicio=resultado_scan["mlt_inicio"],
        mlt_fin=resultado_scan["mlt_fin"],
    )