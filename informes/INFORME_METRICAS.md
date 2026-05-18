# Informe de métricas — Sistema Experto de Evaluación Prequirúrgica

**Fecha de ejecución:** 2026-05-17 20:13  
**Casos evaluados:** 45  
**Motor:** encadenamiento hacia adelante + lógica difusa (reglas R1–R34, validación R35)

---

## 1. Resumen ejecutivo

| Métrica | Valor |
|---------|-------|
| **Tasa de acierto del diagnóstico** | **100.00%** (45/45) |
| **Tiempo promedio de inferencia** | **0.133 ms** |
| Tiempo mínimo / máximo | 0.009 ms / 0.304 ms |
| **Porcentaje de casos derivados a incertidumbre** | **26.67%** (12/45) |
| Incertidumbre (solo datos completos) | 0.00% (0/33) |

---

## 2. Definición de métricas

### 2.1 Tasa de acierto del diagnóstico

Proporción de casos en los que la salida del motor coincide con el **gold standard**
predefinido en `tests/casos_benchmark.py` (clasificación preliminar, nivel de riesgo,
adecuación del procedimiento y, cuando aplica, conductas clave). Los campos esperados
en `None` no se exigen en la comparación.

### 2.2 Tiempo promedio de inferencia

Promedio del tiempo de CPU medido con `time.perf_counter()` alrededor de una llamada
completa a `MotorInferencias.evaluar()`, incluyendo validación, cálculo de variables,
fuzzificación, aplicación de reglas y generación del resultado.

### 2.3 Porcentaje de casos derivados a incertidumbre

Proporción de ejecuciones cuya clasificación final pertenece al conjunto de salidas
**no conclusivas**, en las que el sistema no emite una recomendación preliminar definida:

- «fuera del dominio», «información insuficiente»

En la práctica, la regla **R35** (información insuficiente) concentra estos casos cuando
faltan datos obligatorios del paciente.

---

## 3. Metodología

1. **Gold standard:** conjunto fijo de perfiles clínicos (consigna + sintéticos + datos incompletos).
2. **Simulación masiva:** cada perfil se evalúa de forma automática sin intervención manual.
3. **Comparación:** resultado obtenido vs. esperado campo a campo.
4. **Grupos:** consigna (6), favorables, optimización, postergar, no recomendado, incertidumbre.

Los casos de incertidumbre (`grupo: incertidumbre`) se diseñaron **a propósito** con datos
faltantes; un acierto en esos casos implica que el sistema respondió «información insuficiente».

---

## 4. Resultados por grupo

| Grupo | Casos | Acierto | % Acierto | % Incertidumbre (salida) |
|-------|------:|--------:|----------:|-------------------------:|
| consigna | 6 | 6 | 100.0% | 0.0% |
| incertidumbre | 12 | 12 | 100.0% | 100.0% |
| sintetico_favorable | 12 | 12 | 100.0% | 0.0% |
| sintetico_no_recomendado | 4 | 4 | 100.0% | 0.0% |
| sintetico_optimizacion | 5 | 5 | 100.0% | 0.0% |
| sintetico_postergar | 6 | 6 | 100.0% | 0.0% |

---

## 5. Distribución de clasificaciones obtenidas

| Clasificación | Cantidad | % |
|---------------|----------|---|
| candidato favorable | 13 | 28.9% |
| información insuficiente | 12 | 26.7% |
| postergar | 8 | 17.8% |
| candidato con optimización previa | 7 | 15.6% |
| no recomendado por el momento | 5 | 11.1% |

---

## 6. Casos con discrepancia (gold standard vs. motor)

*No se registraron discrepancias: 100% de acierto.*

---

## 7. Conclusiones

- La **tasa de acierto (100.0%)** indica alta concordancia entre el comportamiento del motor y el gold standard definido.
- El **tiempo promedio de inferencia (0.133 ms)** permite uso interactivo en consulta sin latencia perceptible.
- El **26.7% de salidas en incertidumbre** refleja principalmente los casos con datos incompletos del grupo de prueba; en producción este porcentaje dependerá de la calidad de carga de datos.

---

*Informe generado automáticamente por `python -m tests.evaluar_metricas`.*