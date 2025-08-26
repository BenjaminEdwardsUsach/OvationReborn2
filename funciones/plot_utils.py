import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from matplotlib.font_manager import FontProperties
from datetime import datetime

def plot_cycle(seg1, seg2, boundaries1, boundaries2, 
               spec1_ion, spec2_ion, spec1_ele, spec2_ele,
               energy_edges, main_folder, cycle_index):
    """Grafica completa con todas las fronteras detectadas, separando flujos de iones y electrones"""
    # Configuración de colores para fronteras
    boundary_colors = {
        'b1e': 'cyan', 'b2e': 'magenta', 'b2i': 'yellow',
        'b3a': 'lime', 'b3b': 'green', 'b4s': 'orange',
        'b5e': 'red', 'b5i': 'pink', 'b6': 'brown'
    }
    # Crear figura 5x2 (espec ion, espec ele, flux ion, flux ele, resumen)
    fig, axs = plt.subplots(5, 2, figsize=(20, 22), constrained_layout=True)
    
    # Desactivar último panel derecho (resumen solo en col 0)
    axs[4,1].axis('off')
    
    # Fuente monoespaciada para el resumen
    mono_font = FontProperties(family='monospace')

    # Función para convertir numpy.datetime64 a datetime
    def to_datetime(np_datetime):
        """Convierte numpy.datetime64 a datetime.datetime"""
        ts = (np_datetime - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
        return datetime.utcfromtimestamp(ts)

    # Definir plot_spectrogram con acceso a boundaries1 y boundaries2
    def plot_spectrogram(ax, spec, title, segment, boundaries):
        """Función para graficar espectrogramas con fronteras"""
        time_num = mdates.date2num(segment['time'])
        T = np.linspace(time_num.min(), time_num.max(), len(segment['time']) + 1)
        X, Y = np.meshgrid(T, energy_edges)
        ax.pcolormesh(X, Y, spec, norm=LogNorm(), shading='flat')
        ax.set_yscale('log')
        ax.set_title(title)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Añadir líneas verticales para las fronteras
        for b_name, b_data in boundaries.items():
            if b_data is not None and b_data['index'] is not None and b_data['index'] < len(segment['time']):
                b_time = time_num[b_data['index']]
                ax.axvline(b_time, color=boundary_colors.get(b_name, 'gray'), 
                        linestyle='--', linewidth=1.0)

    # En plot_utils.py, modificar la función plot_flux
    def plot_flux(ax, segment, boundaries, flux_key, title):
        """Función para graficar flujos con fronteras"""
        time = segment['time']
        ax.plot(time, segment[flux_key], 'b-', label='Flujo integrado')
        ax.set_title(title)
        ax.grid(True)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Añadir líneas verticales para las fronteras
        for b_name, b_data in boundaries.items():
            if b_data is not None and b_data['index'] is not None and b_data['index'] < len(time):
                b_time = time[b_data['index']]
                ax.axvline(b_time, color=boundary_colors.get(b_name, 'gray'),
                        linestyle='--', linewidth=1.5, label=b_name)
        
        # Solo añadir leyenda una vez
        if flux_key == 'flux_ele':
            ax.legend(loc='upper right', fontsize=8, ncol=3)

    # --- Segmento 1 (Norte) ---
    plot_spectrogram(axs[0,0], spec1_ion, 'Espectrograma de iones - Seg1 (Norte)', seg1, boundaries1)
    plot_spectrogram(axs[1,0], spec1_ele, 'Espectrograma de electrones - Seg1 (Norte)', seg1, boundaries1)
    plot_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo iones - Seg1 (Norte)')
    plot_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo electrones - Seg1 (Norte)')

    # --- Segmento 2 (Sur) ---
    plot_spectrogram(axs[0,1], spec2_ion, 'Espectrograma de iones - Seg2 (Sur)', seg2, boundaries2)
    plot_spectrogram(axs[1,1], spec2_ele, 'Espectrograma de electrones - Seg2 (Sur)', seg2, boundaries2)
    plot_flux(axs[2,1], seg2, boundaries2, flux_key='flux_ion', title='Flujo iones - Seg2 (Sur)')
    plot_flux(axs[3,1], seg2, boundaries2, flux_key='flux_ele', title='Flujo electrones - Seg2 (Sur)')

    # Panel de resumen
    ax_summary = axs[4,0]
    ax_summary.axis('off')

    # Crear texto de resumen con formato
    summary_text = "Fronteras detectadas (Norte):\n"
    for b_name, b in boundaries1.items():
        if b is not None and b['index'] is not None and b['index'] < len(seg1['time']):
            t = seg1['time'][b['index']]
            # Convertir numpy.datetime64 a datetime
            t_datetime = to_datetime(t) if isinstance(t, np.datetime64) else t
            t_str = t_datetime.strftime('%H:%M:%S')
            lat = seg1['lat'][b['index']]
            dev = b.get('deviation', 0)
            params = b.get('params', {})
            
            # Resaltar fronteras con ajustes
            if dev > 0:
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}° (dev: {dev:.1f}, params: {param_str})\n"
            else:
                summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}°\n"
        else:
            summary_text += f"• {b_name}: No detectada\n"

    summary_text += "\nFronteras detectadas (Sur):\n"
    for b_name, b in boundaries2.items():
        if b is not None and b['index'] is not None and b['index'] < len(seg2['time']):
            t = seg2['time'][b['index']]
            # Convertir numpy.datetime64 a datetime
            t_datetime = to_datetime(t) if isinstance(t, np.datetime64) else t
            t_str = t_datetime.strftime('%H:%M:%S')
            lat = seg2['lat'][b['index']]
            dev = b.get('deviation', 0)
            params = b.get('params', {})
            
            if dev > 0:
                param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}° (dev: {dev:.1f}, params: {param_str})\n"
            else:
                summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}°\n"
        else:
            summary_text += f"• {b_name}: No detectada\n"
    
    # Usar texto monoespaciado y mantener formato
    ax_summary.text(0.05, 0.95, summary_text, fontproperties=mono_font, 
                   verticalalignment='top', transform=ax_summary.transAxes,
                   bbox=dict(facecolor='whitesmoke', alpha=0.8, pad=10))

    # Asegurar mismos límites temporales para cada segmento
    for i in range(4):
        # Segmento norte
        axs[i,0].set_xlim(seg1['time'][0], seg1['time'][-1])
        
        # Segmento sur
        axs[i,1].set_xlim(seg2['time'][0], seg2['time'][-1])

    # Guardar
    folder = os.path.join(main_folder, f'cycle_{cycle_index}')
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f'cycle{cycle_index}_full.png')
    plt.savefig(path, dpi=150)
    plt.close(fig)
    return path
