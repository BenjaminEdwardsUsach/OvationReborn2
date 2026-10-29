import streamlit as st
import os
import sys
import json
import glob
import matplotlib.pyplot as plt
from datetime import datetime

# Intentar importar el módulo con diferentes nombres
try:
    import OvationRebron23 as ovation  # importar modulo
except ImportError:
    try:
        import OvationRebron23 as ovation  # nombre corregido
    except ImportError as e:
        st.error(f"No se pudo importar el módulo de procesamiento: {str(e)}")
        st.stop()


# configuración de la página
st.set_page_config(
    page_title="OvationReborn2 - Procesador DMSP",
    page_icon="🌌",
    layout="wide"
)

# título principal
st.title("OvationReborn2 - Procesador de Datos DMSP")
st.markdown("""
**Procesamiento automático de límites de precipitación nocturna**  
Detección de límites b₁ₑ/b₁ᵢ, b₂ₑ, b₂ᵢ, b₃ₐ/b₃ᵦ, b₄ₛ, b₅, b₆ a partir de datos DMSP
""")

# sidebar para configuración:p
st.sidebar.header("🔧 Configuración")

# selección de modo
modo = st.sidebar.radio(
    "Modo de operación:",
    ["Procesar nuevo archivo", "Explorar espectrogramas", "Visualizar resultados existentes"]
)

# función para listar archivos CDF
def listar_archivos_cdf(directorio="data"):
    if not os.path.exists(directorio):
        os.makedirs(directorio)
        return []
    return [f for f in os.listdir(directorio) if f.endswith('.cdf')]

# función para procesar archivo
def procesar_archivo_cdf(archivo_cdf):
    """Ejecuta el procesamiento de OvationReborn2 sobre un archivo CDF"""
    try:
        # aca llamar a la funcion principal de OvationReborn23.py
        # ajustar a la estructura del codigo
        resultados = ovation.procesar_datos_dmsp(archivo_cdf)
        return resultados
    except Exception as e:
        st.error(f"Error en el procesamiento: {str(e)}")
        return None

# función para cargar resultados existentes
def cargar_resultados(directorio="results"):
    """Busca recursivamente carpetas `cycle_*` bajo `directorio` y carga
    archivos de información (info_*.json o info.txt) y cualquier imagen .png.
    Devuelve una lista de ciclos con metadatos para la UI.
    """
    ciclos = []
    if not os.path.exists(directorio):
        return ciclos

    for root, dirs, files in os.walk(directorio):
        # comprobar si la carpeta actual es un ciclo
        base = os.path.basename(root)
        if base.startswith("cycle_") and os.path.isdir(root):
            info = None

            # buscar info_*.json primero
            for fname in files:
                if fname.startswith("info_") and fname.endswith('.json'):
                    info_path = os.path.join(root, fname)
                    try:
                        with open(info_path, 'r', encoding='utf-8') as f:
                            info = json.load(f)
                    except Exception as e:
                        st.warning(f"Error cargando {info_path}: {str(e)}")
                    break

            # si no hay info_*.json, intentar info.txt
            if info is None and 'info.txt' in files:
                info_path = os.path.join(root, 'info.txt')
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                except Exception as e:
                    st.warning(f"Error cargando {info_path}: {str(e)}")

            # si no hay info, saltar este ciclo
            if info is None:
                continue

            # buscar imágenes .png en la carpeta del ciclo y categorizarlas
            png_files = [f for f in files if f.lower().endswith('.png')]
            ruta_grafica = None
            imagenes = {}
            if png_files:
                # categorizar según nombre
                others = []
                for p in png_files:
                    low = p.lower()
                    if 'polar' in low:
                        imagenes['polar'] = os.path.join(root, p)
                    elif 'full' in low:
                        imagenes['full'] = os.path.join(root, p)
                    elif 'cycle' in low:
                        imagenes['cycle'] = os.path.join(root, p)
                    else:
                        others.append(os.path.join(root, p))
                if others:
                    imagenes['other'] = others

                # preferir polar > full > cycle > first other
                ruta_grafica = imagenes.get('polar') or imagenes.get('full') or imagenes.get('cycle') or (imagenes.get('other')[0] if imagenes.get('other') else None)

            ciclo_info = {
                'nombre': base,
                'ruta': root,
                'info': info,
                'tiene_grafica': ruta_grafica is not None,
                'ruta_grafica': ruta_grafica,
                'imagenes': imagenes
            }
            ciclos.append(ciclo_info)

    # ordenar por nombre de ciclo (inteligente: extraer numero si es posible)
    def key_nombre(x):
        nombre = x.get('nombre', '')
        try:
            num = int(nombre.split('_')[-1])
            return num
        except Exception:
            return nombre

    return sorted(ciclos, key=key_nombre)

