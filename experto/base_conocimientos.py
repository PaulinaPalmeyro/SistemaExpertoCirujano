"""
base_conocimientos.py
---------------------
Base de Conocimientos del Sistema Experto.

Contiene:
    - Conjuntos difusos para IMC, estabilidad de peso, cicatrización,
      expectativas, nivel de riesgo y adecuación del procedimiento.
    - Reglas expertas R1..R35 organizadas por grupo de prioridad:
        1. Reglas críticas de seguridad        (R1..R6)
        2. Reglas de hábitos y disposición     (R7..R10)
        3. Reglas de adecuación del procedimiento (R11..R18)
        4. Reglas de riesgo difuso             (R19..R26)
        5. Reglas de expectativas              (R27..R29)
        6. Reglas de clasificación final       (R30..R34)
      (R35 - información insuficiente - se trata como validación técnica
       en el motor, no como regla médica.)

Cada regla es un diccionario con:
    {
        "codigo": "R1",
        "descripcion": "Texto descriptivo",
        "prioridad": 1,                       # grupo de prioridad
        "condicion": callable(memoria) -> bool,
        "accion":   callable(memoria) -> None,
        "efecto":   "Texto que describe el efecto"
    }

La función `accion` modifica la memoria de trabajo agregando hechos,
factores favorables/alerta, conductas sugeridas y conclusiones parciales.
"""

from typing import Callable, Dict, List

from .logica_difusa import (
    ConjuntoDifuso,
    VariableLinguistica,
    triangular,
    trapezoidal,
)


# ===========================================================================
# CONJUNTOS DIFUSOS
# ===========================================================================

# --- IMC: universo 16-45 ---------------------------------------------------
VARIABLE_IMC = VariableLinguistica(
    nombre="imc",
    conjuntos=[
        ConjuntoDifuso("bajo",                  lambda x: trapezoidal(x, 16, 16, 18, 19.5)),
        ConjuntoDifuso("normal-aceptable",      lambda x: trapezoidal(x, 18.5, 20, 27, 29)),
        ConjuntoDifuso("moderadamente elevado", lambda x: triangular(x, 27, 30, 33)),
        ConjuntoDifuso("elevado",               lambda x: triangular(x, 31, 34.5, 38)),
        ConjuntoDifuso("muy elevado",           lambda x: trapezoidal(x, 36, 39, 45, 45)),
    ],
)

# --- Estabilidad del peso (fluctuación %): universo 0-20 -------------------
VARIABLE_ESTABILIDAD = VariableLinguistica(
    nombre="estabilidad_peso",
    conjuntos=[
        ConjuntoDifuso("estable",      lambda x: trapezoidal(x, 0, 0, 3, 5)),
        ConjuntoDifuso("poco estable", lambda x: triangular(x, 4, 7.5, 11)),
        ConjuntoDifuso("inestable",    lambda x: trapezoidal(x, 9, 12, 20, 20)),
    ],
)

# --- Cicatrización: universo 0-10 ------------------------------------------
VARIABLE_CICATRIZACION = VariableLinguistica(
    nombre="cicatrizacion",
    conjuntos=[
        ConjuntoDifuso("muy mala", lambda x: trapezoidal(x, 0, 0, 1.5, 3)),
        ConjuntoDifuso("mala",     lambda x: triangular(x, 2, 3.5, 5)),
        ConjuntoDifuso("normal",   lambda x: triangular(x, 4, 6, 8)),
        ConjuntoDifuso("buena",    lambda x: trapezoidal(x, 7, 8.5, 10, 10)),
    ],
)

# --- Expectativas: universo 0-10 -------------------------------------------
VARIABLE_EXPECTATIVAS = VariableLinguistica(
    nombre="expectativas",
    conjuntos=[
        ConjuntoDifuso("irreales",    lambda x: trapezoidal(x, 0, 0, 2, 4)),
        ConjuntoDifuso("poco claras", lambda x: triangular(x, 3, 5, 7)),
        ConjuntoDifuso("realistas",   lambda x: trapezoidal(x, 6, 8, 10, 10)),
    ],
)

