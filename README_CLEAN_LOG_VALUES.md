# Ambiente de Prueba - Limpieza de Valores Negativos en Log

## 📋 Resumen

Se ha creado un ambiente de prueba completo para limpiar y filtrar valores negativos en escala logarítmica, reemplazándolos con **NaN**.

## 📁 Archivos Creados

### 1. `funciones/clean_log_values.py`
Módulo con funciones auxiliares para:
- Limpiar valores negativos en arrays 1D
- Limpiar matrices 2D (típico: tiempo x energía)
- Generar estadísticas antes/después
- Mostrar tablas de referencia

**Funciones principales:**
```python
clean_negative_log_values(log_values, replace_with_nan=True, threshold=0.0)
clean_log_array_2d(log_array, replace_with_nan=True, threshold=0.0)
get_statistics_before_after(original_log, cleaned_log)
print_cleaning_report(original_log, cleaned_log, name="Flujo")
print_log_scale_reference()
```

### 2. `test_clean_log_values.py`
Script de prueba ejecutable que demuestra:
- ✅ Prueba 1: Limpieza básica
- ✅ Prueba 2: Limpieza de matriz 2D
- ✅ Prueba 3: Datos aleatorios realistas
- ✅ Prueba 4: Variación de umbrales
- ✅ Prueba 5: Simulación formato DMSP

**Uso:**
```bash
python test_clean_log_values.py
```

## 🧪 Resultados de las Pruebas

### Prueba 5 (Simulación Real DMSP):
```
Flujos de Iones:
  • Valores negativos originales: 48 (48%)
  • Convertidos a NaN: 48
  • Valores válidos: 52

Flujos de Electrones:
  • Valores negativos originales: 31 (31%)
  • Convertidos a NaN: 31
  • Valores válidos: 69
```

## 📊 Interpretación de Escala Logarítmica

```
log10(flujo)  ↔  Flujo [eV/cm²/ster/s]
───────────────────────────────────────
   -10        ↔  1e-10 (muy débil - EXCLUIR)
    -5        ↔  1e-5  (débil - EXCLUIR)
    -1        ↔  0.1   (bajo - considerar EXCLUIR)
     0        ↔  1.0   (umbral típico ← RECOMENDADO)
    +2        ↔  100   (alto - INCLUIR)
    +4        ↔  10000 (muy alto - INCLUIR)
```

**Regla:** `log < 0` → `Flujo < 1 eV/cm²/ster/s` (opcional excluir)

## 🔧 Integración en Código Principal

### Opción 1: Activación Manual (Recomendado para pruebas)

En `OvationRebron23.py`, después de calcular los logs:

```python
from funciones.clean_log_values import clean_negative_log_values, print_cleaning_report

# ... código existente ...

# Calcular logs (como está ahora)
flujos_iones_log = np.log10(flujos_iones_totales + 1e-10)
flujos_elec_log = np.log10(flujos_elec_totales + 1e-10)

# ✨ OPCIÓN: LIMPIAR VALORES NEGATIVOS
# Descomenta la siguiente línea para activar la limpieza
USE_CLEAN_LOG = True  # ← Cambia a False para desactivar

if USE_CLEAN_LOG:
    flujos_iones_log = clean_negative_log_values(flujos_iones_log, 
                                                  replace_with_nan=True, 
                                                  threshold=0.0)
    flujos_elec_log = clean_negative_log_values(flujos_elec_log, 
                                                 replace_with_nan=True, 
                                                 threshold=0.0)
    
    # Mostrar reporte (opcional)
    print_cleaning_report(flujos_iones_log, flujos_elec_log, "Flujos de Iones")
    print_cleaning_report(flujos_elec_log, flujos_elec_log, "Flujos de Electrones")
```

### Opción 2: Función Auxiliar en `OvationRebron23.py`

