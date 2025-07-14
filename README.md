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

## Manual de Usuario

````markdown
# Manual de Instalación y Uso de OvationReborn2

Este documento agrupa todo lo necesario para instalar, configurar y ejecutar el análisis de límites de precipitación nocturna.

---

## 1. Requisitos

- Python 3.8 o superior  
- Acceso a un terminal o consola de comandos  
- Archivo CDF de DMSP para procesar

---

## 2. Instalación

1. **Clona el repositorio**  
   ```bash
   git clone https://github.com/BenjaminEdwardsUsach/OvationReborn2.git
   cd OvationReborn2
````

2. **(Opcional) Crea y activa un entorno virtual**

   * Linux/macOS:

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * Windows:

     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Instala las dependencias**

   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Uso Básico

Ejecuta el script de arranque con los parámetros deseados:

```bash
python starter.py ruta/al/archivo.cdf \
  --fronteras b1e b2e b6 \
  --inicio 2014-12-31T12:00:00 \
  --fin    2014-12-31T12:30:00
```

* **ruta/al/archivo.cdf**: ruta absoluta o relativa al archivo CDF de DMSP.
* **--fronteras**: lista de fronteras a detectar (minúsculas). Opciones:
  `b1e, b2e, b2i, b3a, b3b, b4s, b5e, b5i, b6`
  Usa `all` para todas (valor por defecto).
* **--inicio** y **--fin**: intervalo temporal en formato ISO `YYYY-MM-DDThh:mm:ss` (inclusive).

---

## 4. Características Clave

* **Selección flexible de fronteras**

  * Puedes combinar cualquier subconjunto de las fronteras listadas.
  * Las fronteras dependientes se calculan automáticamente.
  * Las no solicitadas se marcan como no detectadas y no se grafican.

* **Filtrado temporal estricto**

  * Solo se procesan datos dentro del rango `--inicio` a `--fin`.
  * Aviso si no hay datos en el intervalo, pero el script continúa.

* **Retrocompatibilidad**

  * Sin parámetros explí­citos, el comportamiento es idéntico a versiones anteriores (todas las fronteras y todo el archivo).

* **Salida organizada por ciclo**

  ```
  [CDF_FILENAME]/
    ├─ cycle_1/
    │   ├─ info.json      # parámetros y valores de fronteras
    │   ├─ cycle.png      # gráfico del ciclo
    │   └─ fluxes.csv     # flujos integrados (si está habilitado)
    ├─ cycle_2/ …
    └─ resumen_global.json
  ```

---

## 5. Notas Importantes

* **Minúsculas**: los nombres de fronteras son sensibles a mayúsculas/minúsculas.
* **Dependencias internas**: no es necesario indicar fronteras dependientes manualmente.
* **Intervalos sin datos**: recibirás una advertencia si no hay registros en el rango, revisa tu tiempo.
* **Formato de tiempo**: cualquier variación en segundos cambia el filtrado de datos.

Con esto, solo copia y pega este bloque en tu documentación o README y estarás listo para que cualquier usuario instale y ejecute **OvationReborn2** sin complicaciones. ¡Éxito!



--

## Requisitos

- **Python** 3.8+  
- **Dependencias** (en `requirements.txt`):  
  ```text
  cdflib
  numpy
  scipy
  pandas
  matplotlib