# --- Salida: nivel de riesgo (0-100) ---------------------------------------
CONJUNTOS_RIESGO: List[ConjuntoDifuso] = [
    ConjuntoDifuso("bajo",     lambda x: trapezoidal(x, 0, 0, 25, 40)),
    ConjuntoDifuso("moderado", lambda x: triangular(x, 30, 50, 70)),
    ConjuntoDifuso("alto",     lambda x: trapezoidal(x, 60, 75, 100, 100)),
]
UNIVERSO_RIESGO = (0.0, 100.0)

# --- Salida: adecuación del procedimiento (0-100) --------------------------
CONJUNTOS_ADECUACION: List[ConjuntoDifuso] = [
    ConjuntoDifuso("no adecuado",            lambda x: trapezoidal(x, 0, 0, 25, 40)),
    ConjuntoDifuso("parcialmente adecuado",  lambda x: triangular(x, 30, 50, 70)),
    ConjuntoDifuso("adecuado",               lambda x: trapezoidal(x, 60, 75, 100, 100)),
]
UNIVERSO_ADECUACION = (0.0, 100.0)


# ===========================================================================
# Helpers para escribir las reglas con menos verbosidad.
# Reciben la memoria de trabajo, leen hechos y devuelven valores.
# ===========================================================================

def _e(memoria, atributo, default=None):
    """Lee un atributo del paciente (datos de entrada)."""
    return memoria.obtener("paciente", atributo, default)


def _c(memoria, atributo, default=None):
    """Lee un atributo calculado por el sistema."""
    return memoria.obtener("sistema", atributo, default)


def _en_lista(valor, opcion) -> bool:
    if valor is None:
        return False
    if isinstance(valor, list):
        return opcion in valor
    return valor == opcion


# Umbrales regla difusa R33B (coherencia procedimiento–clasificación)
_UMBRAL_MU_NO_ADECUADO = 0.7
_UMBRAL_MU_INCOMPATIBILIDAD = 0.6


def _grado_no_adecuado(memoria) -> float:
    """Grado difuso de «no adecuado» desde activaciones o valor defuzzificado."""
    activacion = memoria.activaciones_adecuacion.get("no adecuado", 0.0)
    if activacion > 0:
        return activacion
    valor = _c(memoria, "adecuacion_valor")
    if valor is None:
        return 0.0
    for conjunto in CONJUNTOS_ADECUACION:
        if conjunto.etiqueta == "no adecuado":
            return conjunto.grado(valor)
    return 0.0


def _grado_incompatibilidad_procedimiento(memoria) -> float:
    """
    Grado de incompatibilidad anatómica entre procedimiento deseado y hallazgos.
    1.0 = incompatibilidad clara (p. ej. liposucción + grasa visceral).
    """
    condicion = _e(memoria, "condicion_corporal_observada", [])
    procedimiento = _e(memoria, "procedimiento_deseado")
    grado = 0.0

    if procedimiento == "liposucción" and "grasa visceral sospechada" in condicion:
        grado = max(grado, 1.0)
    if (
        procedimiento == "liposucción"
        and "exceso de piel" in condicion
        and "grasa localizada" not in condicion
        and "grasa visceral sospechada" not in condicion
    ):
        grado = max(grado, 0.75)

    return grado


def _coherencia_procedimiento_alta(memoria) -> bool:
    """True si aplica la regla difusa de coherencia (R33B)."""
    if _c(memoria, "adecuacion_categoria") != "no adecuado":
        return False
    mu_no_adecuado = _grado_no_adecuado(memoria)
    mu_incompatibilidad = _grado_incompatibilidad_procedimiento(memoria)
    grado_activacion = min(mu_no_adecuado, mu_incompatibilidad)

    memoria.fijar("sistema", "coherencia_mu_no_adecuado", round(mu_no_adecuado, 3))
    memoria.fijar("sistema", "coherencia_mu_incompatibilidad", round(mu_incompatibilidad, 3))
    memoria.fijar("sistema", "coherencia_grado_activacion", round(grado_activacion, 3))

    return (
        mu_no_adecuado >= _UMBRAL_MU_NO_ADECUADO
        and mu_incompatibilidad >= _UMBRAL_MU_INCOMPATIBILIDAD
    )


# ===========================================================================
# Definición de reglas (R1..R34, R33B)
# Cada regla es un dict consumible por el Motor de Inferencias.
# ===========================================================================

REGLAS: List[Dict] = []