```python
def procesar_datos_dmsp_limpio(archivo_cdf, limpiar_log=True, directorio_salida="results"):
    """
    Versión de procesar_datos_dmsp que opcionalmente limpia valores negativos en log.
    
    Parámetro adicional:
        limpiar_log (bool): Si True, reemplaza valores negativos con NaN
    """
    # ... código existente ...
    
    if limpiar_log:
        from funciones.clean_log_values import clean_negative_log_values
        flujos_iones_log = clean_negative_log_values(flujos_iones_log)
        flujos_elec_log = clean_negative_log_values(flujos_elec_log)
    
    # ... continuar como normal ...
```

### Opción 3: Parámetro de Configuración

En `main_app.py`, añadir un checkbox en sidebar:

```python
# En la sección de configuración
st.sidebar.header("🧪 Ambiente de Prueba")
limpiar_log = st.sidebar.checkbox(
    "Limpiar valores negativos en log (test)",
    value=False,
    help="Reemplaza log< 0 con NaN para visualización más limpia"
)

# Pasar al procesamiento
resultados = ovation.procesar_datos_dmsp(archivo_cdf, limpiar_log=limpiar_log)
```

## 📈 Comparación Visual: Antes vs Después

### Antes (Sin limpiar):
```
Gráfico de Flujo:
  • Puntos dispersos desde log = -5 hasta log = +3
  • Muchos puntos en la parte inferior del gráfico
  • Difícil ver la estructura en los valores altos
```

### Después (Con limpiar):
```
Gráfico de Flujo:
  • Solo puntos desde log = 0 hasta log = +3
  • Mejor resolución en escala y distribución clara
  • Más fácil identificar características importantes
  • Puntos con log < 0 aparecen como "huecos" en gráficos
```

## ⚙️ Parámetros de Control

| Parámetro | Valor | Efecto |
|-----------|-------|--------|
| `replace_with_nan` | `True` | Reemplaza negativos con NaN |
| `replace_with_nan` | `False` | Reemplaza con el threshold |
| `threshold` | `0.0` | Excluye flujo < 1 eV/cm²/ster/s |
| `threshold` | `-1.0` | Excluye flujo < 0.1 eV/cm²/ster/s |
| `threshold` | `-2.0` | Excluye flujo < 0.01 eV/cm²/ster/s |

## 📝 Recomendaciones

### Para Visualización Inicial:
```python
threshold = 0.0          # Excluir flujos muy débiles
replace_with_nan = True  # Mostrar como huecos
```

### Para Análisis Detallado:
```python
threshold = -1.0         # Incluir más datos
replace_with_nan = True  # Aún ver gaps donde hay NaN
```

### Para Investigar Ruido de Fondo:
```python
threshold = -2.0         # Incluir casi todo
replace_with_nan = False # Mantener valor mínimo
```

## 🚀 Próximos Pasos

1. **Ejecutar pruebas:**
   ```bash
   python test_clean_log_values.py
   ```

2. **Integrar en código principal:**
   - Elegir una de las 3 opciones de integración
   - Añadir parámetro `limpiar_log` donde sea necesario

3. **Comparar visualizaciones:**
   - Ejecutar con `limpiar_log=False`
   - Ejecutar con `limpiar_log=True`
   - Observar diferencias en los gráficos

4. **Ajustar umbrales según necesidad:**
   - Experimentar con `threshold=-1.0`, `-2.0`, etc.
   - Encontrar el balance entre claridad y retención de datos

## 📚 Referencia Rápida

```python
# Uso básico
from funciones.clean_log_values import clean_negative_log_values

# Limpiar un array
flujos_limpio = clean_negative_log_values(flujos_log, replace_with_nan=True, threshold=0.0)

# Limpiar una matriz 2D
espectro_limpio = clean_log_array_2d(espectro, replace_with_nan=True, threshold=0.0)

# Ver estadísticas
estadísticas = get_statistics_before_after(original, limpio)

# Generar reporte
print_cleaning_report(original, limpio, "Mi Dataset")

# Ver tabla de conversión log ↔ flujo
print_log_scale_reference()
```

---

**Estado:** ✅ Ambiente de prueba completamente funcional  
**Última actualización:** Febrero 2026
