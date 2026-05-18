"""
evaluar_metricas.py
-------------------
Ejecuta el banco de benchmark, calcula métricas y genera el informe.

Uso:
    python -m tests.evaluar_metricas

Salida:
    informes/INFORME_METRICAS.md
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from tests.casos_benchmark import CASOS_BENCHMARK
from tests.metricas import CLASIFICACIONES_INCERTIDUMBRE, ResumenMetricas, evaluar_banco

INFORME_PATH = Path(__file__).resolve().parent.parent / "informes" / "INFORME_METRICAS.md"


def _generar_informe(resumen: ResumenMetricas) -> str:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    por_grupo = resumen.por_grupo()
    fallos = [r for r in resumen.resultados if not r.correcto]

    lineas = [
        "# Informe de métricas — Sistema Experto de Evaluación Prequirúrgica",
        "",
        f"**Fecha de ejecución:** {fecha}  ",
        f"**Casos evaluados:** {resumen.total_casos}  ",
        f"**Motor:** encadenamiento hacia adelante + lógica difusa (reglas R1–R34, validación R35)",
        "",
        "---",
        "",
        "## 1. Resumen ejecutivo",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| **Tasa de acierto del diagnóstico** | **{resumen.tasa_acierto:.2f}%** ({resumen.casos_correctos}/{resumen.total_casos}) |",
        f"| **Tiempo promedio de inferencia** | **{resumen.tiempo_promedio_ms:.3f} ms** |",
        f"| Tiempo mínimo / máximo | {resumen.tiempo_min_ms:.3f} ms / {resumen.tiempo_max_ms:.3f} ms |",
        f"| **Porcentaje de casos derivados a incertidumbre** | **{resumen.porcentaje_incertidumbre:.2f}%** ({resumen.casos_incertidumbre}/{resumen.total_casos}) |",
        f"| Incertidumbre (solo datos completos) | {resumen.porcentaje_incertidumbre_datos_completos:.2f}% ({resumen.incertidumbre_datos_completos}/{resumen.casos_datos_completos}) |",
        "",
        "---",
        "",
        "## 2. Definición de métricas",
        "",
        "### 2.1 Tasa de acierto del diagnóstico",
        "",
        "Proporción de casos en los que la salida del motor coincide con el **gold standard**",
        "predefinido en `tests/casos_benchmark.py` (clasificación preliminar, nivel de riesgo,",
        "adecuación del procedimiento y, cuando aplica, conductas clave). Los campos esperados",
        "en `None` no se exigen en la comparación.",
        "",
        "### 2.2 Tiempo promedio de inferencia",
        "",
        "Promedio del tiempo de CPU medido con `time.perf_counter()` alrededor de una llamada",
        "completa a `MotorInferencias.evaluar()`, incluyendo validación, cálculo de variables,",
        "fuzzificación, aplicación de reglas y generación del resultado.",
        "",
        "### 2.3 Porcentaje de casos derivados a incertidumbre",
        "",
        "Proporción de ejecuciones cuya clasificación final pertenece al conjunto de salidas",
        "**no conclusivas**, en las que el sistema no emite una recomendación preliminar definida:",
        "",
        f"- {', '.join(f'«{c}»' for c in sorted(CLASIFICACIONES_INCERTIDUMBRE))}",
        "",
        "En la práctica, la regla **R35** (información insuficiente) concentra estos casos cuando",
        "faltan datos obligatorios del paciente.",
        "",
        "---",
        "",
        "## 3. Metodología",
        "",
        "1. **Gold standard:** conjunto fijo de perfiles clínicos (consigna + sintéticos + datos incompletos).",
        "2. **Simulación masiva:** cada perfil se evalúa de forma automática sin intervención manual.",
        "3. **Comparación:** resultado obtenido vs. esperado campo a campo.",
        "4. **Grupos:** consigna (6), favorables, optimización, postergar, no recomendado, incertidumbre.",
        "",
        "Los casos de incertidumbre (`grupo: incertidumbre`) se diseñaron **a propósito** con datos",
        "faltantes; un acierto en esos casos implica que el sistema respondió «información insuficiente».",
        "",
        "---",
        "",
        "## 4. Resultados por grupo",
        "",
        "| Grupo | Casos | Acierto | % Acierto | % Incertidumbre (salida) |",
        "|-------|------:|--------:|----------:|-------------------------:|",
    ]

    orden_grupos = sorted(por_grupo.keys())
    for g in orden_grupos:
        d = por_grupo[g]
        lineas.append(
            f"| {g} | {int(d['total'])} | {int(d['correctos'])} | "
            f"{d['tasa_acierto']:.1f}% | {d['pct_incertidumbre']:.1f}% |"
        )

    lineas.extend([
        "",
        "---",
        "",
        "## 5. Distribución de clasificaciones obtenidas",
        "",
        "| Clasificación | Cantidad | % |",
        "|---------------|----------|---|",
    ])

    conteo_clas: dict[str, int] = {}
    for r in resumen.resultados:
        conteo_clas[r.clasificacion] = conteo_clas.get(r.clasificacion, 0) + 1
    for clas, n in sorted(conteo_clas.items(), key=lambda x: -x[1]):
        pct = n / resumen.total_casos * 100
        lineas.append(f"| {clas} | {n} | {pct:.1f}% |")

    lineas.extend([
        "",
        "---",
        "",
        "## 6. Casos con discrepancia (gold standard vs. motor)",
        "",
    ])

    if not fallos:
        lineas.append("*No se registraron discrepancias: 100% de acierto.*")
    else:
        lineas.append(f"Total de discrepancias: **{len(fallos)}**")
        lineas.append("")
        lineas.append("| ID | Grupo | Caso | Detalle |")
        lineas.append("|----|-------|------|---------|")
        for r in fallos[:40]:
            det = "; ".join(r.detalles_fallo) if r.detalles_fallo else "—"
            lineas.append(f"| {r.id} | {r.grupo} | {r.nombre[:50]} | {det} |")
        if len(fallos) > 40:
            lineas.append(f"| … | | *({len(fallos) - 40} casos adicionales)* | |")

    lineas.extend([
        "",
        "---",
        "",
        "## 7. Conclusiones",
        "",
    ])

    if resumen.tasa_acierto >= 95:
        lineas.append(
            f"- La **tasa de acierto ({resumen.tasa_acierto:.1f}%)** indica alta concordancia "
            "entre el comportamiento del motor y el gold standard definido."
        )
    elif resumen.tasa_acierto >= 80:
        lineas.append(
            f"- La **tasa de acierto ({resumen.tasa_acierto:.1f}%)** es aceptable; revisar "
            "los casos fallidos en la sección 6 para ajustar reglas o expectativas."
        )
    else:
        lineas.append(
            f"- La **tasa de acierto ({resumen.tasa_acierto:.1f}%)** sugiere revisar reglas "
            "o el gold standard de los casos sintéticos."
        )

    lineas.append(
        f"- El **tiempo promedio de inferencia ({resumen.tiempo_promedio_ms:.3f} ms)** "
        "permite uso interactivo en consulta sin latencia perceptible."
    )

    lineas.append(
        f"- El **{resumen.porcentaje_incertidumbre:.1f}% de salidas en incertidumbre** "
        "refleja principalmente los casos con datos incompletos del grupo de prueba; "
        "en producción este porcentaje dependerá de la calidad de carga de datos."
    )

    lineas.extend([
        "",
        "---",
        "",
        "*Informe generado automáticamente por `python -m tests.evaluar_metricas`.*",
    ])

    return "\n".join(lineas)


def main() -> int:
    print("Evaluando banco de benchmark...")
    print(f"  Casos cargados: {len(CASOS_BENCHMARK)}")

    resumen = evaluar_banco(CASOS_BENCHMARK)

    print()
    print("=" * 60)
    print("MÉTRICAS")
    print("=" * 60)
    print(f"  Tasa de acierto              : {resumen.tasa_acierto:.2f}%")
    print(f"  Tiempo promedio de inferencia : {resumen.tiempo_promedio_ms:.3f} ms")
    print(f"  % incertidumbre (total)       : {resumen.porcentaje_incertidumbre:.2f}%")
    print(f"  % incertidumbre (datos completos): {resumen.porcentaje_incertidumbre_datos_completos:.2f}%")
    print("=" * 60)

    informe = _generar_informe(resumen)
    INFORME_PATH.parent.mkdir(parents=True, exist_ok=True)
    INFORME_PATH.write_text(informe, encoding="utf-8")
    print(f"\nInforme guardado en: {INFORME_PATH}")

    return 0 if resumen.casos_correctos == resumen.total_casos else 1


if __name__ == "__main__":
    sys.exit(main())
