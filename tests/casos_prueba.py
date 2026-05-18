"""
casos_prueba.py
---------------
Define los 6 casos de prueba descritos en la consigna, con sus entradas
y resultados esperados (clasificación, riesgo y adecuación).

Cada caso es un diccionario:
    {
        "nombre": "...",
        "datos": DatosPaciente(...),
        "esperado": {
            "clasificacion_preliminar": "...",
            "nivel_riesgo": "bajo|moderado|alto",
            "adecuacion_procedimiento": "adecuado|parcialmente adecuado|no adecuado",
            "conductas_clave": ["substring1", ...]   # frases que deben aparecer
        }
    }
"""

from experto.modelos import DatosPaciente


CASOS = []


# CASO 1: candidato favorable
CASOS.append({
    "nombre": "CASO 1 — Candidato favorable (liposucción)",
    "datos": DatosPaciente(
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
    ),
    "esperado": {
        "clasificacion_preliminar": "candidato favorable",
        "nivel_riesgo": "bajo",
        "adecuacion_procedimiento": "adecuado",
        "conductas_clave": ["avanzar"],
    },
})


# CASO 2: candidato con optimización previa (tabaco + abdominoplastía)
CASOS.append({
    "nombre": "CASO 2 — Candidato con optimización previa (abdominoplastía + tabaco)",
    "datos": DatosPaciente(
        edad=40,
        sexo_biologico="femenino",
        embarazo_actual_o_futuro_cercano="no",
        procedimiento_deseado="abdominoplastía",
        peso_actual=75.0,
        altura=1.65,   # IMC ~ 27.5 (moderadamente elevado)
        peso_hace_6_meses=74.5,
        condicion_corporal_observada=["exceso de piel", "flacidez o debilidad de pared abdominal"],
        cicatrizacion="normal",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="no",
        fuma="sí",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="sí",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="realistas",
    ),
    "esperado": {
        "clasificacion_preliminar": "candidato con optimización previa",
        "nivel_riesgo": "moderado",
        "adecuacion_procedimiento": "adecuado",
        "conductas_clave": ["Suspender tabaquismo"],
    },
})


# CASO 3: postergar por peso inestable
CASOS.append({
    "nombre": "CASO 3 — Postergar por peso inestable (abdominoplastía)",
    "datos": DatosPaciente(
        edad=38,
        sexo_biologico="femenino",
        embarazo_actual_o_futuro_cercano="no",
        procedimiento_deseado="abdominoplastía",
        peso_actual=78.0,
        altura=1.65,        # IMC ~ 28.6
        peso_hace_6_meses=68.0,   # fluctuación ~ 14.7%  => inestable
        condicion_corporal_observada=["exceso de piel"],
        cicatrizacion="normal",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="no",
        fuma="no",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="no aplica",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="realistas",
    ),
    "esperado": {
        "clasificacion_preliminar": "postergar",
        "nivel_riesgo": "alto",
        "adecuacion_procedimiento": "parcialmente adecuado",
        "conductas_clave": ["estabilizar peso"],
    },
})


# CASO 4: no recomendado por expectativas irreales
CASOS.append({
    "nombre": "CASO 4 — No recomendado por expectativas irreales (liposucción)",
    "datos": DatosPaciente(
        edad=29,
        sexo_biologico="femenino",
        embarazo_actual_o_futuro_cercano="no",
        procedimiento_deseado="liposucción",
        peso_actual=62.0,
        altura=1.65,
        peso_hace_6_meses=62.0,
        condicion_corporal_observada=["grasa localizada"],
        cicatrizacion="buena",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="no",
        fuma="no",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="no aplica",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="irreales",
    ),
    "esperado": {
        "clasificacion_preliminar": "no recomendado por el momento",
        "nivel_riesgo": None,  # no relevante para este caso
        "adecuacion_procedimiento": None,
        "conductas_clave": ["Orientación", "expectativas"],
    },
})


# CASO 5: procedimiento no adecuado (grasa visceral)
CASOS.append({
    "nombre": "CASO 5 — Procedimiento no adecuado (grasa visceral)",
    "datos": DatosPaciente(
        edad=45,
        sexo_biologico="masculino",
        embarazo_actual_o_futuro_cercano="no aplica",
        procedimiento_deseado="liposucción",
        peso_actual=92.0,
        altura=1.75,   # IMC ~ 30
        peso_hace_6_meses=91.0,
        condicion_corporal_observada=["grasa visceral sospechada"],
        cicatrizacion="normal",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="no",
        fuma="no",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="no aplica",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="realistas",
    ),
    "esperado": {
        "clasificacion_preliminar": "no recomendado por el momento",
        "nivel_riesgo": "bajo",
        "adecuacion_procedimiento": "no adecuado",
        "conductas_clave": ["Redefinir"],
    },
})


# CASO 6: enfermedad no controlada -> postergar
CASOS.append({
    "nombre": "CASO 6 — Postergar por enfermedad no controlada (combinado)",
    "datos": DatosPaciente(
        edad=42,
        sexo_biologico="femenino",
        embarazo_actual_o_futuro_cercano="no",
        procedimiento_deseado="ambos",
        peso_actual=80.0,
        altura=1.66,
        peso_hace_6_meses=79.0,
        condicion_corporal_observada=["exceso de piel", "grasa localizada"],
        cicatrizacion="normal",
        factores_riesgo_especificos=["ninguno"],
        enfermedad_no_controlada="sí",
        fuma="no",
        consumo_problematico_sustancias="no",
        dispuesto_a_dejar_habitos_riesgo="no aplica",
        antecedentes_quirurgicos="sin antecedentes",
        expectativas="realistas",
    ),
    "esperado": {
        "clasificacion_preliminar": "postergar",
        "nivel_riesgo": None,
        "adecuacion_procedimiento": None,
        "conductas_clave": ["control clínico"],
    },
})