def _registrar(codigo, descripcion, prioridad, condicion, accion, efecto):
    REGLAS.append({
        "codigo": codigo,
        "descripcion": descripcion,
        "prioridad": prioridad,
        "condicion": condicion,
        "accion": accion,
        "efecto": efecto,
    })


# ---------------------------------------------------------------------------
# GRUPO 1 - REGLAS CRÍTICAS DE SEGURIDAD
# ---------------------------------------------------------------------------

def _r1_cond(m): return _e(m, "enfermedad_no_controlada") == "sí"
def _r1_acc(m):
    m.fijar_clasificacion("postergar", prioridad=1, origen="R1")
    m.agregar_conducta("Realizar control clínico previo de la enfermedad antes de avanzar")
    m.agregar_alerta("Enfermedad no controlada")
_registrar("R1", "Enfermedad no controlada", 1, _r1_cond, _r1_acc,
           "Clasifica como POSTERGAR y exige control clínico previo")


def _r2_cond(m):
    return (_e(m, "sexo_biologico") == "femenino"
            and _e(m, "embarazo_actual_o_futuro_cercano") == "embarazo actual")
def _r2_acc(m):
    m.fijar_clasificacion("postergar", prioridad=1, origen="R2")
    m.agregar_conducta("Postergar la cirugía estética: embarazo actual")
    m.agregar_alerta("Embarazo actual")
_registrar("R2", "Embarazo actual", 1, _r2_cond, _r2_acc,
           "Clasifica como POSTERGAR por embarazo actual")


def _r3_cond(m):
    return (_e(m, "sexo_biologico") == "femenino"
            and _e(m, "embarazo_actual_o_futuro_cercano") == "embarazo futuro cercano"
            and _e(m, "procedimiento_deseado") in ("abdominoplastía", "ambos"))
def _r3_acc(m):
    m.fijar_clasificacion("postergar", prioridad=1, origen="R3")
    m.agregar_conducta("Postergar: embarazo futuro cercano y procedimiento abdominal")
    m.agregar_alerta("Embarazo futuro cercano + abdominoplastía / combinado")
_registrar("R3", "Embarazo futuro cercano en abdominoplastía", 1, _r3_cond, _r3_acc,
           "Clasifica como POSTERGAR por embarazo futuro cercano y procedimiento abdominal")


def _r4_cond(m):
    return _en_lista(_e(m, "factores_riesgo_especificos"), "riesgo tromboembólico aumentado")
def _r4_acc(m):
    m.fijar_riesgo_categorico("alto", origen="R4")
    m.agregar_conducta("Solicitar evaluación preoperatoria específica o interconsulta por riesgo tromboembólico")
    m.agregar_alerta("Riesgo tromboembólico aumentado")
_registrar("R4", "Riesgo tromboembólico aumentado", 1, _r4_cond, _r4_acc,
           "Eleva el nivel de riesgo a ALTO e indica interconsulta específica")


def _r5_cond(m):
    return _en_lista(_e(m, "factores_riesgo_especificos"), "hernia sospechada")
def _r5_acc(m):
    m.tender_adecuacion_a("parcialmente adecuado", origen="R5")
    m.agregar_conducta("Solicitar evaluación técnica específica por sospecha de hernia")
    m.agregar_alerta("Hernia sospechada")
_registrar("R5", "Hernia sospechada", 1, _r5_cond, _r5_acc,
           "Tiende adecuación a PARCIALMENTE ADECUADO; exige evaluación técnica")


def _r6_cond(m):
    return (_en_lista(_e(m, "factores_riesgo_especificos"), "diástasis sospechada")
            and _e(m, "procedimiento_deseado") in ("abdominoplastía", "ambos"))
def _r6_acc(m):
    m.agregar_conducta("Evaluar técnica quirúrgica específica para diástasis (plicatura, etc.)")
    m.agregar_alerta("Diástasis sospechada en procedimiento abdominal")
_registrar("R6", "Diástasis sospechada con procedimiento abdominal", 1, _r6_cond, _r6_acc,
           "Indica evaluación de técnica quirúrgica específica")


# ---------------------------------------------------------------------------
# GRUPO 2 - HÁBITOS Y DISPOSICIÓN A OPTIMIZAR
# ---------------------------------------------------------------------------

