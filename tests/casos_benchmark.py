"""
casos_benchmark.py
------------------
Banco ampliado de casos con gold standard (resultado esperado predefinido)
para medir tasa de acierto, tiempo de inferencia e incertidumbre.

Incluye:
  - Los 6 casos de la consigna
  - Variantes clínicas sintéticas (perfiles reproducibles)
  - Casos con datos incompletos (incertidumbre esperada)
"""

from __future__ import annotations

from typing import Any, Dict, List

from experto.modelos import DatosPaciente

from tests.casos_prueba import CASOS as CASOS_CONSIGNA


def _caso(
    id: str,
    nombre: str,
    grupo: str,
    datos: DatosPaciente,
    esperado: Dict[str, Any],
) -> Dict:
    return {"id": id, "nombre": nombre, "grupo": grupo, "datos": datos, "esperado": esperado}


def _favorable(**cambios) -> DatosPaciente:
    """Perfil base de candidato favorable (liposucción, peso estable)."""
    base = dict(
        edad=32,
        sexo_biologico="femenino",
        embarazo_actual_o_futuro_cercano="no",
        procedimiento_deseado="liposucción",
        peso_actual=68.0,
        altura=1.68,
        peso_hace_6_meses=67.5,
        condicion_corporal_observada=["grasa localizada"],
        cicatrizacion="buena",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="no",
        fuma="no",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="no aplica",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="realistas",
    )
    base.update(cambios)
    return DatosPaciente(**base)


def _esperado_favorable() -> Dict[str, Any]:
    return {
        "clasificacion_preliminar": "candidato favorable",
        "nivel_riesgo": "bajo",
        "adecuacion_procedimiento": "adecuado",
        "conductas_clave": ["avanzar"],
    }


def _consigna_a_benchmark() -> List[Dict]:
    casos = []
    for i, c in enumerate(CASOS_CONSIGNA, start=1):
        casos.append(_caso(
            id=f"C{i:02d}",
            nombre=c["nombre"],
            grupo="consigna",
            datos=c["datos"],
            esperado=c["esperado"],
        ))
    return casos


def _casos_favorables_variantes() -> List[Dict]:
    """Variantes del perfil favorable (liposucción + peso estable + sin alertas)."""
    casos = []
    idx = 1
    for edad in (25, 28, 35, 42, 48):
        casos.append(_caso(
            id=f"F{idx:02d}",
            nombre=f"Favorable — edad {edad}, liposucción",
            grupo="sintetico_favorable",
            datos=_favorable(edad=edad),
            esperado=_esperado_favorable(),
        ))
        idx += 1
    for cic in ("normal", "buena"):
        casos.append(_caso(
            id=f"F{idx:02d}",
            nombre=f"Favorable — cicatrización {cic}",
            grupo="sintetico_favorable",
            datos=_favorable(cicatrizacion=cic),
            esperado=_esperado_favorable(),
        ))
        idx += 1
    for peso, peso6 in ((65.0, 64.5), (72.0, 71.8), (80.0, 79.5)):
        casos.append(_caso(
            id=f"F{idx:02d}",
            nombre=f"Favorable — peso estable {peso} kg",
            grupo="sintetico_favorable",
            datos=_favorable(peso_actual=peso, peso_hace_6_meses=peso6),
            esperado=_esperado_favorable(),
        ))
        idx += 1
    for sexo, emb in (("masculino", "no aplica"), ("femenino", "no")):
        casos.append(_caso(
            id=f"F{idx:02d}",
            nombre=f"Favorable — {sexo}",
            grupo="sintetico_favorable",
            datos=_favorable(sexo_biologico=sexo, embarazo_actual_o_futuro_cercano=emb),
            esperado=_esperado_favorable(),
        ))
        idx += 1
    return casos