# MODO: procesar nuevo archivo
if modo == "Procesar nuevo archivo":
    st.header("📁 Procesar Nuevo Archivo CDF")
    
    # subir archivo o seleccionar existente
    archivos_existentes = listar_archivos_cdf()
    
    if archivos_existentes:
        opcion_archivo = st.radio(
            "Selecciona archivo:",
            ["Usar archivo existente", "Subir nuevo archivo"]
        )
    else:
        opcion_archivo = "Subir nuevo archivo"
    
    if opcion_archivo == "Subir nuevo archivo":
        archivo_subido = st.file_uploader(
            "Subir archivo CDF DMSP", 
            type=['cdf'],
            help="Archivo CDF de datos DMSP (32 eV–30 keV, resolución 1 s)"
        )
        
        if archivo_subido is not None:
            # guardar archivo subido
            os.makedirs("data", exist_ok=True)
            ruta_archivo = os.path.join("data", archivo_subido.name)
            
            with open(ruta_archivo, "wb") as f:
                f.write(archivo_subido.getbuffer())
            
            st.success(f"Archivo guardado: {ruta_archivo}")
            archivo_a_procesar = ruta_archivo
            
    else:  # usar archivo existente
        archivo_seleccionado = st.selectbox(
            "Seleccionar archivo CDF:",
            archivos_existentes
        )
        archivo_a_procesar = os.path.join("data", archivo_seleccionado)
    
    # Botón de procesamiento
    if 'archivo_a_procesar' in locals():
        st.info(f"Archivo seleccionado: `{archivo_a_procesar}`")
        
        if st.button("🚀 Ejecutar Procesamiento", type="primary"):
            with st.spinner("Procesando datos DMSP..."):
                # ejecutar el procesamiento
                resultados = procesar_archivo_cdf(archivo_a_procesar)
                
                if resultados:
                    st.success("¡Procesamiento completado!")
                    
                    # mostrar resultados inmediatos
                    st.subheader("📊 Resultados del Procesamiento")
                    
                    # aquí se puede mostrar resultados específicos del procesamiento
                    # esto depende de lo que retorne tu función de procesamiento
                    
                    # mostrar gráfica si está disponible
                    ciclos = cargar_resultados()
                    if ciclos:
                        ciclo_mas_reciente = ciclos[-1]  # ultimo ciclo procesado
                        
                        # mostrar preferentemente la gráfica polar si existe
                        img_path = None
                        imgs = ciclo_mas_reciente.get('imagenes', {})
                        img_path = imgs.get('polar') or imgs.get('full') or ciclo_mas_reciente.get('ruta_grafica')
                        if img_path:
                            st.image(
                                img_path,
                                caption=f"Gráfica: {ciclo_mas_reciente['nombre']}",
                                use_column_width=True
                            )