def _r7_cond(m):
    return _e(m, "fuma") == "sí" and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "sí"
def _r7_acc(m):
    m.elevar_clasificacion_a_minimo("candidato con optimización previa", origen="R7")
    m.agregar_conducta("Suspender tabaquismo antes de avanzar (al menos 4-6 semanas previas)")
    m.agregar_alerta("Tabaquismo activo (con disposición a dejar)")
_registrar("R7", "Tabaquismo activo con disposición a dejar", 2, _r7_cond, _r7_acc,
           "Eleva a mínimo CANDIDATO CON OPTIMIZACIÓN PREVIA; pide suspender tabaco")


def _r8_cond(m):
    return _e(m, "fuma") == "sí" and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "no"
def _r8_acc(m):
    m.fijar_clasificacion("no recomendado por el momento", prioridad=2, origen="R8")
    m.agregar_conducta("No operar por ahora: paciente sin disposición a suspender tabaco")
    m.agregar_alerta("Tabaquismo activo sin disposición a dejar")
_registrar("R8", "Tabaquismo activo sin disposición a dejar", 2, _r8_cond, _r8_acc,
           "Clasifica como NO RECOMENDADO POR EL MOMENTO")


def _r9_cond(m):
    return (_e(m, "consumo_problematico_sustancias") == "sí"
            and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "sí")
def _r9_acc(m):
    m.fijar_clasificacion("postergar", prioridad=2, origen="R9")
    m.agregar_conducta("Solicitar interconsulta o evaluación específica por consumo problemático")
    m.agregar_alerta("Consumo problemático de sustancias (con disposición a tratar)")
_registrar("R9", "Consumo problemático de sustancias con disposición a dejar", 2, _r9_cond, _r9_acc,
           "Clasifica como POSTERGAR; pide interconsulta")


def _r10_cond(m):
    return (_e(m, "consumo_problematico_sustancias") == "sí"
            and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "no")
def _r10_acc(m):
    m.fijar_clasificacion("no recomendado por el momento", prioridad=2, origen="R10")
    m.agregar_conducta("No operar por ahora: consumo problemático sin disposición a modificar")
    m.agregar_alerta("Consumo problemático de sustancias sin disposición a dejar")
_registrar("R10", "Consumo problemático sin disposición a dejar", 2, _r10_cond, _r10_acc,
           "Clasifica como NO RECOMENDADO POR EL MOMENTO")


# ---------------------------------------------------------------------------
# GRUPO 3 - ADECUACIÓN DEL PROCEDIMIENTO
# ---------------------------------------------------------------------------

def _r11_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "liposucción"
            and "grasa localizada" in cond
            and "grasa visceral sospechada" not in cond
            and _c(m, "estabilidad_peso") in ("estable", "poco estable")
            and _e(m, "expectativas") == "realistas")
def _r11_acc(m):
    m.activar_adecuacion("adecuado", 1.0, origen="R11")
    m.agregar_favorable("Liposucción coherente: grasa localizada con peso estable/poco estable y expectativas realistas")
_registrar("R11", "Liposucción adecuada", 3, _r11_cond, _r11_acc,
           "Activa adecuación ADECUADO")


def _r12_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "liposucción"
            and "exceso de piel" in cond)
def _r12_acc(m):
    m.activar_adecuacion("parcialmente adecuado", 1.0, origen="R12")
    m.agregar_conducta("Redefinir técnica: con exceso de piel, considerar abdominoplastía o combinación")
    m.agregar_alerta("Liposucción solicitada con exceso de piel")
_registrar("R12", "Liposucción parcialmente adecuada por exceso de piel", 3, _r12_cond, _r12_acc,
           "Activa PARCIALMENTE ADECUADO; sugiere redefinir técnica")


def _r13_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "liposucción"
            and "grasa visceral sospechada" in cond)
def _r13_acc(m):
    m.activar_adecuacion("no adecuado", 1.0, origen="R13")
    m.agregar_conducta("Redefinir técnica o indicar evaluación adicional: la grasa visceral no se trata con liposucción")
    m.agregar_alerta("Grasa visceral sospechada (no candidato a liposucción)")
_registrar("R13", "Liposucción no adecuada por grasa visceral", 3, _r13_cond, _r13_acc,
           "Activa adecuación NO ADECUADO")