def _casos_optimizacion() -> List[Dict]:
    esp = {
        "clasificacion_preliminar": "candidato con optimización previa",
        "nivel_riesgo": "moderado",
        "adecuacion_procedimiento": "adecuado",
    }
    return [
        _caso(
            "O01", "Tabaco dispuesto a dejar — abdominoplastía", "sintetico_optimizacion",
            DatosPaciente(
                edad=40, sexo_biologico="femenino", embarazo_actual_o_futuro_cercano="no",
                procedimiento_deseado="abdominoplastía", peso_actual=75.0, altura=1.65,
                peso_hace_6_meses=74.5,
                condicion_corporal_observada=["exceso de piel", "flacidez o debilidad de pared abdominal"],
                cicatrizacion="normal", factores_riesgo_especificos=["ninguno"],
                enfermedad_no_controlada="no", fuma="sí", consumo_problematico_sustancias="no",
                dispuesto_a_dejar_habitos_riesgo="sí", antecedentes_quirurgicos="sin antecedentes",
                expectativas="realistas",
            ),
            {**esp, "conductas_clave": ["tabaquismo"]},
        ),
        _caso(
            "O02", "Expectativas poco claras", "sintetico_optimizacion",
            _favorable(expectativas="poco claras"),
            {**esp, "nivel_riesgo": "bajo", "adecuacion_procedimiento": "parcialmente adecuado"},
        ),
        _caso(
            "O03", "Factor hernia sospechada", "sintetico_optimizacion",
            _favorable(factores_riesgo_especificos=["hernia sospechada"]),
            {**esp, "nivel_riesgo": "bajo"},
        ),
        _caso(
            "O04", "IMC elevado estable", "sintetico_optimizacion",
            _favorable(peso_actual=95.0, altura=1.70, peso_hace_6_meses=94.0),
            {**esp, "nivel_riesgo": "moderado"},
        ),
        _caso(
            "O05", "Grasa visceral + liposucción (adecuación no adecuada)", "sintetico_optimizacion",
            DatosPaciente(
                edad=45, sexo_biologico="masculino", embarazo_actual_o_futuro_cercano="no aplica",
                procedimiento_deseado="liposucción", peso_actual=92.0, altura=1.75, peso_hace_6_meses=91.0,
                condicion_corporal_observada=["grasa visceral sospechada"], cicatrizacion="normal",
                factores_riesgo_especificos=["ninguno"], enfermedad_no_controlada="no",
                fuma="no", consumo_problematico_sustancias="no", dispuesto_a_dejar_habitos_riesgo="no aplica",
                antecedentes_quirurgicos="sin antecedentes", expectativas="realistas",
            ),
            {
                "clasificacion_preliminar": "no recomendado por el momento",
                "nivel_riesgo": "bajo",
                "adecuacion_procedimiento": "no adecuado",
                "conductas_clave": ["Redefinir"],
            },
        ),
    ]


def _casos_postergar() -> List[Dict]:
    esp_base = {
        "clasificacion_preliminar": "postergar",
        "adecuacion_procedimiento": "parcialmente adecuado",
    }
    return [
        _caso(
            "P01", "Peso inestable >10%", "sintetico_postergar",
            DatosPaciente(
                edad=38, sexo_biologico="femenino", embarazo_actual_o_futuro_cercano="no",
                procedimiento_deseado="abdominoplastía", peso_actual=78.0, altura=1.65,
                peso_hace_6_meses=68.0, condicion_corporal_observada=["exceso de piel"],
                cicatrizacion="normal", factores_riesgo_especificos=["ninguno"],
                enfermedad_no_controlada="no", fuma="no", consumo_problematico_sustancias="no",
                dispuesto_a_dejar_habitos_riesgo="no aplica", antecedentes_quirurgicos="sin antecedentes",
                expectativas="realistas",
            ),
            {**esp_base, "nivel_riesgo": "alto", "conductas_clave": ["estabilizar peso"]},
        ),
        _caso(
            "P02", "Embarazo actual", "sintetico_postergar",
            _favorable(embarazo_actual_o_futuro_cercano="embarazo actual"),
            {**esp_base, "nivel_riesgo": "bajo", "adecuacion_procedimiento": "adecuado"},
        ),
        _caso(
            "P03", "Embarazo futuro + abdominoplastía", "sintetico_postergar",
            _favorable(
                embarazo_actual_o_futuro_cercano="embarazo futuro cercano",
                procedimiento_deseado="abdominoplastía",
            ),
            {**esp_base, "nivel_riesgo": "bajo", "adecuacion_procedimiento": "no adecuado"},
        ),
        _caso(
            "P04", "Enfermedad no controlada — combinado", "sintetico_postergar",
            DatosPaciente(
                edad=42, sexo_biologico="femenino", embarazo_actual_o_futuro_cercano="no",
                procedimiento_deseado="ambos", peso_actual=80.0, altura=1.66, peso_hace_6_meses=79.0,
                condicion_corporal_observada=["exceso de piel", "grasa localizada"],
                cicatrizacion="normal", factores_riesgo_especificos=["ninguno"],
                enfermedad_no_controlada="sí", fuma="no", consumo_problematico_sustancias="no",
                dispuesto_a_dejar_habitos_riesgo="no aplica", antecedentes_quirurgicos="sin antecedentes",
                expectativas="realistas",
            ),
            {
                "clasificacion_preliminar": "postergar",
                "nivel_riesgo": "moderado",
                "adecuacion_procedimiento": "adecuado",
                "conductas_clave": ["control clínico"],
            },
        ),
        _caso(
            "P05", "Cicatrización muy mala", "sintetico_postergar",
            _favorable(cicatrizacion="muy mala"),
            {**esp_base, "nivel_riesgo": "alto", "adecuacion_procedimiento": "adecuado"},
        ),
        _caso(
            "P06", "Riesgo tromboembólico + peso inestable", "sintetico_postergar",
            DatosPaciente(
                edad=50, sexo_biologico="femenino", embarazo_actual_o_futuro_cercano="no",
                procedimiento_deseado="ambos", peso_actual=85.0, altura=1.60, peso_hace_6_meses=75.0,
                condicion_corporal_observada=["exceso de piel"],
                cicatrizacion="mala", factores_riesgo_especificos=["riesgo tromboembólico aumentado"],
                enfermedad_no_controlada="no", fuma="no", consumo_problematico_sustancias="no",
                dispuesto_a_dejar_habitos_riesgo="no aplica", antecedentes_quirurgicos="sin antecedentes",
                expectativas="realistas",
            ),
            {**esp_base, "nivel_riesgo": "alto"},
        ),
    ]


