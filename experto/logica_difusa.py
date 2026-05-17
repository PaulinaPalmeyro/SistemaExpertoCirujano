"""
logica_difusa.py
----------------
Implementación manual de:
    - Funciones de membresía triangular y trapezoidal.
    - Conjuntos difusos (clase ConjuntoDifuso).
    - Variables lingüísticas con varios conjuntos.
    - Defuzzificación por método del centroide.

Solo utiliza la librería estándar de Python.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Funciones de membresía
# ---------------------------------------------------------------------------

def triangular(x: float, a: float, b: float, c: float) -> float:
    """
    Función de membresía triangular definida por los puntos (a, b, c).
        - a, c: extremos donde la membresía es 0.
        - b:    pico donde la membresía es 1.
    """
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if (b - a) != 0 else 1.0
    # x > b
    return (c - x) / (c - b) if (c - b) != 0 else 1.0


def trapezoidal(x: float, a: float, b: float, c: float, d: float) -> float:
    """
    Función de membresía trapezoidal definida por los puntos (a, b, c, d).
        - a, d: extremos donde la membresía es 0.
        - b..c: meseta donde la membresía es 1.
    """
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a) if (b - a) != 0 else 1.0
    # c < x < d
    return (d - x) / (d - c) if (d - c) != 0 else 1.0


# ---------------------------------------------------------------------------
# Conjuntos difusos y variables lingüísticas
# ---------------------------------------------------------------------------

@dataclass
class ConjuntoDifuso:
    """
    Conjunto difuso con etiqueta lingüística y función de membresía.

    La función debe aceptar un valor `x` y devolver un grado de pertenencia
    en el intervalo [0, 1].
    """
    etiqueta: str
    funcion: Callable[[float], float]

    def grado(self, x: float) -> float:
        valor = self.funcion(x)
        # acotamos por seguridad
        if valor < 0:
            return 0.0
        if valor > 1:
            return 1.0
        return valor


class VariableLinguistica:
    """
    Variable lingüística compuesta por uno o varios conjuntos difusos.

    Permite:
        - Calcular el grado de pertenencia a cada conjunto.
        - Determinar la etiqueta con mayor grado (categoría dominante).
    """

    def __init__(self, nombre: str, conjuntos: List[ConjuntoDifuso]):
        self.nombre = nombre
        self.conjuntos = conjuntos

    def fuzzificar(self, x: float) -> Dict[str, float]:
        """Devuelve un diccionario {etiqueta: grado} para el valor x."""
        return {c.etiqueta: c.grado(x) for c in self.conjuntos}

    def etiqueta_dominante(self, x: float) -> str:
        grados = self.fuzzificar(x)
        return max(grados.items(), key=lambda kv: kv[1])[0]


# ---------------------------------------------------------------------------
# Defuzzificación por método del centroide
# ---------------------------------------------------------------------------

def defuzzificar_centroide(
    activaciones: Dict[str, float],
    conjuntos_salida: List[ConjuntoDifuso],
    universo: Tuple[float, float],
    paso: float = 0.5,
) -> float:
    """
    Aplica el método del centroide:
        valor_defuzzificado = Σ(x * μ(x)) / Σ μ(x)

    Parámetros:
        activaciones: dict {etiqueta_conjunto: grado_de_activación}
        conjuntos_salida: lista de ConjuntoDifuso para la variable de salida.
        universo: tupla (min, max) del universo de discurso.
        paso: discretización del universo.

    Devuelve:
        Valor crisp en el universo.
    """
    minimo, maximo = universo
    if minimo >= maximo:
        return 0.0

    suma_num = 0.0
    suma_den = 0.0

    # Construimos un diccionario rápido por etiqueta.
    mapa = {c.etiqueta: c for c in conjuntos_salida}

    x = minimo
    while x <= maximo + 1e-9:
        # μ(x) agregada: para cada conjunto activado calculamos
        # min(activación, grado) y luego tomamos el máximo (Mamdani).
        mu_agregada = 0.0
        for etiqueta, activacion in activaciones.items():
            if activacion <= 0 or etiqueta not in mapa:
                continue
            grado = mapa[etiqueta].grado(x)
            mu_clipped = min(activacion, grado)
            if mu_clipped > mu_agregada:
                mu_agregada = mu_clipped

        suma_num += x * mu_agregada
        suma_den += mu_agregada
        x += paso

    if suma_den == 0:
        return 0.0
    return suma_num / suma_den


# ---------------------------------------------------------------------------
# Categorización a partir del valor defuzzificado (escala 0-100)
# ---------------------------------------------------------------------------

def categorizar_riesgo(valor: float) -> str:
    """0-35: bajo / 36-70: moderado / 71-100: alto."""
    if valor <= 35:
        return "bajo"
    if valor <= 70:
        return "moderado"
    return "alto"


def categorizar_adecuacion(valor: float) -> str:
    """0-35: no adecuado / 36-70: parcialmente adecuado / 71-100: adecuado."""
    if valor <= 35:
        return "no adecuado"
    if valor <= 70:
        return "parcialmente adecuado"
    return "adecuado"