def _r14_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "abdominoplastía"
            and ("exceso de piel" in cond
                 or "flacidez o debilidad de pared abdominal" in cond)
            and _c(m, "estabilidad_peso") == "estable"
            and _e(m, "expectativas") == "realistas")
def _r14_acc(m):
    m.activar_adecuacion("adecuado", 1.0, origen="R14")
    m.agregar_favorable("Abdominoplastía coherente: exceso de piel o flacidez con peso estable y expectativas realistas")
_registrar("R14", "Abdominoplastía adecuada", 3, _r14_cond, _r14_acc,
           "Activa adecuación ADECUADO")


def _r15_cond(m):
    return (_e(m, "procedimiento_deseado") == "abdominoplastía"
            and _c(m, "estabilidad_peso") == "poco estable")
def _r15_acc(m):
    m.activar_adecuacion("parcialmente adecuado", 0.8, origen="R15")
    m.agregar_conducta("Estabilizar peso antes de avanzar (objetivo: fluctuación < 3-5%)")
    m.agregar_alerta("Peso poco estable para abdominoplastía")
_registrar("R15", "Abdominoplastía parcialmente adecuada por peso poco estable", 3, _r15_cond, _r15_acc,
           "Activa PARCIALMENTE ADECUADO; pide estabilizar peso")


def _r16_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "abdominoplastía"
            and "exceso de piel" not in cond
            and "flacidez o debilidad de pared abdominal" not in cond)
def _r16_acc(m):
    m.activar_adecuacion("no adecuado", 1.0, origen="R16")
    m.agregar_conducta("Redefinir técnica: sin exceso de piel ni flacidez, la abdominoplastía no es la indicación")
    m.agregar_alerta("Abdominoplastía sin indicación corporal compatible")
_registrar("R16", "Abdominoplastía no adecuada sin exceso de piel ni flacidez", 3, _r16_cond, _r16_acc,
           "Activa adecuación NO ADECUADO")


def _r17_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    return (_e(m, "procedimiento_deseado") == "ambos"
            and "exceso de piel" in cond
            and "grasa localizada" in cond
            and "grasa visceral sospechada" not in cond
            and _c(m, "estabilidad_peso") == "estable"
            and _e(m, "expectativas") == "realistas")
def _r17_acc(m):
    m.activar_adecuacion("adecuado", 1.0, origen="R17")
    m.agregar_favorable("Procedimiento combinado coherente con la condición corporal observada")
_registrar("R17", "Procedimiento combinado adecuado", 3, _r17_cond, _r17_acc,
           "Activa adecuación ADECUADO para procedimiento combinado")


def _r18_cond(m):
    cond = _e(m, "condicion_corporal_observada", [])
    base_anatomica = ("exceso de piel" in cond or "grasa localizada" in cond)
    factores_adversos = (
        _c(m, "estabilidad_peso") == "poco estable"
        or _c(m, "cicatrizacion_categoria") == "mala"
        or any(f in _e(m, "factores_riesgo_especificos", []) for f in
               ("diástasis sospechada", "hernia sospechada", "riesgo tromboembólico aumentado"))
    )
    return (_e(m, "procedimiento_deseado") == "ambos"
            and base_anatomica
            and factores_adversos)
def _r18_acc(m):
    m.activar_adecuacion("parcialmente adecuado", 0.9, origen="R18")
    m.agregar_alerta("Procedimiento combinado con factores adversos (peso, cicatrización o riesgo específico)")
_registrar("R18", "Procedimiento combinado parcialmente adecuado", 3, _r18_cond, _r18_acc,
           "Activa PARCIALMENTE ADECUADO en procedimiento combinado")


# ---------------------------------------------------------------------------
# GRUPO 4 - REGLAS DE RIESGO DIFUSO (R19..R26)
# ---------------------------------------------------------------------------

def _r19_cond(m):
    imc_cat = _c(m, "categoria_imc")
    return (imc_cat in ("normal-aceptable", "moderadamente elevado")
            and _c(m, "estabilidad_peso") == "estable"
            and _c(m, "cicatrizacion_categoria") in ("normal", "buena")
            and _e(m, "enfermedad_no_controlada") == "no"
            and _e(m, "fuma") == "no"
            and _e(m, "consumo_problematico_sustancias") == "no"
            and ("ninguno" in _e(m, "factores_riesgo_especificos", [])
                 or len(_e(m, "factores_riesgo_especificos", [])) == 0))
