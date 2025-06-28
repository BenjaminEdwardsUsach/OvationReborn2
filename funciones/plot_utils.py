import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedLocator


def plot_cycle(
    seg1,
    seg2,
    cand1,
    cand2,
    spec1,
    spec2,
    energy_edges,
    main_folder,
    cycle_index
):
    """
    Genera y guarda una figura 2x2 para cada ciclo:
     - Espectrograma seg1 usando spec1
     - Flujo integrado seg1 con etiquetas de seg1
     - Espectrograma seg2 usando spec2
     - Flujo integrado seg2 con etiquetas de seg2

    Parámetros:
      seg1, seg2: dict con claves 'time', 'flux', 'coords_aacgm', 'coords_geo'
      cand1, cand2: dict con 't_candidate', 'flux_candidate'
      spec1, spec2: 2D arrays (E×T) para cada mitad
      energy_edges: 1D array (E+1)
      main_folder: carpeta base
      cycle_index: índice del ciclo
    """
    # Extraer datos y pasar a numpy
    ts1 = np.array(seg1['time'])
    fs1 = np.array(seg1['flux'])
    ca1 = np.array(seg1['coords_aacgm'])
    cg1 = np.array(seg1['coords_geo'])

    ts2 = np.array(seg2['time'])
    fs2 = np.array(seg2['flux'])
    ca2 = np.array(seg2['coords_aacgm'])
    cg2 = np.array(seg2['coords_geo'])

    # Candidatos
    t1 = cand1['t_candidate']
    f1 = cand1['flux_candidate']
    t2 = cand2['t_candidate']
    f2 = cand2['flux_candidate']

    # Convertir tiempos a floats Matplotlib
    ts1_num = mdates.date2num(ts1)
    ts2_num = mdates.date2num(ts2)

    # Formateador
    fmt = mdates.DateFormatter('%H:%M:%S')

    # Crear figura y ejes
    fig, axs = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
    ax_spec1, ax_spec2 = axs[0, 0], axs[0, 1]
    ax_flux1, ax_flux2 = axs[1, 0], axs[1, 1]

    # --- Espectrograma seg1 ---
    # Ajustamos T1 para que coincida con energy_edges tamaño E+1
    T1 = np.linspace(ts1_num.min(), ts1_num.max(), spec1.shape[1] + 1)
    X1, Y1 = np.meshgrid(T1, energy_edges)
    pcm1 = ax_spec1.pcolormesh(
        X1, Y1, spec1,
        norm=plt.matplotlib.colors.LogNorm(), shading='flat'
    )
    ax_spec1.set_yscale('log')
    ax_spec1.set_title(f'Spectrogram seg1 - Cycle {cycle_index}')
    ax_spec1.set_ylabel('Energy (eV)')
    ax_spec1.xaxis_date(); ax_spec1.xaxis.set_major_formatter(fmt)
    fig.colorbar(pcm1, ax=ax_spec1, label='Flux')

    # --- Flujo integrado seg1 ---
    ax_flux1.scatter(ts1, fs1, label='Integrated Flux seg1')
    ax_flux1.set_title(f'Cycle {cycle_index} seg1')
    ax_flux1.set_ylabel('Integrated Flux')
    ax_flux1.axvline(t1, color='red', linestyle='--', label=f'Cand: {f1:.2f}')
    ax_flux1.legend(); ax_flux1.grid(True)
    ax_flux1.xaxis_date(); ax_flux1.xaxis.set_major_formatter(fmt)
    # Etiquetas personalizadas seg1
    locs1 = ax_flux1.get_xticks()
    labels1 = []
    for i, loc in enumerate(locs1):
        dt = mdates.num2date(loc)
        idx = np.argmin(np.abs(ts1_num - loc))
        prefix = 'UT: ' + dt.strftime('%H:%M:%S') if i == 0 else dt.strftime('%H:%M:%S')
        labels1.append(f"{prefix}\nAACGM: {ca1[idx]:.1f}\nGEO: {cg1[idx]:.1f}")
    ax_flux1.xaxis.set_major_locator(FixedLocator(locs1))
    ax_flux1.set_xticklabels(labels1, rotation=0, ha='center')

    # --- Espectrograma seg2 ---
    # Ajustamos T2 de igual forma
    T2 = np.linspace(ts2_num.min(), ts2_num.max(), spec2.shape[1] + 1)
    X2, Y2 = np.meshgrid(T2, energy_edges)
    pcm2 = ax_spec2.pcolormesh(
        X2, Y2, spec2,
        norm=plt.matplotlib.colors.LogNorm(), shading='flat'
    )
    ax_spec2.set_yscale('log')
    ax_spec2.set_title(f'Spectrogram seg2 - Cycle {cycle_index}')
    ax_spec2.set_ylabel('Energy (eV)')
    ax_spec2.xaxis_date(); ax_spec2.xaxis.set_major_formatter(fmt)
    fig.colorbar(pcm2, ax=ax_spec2, label='Flux')

    # --- Flujo integrado seg2 ---
    ax_flux2.plot(ts2, fs2, label='Integrated Flux seg2')
    ax_flux2.set_title(f'Cycle {cycle_index} seg2')
    ax_flux2.set_ylabel('Integrated Flux')
    ax_flux2.axvline(t2, color='red', linestyle='--', label=f'Cand: {f2:.2f}')
    ax_flux2.legend(); ax_flux2.grid(True)
    ax_flux2.xaxis_date(); ax_flux2.xaxis.set_major_formatter(fmt)
    # Etiquetas personalizadas seg2
    locs2 = ax_flux2.get_xticks()
    labels2 = []
    for i, loc in enumerate(locs2):
        dt = mdates.num2date(loc)
        idx = np.argmin(np.abs(ts2_num - loc))
        prefix = 'UT: ' + dt.strftime('%H:%M:%S') if i == 0 else dt.strftime('%H:%M:%S')
        labels2.append(f"{prefix}\nAACGM: {ca2[idx]:.1f}\nGEO: {cg2[idx]:.1f}")
    ax_flux2.xaxis.set_major_locator(FixedLocator(locs2))
    ax_flux2.set_xticklabels(labels2, rotation=0, ha='center')

    # Guardar figura
    folder = os.path.join(main_folder, f'cycle_{cycle_index}')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f'cycle{cycle_index}.png')
    plt.savefig(path)
    plt.close(fig)
    return path
