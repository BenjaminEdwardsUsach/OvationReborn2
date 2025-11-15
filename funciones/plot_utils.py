# plot_utils.py
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LogNorm
from matplotlib.font_manager import FontProperties
from datetime import datetime

# ✅ CORRECCIÓN: Eliminar parámetro 'unidad' no utilizado
def plot_cycle(seg1, seg2, boundaries1, boundaries2, 
               spec1_ion, spec2_ion, spec1_ele, spec2_ele,
               energy_edges, main_folder, cycle_index):  # ❌ QUITADO: unidad=False
    """Grafica completa con todas las fronteras detectadas - CON MANEJO DE ARRAYS VACÍOS"""
    
    # CORRECCIÓN: Verificar si los segmentos están vacíos
    seg1_empty = len(seg1['time']) == 0 if seg1 is not None else True
    seg2_empty = len(seg2['time']) == 0 if seg2 is not None else True
    
    if seg1_empty and seg2_empty:
        print(f"⚠️  Ciclo {cycle_index}: Ambos segmentos vacíos, no se puede graficar")
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
    fig, axs = plt.subplots(5, 2, figsize=(20, 22), constrained_layout=True)
    axs[4,1].axis('off')
    
    mono_font = FontProperties(family='monospace')

    # Función para convertir numpy.datetime64 a datetime
    def to_datetime(np_datetime):
        """Convierte numpy.datetime64 a datetime.datetime sin warnings"""
        if isinstance(np_datetime, np.datetime64):
            ts = (np_datetime - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's')
            return datetime.utcfromtimestamp(ts)
        elif isinstance(np_datetime, datetime):
            return np_datetime
        else:
            try:
                return datetime.fromisoformat(str(np_datetime))
            except:
                return datetime.now()

    def plot_spectrogram(ax, spec, title, segment, boundaries):
        """Función para graficar espectrogramas con fronteras - CON VERIFICACIÓN DE VACÍO"""
        # CORRECCIÓN: Verificar si el segmento está vacío
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return
        
        # CORRECCIÓN: Verificar si el espectrograma está vacío
        if spec.size == 0 or spec.shape[1] == 0:
            ax.text(0.5, 0.5, 'Espectrograma vacío', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return

        try:
            time_num = mdates.date2num(segment['time'])
            
            # CORRECCIÓN: Verificar que time_num no esté vacío
            if len(time_num) == 0:
                ax.text(0.5, 0.5, 'No hay datos temporales', transform=ax.transAxes, ha='center', va='center', fontsize=12)
                ax.set_title(title)
                return
                
            T = np.linspace(time_num.min(), time_num.max(), len(segment['time']) + 1)
            X, Y = np.meshgrid(T, energy_edges)
            
            # CORRECCIÓN: Verificar dimensiones del espectrograma
            if spec.shape[1] != len(segment['time']):
                print(f"⚠️  Dimensiones no coinciden: spec {spec.shape} vs time {len(segment['time'])}")
                # Ajustar spec si es necesario
                min_len = min(spec.shape[1], len(segment['time']))
                spec = spec[:, :min_len]
                time_num = time_num[:min_len]
                T = np.linspace(time_num.min(), time_num.max(), min_len + 1)
                X, Y = np.meshgrid(T, energy_edges)
            
            ax.pcolormesh(X, Y, spec, norm=LogNorm(), shading='flat')
            ax.set_yscale('log')
            ax.set_title(title)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            
            # Añadir líneas verticales para las fronteras
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < len(segment['time'])):
                    b_time = time_num[b_data['index']]
                    ax.axvline(b_time, color=boundary_colors.get(b_name, 'gray'), 
                            linestyle='--', linewidth=1.0)
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title)

    def plot_flux(ax, segment, boundaries, flux_key, title):
        """Función para graficar flujos con fronteras - CON VERIFICACIÓN DE VACÍO"""
        # CORRECCIÓN: Verificar si el segmento está vacío
        if len(segment['time']) == 0:
            ax.text(0.5, 0.5, 'Sin datos', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return
        
        # CORRECCIÓN: Verificar si existe el flujo
        if flux_key not in segment or len(segment[flux_key]) == 0:
            ax.text(0.5, 0.5, f'No hay datos de {flux_key}', transform=ax.transAxes, ha='center', va='center', fontsize=12)
            ax.set_title(title)
            return

        try:
            time = segment['time']
            ax.plot(time, segment[flux_key], 'b-', label='Flujo integrado')
            ax.set_title(title)
            ax.grid(True)
            
            # Personalizar ticks para mostrar UT, AACGM y GEO
            time_num = mdates.date2num(time)
            
            # Obtener ticks actuales y asegurar que estén dentro del rango de datos
            current_ticks = ax.get_xticks()
            valid_ticks = current_ticks[(current_ticks >= time_num[0]) & (current_ticks <= time_num[-1])]
            
            # Si no hay suficientes ticks, crear unos nuevos
            if len(valid_ticks) < 3:
                valid_ticks = np.linspace(time_num[0], time_num[-1], 4)
            
            new_labels = []
            for tick in valid_ticks:
                # Encontrar el índice más cercano
                idx = np.argmin(np.abs(time_num - tick))
                
                # Obtener valores de coordenadas
                aacgm_val = segment['coords_aacgm'][idx]
                geo_val = segment['coords_geo'][idx] if 'coords_geo' in segment else segment['lat'][idx]
                
                # Formatear etiqueta
                dt = mdates.num2date(tick)
                if tick == valid_ticks[0]:  # Primera etiqueta
                    label = dt.strftime('UT: %H:%M:%S') + f"\nAACGM: {aacgm_val:.2f}°\nGEO: {geo_val:.2f}°"
                else:
                    label = dt.strftime('%H:%M:%S') + f"\n{aacgm_val:.2f}°\n{geo_val:.2f}°"
                
                new_labels.append(label)
            
            # Establecer nuevos ticks y etiquetas
            ax.set_xticks(valid_ticks)
            ax.set_xticklabels(new_labels, rotation=0, ha='center')
            
            # Añadir líneas verticales para las fronteras
            for b_name, b_data in boundaries.items():
                if (b_data is not None and b_data['index'] is not None and 
                    b_data['index'] < len(time)):
                    b_time = time[b_data['index']]
                    ax.axvline(b_time, color=boundary_colors.get(b_name, 'gray'),
                            linestyle='--', linewidth=1.5, label=b_name)
            
            # Solo añadir leyenda una vez
            if flux_key == 'flux_ele':
                ax.legend(loc='upper right', fontsize=8, ncol=3)
                
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center', fontsize=10)
            ax.set_title(title)

    # --- Segmento 1 (Norte) ---
    if not seg1_empty:
        plot_spectrogram(axs[0,0], spec1_ion, 'Espectrograma de iones - Seg1 (Norte)', seg1, boundaries1)
        plot_spectrogram(axs[1,0], spec1_ele, 'Espectrograma de electrones - Seg1 (Norte)', seg1, boundaries1)
        plot_flux(axs[2,0], seg1, boundaries1, flux_key='flux_ion', title='Flujo iones - Seg1 (Norte)')
        plot_flux(axs[3,0], seg1, boundaries1, flux_key='flux_ele', title='Flujo electrones - Seg1 (Norte)')
    else:
        # Desactivar axes si seg1 está vacío
        for i in range(4):
            axs[i,0].text(0.5, 0.5, 'Segmento Norte vacío', transform=axs[i,0].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,0].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Seg1 (Norte)')

    # --- Segmento 2 (Sur) ---
    # ✅ CORRECCIÓN: Eliminar referencia a 'unidad'
    if seg2 is not None and not seg2_empty:
        plot_spectrogram(axs[0,1], spec2_ion, 'Espectrograma de iones - Seg2 (Sur)', seg2, boundaries2_adj)
        plot_spectrogram(axs[1,1], spec2_ele, 'Espectrograma de electrones - Seg2 (Sur)', seg2, boundaries2_adj)
        plot_flux(axs[2,1], seg2, boundaries2_adj, flux_key='flux_ion', title='Flujo iones - Seg2 (Sur)')
        plot_flux(axs[3,1], seg2, boundaries2_adj, flux_key='flux_ele', title='Flujo electrones - Seg2 (Sur)')
    else:
        # Desactivar axes si no hay segmento 2
        for i in range(4):
            axs[i,1].text(0.5, 0.5, 'Segmento Sur vacío', transform=axs[i,1].transAxes, 
                         ha='center', va='center', fontsize=12)
            axs[i,1].set_title(f'{"Espectrograma" if i < 2 else "Flujo"} - Seg2 (Sur)')

    # Panel de resumen
    ax_summary = axs[4,0]
    ax_summary.axis('off')

    # Crear texto de resumen con formato
    summary_text = "Fronteras detectadas (Norte):\n"
    if not seg1_empty:
        for b_name, b in boundaries1.items():
            if b is not None and b['index'] is not None and b['index'] < len(seg1['time']):
                t = seg1['time'][b['index']]
                t_datetime = to_datetime(t) if isinstance(t, np.datetime64) else t
                t_str = t_datetime.strftime('%H:%M:%S')
                lat = seg1['lat'][b['index']]
                dev = b.get('deviation', 0)
                params = b.get('params', {})
                
                if dev > 0:
                    param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                    summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}° (dev: {dev:.1f}, params: {param_str})\n"
                else:
                    summary_text += f"• {b_name}: {t_str}, lat={lat:.2f}°\n"
            else:
                summary_text += f"• {b_name}: No detectada\n"
    else:
        summary_text += "• Segmento Norte vacío\n"

    if seg2 is not None and not seg2_empty:
        summary_text += "\nFronteras detectadas (Sur):\n"
        for b_name, b in boundaries2_adj.items():
            if b is not None and b['index'] is not None and b['index'] < len(seg2['time']):
                t = seg2['time'][b['index']]
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
    else:
        summary_text += "\nFronteras detectadas (Sur):\n• Segmento Sur vacío\n"
    
    # Usar texto monoespaciado y mantener formato
    ax_summary.text(0.05, 0.95, summary_text, fontproperties=mono_font, 
                   verticalalignment='top', transform=ax_summary.transAxes,
                   bbox=dict(facecolor='whitesmoke', alpha=0.8, pad=10))

    # Asegurar mismos límites temporales para cada segmento
    for i in range(4):
        if not seg1_empty:
            axs[i,0].set_xlim(seg1['time'][0], seg1['time'][-1])
        if seg2 is not None and not seg2_empty:
            axs[i,1].set_xlim(seg2['time'][0], seg2['time'][-1])

    # Guardar con manejo de errores
    try:
        folder = os.path.join(main_folder, f'cycle_{cycle_index}')
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f'cycle{cycle_index}_full.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"✅ Gráfico guardado: {path}")
        return path
    except Exception as e:
        print(f"❌ Error guardando gráfico del ciclo {cycle_index}: {e}")
        plt.close(fig)
        return None