def _r19_acc(m):
    m.activar_riesgo("bajo", 1.0, origen="R19")
    m.agregar_favorable("Ausencia de factores modificables que eleven el riesgo")
_registrar("R19", "Riesgo bajo", 4, _r19_cond, _r19_acc,
           "Activa el conjunto RIESGO BAJO")


def _r20_cond(m):
    imc_cat = _c(m, "categoria_imc")
    return (imc_cat in ("moderadamente elevado", "elevado")
            or _c(m, "estabilidad_peso") == "poco estable"
            or _c(m, "cicatrizacion_categoria") == "mala"
            or (_e(m, "fuma") == "sí" and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "sí"))
def _r20_acc(m):
    m.activar_riesgo("moderado", 0.9, origen="R20")
    m.agregar_alerta("Factores modificables detectados que elevan el riesgo a moderado")
_registrar("R20", "Riesgo moderado por factores modificables", 4, _r20_cond, _r20_acc,
           "Activa el conjunto RIESGO MODERADO")


def _r21_cond(m):
    factores = 0
    if _c(m, "categoria_imc") in ("elevado", "muy elevado"):
        factores += 1
    if _c(m, "estabilidad_peso") == "poco estable":
        factores += 1
    if _c(m, "cicatrizacion_categoria") == "mala":
        factores += 1
    if _e(m, "fuma") == "sí":
        factores += 1
    if _e(m, "antecedentes_quirurgicos") == "cirugía previa con complicaciones":
        factores += 1
    fre = _e(m, "factores_riesgo_especificos", [])
    if any(f in fre for f in ("diástasis sospechada", "hernia sospechada", "riesgo tromboembólico aumentado")):
        factores += 1
    m.fijar("sistema", "factores_acumulados_riesgo", factores)
    return factores >= 3
def _r21_acc(m):
    m.activar_riesgo("alto", 1.0, origen="R21")
    m.agregar_alerta("Tres o más factores moderados acumulados elevan el riesgo a alto")
_registrar("R21", "Riesgo alto por acumulación de factores", 4, _r21_cond, _r21_acc,
           "Activa el conjunto RIESGO ALTO")


def _r22_cond(m): return _c(m, "categoria_imc") == "muy elevado"
def _r22_acc(m):
    m.activar_riesgo("alto", 1.0, origen="R22")
    m.agregar_conducta("Optimización clínica o nutricional previa (descenso de peso supervisado)")
    m.agregar_alerta("IMC muy elevado")
_registrar("R22", "Riesgo alto por IMC muy elevado", 4, _r22_cond, _r22_acc,
           "Activa RIESGO ALTO y pide optimización previa")


def _r23_cond(m): return _c(m, "estabilidad_peso") == "inestable"
def _r23_acc(m):
    m.activar_riesgo("alto", 1.0, origen="R23")
    m.fijar_clasificacion("postergar", prioridad=3, origen="R23")
    m.agregar_conducta("Postergar hasta estabilizar peso (fluctuación < 3-5% sostenida)")
    m.agregar_alerta("Peso inestable (fluctuación elevada)")
_registrar("R23", "Riesgo alto por peso inestable", 4, _r23_cond, _r23_acc,
           "Activa RIESGO ALTO, fija POSTERGAR y pide estabilizar peso")


def _r24_cond(m): return _c(m, "cicatrizacion_categoria") == "muy mala"
def _r24_acc(m):
    m.activar_riesgo("alto", 1.0, origen="R24")
    m.agregar_conducta("Evaluación específica de cicatrización antes de avanzar")
    m.agregar_alerta("Cicatrización muy mala")
_registrar("R24", "Riesgo alto por cicatrización muy mala", 4, _r24_cond, _r24_acc,
           "Activa RIESGO ALTO; pide evaluación específica")


def _r25_cond(m): return _e(m, "antecedentes_quirurgicos") == "cirugía previa sin complicaciones"
def _r25_acc(m):
    m.fijar("sistema", "antecedente_informativo", True)
    # No eleva el riesgo por sí solo: solo registra factor informativo.
