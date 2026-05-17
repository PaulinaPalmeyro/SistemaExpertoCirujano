"""
modelos.py
----------
Define las estructuras de datos y constantes del dominio.

Incluye:
    - Constantes con los valores admitidos para cada variable categórica.
    - Dataclass `DatosPaciente` con todas las variables de entrada.
    - Funciones utilitarias de validación y conversión de categorías a escalas.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Constantes / dominios admitidos
# ---------------------------------------------------------------------------

SEXO_OPCIONES = ["femenino", "masculino", "intersexual", "no especificado"]

EMBARAZO_OPCIONES = [
    "no aplica",
    "no",
    "embarazo actual",
    "embarazo futuro cercano",
    "no sabe",
]

# Opciones mostradas en formularios (sin "no aplica"; se asigna automáticamente)
EMBARAZO_OPCIONES_FORMULARIO = [
    "no",
    "embarazo actual",
    "embarazo futuro cercano",
    "no sabe",
]

PROCEDIMIENTO_OPCIONES = ["abdominoplastía", "liposucción", "ambos"]

CONDICION_CORPORAL_OPCIONES = [
    "exceso de piel",
    "grasa localizada",
    "grasa visceral sospechada",
    "flacidez o debilidad de pared abdominal",
    "ninguno",
]

CICATRIZACION_OPCIONES = ["muy mala", "mala", "normal", "buena"]

FACTORES_RIESGO_OPCIONES = [
    "ninguno",
    "diástasis sospechada",
    "hernia sospechada",
    "riesgo tromboembólico aumentado",
]

ANTECEDENTES_OPCIONES = [
    "sin antecedentes",
    "cirugía previa sin complicaciones",
    "cirugía previa con complicaciones",
]

EXPECTATIVAS_OPCIONES = ["realistas", "poco claras", "irreales"]

SI_NO_OPCIONES = ["sí", "no"]
SI_NO_NA_OPCIONES = ["sí", "no", "no aplica"]

# Solo sí/no en formularios; "no aplica" se asigna automáticamente cuando corresponde
DISPUESTO_HABITOS_OPCIONES = ["sí", "no"]


def resolver_embarazo(sexo_biologico: Optional[str], embarazo_seleccionado: Optional[str]) -> str:
    """Asigna 'no aplica' si el sexo biológico no es femenino."""
    if sexo_biologico != "femenino":
        return "no aplica"
    return embarazo_seleccionado or "no"


OPCION_NINGUNO = "ninguno"


def seleccion_valida_sin_ninguno_mixto(seleccion: List[str]) -> bool:
    """True si no se mezcla 'ninguno' con otras opciones."""
    return not (
        OPCION_NINGUNO in seleccion
        and len(seleccion) > 1
    )


def resolver_dispuesto_habitos(
    fuma: Optional[str],
    consumo_problematico: Optional[str],
    dispuesto_seleccionado: Optional[str],
) -> str:
    """Asigna 'no aplica' si no fuma ni tiene consumo problemático."""
    if fuma == "no" and consumo_problematico == "no":
        return "no aplica"
    return dispuesto_seleccionado or "no"


# ---------------------------------------------------------------------------
# Equivalencias categoría -> valor numérico para fuzzificación
# ---------------------------------------------------------------------------

CICATRIZACION_A_NUMERO = {
    "muy mala": 1.5,
    "mala": 3.5,
    "normal": 6.0,
    "buena": 8.5,
}

EXPECTATIVAS_A_NUMERO = {
    "irreales": 2.0,
    "poco claras": 5.0,
    "realistas": 8.5,
}


# ---------------------------------------------------------------------------
# Dataclass principal con los datos del paciente
# ---------------------------------------------------------------------------

@dataclass
class DatosPaciente:
    """
    Estructura con todas las variables de entrada que carga u observa
    el cirujano plástico durante la consulta prequirúrgica inicial.
    """

    # Datos generales
    edad: Optional[float] = None
    sexo_biologico: Optional[str] = None
    embarazo_actual_o_futuro_cercano: Optional[str] = None
    procedimiento_deseado: Optional[str] = None

    # Datos antropométricos
    peso_actual: Optional[float] = None
    altura: Optional[float] = None
    peso_hace_6_meses: Optional[float] = None

    # Evaluación corporal
    condicion_corporal_observada: List[str] = field(default_factory=list)
    cicatrizacion: Optional[str] = None  # categoría

    # Estado clínico y hábitos
    factores_riesgo_especificos: List[str] = field(default_factory=list)
    enfermedad_no_controlada: Optional[str] = None
    fuma: Optional[str] = None
    consumo_problematico_sustancias: Optional[str] = None
    dispuesto_a_dejar_habitos_riesgo: Optional[str] = None

    # Antecedentes y expectativas
    antecedentes_quirurgicos: Optional[str] = None
    expectativas: Optional[str] = None

    # ------------------------------------------------------------------ utils

    def como_diccionario(self) -> dict:
        """Devuelve una representación de diccionario simple."""
        return {
            "edad": self.edad,
            "sexo_biologico": self.sexo_biologico,
            "embarazo_actual_o_futuro_cercano": self.embarazo_actual_o_futuro_cercano,
            "procedimiento_deseado": self.procedimiento_deseado,
            "peso_actual": self.peso_actual,
            "altura": self.altura,
            "peso_hace_6_meses": self.peso_hace_6_meses,
            "condicion_corporal_observada": list(self.condicion_corporal_observada),
            "cicatrizacion": self.cicatrizacion,
            "factores_riesgo_especificos": list(self.factores_riesgo_especificos),
            "enfermedad_no_controlada": self.enfermedad_no_controlada,
            "fuma": self.fuma,
            "consumo_problematico_sustancias": self.consumo_problematico_sustancias,
            "dispuesto_a_dejar_habitos_riesgo": self.dispuesto_a_dejar_habitos_riesgo,
            "antecedentes_quirurgicos": self.antecedentes_quirurgicos,
            "expectativas": self.expectativas,
        }


# ---------------------------------------------------------------------------
# Validación de campos obligatorios
# ---------------------------------------------------------------------------

CAMPOS_OBLIGATORIOS = [
    "edad",
    "sexo_biologico",
    "embarazo_actual_o_futuro_cercano",
    "procedimiento_deseado",
    "peso_actual",
    "altura",
    "peso_hace_6_meses",
    "cicatrizacion",
    "enfermedad_no_controlada",
    "fuma",
    "consumo_problematico_sustancias",
    "dispuesto_a_dejar_habitos_riesgo",
    "antecedentes_quirurgicos",
    "expectativas",
]


def validar_informacion_completa(datos: DatosPaciente) -> (bool, List[str]):
    """
    Verifica que los campos obligatorios estén presentes.
    Devuelve una tupla (completa, lista_de_faltantes).
    """
    faltantes: List[str] = []
    d = datos.como_diccionario()
    for campo in CAMPOS_OBLIGATORIOS:
        valor = d.get(campo)
        if valor is None or valor == "" or (isinstance(valor, (int, float)) and valor <= 0 and campo in {"edad", "peso_actual", "altura", "peso_hace_6_meses"}):
            faltantes.append(campo)
    return (len(faltantes) == 0, faltantes)