# ✅ CORRECCIÓN: Eliminar parámetro 'unidad' no utilizado
def plot_polar_cycle(seg1, seg2, boundaries1, boundaries2, 
                    spec1_ion, spec2_ion, spec1_ele, spec2_ele,
                    energy_edges, main_folder, cycle_index):  # ❌ QUITADO: unidad=False
    """Grafica polar completa - VERSIÓN CORREGIDA DIMENSIONES"""
    
    # Verificar si los segmentos están vacíos
    seg1_empty = len(seg1['time']) == 0 if seg1 is not None else True
    seg2_empty = len(seg2['time']) == 0 if seg2 is not None else True
    
    if seg1_empty and seg2_empty:
        print(f"⚠️  Ciclo {cycle_index}: Ambos segmentos vacíos, no se puede graficar polar")
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
            print(f"🔍 Espectrograma: {spec.shape} (energía × tiempo)")
            print(f"🔍 Energy edges: {len(energy_edges)} puntos")
            
            # CORRECCIÓN CRÍTICA: Crear arrays de coordenadas con dimensiones correctas
            # Para shading='flat': X e Y deben tener dimensiones (n_energy+1, n_time+1)
            # Para shading='auto': X e Y deben tener dimensiones (n_energy, n_time) o (n_energy+1, n_time+1)
            
            # Opción 1: Usar shading='auto' con dimensiones mínimas
            theta = np.linspace(0, 2 * np.pi, n_time)
            r = energy_edges[:n_energy]  # Tomar solo los necesarios
            
            # Crear mallas 2D
            theta_grid, r_grid = np.meshgrid(theta, r)
            
            print(f"🔍 Mallas: theta_grid {theta_grid.shape}, r_grid {r_grid.shape}")
            
            # Verificar compatibilidad de dimensiones
            if theta_grid.shape == spec.shape and r_grid.shape == spec.shape:
                im = ax.pcolormesh(theta_grid, r_grid, spec, norm=LogNorm(), shading='auto', cmap='viridis')
            else:
                # Opción de respaldo: usar imshow
                print(f"⚠️  Dimensiones no coinciden, usando imshow")
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
            print(f"❌ Error en espectrograma polar: {e}")
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
    # ✅ CORRECCIÓN: Eliminar referencia a 'unidad'
    if seg2 is not None and not seg2_empty:
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
        print(f"✅ Gráfico POLAR guardado: {path}")
        return path
    except Exception as e:
        print(f"❌ Error guardando gráfico POLAR del ciclo {cycle_index}: {e}")
        plt.close(fig)
        return None