_registrar("R25", "Antecedentes quirúrgicos sin complicaciones", 4, _r25_cond, _r25_acc,
           "Registra factor informativo (no eleva el riesgo por sí solo)")


def _r26_cond(m): return _e(m, "antecedentes_quirurgicos") == "cirugía previa con complicaciones"
def _r26_acc(m):
    m.activar_riesgo("moderado", 0.8, origen="R26")
    m.agregar_conducta("Solicitar evaluación quirúrgica detallada de antecedentes y complicaciones previas")
    m.agregar_alerta("Antecedente quirúrgico con complicaciones")
_registrar("R26", "Antecedentes quirúrgicos con complicaciones", 4, _r26_cond, _r26_acc,
           "Eleva riesgo a al menos MODERADO; pide evaluación detallada")


# ---------------------------------------------------------------------------
# GRUPO 5 - REGLAS DE EXPECTATIVAS (R27..R29)
# ---------------------------------------------------------------------------

def _r27_cond(m): return _e(m, "expectativas") == "realistas"
def _r27_acc(m):
    m.agregar_favorable("Expectativas realistas")
_registrar("R27", "Expectativas realistas", 5, _r27_cond, _r27_acc,
           "Factor favorable")


def _r28_cond(m): return _e(m, "expectativas") == "poco claras"
def _r28_acc(m):
    m.bloquear_candidato_favorable(origen="R28")
    m.agregar_conducta("Ajustar expectativas antes de avanzar (entrevista, material informativo)")
    m.agregar_alerta("Expectativas poco claras")
_registrar("R28", "Expectativas poco claras", 5, _r28_cond, _r28_acc,
           "Bloquea CANDIDATO FAVORABLE; pide ajustar expectativas")


def _r29_cond(m): return _e(m, "expectativas") == "irreales"
def _r29_acc(m):
    m.fijar_clasificacion("no recomendado por el momento", prioridad=2, origen="R29")
    m.agregar_conducta("Orientación o evaluación adicional sobre expectativas (eventualmente psicología)")
    m.agregar_alerta("Expectativas irreales")
_registrar("R29", "Expectativas irreales", 5, _r29_cond, _r29_acc,
           "Clasifica como NO RECOMENDADO POR EL MOMENTO")


# ---------------------------------------------------------------------------
# GRUPO 6 - REGLAS DE CLASIFICACIÓN FINAL (R30..R34)
#   Se aplican después de la defuzzificación de riesgo y adecuación.
# ---------------------------------------------------------------------------

def _sin_reglas_criticas(m):
    return not m.hay_clasificacion_fijada()


def _r30_cond(m):
    return (_sin_reglas_criticas(m)
            and _c(m, "nivel_riesgo_categoria") == "bajo"
            and _c(m, "adecuacion_categoria") == "adecuado"
            and _e(m, "expectativas") == "realistas"
            and _c(m, "estabilidad_peso") == "estable"
            and _e(m, "enfermedad_no_controlada") == "no"
            and _e(m, "fuma") == "no"
            and _e(m, "consumo_problematico_sustancias") == "no"
            and not m.bloqueado_candidato_favorable()
            and ("ninguno" in _e(m, "factores_riesgo_especificos", [])
                 or len(_e(m, "factores_riesgo_especificos", [])) == 0))
def _r30_acc(m):
    m.fijar_clasificacion("candidato favorable", prioridad=6, origen="R30")
    m.agregar_conducta("Avanzar con evaluación preoperatoria")
_registrar("R30", "Candidato favorable", 6, _r30_cond, _r30_acc,
           "Clasifica como CANDIDATO FAVORABLE y sugiere avanzar")


def _r31_cond(m):
    return (_sin_reglas_criticas(m)
            and _c(m, "nivel_riesgo_categoria") == "moderado"
            and _c(m, "adecuacion_categoria") in ("adecuado", "parcialmente adecuado"))
def _r31_acc(m):
    m.fijar_clasificacion("candidato con optimización previa", prioridad=6, origen="R31")
    m.agregar_conducta("Optimizar condiciones previas antes de la cirugía")
_registrar("R31", "Candidato con optimización previa", 6, _r31_cond, _r31_acc,
           "Clasifica como CANDIDATO CON OPTIMIZACIÓN PREVIA")


