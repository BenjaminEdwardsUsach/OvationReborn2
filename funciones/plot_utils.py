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

    def plot_spectrogram(ax, spec, title, segment, boundaries, particle_type='both'):
        """Grafica espectrogramas con SEGMENTO COMPLETO y fronteras
        particle_type: 'ion', 'ele' o 'both' para filtrar fronteras"""
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
            
            # Función auxiliar para filtrar fronteras según tipo de partícula
            def should_show_boundary(boundary_name, p_type):
                if p_type == 'both':
                    return True
                elif p_type == 'ion':
                    # Mostrar solo fronteras de iones (sufijo 'i')
                    return boundary_name.endswith('i') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                elif p_type == 'ele':
                    # Mostrar solo fronteras de electrones (sufijo 'e')
                    return boundary_name.endswith('e') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                return False
            
            # Añadir líneas verticales para las fronteras SOBRE el espectrograma completo
            for b_name, b_data in boundaries.items():
                if should_show_boundary(b_name, particle_type):
                    if (b_data is not None and b_data['index'] is not None and 
                        b_data['index'] < len(time_python)):
                        b_time = time_num[b_data['index']]
                        ax.axvline(b_time, color=boundary_colors.get(b_name, 'white'), 
                                linestyle='--', linewidth=2.0, alpha=0.8)
                        # Etiquetar la frontera
                        ax.text(b_time, energy_edges[-2], b_name, 
                               color=boundary_colors.get(b_name, 'white'), fontsize=8,
                               bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
            
            # Añadir colorbar con etiqueta de unidades
            plt.colorbar(im, ax=ax, label='Flujo Diferencial [eV/cm²/ΔeV/ster/s]')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title)

    def plot_flux(ax, segment, boundaries, flux_key, title, particle_type='both'):
        """Grafica flujos con SEGMENTO COMPLETO y fronteras
        particle_type: 'ion', 'ele' o 'both' para filtrar fronteras"""
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
            
            # Graficar FLUJO COMPLETO CON PUNTOS EN LUGAR DE LÍNEAS
            ax.scatter(time_python, flux_data, color='blue', s=30, label='Flujo integrado', alpha=0.6, marker='o')
            ax.set_title(title, fontsize=10, pad=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylabel('Log Flujo Total [eV/cm²/ster/s]')
            
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
            
            # Función auxiliar para filtrar fronteras según tipo de partícula
            def should_show_boundary(boundary_name, p_type):
                if p_type == 'both':
                    return True
                elif p_type == 'ion':
                    # Mostrar solo fronteras de iones (sufijo 'i')
                    return boundary_name.endswith('i') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                elif p_type == 'ele':
                    # Mostrar solo fronteras de electrones (sufijo 'e')
                    return boundary_name.endswith('e') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                return False
            
            # Añadir líneas verticales para las fronteras SOBRE el flujo completo
            for b_name, b_data in boundaries.items():
                if should_show_boundary(b_name, particle_type):
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
        plot_spectrogram(axs[0,0], spec1_ion, 'Espectrograma de Iones - Segmento Norte\n[eV/cm²/ΔeV/ster/s]', seg1, boundaries1, particle_type='ion')
        plot_spectrogram(axs[1,0], spec1_ele, 'Espectrograma de Electrones - Segmento Norte\n[eV/cm²/ΔeV/ster/s]', seg1, boundaries1, particle_type='ele')
        plot_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo Integrado de Iones - Norte [eV/cm²/ster/s]', particle_type='ion')
        plot_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo Integrado de Electrones - Norte [eV/cm²/ster/s]', particle_type='ele')
    else:
        for i in range(4):
            axs[i,0].text(0.5, 0.5, 'Segmento Norte vacío', transform=axs[i,0].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,0].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Segmento Norte')

    # --- Segmento 2 (Sur) ---
    if seg2 is not None and not seg2_empty:
        plot_spectrogram(axs[0,1], spec2_ion, 'Espectrograma de Iones - Segmento Sur\n[eV/cm²/ΔeV/ster/s]', seg2, boundaries2_adj, particle_type='ion')
        plot_spectrogram(axs[1,1], spec2_ele, 'Espectrograma de Electrones - Segmento Sur\n[eV/cm²/ΔeV/ster/s]', seg2, boundaries2_adj, particle_type='ele')
        plot_flux(axs[2,1], seg2, boundaries2_adj, flux_key='flux_ion', title='Flujo Integrado de Iones - Sur [eV/cm²/ster/s]', particle_type='ion')
        plot_flux(axs[3,1], seg2, boundaries2_adj, flux_key='flux_ele', title='Flujo Integrado de Electrones - Sur [eV/cm²/ster/s]', particle_type='ele')
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

    def plot_polar_spectrogram(ax, spec, title, segment, boundaries, particle_type='both'):
        """CORRECCIÓN COMPLETA: Dimensiones compatibles para pcolormesh
        particle_type: 'ion', 'ele' o 'both' para filtrar fronteras"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return
        
        if spec.size == 0 or spec.shape[1] == 0:
            ax.text(0.5, 0.5, 'Espectrograma vacío', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return

        try:
            # Dimensiones del espectrograma
            n_energy, n_time = spec.shape

            # Bordes angulares para pcolormesh (n_time+1) y centros (n_time)
            theta_edges = np.linspace(0, 2 * np.pi, n_time + 1, endpoint=True)
            theta_centers = 0.5 * (theta_edges[:-1] + theta_edges[1:])

            # Bordes radiales: esperamos que `energy_edges` tenga longitud n_energy+1
            if len(energy_edges) == n_energy + 1:
                r_edges = energy_edges
            else:
                # Si nos pasan energías en lugar de bordes, construir bordes por promedios
                energies = np.asarray(energy_edges[:n_energy])
                r_edges = np.concatenate(( [energies[0] - (energies[1]-energies[0])/2],
                                           (energies[:-1] + energies[1:]) / 2,
                                           [energies[-1] + (energies[-1]-energies[-2])/2] ))

            # Crear mallas de bordes para pcolormesh
            theta_grid, r_grid = np.meshgrid(theta_edges, r_edges)

            # pcolormesh con bordes asegura que los bins y las líneas coincidan con los centros
            im = ax.pcolormesh(theta_grid, r_grid, spec, norm=LogNorm(), shading='auto', cmap='viridis')
            ax.set_yscale('log')

            ax.set_title(title, pad=20)
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            ax.grid(True, alpha=0.3)

            # Función auxiliar para filtrar fronteras según tipo de partícula
            def should_show_boundary(boundary_name, p_type):
                if p_type == 'both':
                    return True
                elif p_type == 'ion':
                    # Mostrar solo fronteras de iones (sufijo 'i')
                    return boundary_name.endswith('i') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                elif p_type == 'ele':
                    # Mostrar solo fronteras de electrones (sufijo 'e')
                    return boundary_name.endswith('e') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                return False

            # Añadir líneas para las fronteras usando los centros angulares
            for b_name, b_data in boundaries.items():
                if should_show_boundary(b_name, particle_type):
                    if (b_data is not None and b_data['index'] is not None and 
                        b_data['index'] < n_time):
                        b_theta = theta_centers[b_data['index']]
                        ax.axvline(b_theta, color=boundary_colors.get(b_name, 'gray'), 
                                  linestyle='--', linewidth=2.0, alpha=0.8)

            # Añadir barra de color
            if 'im' in locals():
                plt.colorbar(im, ax=ax, shrink=0.8, pad=0.05, label='Flujo Diferencial')

        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, 
                   ha='center', va='center', fontsize=10)
            ax.set_title(title, pad=20)

    def plot_polar_flux(ax, segment, boundaries, flux_key, title, particle_type='both'):
        """Grafica flujos en coordenadas polares: MLT (ángulo) vs LAT (radio) con flujo integrado (color)
        particle_type: 'ion', 'ele' o 'both' para filtrar fronteras"""
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return
        
        if flux_key not in segment or len(segment[flux_key]) == 0:
            ax.text(0.5, 0.5, f'No hay datos de {flux_key}', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title, pad=20)
            return

        try:
            # Verificar si tenemos MLT y LAT disponibles
            if 'mlt' not in segment or len(segment['mlt']) == 0:
                ax.text(0.5, 0.5, 'No hay datos de MLT disponibles', transform=ax.transAxes, ha='center', va='center', fontsize=12)
                ax.set_title(title, pad=20)
                return
            
            if 'lat' not in segment or len(segment['lat']) == 0:
                ax.text(0.5, 0.5, 'No hay datos de LAT disponibles', transform=ax.transAxes, ha='center', va='center', fontsize=12)
                ax.set_title(title, pad=20)
                return

            mlt = np.asarray(segment['mlt'])
            lat = np.asarray(segment['lat'])
            flux = np.asarray(segment[flux_key])

            # Convertir MLT (0-24 horas) a ángulo (radianes: 0-2π)
            # 0 MLT = norte (π/2), 6 MLT = dusk (π), 12 MLT = sur (3π/2), 18 MLT = dawn (0)
            theta = (mlt / 24.0) * 2 * np.pi
            
            # Normalizar LAT para usarlo como radio
            # Los valores van típicamente de -90 a 90, normalizamos a 0-1
            lat_clean = np.nan_to_num(lat, nan=0.0)
            lat_normalized = (lat_clean + 90) / 180.0  # Rango [0, 1]
            lat_normalized = np.clip(lat_normalized, 0.01, 1.0)  # Mínimo radio para visualización
            
            # Normalizar el flujo para el color
            flux_clean = np.nan_to_num(flux, nan=1e-15)
            flux_clean = np.maximum(flux_clean, 1e-15)
            
            # Usar escala logarítmica para el flujo
            flux_log = np.log10(flux_clean)
            
            # Normalizar el flujo logarítmico para colormap
            flux_min = np.percentile(flux_log[flux_log > -np.inf], 5) if np.any(flux_log > -np.inf) else -10
            flux_max = np.percentile(flux_log[flux_log > -np.inf], 95) if np.any(flux_log > -np.inf) else 0
            flux_normalized = (flux_log - flux_min) / (flux_max - flux_min + 1e-10)
            flux_normalized = np.clip(flux_normalized, 0, 1)

            # Graficar scatter plot en coordenadas polares con color = flujo
            scatter = ax.scatter(theta, lat_normalized, c=flux_normalized, s=100, cmap='viridis', 
                               alpha=0.7, edgecolors='black', linewidth=0.5)
            
            # Añadir barra de color
            cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
            cbar.set_label('Flujo Integrado (log)', rotation=270, labelpad=20, fontsize=9)

            ax.set_title(title, pad=20)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 1.0)

            # Configurar etiquetas radiales como latitudes
            ax.set_rgrids([0.25, 0.5, 0.75, 1.0], labels=['65°', '45°', '25°', '90°'], fontsize=9)
            
            # Configurar etiquetas angulares como MLT
            ax.set_xticks(np.linspace(0, 2*np.pi, 24, endpoint=False))
            ax.set_xticklabels([f'{i:02d}' for i in range(24)], fontsize=8)
            ax.set_xlabel('MLT', fontsize=10, labelpad=30)

            # Añadir líneas para las fronteras
            # Función auxiliar para filtrar fronteras según tipo de partícula
            def should_show_boundary(boundary_name, p_type):
                if p_type == 'both':
                    return True
                elif p_type == 'ion':
                    # Mostrar solo fronteras de iones (sufijo 'i')
                    return boundary_name.endswith('i') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                elif p_type == 'ele':
                    # Mostrar solo fronteras de electrones (sufijo 'e')
                    return boundary_name.endswith('e') or boundary_name in ['b4s', 'b3a', 'b3b', 'b6']
                return False
            
            for b_name, b_data in boundaries.items():
                if should_show_boundary(b_name, particle_type):
                    if (b_data is not None and b_data.get('index') is not None):
                        b_index = b_data['index']
                        if b_index < len(theta):
                            b_theta = theta[b_index]
                            b_lat = lat_normalized[b_index]
                            # Marcar la frontera con una línea radial
                            ax.plot([b_theta, b_theta], [0, b_lat], 
                                   color=boundary_colors.get(b_name, 'gray'),
                                   linestyle='--', linewidth=2.0, alpha=0.8, label=b_name)

            # Configurar polar
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)
            
        except Exception as e:
            import traceback
            print(f"Error en plot_polar_flux: {e}")
            traceback.print_exc()
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title, pad=20)

    # --- Segmento 1 (Norte) ---
    if not seg1_empty:
        plot_polar_spectrogram(axs[0,0], spec1_ion, 'Espectrograma Iones - Seg1 (Norte) - Polar', seg1, boundaries1, particle_type='ion')
        plot_polar_spectrogram(axs[1,0], spec1_ele, 'Espectrograma Electrones - Seg1 (Norte) - Polar', seg1, boundaries1, particle_type='ele')
        plot_polar_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo Iones - Seg1 (Norte) - Polar', particle_type='ion')
        plot_polar_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo Electrones - Seg1 (Norte) - Polar', particle_type='ele')
    else:
        for i in range(4):
            axs[i,0].text(0.5, 0.5, 'Segmento Norte vacío', transform=axs[i,0].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,0].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Seg1 (Norte) - Polar', pad=20)

    # --- Segmento 2 (Sur) ---
    if not unidad and seg2 is not None and not seg2_empty:
        plot_polar_spectrogram(axs[0,1], spec2_ion, 'Espectrograma Iones - Seg2 (Sur) - Polar', seg2, boundaries2_adj, particle_type='ion')
        plot_polar_spectrogram(axs[1,1], spec2_ele, 'Espectrograma Electrones - Seg2 (Sur) - Polar', seg2, boundaries2_adj, particle_type='ele')
        plot_polar_flux(axs[2,1], seg2, boundaries2_adj, flux_key='flux_ion', title='Flujo Iones - Seg2 (Sur) - Polar', particle_type='ion')
        plot_polar_flux(axs[3,1], seg2, boundaries2_adj, flux_key='flux_ele', title='Flujo Electrones - Seg2 (Sur) - Polar', particle_type='ele')
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