def _casos_no_recomendado() -> List[Dict]:
    esp = {
        "clasificacion_preliminar": "no recomendado por el momento",
        "nivel_riesgo": "bajo",
        "adecuacion_procedimiento": "adecuado",
    }
    return [
        _caso(
            "N01", "Expectativas irreales", "sintetico_no_recomendado",
            _favorable(expectativas="irreales"),
            {**esp, "nivel_riesgo": None, "adecuacion_procedimiento": None, "conductas_clave": ["expectativas"]},
        ),
        _caso(
            "N02", "Tabaco sin disposición a dejar", "sintetico_no_recomendado",
            _favorable(fuma="sí", dispuesto_a_dejar_habitos_riesgo="no"),
            {**esp, "conductas_clave": ["tabaco"]},
        ),
        _caso(
            "N03", "Consumo problemático sin disposición", "sintetico_no_recomendado",
            _favorable(consumo_problematico_sustancias="sí", dispuesto_a_dejar_habitos_riesgo="no"),
            esp,
        ),
        _caso(
            "N04", "Tabaco + consumo sin disposición", "sintetico_no_recomendado",
            _favorable(
                fuma="sí", consumo_problematico_sustancias="sí",
                dispuesto_a_dejar_habitos_riesgo="no",
            ),
            esp,
        ),
    ]


def _casos_incertidumbre() -> List[Dict]:
    """Datos incompletos: el sistema no debe emitir recomendación concluyente."""
    esp = {
        "clasificacion_preliminar": "información insuficiente",
        "nivel_riesgo": None,
        "adecuacion_procedimiento": None,
        "incertidumbre": True,
    }
    casos = []

    def incompleto(**cambios) -> DatosPaciente:
        params = _favorable().__dict__
        params.update(cambios)
        return DatosPaciente(**params)

    escenarios = [
        ("U01", "Sin altura", {"altura": None}),
        ("U02", "Sin peso actual", {"peso_actual": None}),
        ("U03", "Sin peso hace 6 meses", {"peso_hace_6_meses": None}),
        ("U04", "Sin edad", {"edad": None}),
        ("U05", "Sin procedimiento", {"procedimiento_deseado": None}),
        ("U06", "Sin cicatrización", {"cicatrizacion": None}),
        ("U07", "Sin expectativas", {"expectativas": None}),
        ("U08", "Sin sexo biológico", {"sexo_biologico": None}),
        ("U09", "Sin embarazo", {"embarazo_actual_o_futuro_cercano": None}),
        ("U10", "Solo edad y sexo", {
            "edad": 30, "sexo_biologico": "femenino",
            "embarazo_actual_o_futuro_cercano": None, "procedimiento_deseado": None,
            "peso_actual": None, "altura": None, "peso_hace_6_meses": None,
            "cicatrizacion": None, "enfermedad_no_controlada": None,
            "fuma": None, "consumo_problematico_sustancias": None,
            "dispuesto_a_dejar_habitos_riesgo": None, "antecedentes_quirurgicos": None,
            "expectativas": None,
        }),
        ("U11", "Peso y altura en cero", {"peso_actual": 0, "altura": 0}),
        ("U12", "Sin hábitos ni enfermedad", {
            "enfermedad_no_controlada": None, "fuma": None,
            "consumo_problematico_sustancias": None, "dispuesto_a_dejar_habitos_riesgo": None,
        }),
    ]
    for id_, nombre, cambios in escenarios:
        casos.append(_caso(id_, nombre, "incertidumbre", incompleto(**cambios), esp))
    return casos


def construir_banco_benchmark() -> List[Dict]:
    """Arma el banco completo de evaluación."""
    return (
        _consigna_a_benchmark()
        + _casos_favorables_variantes()
        + _casos_optimizacion()
        + _casos_postergar()
        + _casos_no_recomendado()
        + _casos_incertidumbre()
    )


# Banco exportado (≈ 50+ casos)
CASOS_BENCHMARK: List[Dict] = construir_banco_benchmark()
