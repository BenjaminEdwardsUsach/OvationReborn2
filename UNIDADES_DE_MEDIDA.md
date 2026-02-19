# Unidades de Medida - Proyecto OvationReborn2

## Documento de Referencia de Unidades Físicas

Todas las variables en el código están acompañadas de comentarios indicando sus unidades. Este documento proporciona una referencia centralizada de todas las unidades utilizadas.

---

## Variables Principales del Dataset DMSP SSJ

### Energía
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `CHANNEL_ENERGIES` | **eV** (electronvoltios) | Energía central de cada canal (19 canales: 30 eV a 30 keV) |
| `ELE_AVG_ENERGY` | **eV** | Energía promedio de los electrones |

### Flujos Diferenciales (sin integrar)
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `ELE_DIFF_ENERGY_FLUX` | **eV/cm²/ΔeV/ster/s** | Flujo diferencial de electrones |
| `ION_DIFF_ENERGY_FLUX` | **eV/cm²/ΔeV/ster/s** | Flujo diferencial de iones |

**Desglose de la unidad compuesta:**
- **eV**: energía en electronvoltios
- **cm²**: área de sección transversal del detector
- **ΔeV**: ancho del intervalo de energía del canal
- **ster**: esterradián (ángulo sólido)
- **s**: segundo

### Flujos Integrados (integrados sobre energía)
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `ELE_TOTAL_ENERGY_FLUX` | **eV/cm²/ster/s** | Flujo energético total integrado de electrones |
| `ION_TOTAL_ENERGY_FLUX` | **eV/cm²/ster/s** | Flujo energético total integrado de iones |
| `flujos_elec_log` | **log(eV/cm²/ster/s)** | Flujo de electrones en escala logarítmica (para visualización) |
| `flujos_iones_log` | **log(eV/cm²/ster/s)** | Flujo de iones en escala logarítmica (para visualización) |
| `flujos_iones_b2i` | **eV/cm²/ster/s** | Flujo integrado de iones en banda B2i (3-30 keV) |

**Nota sobre integración:**
La integración se realiza multiplicando el flujo diferencial por el ancho del canal:
$$\text{Flujo Total} = \sum_{i} \text{Flujo Diferencial}[i] \times \Delta E[i]$$

### Coordenadas Geográficas
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `SC_AACGM_LAT` | **grados (°)** | Latitud geomagnética (coordenadas AACGM) |
| `SC_GEOCENTRIC_LAT` | **grados (°)** | Latitud geocéntrica (coordenadas geográficas) |
| `SC_AACGM_LON` | **grados (°)** | Longitud geomagnética (coordenadas AACGM) |
| `MLT` | **horas (h)** | Tiempo magnético local (Magnetic Local Time) |

### Tiempo
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `Epoch` | **ms** | Marca de tiempo (milisegundos desde 1970-01-01) |
| `tiempo_final` | **datetime** | Tiempos en formato Python datetime |

---

## Variables Derivadas durante el Procesamiento

### Factores Geométricos
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `ELE_GEOMETRIC` | **cm²·eV·ster·sec** | Factor geométrico para electrones |
| `ION_GEOMETRIC` | **cm²·eV·ster·sec** | Factor geométrico para iones |

### Otros Parámetros
| Variable | Unidad | Descripción |
|----------|--------|-------------|
| `delta` | **eV** | Ancho de cada canal de energía |
| `energy_edges` | **eV** | Bordes de los intervalos de energía |

---

## Unidades en Gráficos

### Espectrogramas
- **Eje Y**: Energía en escala logarítmica [eV]
- **Eje X**: Tiempo en formato UT (Hora Universal)
- **Colorbar**: Flujo Diferencial [**eV/cm²/ΔeV/ster/s**]

### Gráficos de Flujo Integrado
- **Eje Y**: Log Flujo Total [**eV/cm²/ster/s**]
- **Eje X**: Tiempo con información de latitud (AACGM y geocéntrica)
- **Líneas verticales**: Ubicación de las fronteras (b1e, b2e, b2i, b3a, b3b, b4s, b5e, b5i, b6)

---

## Ubicación de Comentarios en el Código

Los comentarios con unidades se encuentran en:

1. **`funciones/cargar_datos_cdf.py`** - Variables cargadas del archivo CDF
2. **`funciones/plot_utils.py`** - Etiquetas en gráficos y colorbars
3. **`funciones/integrar_flujo_diferencial.py`** - Descripción de la integración
4. **`funciones/procesar_ciclos.py`** - Variables del diccionario global_data
5. **`funciones/filtrar_canales.py`** - Preservación de unidades en filtrado
6. **`OvationRebron23.py`** - Variables principales de procesamiento

---

## Conversiones Útiles

- **1 keV** = 1000 eV
- **1 cm²** = 10⁻⁴ m²
- **1 esterradián (sr)** ≈ 1 "unidad de ángulo sólido" (máximo 4π sr en esfera completa)

---

## Rango de Energía Observado

El instrumento SSJ del DMSP observa precipitación de partículas (electrones e iones) en el rango de **30 eV a 30 keV**, lo que corresponde a:

- **Baja energía**: 30 eV - 300 eV (electrones de energía moderada)
- **Media energía**: 300 eV - 3 keV (precipitación auroral típica)
- **Alta energía**: 3 keV - 30 keV (precipitación substormática)

---

**Última actualización**: Febrero 2026
**Proyecto**: OvationReborn2 - Detección de Límites de Precipitación DMSP