def _r32_cond(m):
    if m.hay_clasificacion_fijada():
        return False
    if _c(m, "nivel_riesgo_categoria") != "alto":
        return False
    # Factores modificables presentes
    modificables = (
        _c(m, "estabilidad_peso") == "inestable"
        or _e(m, "fuma") == "sí"
        or _c(m, "categoria_imc") == "muy elevado"
        or _c(m, "cicatrizacion_categoria") == "muy mala"
    )
    return modificables
def _r32_acc(m):
    m.fijar_clasificacion("postergar", prioridad=6, origen="R32")
    m.agregar_conducta("Postergar hasta optimizar los factores modificables identificados")
_registrar("R32", "Postergar por factores modificables", 6, _r32_cond, _r32_acc,
           "Clasifica como POSTERGAR")


def _r33_cond(m):
    if m.hay_clasificacion_fijada():
        return False
    return (
        _e(m, "expectativas") == "irreales"
        or (_e(m, "fuma") == "sí" and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "no")
        or (_e(m, "consumo_problematico_sustancias") == "sí"
            and _e(m, "dispuesto_a_dejar_habitos_riesgo") == "no")
    )
def _r33_acc(m):
    m.fijar_clasificacion("no recomendado por el momento", prioridad=6, origen="R33")
    m.agregar_conducta("No operar por ahora: combinación de factores no controlados")
_registrar("R33", "No recomendado por el momento", 6, _r33_cond, _r33_acc,
           "Clasifica como NO RECOMENDADO POR EL MOMENTO")


def _r33b_cond(m):
    if m.hay_clasificacion_fijada():
        return False
    return _coherencia_procedimiento_alta(m)


def _r33b_acc(m):
    if _c(m, "nivel_riesgo_categoria") == "alto":
        m.fijar_clasificacion("postergar", prioridad=6, origen="R33B")
    else:
        m.fijar_clasificacion("no recomendado por el momento", prioridad=6, origen="R33B")
    m.agregar_conducta(
        "Redefinir procedimiento: incompatibilidad anatómica con la técnica solicitada"
    )
    m.agregar_alerta("Incompatibilidad procedimiento–condición corporal (coherencia difusa R33B)")


_registrar(
    "R33B",
    "Coherencia difusa procedimiento–clasificación",
    6,
    _r33b_cond,
    _r33b_acc,
    "Si no adecuado ∧ incompatibilidad alta → no recomendado/postergar (no optimización previa)",
)


def _r34_cond(m):
    if m.hay_clasificacion_fijada():
        return False
    if _c(m, "adecuacion_categoria") not in ("no adecuado", "parcialmente adecuado"):
        return False
    if _coherencia_procedimiento_alta(m):
        return False
    return True


def _r34_acc(m):
    if _c(m, "nivel_riesgo_categoria") == "alto":
        m.fijar_clasificacion("postergar", prioridad=6, origen="R34")
    else:
        m.fijar_clasificacion("candidato con optimización previa", prioridad=6, origen="R34")
    m.agregar_conducta("Revisar si corresponde abdominoplastía, liposucción o combinación (redefinir técnica)")
_registrar("R34", "Procedimiento requiere redefinir técnica", 6, _r34_cond, _r34_acc,
           "Clasifica según riesgo y sugiere redefinir técnica")


# ---------------------------------------------------------------------------
# Acceso público
# ---------------------------------------------------------------------------

class BaseConocimientos:
    """
    Encapsula los recursos de conocimiento del sistema:
        - variables lingüísticas,
        - conjuntos difusos de salida,
        - reglas R1..R34 y R33B (coherencia difusa).
    """

    def __init__(self):
        self.variable_imc = VARIABLE_IMC
        self.variable_estabilidad = VARIABLE_ESTABILIDAD
        self.variable_cicatrizacion = VARIABLE_CICATRIZACION
        self.variable_expectativas = VARIABLE_EXPECTATIVAS
        self.conjuntos_riesgo = CONJUNTOS_RIESGO
        self.universo_riesgo = UNIVERSO_RIESGO
        self.conjuntos_adecuacion = CONJUNTOS_ADECUACION
        self.universo_adecuacion = UNIVERSO_ADECUACION
        self.reglas = REGLAS

    def reglas_por_prioridad(self, prioridad: int) -> List[Dict]:
        return [r for r in self.reglas if r["prioridad"] == prioridad]
