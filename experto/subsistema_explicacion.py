"""
subsistema_explicacion.py
-------------------------
Subsistema de Explicación.

Genera una explicación clara y trazable en lenguaje natural a partir de la
Memoria de Trabajo. Incluye:
    - Resultado principal (clasificación, riesgo, adecuación, conductas).
    - Datos calculados.
    - Factores favorables y de alerta.
    - Reglas activadas.
    - Reglas críticas descartadas (qué condiciones críticas se evaluaron
      y no se activaron).
    - Texto en lenguaje natural.
"""

from typing import Dict, List


CRITICAS_INFO = [
    ("R1", "Enfermedad no controlada", "enfermedad_no_controlada", "sí"),
    ("R2", "Embarazo actual", "embarazo_actual_o_futuro_cercano", "embarazo actual"),
    ("R8", "Tabaquismo sin disposición a dejar", None, None),
    ("R10", "Consumo problemático sin disposición a dejar", None, None),
    ("R29", "Expectativas irreales", "expectativas", "irreales"),
    ("R4", "Riesgo tromboembólico aumentado", None, None),
]


class SubsistemaExplicacion:
    """Generador de explicación trazable en lenguaje natural."""

    def reglas_criticas_descartadas(self, memoria) -> List[Dict[str, str]]:
        """
        Lista las reglas críticas que NO se activaron, para dar trazabilidad
        (por ejemplo: "enfermedad no controlada NO detectada").
        """
        activadas = {r["codigo"] for r in memoria.reglas_activadas}
        descartadas = []

        if "R1" not in activadas and memoria.obtener("paciente", "enfermedad_no_controlada") == "no":
            descartadas.append({"codigo": "R1", "descripcion": "Enfermedad no controlada no detectada"})
        if "R2" not in activadas:
            descartadas.append({"codigo": "R2", "descripcion": "Embarazo actual no detectado"})
        if "R3" not in activadas:
            descartadas.append({"codigo": "R3", "descripcion": "Embarazo futuro cercano + abdominoplastía no detectado"})
        if "R4" not in activadas:
            descartadas.append({"codigo": "R4", "descripcion": "Riesgo tromboembólico aumentado no detectado"})
        if "R8" not in activadas and "R10" not in activadas:
            descartadas.append({"codigo": "R8/R10", "descripcion": "Falta de disposición a abandonar hábitos no detectada"})
        if "R29" not in activadas and memoria.obtener("paciente", "expectativas") != "irreales":
            descartadas.append({"codigo": "R29", "descripcion": "Expectativas irreales no detectadas"})
        if "R9" not in activadas and memoria.obtener("paciente", "consumo_problematico_sustancias") == "no":
            descartadas.append({"codigo": "R9", "descripcion": "Consumo problemático de sustancias no detectado"})

        return descartadas

    def generar(self, memoria, clasificacion: str, nivel_riesgo: Dict,
                adecuacion: Dict, datos_calculados: Dict) -> str:
        """
        Devuelve una explicación en lenguaje natural.
        """
        paciente_proc = memoria.obtener("paciente", "procedimiento_deseado") or "el procedimiento solicitado"

        partes: List[str] = []

        partes.append(
            f"El sistema clasifica al paciente como **{clasificacion}**."
        )

        partes.append(
            f"El procedimiento solicitado ({paciente_proc}) se considera "
            f"**{adecuacion.get('categoria', 'no determinado')}** "
            f"(valor difuso ≈ {adecuacion.get('valor')})."
        )

        partes.append(
            f"El nivel de riesgo estimado es **{nivel_riesgo.get('categoria')}** "
            f"(valor difuso ≈ {nivel_riesgo.get('valor')})."
        )

        partes.append(
            f"IMC calculado: {datos_calculados.get('imc_calculado')} "
            f"({datos_calculados.get('categoria_imc')}). "
            f"Fluctuación de peso en los últimos 6 meses: "
            f"{datos_calculados.get('fluctuacion_peso_calculada')}% "
            f"({datos_calculados.get('estabilidad_peso')})."
        )

        if memoria.factores_favorables:
            partes.append(
                "Factores favorables: " + "; ".join(memoria.factores_favorables) + "."
            )

        if memoria.factores_alerta:
            partes.append(
                "Factores de alerta: " + "; ".join(memoria.factores_alerta) + "."
            )

        if memoria.conductas_sugeridas:
            partes.append(
                "Conductas sugeridas: " + "; ".join(memoria.conductas_sugeridas) + "."
            )

        if memoria.reglas_activadas:
            cods = ", ".join(r["codigo"] for r in memoria.reglas_activadas)
            partes.append(f"Reglas activadas: {cods}.")

        # Cierre
        partes.append(
            "Esta evaluación es una herramienta de apoyo y no reemplaza la "
            "decisión médica del cirujano plástico."
        )

        return " ".join(partes)
