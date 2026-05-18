"""
metricas.py
-----------
Utilidades para evaluar el sistema experto: comparación con gold standard,
medición de tiempos y detección de incertidumbre.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from experto.motor_inferencias import MotorInferencias
from experto.modelos import DatosPaciente

# Clasificaciones sin recomendación concluyente (R35 / dominio no resuelto)
CLASIFICACIONES_INCERTIDUMBRE = frozenset({
    "información insuficiente",
    "fuera del dominio",
})


@dataclass
class ResultadoCaso:
    id: str
    nombre: str
    grupo: str
    correcto: bool
    tiempo_ms: float
    es_incertidumbre: bool
    clasificacion: str
    esperado: Dict[str, Any]
    obtenido: Dict[str, Any]
    detalles_fallo: List[str] = field(default_factory=list)


@dataclass
class ResumenMetricas:
    total_casos: int
    casos_correctos: int
    tasa_acierto: float
    tiempo_promedio_ms: float
    tiempo_min_ms: float
    tiempo_max_ms: float
    casos_incertidumbre: int
    porcentaje_incertidumbre: float
    casos_datos_completos: int
    incertidumbre_datos_completos: int
    porcentaje_incertidumbre_datos_completos: float
    resultados: List[ResultadoCaso] = field(default_factory=list)

    def por_grupo(self) -> Dict[str, Dict[str, float]]:
        grupos: Dict[str, Dict[str, float]] = {}
        for r in self.resultados:
            if r.grupo not in grupos:
                grupos[r.grupo] = {"total": 0, "correctos": 0, "incertidumbre": 0}
            grupos[r.grupo]["total"] += 1
            if r.correcto:
                grupos[r.grupo]["correctos"] += 1
            if r.es_incertidumbre:
                grupos[r.grupo]["incertidumbre"] += 1
        for g in grupos.values():
            t = g["total"]
            g["tasa_acierto"] = (g["correctos"] / t * 100) if t else 0.0
            g["pct_incertidumbre"] = (g["incertidumbre"] / t * 100) if t else 0.0
        return grupos


def _ok(actual: Any, esperado: Any) -> bool:
    if esperado is None:
        return True
    return actual == esperado


def _contiene_conductas(conductas: List[str], claves: List[str]) -> bool:
    if not claves:
        return True
    texto = " ".join(conductas).lower()
    return all(clave.lower() in texto for clave in claves)


def caso_coincide_con_esperado(resultado: Dict, esperado: Dict) -> tuple[bool, List[str]]:
    """Compara salida del motor con el gold standard del caso."""
    fallos: List[str] = []

    clas = resultado.get("clasificacion_preliminar")
    esp_clas = esperado.get("clasificacion_preliminar")
    if not _ok(clas, esp_clas):
        fallos.append(f"clasificación: obtuvo «{clas}», esperado «{esp_clas}»")

    riesgo = resultado.get("nivel_riesgo", {}).get("categoria")
    if not _ok(riesgo, esperado.get("nivel_riesgo")):
        fallos.append(f"riesgo: obtuvo «{riesgo}», esperado «{esperado.get('nivel_riesgo')}»")

    ade = resultado.get("adecuacion_procedimiento", {}).get("categoria")
    if not _ok(ade, esperado.get("adecuacion_procedimiento")):
        fallos.append(
            f"adecuación: obtuvo «{ade}», esperado «{esperado.get('adecuacion_procedimiento')}»"
        )

    if esperado.get("incertidumbre"):
        if clas not in CLASIFICACIONES_INCERTIDUMBRE:
            fallos.append(
                f"incertidumbre: se esperaba clasificación en {CLASIFICACIONES_INCERTIDUMBRE}"
            )
    elif esp_clas in CLASIFICACIONES_INCERTIDUMBRE:
        if clas != esp_clas:
            fallos.append(f"clasificación incertidumbre: obtuvo «{clas}»")

    conductas = resultado.get("conducta_sugerida", [])
    claves = esperado.get("conductas_clave", [])
    if claves and not _contiene_conductas(conductas, claves):
        fallos.append(f"conductas: no contiene todas las claves {claves}")

    return (len(fallos) == 0, fallos)


def evaluar_banco(
    casos: List[Dict],
    motor: Optional[MotorInferencias] = None,
) -> ResumenMetricas:
    """Ejecuta todos los casos y calcula las métricas agregadas."""
    motor = motor or MotorInferencias()
    resultados: List[ResultadoCaso] = []
    tiempos: List[float] = []

    for caso in casos:
        datos: DatosPaciente = caso["datos"]
        esperado = caso["esperado"]

        inicio = time.perf_counter()
        salida = motor.evaluar(datos)
        fin = time.perf_counter()
        tiempo_ms = (fin - inicio) * 1000
        tiempos.append(tiempo_ms)

        clas = salida.get("clasificacion_preliminar", "")
        es_incert = clas in CLASIFICACIONES_INCERTIDUMBRE
        correcto, fallos = caso_coincide_con_esperado(salida, esperado)

        resultados.append(
            ResultadoCaso(
                id=caso.get("id", "?"),
                nombre=caso.get("nombre", ""),
                grupo=caso.get("grupo", "general"),
                correcto=correcto,
                tiempo_ms=tiempo_ms,
                es_incertidumbre=es_incert,
                clasificacion=clas,
                esperado=esperado,
                obtenido={
                    "clasificacion_preliminar": clas,
                    "nivel_riesgo": salida.get("nivel_riesgo", {}).get("categoria"),
                    "adecuacion_procedimiento": salida.get("adecuacion_procedimiento", {}).get("categoria"),
                },
                detalles_fallo=fallos,
            )
        )

    total = len(resultados)
    correctos = sum(1 for r in resultados if r.correcto)
    incert = sum(1 for r in resultados if r.es_incertidumbre)
    completos = [r for r in resultados if r.grupo != "incertidumbre"]
    incert_completos = sum(1 for r in completos if r.es_incertidumbre)
    n_completos = len(completos)

    return ResumenMetricas(
        total_casos=total,
        casos_correctos=correctos,
        tasa_acierto=(correctos / total * 100) if total else 0.0,
        tiempo_promedio_ms=sum(tiempos) / len(tiempos) if tiempos else 0.0,
        tiempo_min_ms=min(tiempos) if tiempos else 0.0,
        tiempo_max_ms=max(tiempos) if tiempos else 0.0,
        casos_incertidumbre=incert,
        porcentaje_incertidumbre=(incert / total * 100) if total else 0.0,
        casos_datos_completos=n_completos,
        incertidumbre_datos_completos=incert_completos,
        porcentaje_incertidumbre_datos_completos=(
            (incert_completos / n_completos * 100) if n_completos else 0.0
        ),
        resultados=resultados,
    )
