# OvationReborn2

**Herramienta en Python para la implementación automatizada del esquema de clasificación de precipitación nocturna propuesto por Newell et al. (1996).**

---

## Descripción

OvationReborn2 reproduce el esquema cuantitativo de identificación de límites de precipitación nocturna (b₁ₑ/b₁ᵢ, b₂ₑ, b₂ᵢ, b₃ₐ/b₃ᵦ, b₄ₛ, b₅, b₆) descrito en *Morphology of nightside precipitation* :contentReference[oaicite:0]{index=0}. El proyecto:

- Carga datos CDF de DMSP (32 eV–30 keV, resolución 1 s).  
- Aplica filtros, limpieza de outliers y cálculo de flujos integrados.  
- Detecta automáticamente los límites operacionales definidos en Newell et al. (1996) mediante técnicas de promedio móvil y correlación de espectros :contentReference[oaicite:1]{index=1}.  
- Produce gráficos espectrales (pcolormesh con escala log) y series de flujo integrado con marcas de candidatos b₂ᵢ.  
- Guarda resultados en JSON y figuras PNG por ciclo.

---

## Estructura del Código

Basado en `nuevo1.py`:

- **`moving_average`, `detectar_b2i_sliding_vec`**: funciones para promedio móvil y detección de b₂ᵢ con ventana deslizante :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}.  
- Carga CDF y extracción de variables con filtros `VALIDMIN`/`VALIDMAX`.  
- Filtrado de canales entre 30 eV y 30 keV, cálculo de `flujos_iones`.  
- Limpieza de outliers con mediana y MAD.  
- Segmentación por latitud AACGM, detección de cruces de signo y pares de extremos.  
- Detección de candidatos en primera y segunda mitad de cada segmento, con umbrales basados en percentiles.  
- Visualización: figuras 2×2 (espectrograma y flujo integrado), etiquetando UT, latitudes AACGM/GEO en los ticks.  
- Salida: carpeta principal (nombrada como el CDF), subcarpetas `cycle_<n>` con `info.txt` (JSON serializable) y `cycle.png` :contentReference[oaicite:4]{index=4}:contentReference[oaicite:5]{index=5}.

---

## Descarga de Datos Satelitales

Para obtener los archivos CDF desde CDAWeb (usado en el script):

1. Visitar el buscador CDAWeb:  
   https://cdaweb.gsfc.nasa.gov/index.html  
2. Seleccionar satélite e instrumento (p. ej., SSJ4 de DMSP).  
3. Elegir ventana temporal y variable deseada.  
4. En “Select an activity” elegir **Download CDF** y pulsar **Submit**.  
5. Descargar el archivo CDF desde el enlace en la nueva página https://cdaweb.gsfc.nasa.gov/index.html.

---

## Requisitos

- **Python** 3.8+  
- **Dependencias** (en `requirements.txt`):  
  ```text
  cdflib
  numpy
  scipy
  pandas
  matplotlib
