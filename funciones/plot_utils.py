# plot_utils.py - VERSIÓN CORREGIDA PARA numpy.datetime64
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from matplotlib.font_manager import FontProperties
from datetime import datetime

def convert_to_datetime(numpy_dt):
    """Convierte numpy.datetime64 a datetime de Python"""
    if isinstance(numpy_dt, np.datetime64):
        # Convertir a datetime de Python
        return numpy_dt.astype('datetime64[ms]').astype(datetime)
    elif isinstance(numpy_dt, datetime):
        return numpy_dt
    else:
        # Intentar conversión genérica
        try:
            return datetime.fromisoformat(str(numpy_dt))
        except:
            return datetime.now()

def plot_cycle(seg1, seg2, boundaries1, boundaries2, 
               spec1_ion, spec2_ion, spec1_ele, spec2_ele,
               energy_edges, main_folder, cycle_index):
    """Grafica completa mostrando SEGMENTOS COMPLETOS con fronteras superpuestas"""
    
    # Verificar si los segmentos están vacíos
    seg1_empty = len(seg1['time']) == 0 if seg1 is not None else True
    seg2_empty = len(seg2['time']) == 0 if seg2 is not None else True
    
    if seg1_empty and seg2_empty:
        return None

    # Configuración de colores para fronteras
    boundary_colors = {
        'b1e': 'cyan', 'b2e': 'magenta', 'b2i': 'yellow',
        'b3a': 'lime', 'b3b': 'green', 'b4s': 'orange',
        'b5e': 'red', 'b5i': 'pink', 'b6': 'brown'
    }
    
    # Ajustar índices de fronteras para el segmento 2
    boundaries2_adj = {}
    if boundaries2 and seg2 is not None and not seg2_empty:
        for b_name, b_data in boundaries2.items():
            if b_data and b_data['index'] is not None:
                original_idx = len(seg2['time']) - 1 - b_data['index']
                boundaries2_adj[b_name] = {
                    'index': original_idx,
                    'time': seg2['time'][original_idx],
                    'lat': seg2['lat'][original_idx],
                    'deviation': b_data.get('deviation', 0),
                    'params': b_data.get('params', {})
                }
            else:
                boundaries2_adj[b_name] = b_data
    else:
        boundaries2_adj = boundaries2

    # Crear figura 5x2
    fig, axs = plt.subplots(5, 2, figsize=(24, 25), constrained_layout=True)
    axs[4,1].axis('off')
    
    mono_font = FontProperties(family='monospace')

    def plot_spectrogram(ax, spec, title, segment, boundaries):
        """Grafica espectrogramas con SEGMENTO COMPLETO y fronteras"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return
        
        if spec.size == 0 or spec.shape[1] == 0:
            ax.text(0.5, 0.5, 'Espectrograma vacío', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return

        try:
            # Convertir tiempos a datetime de Python para matplotlib
            time_python = [convert_to_datetime(t) for t in segment['time']]
            time_num = mdates.date2num(time_python)
            
            # Usar TODOS los puntos del segmento
            T = np.linspace(time_num.min(), time_num.max(), len(time_python) + 1)
            X, Y = np.meshgrid(T, energy_edges)
            
            # Ajustar dimensiones si es necesario
            if spec.shape[1] != len(time_python):
                min_len = min(spec.shape[1], len(time_python))
                spec = spec[:, :min_len]
                time_num = time_num[:min_len]
                T = np.linspace(time_num.min(), time_num.max(), min_len + 1)
                X, Y = np.meshgrid(T, energy_edges)
            
            # Graficar ESPECTROGRAMA COMPLETO
            im = ax.pcolormesh(X, Y, spec, norm=LogNorm(), shading='flat', cmap='viridis')
            ax.set_yscale('log')
            ax.set_title(title, fontsize=10, pad=10)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            # Añadir líneas verticales para las fronteras SOBRE el espectrograma completo
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < len(time_python)):
                    b_time = time_num[b_data['index']]
                    ax.axvline(b_time, color=boundary_colors.get(b_name, 'white'), 
                            linestyle='--', linewidth=2.0, alpha=0.8)
                    # Etiquetar la frontera
                    ax.text(b_time, energy_edges[-2], b_name, 
                           color=boundary_colors.get(b_name, 'white'), fontsize=8,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
            
            # Añadir colorbar
            plt.colorbar(im, ax=ax, label='Flujo Diferencial (eV/cm²/sr/s/eV)')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title)

    def plot_flux(ax, segment, boundaries, flux_key, title):
        """Grafica flujos con SEGMENTO COMPLETO y fronteras"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return
        
        if flux_key not in segment or len(segment[flux_key]) == 0:
            ax.text(0.5, 0.5, f'No hay datos de {flux_key}', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return

        try:
            # Convertir tiempos a datetime de Python
            time_python = [convert_to_datetime(t) for t in segment['time']]
            flux_data = segment[flux_key]
            
            # Graficar FLUJO COMPLETO
            ax.plot(time_python, flux_data, 'b-', linewidth=1.5, label='Flujo integrado', alpha=0.8)
            ax.set_title(title, fontsize=10, pad=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylabel('Log Flux')
            
            # Configurar ticks temporales para mostrar todo el segmento
            if len(time_python) > 0:
                ax.set_xlim(time_python[0], time_python[-1])
                
                # Seleccionar 4-6 puntos temporales para etiquetas
                if len(time_python) > 6:
                    tick_indices = np.linspace(0, len(time_python)-1, 6, dtype=int)
                else:
                    tick_indices = range(len(time_python))
                
                tick_times = [time_python[i] for i in tick_indices]
                tick_labels = []
                
                for i, t in enumerate(tick_times):
                    idx = tick_indices[i]
                    aacgm_val = segment['coords_aacgm'][idx]
                    geo_val = segment['coords_geo'][idx] if 'coords_geo' in segment else segment['lat'][idx]
                    
                    if i == 0:  # Primera etiqueta
                        label = t.strftime('UT: %H:%M:%S') + f"\nAACGM: {aacgm_val:.1f}°\nGEO: {geo_val:.1f}°"
                    else:
                        label = t.strftime('%H:%M:%S') + f"\n{aacgm_val:.1f}°\n{geo_val:.1f}°"
                    
                    tick_labels.append(label)
                
                ax.set_xticks(tick_times)
                ax.set_xticklabels(tick_labels, rotation=0, ha='center', fontsize=8)
            
            # Añadir líneas verticales para las fronteras SOBRE el flujo completo
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < len(time_python)):
                    b_time = time_python[b_data['index']]
                    b_lat = segment['coords_aacgm'][b_data['index']]
                    
                    ax.axvline(b_time, color=boundary_colors.get(b_name, 'red'),
                            linestyle='--', linewidth=2.0, alpha=0.8, label=f'{b_name} ({b_lat:.1f}°)')
            
            # Solo añadir leyenda una vez
            if flux_key == 'flux_ele':
                ax.legend(loc='upper right', fontsize=8, ncol=2)
                
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title)

    # --- Segmento 1 (Norte) ---
    if not seg1_empty:
        plot_spectrogram(axs[0,0], spec1_ion, 'Espectrograma de Iones - Segmento Norte', seg1, boundaries1)
        plot_spectrogram(axs[1,0], spec1_ele, 'Espectrograma de Electrones - Segmento Norte', seg1, boundaries1)
        plot_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo Integrado de Iones - Norte')
        plot_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo Integrado de Electrones - Norte')
    else:
        for i in range(4):
            axs[i,0].text(0.5, 0.5, 'Segmento Norte vacío', transform=axs[i,0].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,0].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Segmento Norte')

    # --- Segmento 2 (Sur) ---
    if seg2 is not None and not seg2_empty:
        plot_spectrogram(axs[0,1], spec2_ion, 'Espectrograma de Iones - Segmento Sur', seg2, boundaries2_adj)
        plot_spectrogram(axs[1,1], spec2_ele, 'Espectrograma de Electrones - Segmento Sur', seg2, boundaries2_adj)
        plot_flux(axs[2,1], seg2, boundaries2_adj, flux_key='flux_ion', title='Flujo Integrado de Iones - Sur')
        plot_flux(axs[3,1], seg2, boundaries2_adj, flux_key='flux_ele', title='Flujo Integrado de Electrones - Sur')
    else:
        for i in range(4):
            axs[i,1].text(0.5, 0.5, 'Segmento Sur vacío', transform=axs[i,1].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,1].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Segmento Sur')

    # Panel de resumen 
    ax_summary = axs[4,0]
    ax_summary.axis('off')

    # Crear texto de resumen con formato 
    summary_text = f"RESUMEN CICLO {cycle_index}\n"
    summary_text += "="*50 + "\n"
    
    if not seg1_empty:
        summary_text += f"SEGMENTO NORTE: {len(seg1['time'])} puntos\n"
        summary_text += f"Dirección: {seg1.get('direccion_original', 'N/A')}\n"
        summary_text += "Fronteras detectadas:\n"
        
        for b_name, b in boundaries1.items():
            if b is not None and b['index'] is not None and b['index'] < len(seg1['time']):
                t = seg1['time'][b['index']]
                t_datetime = convert_to_datetime(t)
                t_str = t_datetime.strftime('%H:%M:%S')
                lat = seg1['lat'][b['index']]
                summary_text += f"  • {b_name}: {t_str}, lat={lat:.2f}°\n"
            else:
                summary_text += f"  • {b_name}: No detectada\n"
    else:
        summary_text += "SEGMENTO NORTE: Vacío\n"

    if seg2 is not None and not seg2_empty:
        summary_text += f"\nSEGMENTO SUR: {len(seg2['time'])} puntos\n"
        summary_text += f"Dirección: {seg2.get('direccion_original', 'N/A')}\n"
        summary_text += "Fronteras detectadas:\n"
        
        for b_name, b in boundaries2_adj.items():
            if b is not None and b['index'] is not None and b['index'] < len(seg2['time']):
                t = seg2['time'][b['index']]
                t_datetime = convert_to_datetime(t)
                t_str = t_datetime.strftime('%H:%M:%S')
                lat = seg2['lat'][b['index']]
                summary_text += f"  • {b_name}: {t_str}, lat={lat:.2f}°\n"
            else:
                summary_text += f"  • {b_name}: No detectada\n"
    else:
        summary_text += "\nSEGMENTO SUR: Vacío\n"
    
    # Usar texto monoespaciado
    ax_summary.text(0.02, 0.98, summary_text, fontproperties=mono_font, 
                   verticalalignment='top', transform=ax_summary.transAxes, fontsize=9,
                   bbox=dict(facecolor='lightgray', alpha=0.8, pad=10))

    # Guardar con alta resolución
    try:
        folder = os.path.join(main_folder, f'cycle_{cycle_index}')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f'cycle{cycle_index}_full.png')
        plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        return path
    except Exception:
        plt.close(fig)
        return None

