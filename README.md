# OvationReborn2

**Herramienta en Python para la implementación automatizada del esquema de clasificación de precipitación nocturna propuesto por Newell et al. (1996).**

---

## Descripción

OvationReborn2 procesa datos de precipitación nocturna de la misión DMSP y detecta los límites aurorales operacionales:
- b₁ₑ / b₁ᵢ
- b₂ₑ
- b₂ᵢ
- b₃ₐ / b₃ᵦ
- b₄ₛ
- b₅
- b₆

El proyecto trabaja con archivos CDF de DMSP y realiza:
- Carga de datos con validación de rangos y extracción de variables clave.
- Filtrado de canales entre 30 eV y 30 keV.
- Cálculo de flujos integrados y transformaciones logarítmicas.
- Segmentación por latitud AACGM y detección de extremos y candidatos de ciclo.
- Almacenamiento de resultados por ciclo en `results/`.
- Visualización mediante una interfaz de Streamlit (`main_app.py`).

---

## Componentes principales

- `main_app.py`: interfaz web en Streamlit para procesar archivos CDF y visualizar resultados.
- `OvationRebron23.py`: script principal de procesamiento en línea de comandos.
- `funciones/`: paquete con las rutinas de carga, limpieza, filtrado, detección y exportación.
- `data/`: carpeta sugerida para almacenar archivos CDF de entrada.
- `results/`: carpeta donde se guarda la salida organizada por ciclo.

---

## Uso

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la interfaz Streamlit

```bash
streamlit run main_app.py
```

Desde la aplicación web puedes subir un archivo CDF o seleccionar uno existente en `data/` y procesarlo.

En **Explorar espectrogramas** puedes analizar un CDF por ciclos/pasadas orbitales, seleccionar un ciclo y revisar sus espectrogramas y candidatas sin ejecutar la detección de fronteras. La búsqueda usa registros entre MLT 12:00 y 24:00 y electrones desde 200 eV; los espectrogramas muestran todos los canales desde 30 eV. Desde Python:

```python
from ExtensionV.scan import generar_espectrogramas, graficar_ciclo

resultado = generar_espectrogramas("data/archivo_dmsp.cdf")
ciclo = resultado["ciclos"][0]
figuras = graficar_ciclo(resultado, ciclo)
```

`resultado["ciclos"]` y `resultado["candidatos"]` contienen los tramos orbitales y las candidatas. Usa `graficar_ciclo(resultado, ciclo)` para generar las figuras del ciclo seleccionado.

La exploración también genera **candidatas**: busca tramos de 30–90 segundos donde el flujo electrónico integrado desde 200 eV supera una mediana local de hasta cinco minutos por al menos 0,5 décadas (aprox. 3,2 veces) y tres desviaciones robustas. Informa la duración, latitud AACGM, contraste local y energía media característica; indica si esta aumenta hacia el centro del tramo. Estos son criterios iniciales para revisión visual, no una confirmación física ni umbrales universales. Los valores publicados en un ejemplo se muestran como contexto y no se usan como cortes obligatorios.

### 3. Ejecutar por línea de comandos

```bash
python OvationRebron23.py ruta/al/archivo.cdf --fronteras b1e b2e b2i --inicio 2014-12-31T12:00:00 --fin 2014-12-31T12:30:00
```

Opciones principales:
- `ruta/al/archivo.cdf`: ruta absoluta o relativa al archivo CDF de DMSP.
- `--fronteras`: lista de fronteras a calcular. Si se incluye `all`, procesa todas.
- `--inicio` y `--fin`: intervalo temporal en formato ISO `YYYY-MM-DDThh:mm:ss`.

> Nota: en el código actual, `OvationRebron23.py` procesa todas las fronteras si `--fronteras all` se pasa o si se omite `all`.

---

## Salida de resultados

El procesamiento crea una carpeta bajo `results/` basada en el nombre del archivo CDF y genera subcarpetas por ciclo.

Ejemplo de estructura esperada:

```text
results/
  <nombre_del_cdf>_YYYYMMDD_HHMMSS/
    cycle_0/
      info.json
      cycle.png
    cycle_1/
      info.json
      cycle.png
    ...
```

Cada ciclo contiene metadatos de detección y gráficos generados durante el análisis.

---

## Requisitos

- **Python** 3.8+
- Dependencias en `requirements.txt`:
  ```text
  streamlit>=1.28.0
  matplotlib>=3.5.0
  numpy>=1.21.0
  pandas>=1.3.0
  cdflib>=0.4.0
  scipy>=1.7.0
  ```

---

## Consejos rápidos

- Coloca los archivos CDF en `data/` para usarlos fácilmente desde la app Streamlit.
- Si deseas procesar el mismo archivo varias veces, revisa `results/` para evitar sobrescribir datos.
- Usa `streamlit run main_app.py` si quieres una experiencia visual; usa `python OvationRebron23.py ...` para un procesamiento directo.