# MODO: explorar datos sin detectar fronteras
elif modo == "Explorar espectrogramas":
    from ExtensionV.scan import generar_espectrogramas, graficar_ciclo

    st.header("🔎 Exploración visual de datos DMSP")
    st.write(
        "Genera espectrogramas y propone candidatas a V invertida, "
        "sin ejecutar la detección de fronteras."
    )

    archivos_existentes = listar_archivos_cdf()
    if archivos_existentes:
        opcion_archivo = st.radio(
            "Selecciona archivo para explorar:",
            ["Usar archivo existente", "Subir nuevo archivo"],
            key="scan_opcion_archivo",
        )
    else:
        opcion_archivo = "Subir nuevo archivo"

    archivo_a_explorar = None
    if opcion_archivo == "Subir nuevo archivo":
        archivo_subido = st.file_uploader(
            "Subir archivo CDF DMSP",
            type=["cdf"],
            help="Archivo CDF de datos DMSP.",
            key="scan_archivo_subido",
        )
        if archivo_subido is not None:
            os.makedirs("data", exist_ok=True)
            archivo_a_explorar = os.path.join("data", archivo_subido.name)
            with open(archivo_a_explorar, "wb") as archivo:
                archivo.write(archivo_subido.getbuffer())
    else:
        archivo_seleccionado = st.selectbox(
            "Seleccionar archivo CDF:",
            archivos_existentes,
            key="scan_archivo_existente",
        )
        archivo_a_explorar = os.path.join("data", archivo_seleccionado)

    if archivo_a_explorar:
        st.info(f"Archivo seleccionado: `{archivo_a_explorar}`")
        if st.button("📈 Analizar archivo", type="primary"):
            try:
                with st.spinner("Analizando el archivo por ciclos orbitales..."):
                    st.session_state["scan_resultado"] = generar_espectrogramas(
                        archivo_a_explorar
                    )
                    st.session_state["scan_archivo_resultado"] = archivo_a_explorar
            except Exception as error:
                st.error(f"No se pudo analizar el archivo: {error}")

        resultado_scan = st.session_state.get("scan_resultado")
        if (
            resultado_scan
            and st.session_state.get("scan_archivo_resultado") == archivo_a_explorar
        ):
            st.success(
                f"Análisis completado: {resultado_scan['puntos_mlt']:,} de "
                f"{resultado_scan['puntos_totales']:,} registros MLT, "
                f"{resultado_scan['canales']} canales visibles desde "
                f"{resultado_scan['energia_minima_grafico_ev']} eV y "
                f"{len(resultado_scan['ciclos'])} ciclos."
            )
            st.caption(
                "El detector de candidatas usa electrones desde 200 eV; "
                "el espectrograma conserva los canales desde 30 eV."
            )

            candidatos_por_ciclo = {}
            for candidato in resultado_scan["candidatos"]:
                candidatos_por_ciclo.setdefault(candidato["ciclo"], []).append(candidato)
            ciclos_con_candidatos = [
                ciclo
                for ciclo in resultado_scan["ciclos"]
                if ciclo["ciclo"] in candidatos_por_ciclo
            ]
            st.caption(
                f"Ciclos con candidatas: {len(ciclos_con_candidatos)} de "
                f"{len(resultado_scan['ciclos'])}."
            )
            if not ciclos_con_candidatos:
                st.info("No se encontraron candidatas en los ciclos del intervalo seleccionado.")
            else:
                opciones_ciclos = [
                    f"Ciclo {ciclo['ciclo']} · {ciclo['inicio']} — {ciclo['fin']} "
                    f"· {len(candidatos_por_ciclo[ciclo['ciclo']])} candidata(s)"
                    for ciclo in ciclos_con_candidatos
                ]
                ciclo_idx = st.selectbox(
                    "Seleccionar ciclo/pasada:",
                    range(len(ciclos_con_candidatos)),
                    format_func=lambda index: opciones_ciclos[index],
                    key="scan_ciclo_seleccionado",
                )
                ciclo = ciclos_con_candidatos[ciclo_idx]
                candidatos = candidatos_por_ciclo[ciclo["ciclo"]]
                st.subheader(f"Ciclo {ciclo['ciclo']} · candidatas a V invertida")
                st.caption(
                    "Candidatas exploratorias de 30–90 s; el sombreado rojo "
                    "marca el intervalo. Deben confirmarse visualmente."
                )
                st.caption(
                    "Se buscan aumentos de al menos 0,5 décadas (≈3,2×) y "
                    "3 desviaciones robustas sobre una mediana local de hasta "
                    "5 minutos. La energía media del centro se informa, pero "
                    "no es un criterio de descarte."
                )
                st.dataframe(candidatos, width="stretch")

                try:
                    figuras_ciclo = graficar_ciclo(resultado_scan, ciclo)
                    col_electrones, col_iones = st.columns(2)
                    with col_electrones:
                        st.pyplot(figuras_ciclo["electrones"])
                        plt.close(figuras_ciclo["electrones"])
                    with col_iones:
                        st.pyplot(figuras_ciclo["iones"])
                        plt.close(figuras_ciclo["iones"])
                except Exception as error:
                    st.error(f"No se pudieron generar los gráficos del ciclo: {error}")