# También actualizar plot_polar_cycle si es necesario (similar corrección)

def plot_polar_cycle(seg1, seg2, boundaries1, boundaries2, 
                    spec1_ion, spec2_ion, spec1_ele, spec2_ele,
                    energy_edges, main_folder, cycle_index, unidad=False):
    """Grafica polar completa - VERSIÓN CORREGIDA DIMENSIONES"""
    
    # Verificar si los segmentos están vacíos
    seg1_empty = len(seg1['time']) == 0 if seg1 is not None else True
    seg2_empty = len(seg2['time']) == 0 if seg2 is not None else True
    
    if seg1_empty and seg2_empty:
        return None
    
    # Configuración de colores para fronteras
    boundary_colors = {
        'b1e': 'cyan', 'b2e': 'magenta', 'b2i': 'yellow',
        'b3a': 'lime', 'b3b': 'green', 'b4s': 'orange',
        'b5e': 'red', 'b5i': 'pink', 'b6': 'brown'
    }
    
    # Ajustar índices de fronteras para el segmento 2
    boundaries2_adj = {}
    if boundaries2 and seg2 is not None and not seg2_empty:
        for b_name, b_data in boundaries2.items():
            if b_data and b_data['index'] is not None:
                original_idx = len(seg2['time']) - 1 - b_data['index']
                boundaries2_adj[b_name] = {
                    'index': original_idx,
                    'time': seg2['time'][original_idx],
                    'lat': seg2['lat'][original_idx],
                    'deviation': b_data.get('deviation', 0),
                    'params': b_data.get('params', {})
                }
            else:
                boundaries2_adj[b_name] = b_data
    else:
        boundaries2_adj = boundaries2

    # Crear figura polar 4x2
    fig, axs = plt.subplots(4, 2, figsize=(20, 18), 
                           subplot_kw=dict(projection='polar'),
                           constrained_layout=True)

    def plot_polar_spectrogram(ax, spec, title, segment, boundaries):
        """CORRECCIÓN COMPLETA: Dimensiones compatibles para pcolormesh"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return
        
        if spec.size == 0 or spec.shape[1] == 0:
            ax.text(0.5, 0.5, 'Espectrograma vacío', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return

        try:
            # DIAGNÓSTICO: Mostrar dimensiones
            n_energy, n_time = spec.shape
            
            theta = np.linspace(0, 2 * np.pi, n_time)
            r = energy_edges[:n_energy]  
            
            # Crear mallas 2D
            theta_grid, r_grid = np.meshgrid(theta, r)
            
            # Verificar compatibilidad de dimensiones
            if theta_grid.shape == spec.shape and r_grid.shape == spec.shape:
                im = ax.pcolormesh(theta_grid, r_grid, spec, norm=LogNorm(), shading='auto', cmap='viridis')
            else:
                im = ax.imshow(spec, extent=[0, 2*np.pi, energy_edges[-1], energy_edges[0]], 
                              aspect='auto', norm=LogNorm(), cmap='viridis')
                ax.set_yscale('log')
            
            ax.set_title(title, pad=20)
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.grid(True, alpha=0.3)
            
            # Añadir líneas para las fronteras
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < n_time):
                    b_theta = theta[b_data['index']] if b_data['index'] < len(theta) else theta[-1]
                    ax.axvline(b_theta, color=boundary_colors.get(b_name, 'gray'), 
                              linestyle='--', linewidth=2.0, alpha=0.8)
            
            # Añadir barra de color
            if 'im' in locals():
                plt.colorbar(im, ax=ax, shrink=0.8, pad=0.05, label='Flujo Diferencial')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=10)
            ax.set_title(title, pad=20)

    def plot_polar_flux(ax, segment, boundaries, flux_key, title):
        """Función para graficar flujos en coordenadas polares - MANTENIDO"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return
        
        if flux_key not in segment or len(segment[flux_key]) == 0:
            ax.text(0.5, 0.5, f'No hay datos de {flux_key}', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return

        try:
            times = segment['time']
            flux = segment[flux_key]
            
            # Convertir tiempo a ángulo
            n_time = len(times)
            theta = np.linspace(0, 2 * np.pi, n_time)
            
            # Normalizar el flujo para el radio
            flux_clean = np.nan_to_num(flux, nan=-10)
            flux_pos = np.maximum(flux_clean, -9)
            if np.max(flux_pos) > np.min(flux_pos):
                flux_normalized = 0.1 + 0.8 * (flux_pos - np.min(flux_pos)) / (np.max(flux_pos) - np.min(flux_pos))
            else:
                flux_normalized = np.ones_like(flux_pos) * 0.5
            
            # Graficar flujo polar
            ax.plot(theta, flux_normalized, 'b-', linewidth=2, label='Flujo')
            ax.fill_between(theta, 0.1, flux_normalized, alpha=0.3, color='blue')
            
            ax.set_title(title, pad=20)
            ax.grid(True, alpha=0.3)
            
            # Añadir líneas para las fronteras
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < n_time):
                    b_theta = theta[b_data['index']]
                    ax.axvline(b_theta, color=boundary_colors.get(b_name, 'gray'),
                              linestyle='--', linewidth=2.0, alpha=0.8, label=b_name)
            
            # Configurar polar
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.set_ylim(0, 1)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title, pad=20)

    # --- Segmento 1 (Norte) ---
    if not seg1_empty:
        plot_polar_spectrogram(axs[0,0], spec1_ion, 'Espectrograma Iones - Seg1 (Norte) - Polar', seg1, boundaries1)
        plot_polar_spectrogram(axs[1,0], spec1_ele, 'Espectrograma Electrones - Seg1 (Norte) - Polar', seg1, boundaries1)
        plot_polar_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo Iones - Seg1 (Norte) - Polar')
        plot_polar_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo Electrones - Seg1 (Norte) - Polar')
    else:
        for i in range(4):
            axs[i,0].text(0.5, 0.5, 'Segmento Norte vacío', transform=axs[i,0].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,0].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Seg1 (Norte) - Polar', pad=20)

    # --- Segmento 2 (Sur) ---
    if not unidad and seg2 is not None and not seg2_empty:
        plot_polar_spectrogram(axs[0,1], spec2_ion, 'Espectrograma Iones - Seg2 (Sur) - Polar', seg2, boundaries2_adj)
        plot_polar_spectrogram(axs[1,1], spec2_ele, 'Espectrograma Electrones - Seg2 (Sur) - Polar', seg2, boundaries2_adj)
        plot_polar_flux(axs[2,1], seg2, boundaries2_adj, flux_key='flux_ion', title='Flujo Iones - Seg2 (Sur) - Polar')
        plot_polar_flux(axs[3,1], seg2, boundaries2_adj, flux_key='flux_ele', title='Flujo Electrones - Seg2 (Sur) - Polar')
    else:
        for i in range(4):
            axs[i,1].text(0.5, 0.5, 'Segmento Sur vacío', transform=axs[i,1].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,1].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Seg2 (Sur) - Polar', pad=20)

    # Guardar gráfico polar
    try:
        folder = os.path.join(main_folder, f'cycle_{cycle_index}')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f'cycle{cycle_index}_polar.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path
    except Exception:
        plt.close(fig)
        return None