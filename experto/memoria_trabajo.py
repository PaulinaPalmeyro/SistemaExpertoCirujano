"""
memoria_trabajo.py
------------------
Memoria de Trabajo del Sistema Experto.

Almacena:
    1. Datos ingresados por el cirujano (objeto = "paciente").
    2. Datos calculados por el sistema (objeto = "sistema").
    3. Conclusiones parciales.
    4. Reglas activadas (con código y descripción).
    5. Factores favorables.
    6. Factores de alerta.
    7. Conductas sugeridas.
    8. Activaciones difusas para nivel de riesgo y adecuación.
    9. Resultado final.

Los hechos se guardan en formato tripla `objeto - atributo - valor`:
    paciente - edad - 36
    sistema  - imc_calculado - 28.4
    sistema  - regla_activada - R7

La memoria también administra prioridades de clasificación preliminar para
que las reglas críticas no sean sobrescritas por reglas posteriores.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# Mapa de prioridad: número más bajo = prioridad mayor.
# Permite que una regla R1 (prioridad 1) no sea sobrescrita por una R30.
PRIORIDADES_CLASIFICACION = {
    1: "crítica de seguridad",
    2: "hábitos / disposición",
    3: "riesgo difuso o adecuación",
    6: "clasificación final",
    99: "validación técnica",
}


@dataclass
class MemoriaTrabajo:
    """Memoria de trabajo. Almacena hechos y conclusiones parciales."""

    # Hechos en formato objeto -> atributo -> valor
    _hechos: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {"paciente": {}, "sistema": {}})

    # Trazabilidad
    reglas_activadas: List[Dict[str, str]] = field(default_factory=list)
    factores_favorables: List[str] = field(default_factory=list)
    factores_alerta: List[str] = field(default_factory=list)
    conductas_sugeridas: List[str] = field(default_factory=list)

    # Activaciones difusas
    activaciones_riesgo: Dict[str, float] = field(default_factory=dict)
    activaciones_adecuacion: Dict[str, float] = field(default_factory=dict)

    # Clasificación preliminar con prioridad asociada
    _clasificacion: Optional[str] = None
    _prioridad_clasificacion: int = 100  # cuanto menor, más prioritaria

    # Bandera para impedir CANDIDATO FAVORABLE
    _bloquear_favorable: bool = False

    # Riesgo categórico fijado por reglas críticas (R4 por ejemplo)
    _riesgo_categorico: Optional[str] = None

    # ----------------------------------------------------------- carga inicial

    def cargar_datos_paciente(self, datos: Dict[str, Any]) -> None:
        """Carga datos del paciente como hechos."""
        for k, v in datos.items():
            self._hechos["paciente"][k] = v

    # ----------------------------------------------------------- API hechos

    def fijar(self, objeto: str, atributo: str, valor: Any) -> None:
        if objeto not in self._hechos:
            self._hechos[objeto] = {}
        self._hechos[objeto][atributo] = valor

    def obtener(self, objeto: str, atributo: str, default: Any = None) -> Any:
        return self._hechos.get(objeto, {}).get(atributo, default)

    def listar_hechos(self) -> List[Tuple[str, str, Any]]:
        """Devuelve lista de triplas (objeto, atributo, valor)."""
        triplas: List[Tuple[str, str, Any]] = []
        for obj, atributos in self._hechos.items():
            for atr, val in atributos.items():
                triplas.append((obj, atr, val))
        return triplas

    # ----------------------------------------------------------- reglas

    def registrar_regla(self, codigo: str, descripcion: str, efecto: str) -> None:
        self.reglas_activadas.append({
            "codigo": codigo,
            "descripcion": descripcion,
            "efecto": efecto,
        })
        # Mantener también como hecho del sistema
        actuales = self.obtener("sistema", "reglas_activadas", [])
        if codigo not in actuales:
            actuales = actuales + [codigo]
        self.fijar("sistema", "reglas_activadas", actuales)

    # ----------------------------------------------------------- factores

    def agregar_favorable(self, texto: str) -> None:
        if texto not in self.factores_favorables:
            self.factores_favorables.append(texto)

    def agregar_alerta(self, texto: str) -> None:
        if texto not in self.factores_alerta:
            self.factores_alerta.append(texto)

    def agregar_conducta(self, texto: str) -> None:
        if texto not in self.conductas_sugeridas:
            self.conductas_sugeridas.append(texto)

    # ----------------------------------------------------------- activaciones difusas

    def activar_riesgo(self, etiqueta: str, grado: float, origen: str = "") -> None:
        actual = self.activaciones_riesgo.get(etiqueta, 0.0)
        if grado > actual:
            self.activaciones_riesgo[etiqueta] = grado

    def activar_adecuacion(self, etiqueta: str, grado: float, origen: str = "") -> None:
        actual = self.activaciones_adecuacion.get(etiqueta, 0.0)
        if grado > actual:
            self.activaciones_adecuacion[etiqueta] = grado

    def tender_adecuacion_a(self, etiqueta: str, origen: str = "") -> None:
        """Pone un piso mínimo de activación para 'parcialmente adecuado'."""
        self.activar_adecuacion(etiqueta, 0.7, origen)

    def fijar_riesgo_categorico(self, categoria: str, origen: str = "") -> None:
        """Reglas críticas pueden fijar el nivel de riesgo directamente."""
        self._riesgo_categorico = categoria
        self.activar_riesgo(categoria, 1.0, origen)

    def riesgo_categorico_fijado(self) -> Optional[str]:
        return self._riesgo_categorico

    # ----------------------------------------------------------- clasificación

    def fijar_clasificacion(self, valor: str, prioridad: int, origen: str = "") -> None:
        """
        Una regla intenta fijar una clasificación preliminar.
        Sólo prevalece si su prioridad es <= a la previamente fijada.
        """
        if prioridad <= self._prioridad_clasificacion:
            self._clasificacion = valor
            self._prioridad_clasificacion = prioridad

    def elevar_clasificacion_a_minimo(self, valor: str, origen: str = "") -> None:
        """
        Garantiza que la clasificación sea al menos `valor`, sin pisar otra
        más restrictiva. Se usa en R7 (al menos 'candidato con optimización
        previa').
        """
        orden = {
            "candidato favorable": 1,
            "candidato con optimización previa": 2,
            "postergar": 3,
            "no recomendado por el momento": 4,
            "información insuficiente": 5,
        }
        actual_orden = orden.get(self._clasificacion, 0)
        nuevo_orden = orden.get(valor, 0)
        if nuevo_orden > actual_orden:
            # Se aplica con prioridad alta (igual que crítica) para no ser sobrescrita
            self.fijar_clasificacion(valor, prioridad=2, origen=origen)

    def hay_clasificacion_fijada(self) -> bool:
        """True si una regla crítica/intermedia ya fijó la clasificación."""
        return self._clasificacion is not None and self._prioridad_clasificacion < 6

    def clasificacion_actual(self) -> Optional[str]:
        return self._clasificacion

    def bloquear_candidato_favorable(self, origen: str = "") -> None:
        self._bloquear_favorable = True

    def bloqueado_candidato_favorable(self) -> bool:
        return self._bloquear_favorable

    # ----------------------------------------------------------- impresión

    def imprimir_hechos(self) -> str:
        partes = []
        for obj, atr, val in self.listar_hechos():
            partes.append(f"{obj:<10} - {atr:<35} - {val}")
        return "\n".join(partes)