# MODO: visualizar resultados existentes
else:
    st.header(" Visualizar Resultados Existentes")
    
    # cargar resultados
    ciclos = cargar_resultados()
    
    if not ciclos:
        st.warning("""
        No se encontraron resultados previos. 
        
        **Para generar resultados:**
        1. Ve al modo **'Procesar nuevo archivo'**
        2. Sube un archivo CDF DMSP
        3. Ejecuta el procesamiento
        """)
    else:
        # selector de ciclo
        nombres_ciclos = [ciclo['nombre'] for ciclo in ciclos]
        ciclo_seleccionado = st.selectbox(
            "Seleccionar ciclo para visualizar:",
            nombres_ciclos
        )
        
        # encontrar ciclo seleccionado
        ciclo = next((c for c in ciclos if c['nombre'] == ciclo_seleccionado), None)
        
        if ciclo:
            # helper para extraer límites desde estructuras JSON anidadas
            def find_key_recursive(d, key):
                if isinstance(d, dict):
                    if key in d:
                        return d[key]
                    for v in d.values():
                        res = find_key_recursive(v, key)
                        if res is not None:
                            return res
                elif isinstance(d, list):
                    for item in d:
                        res = find_key_recursive(item, key)
                        if res is not None:
                            return res
                return None

            def extract_limit_value(info_obj, key_name):
                node = find_key_recursive(info_obj, key_name)
                if node is None:
                    return None
                # si node es un dict, preferir 'lat' luego 'time' luego 'index'
                if isinstance(node, dict):
                    for attr in ('lat', 'time', 'index'):
                        if attr in node and node[attr] is not None:
                            return node[attr]
                    return None
                # si es lista o valor directo
                return node

            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader(f" Visualización: {ciclo['nombre']}")

                # mostrar selector para tipo de imagen (si hay más de una disponible)
                imgs = ciclo.get('imagenes', {})
                opciones = []
                if 'polar' in imgs:
                    opciones.append('Polar')
                if 'full' in imgs:
                    opciones.append('Full')
                if 'cycle' in imgs:
                    opciones.append('Cycle')
                if 'other' in imgs:
                    opciones.append('Other')
                if not opciones and ciclo.get('ruta_grafica'):
                    opciones = ['Imagen']

                modo_img = None
                if opciones:
                    # añadir opción para mostrar ambas si hay polar y full
                    if 'Polar' in opciones and 'Full' in opciones:
                        opciones = ['Polar', 'Full', 'Ambas']
                    modo_img = st.selectbox('Seleccionar imagen', opciones)

                # mostrar según selección
                if modo_img:
                    if modo_img == 'Ambas':
                        col_img_left, col_img_right = st.columns(2)
                        with col_img_left:
                            st.image(imgs.get('polar'))
                        with col_img_right:
                            st.image(imgs.get('full'))
                    else:
                        key = modo_img.lower()
                        path = imgs.get(key) or ciclo.get('ruta_grafica')
                        if path:
                            st.image(path, use_column_width=True, caption=f"{modo_img} - {ciclo['nombre']}")
                        else:
                            st.warning('No hay imagen disponible para la opción seleccionada')
                else:
                    st.warning("No se encontró la gráfica para este ciclo")
            
            with col2:
                st.subheader("📍 Límites Detectados")
                
                info = ciclo['info']

                # mostrar límites principales (extraer valor real desde JSON anidado)
                limites_map = [
                    ("b₁ₑ (límite exterior electrones)", 'b1e'),
                    ("b₁ᵢ (límite exterior iones)", 'b1i'),
                    ("b₂ₑ (límite interior electrones)", 'b2e'),
                    ("b₂ᵢ (límite interior iones)", 'b2i'),
                    ("b₃ₐ (límite auroral)", 'b3a'),
                    ("b₃ᵦ (límite subauroral)", 'b3b'),
                    ("b₄ₛ (límite de separación)", 'b4s'),
                    ("b₅ (límite polar)", 'b5'),
                    ("b₆ (límite de cierre)", 'b6')
                ]

                for nombre, key in limites_map:
                    valor = extract_limit_value(info, key)
                    if valor is not None:
                        # si es fecha/hora mostrar como string, si es lat mostrar con 2 decimales
                        try:
                            if isinstance(valor, (int, float)):
                                st.metric(nombre, f"{valor:.2f}")
                            else:
                                st.metric(nombre, str(valor))
                        except Exception:
                            st.metric(nombre, str(valor))
                    else:
                        st.metric(nombre, "No detectado", delta="N/A")
                
                # información adicional
                st.subheader("📋 Información del Ciclo")
                if 'timestamp' in info:
                    st.write(f"**Timestamp:** {info['timestamp']}")
                if 'data_points' in info:
                    st.write(f"**Puntos de datos:** {info['data_points']}")
            
            # datos completos en expander
            with st.expander("🔍 Ver datos completos del ciclo"):
                st.json(ciclo['info'])

# información general
st.markdown("---")
st.markdown("""
### información del Procesamiento

**parámetros del esquema:**
- **rango energético:** 32 eV – 30 keV
- **resolución temporal:** 1 segundo
- **coordenadas:** AACGM/GEO
- **límites detectados:** b₁ₑ/b₁ᵢ, b₂ₑ, b₂ᵢ, b₃ₐ/b₃ᵦ, b₄ₛ, b₅, b₆

**referencias:**
- basado en *Morphology of nightside precipitation*
- detección automática según Newell et al. (1996)
- datos DMSP procesados con cdflib
""")
