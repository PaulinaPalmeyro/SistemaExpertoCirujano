"""
motor_inferencias.py
--------------------
Motor de Inferencias del Sistema Experto.

Implementa encadenamiento hacia adelante (forward chaining) con el ciclo:
    Aparear -> Seleccionar -> Ejecutar

Etapas (según el documento "SE Revisado"):
    1. Recibir datos de entrada.
    2. Cargar hechos en la memoria de trabajo.
    3. Validar información obligatoria.
    4. Calcular variables derivadas (IMC, categoría IMC, fluctuación,
       estabilidad del peso, escala de cicatrización, escala de expectativas).
    5. Fuzzificar variables.
    6. Aplicar reglas críticas de seguridad        (prioridad 1).
    7. Aplicar reglas de hábitos y disposición     (prioridad 2).
    8. Aplicar reglas de adecuación del procedimiento (prioridad 3).
    9. Aplicar reglas de riesgo difuso             (prioridad 4).
   10. Aplicar reglas de expectativas              (prioridad 5).
   11. Defuzzificar nivel de riesgo y adecuación.
   12. Aplicar reglas de clasificación final       (prioridad 6).
   13. Generar conducta sugerida.
   14. Generar justificación (delegada al SubsistemaExplicacion).
   15. Devolver resultado completo.
"""

from typing import Dict, List, Tuple

from .base_conocimientos import BaseConocimientos
from .logica_difusa import (
    categorizar_adecuacion,
    categorizar_riesgo,
    defuzzificar_centroide,
)
from .memoria_trabajo import MemoriaTrabajo
from .modelos import (
    CICATRIZACION_A_NUMERO,
    EXPECTATIVAS_A_NUMERO,
    DatosPaciente,
    validar_informacion_completa,
)
from .subsistema_explicacion import SubsistemaExplicacion


class MotorInferencias:
    """Motor de Inferencias con encadenamiento hacia adelante."""

    def __init__(self, base: BaseConocimientos = None):
        self.base = base or BaseConocimientos()
        self.explicador = SubsistemaExplicacion()

    # ======================================================================
    # PUNTO DE ENTRADA
    # ======================================================================

    def evaluar(self, datos: DatosPaciente) -> Dict:
        """
        Evalúa al paciente y devuelve el diccionario de resultado completo.
        """
        memoria = MemoriaTrabajo()

        # 1 y 2. Cargar hechos del paciente
        memoria.cargar_datos_paciente(datos.como_diccionario())

        # 3. Validar información obligatoria
        completa, faltantes = validar_informacion_completa(datos)
        memoria.fijar("sistema", "informacion_completa", "sí" if completa else "no")
        memoria.fijar("sistema", "campos_faltantes", faltantes)

        if not completa:
            return self._resultado_informacion_insuficiente(memoria, faltantes)

        # 4. Calcular variables derivadas
        self._calcular_variables_derivadas(memoria, datos)

        # 5. Fuzzificar variables
        self._fuzzificar_variables(memoria)

        # 6..10. Aplicar reglas por grupo de prioridad (1..5)
        for prioridad in (1, 2, 3, 4, 5):
            self._ciclo_aparear_seleccionar_ejecutar(memoria, prioridad)

        # 11. Defuzzificar nivel de riesgo y adecuación
        self._defuzzificar(memoria)

        # 12. Reglas de clasificación final (prioridad 6)
        self._ciclo_aparear_seleccionar_ejecutar(memoria, 6)

        # Si por alguna razón ninguna regla fija clasificación, fallback razonable.
        if memoria.clasificacion_actual() is None:
            memoria.fijar_clasificacion(
                "candidato con optimización previa", prioridad=99, origen="fallback")
            memoria.agregar_conducta("Revisar el caso con criterio clínico")

        # 13. Conducta sugerida ya está acumulada en la memoria.

        # 14 y 15. Generar justificación y resultado final
        return self._construir_resultado(memoria)

    # ======================================================================
    # PASOS INTERNOS
    # ======================================================================

    # -- 4. Cálculo de variables derivadas ----------------------------------

    def _calcular_variables_derivadas(self, memoria: MemoriaTrabajo, datos: DatosPaciente) -> None:
        # IMC
        imc = datos.peso_actual / (datos.altura ** 2)
        imc = round(imc, 2)
        memoria.fijar("sistema", "imc_calculado", imc)

        # Categoría IMC: etiqueta dominante de la variable difusa
        categoria_imc = self.base.variable_imc.etiqueta_dominante(imc)
        memoria.fijar("sistema", "categoria_imc", categoria_imc)

        # Fluctuación de peso
        if datos.peso_hace_6_meses and datos.peso_hace_6_meses > 0:
            fluctuacion = abs(datos.peso_actual - datos.peso_hace_6_meses) / datos.peso_hace_6_meses * 100
        else:
            fluctuacion = 0.0
        fluctuacion = round(fluctuacion, 2)
        memoria.fijar("sistema", "fluctuacion_peso_calculada", fluctuacion)

        # Estabilidad del peso: etiqueta dominante
        estabilidad = self.base.variable_estabilidad.etiqueta_dominante(fluctuacion)
        memoria.fijar("sistema", "estabilidad_peso", estabilidad)

        # Cicatrización y expectativas: convertir a escala numérica y categorizar
        cicat_num = CICATRIZACION_A_NUMERO.get(datos.cicatrizacion, 6.0)
        memoria.fijar("sistema", "cicatrizacion_valor", cicat_num)
        cicat_cat = self.base.variable_cicatrizacion.etiqueta_dominante(cicat_num)
        memoria.fijar("sistema", "cicatrizacion_categoria", cicat_cat)

        exp_num = EXPECTATIVAS_A_NUMERO.get(datos.expectativas, 5.0)
        memoria.fijar("sistema", "expectativas_valor", exp_num)
        exp_cat = self.base.variable_expectativas.etiqueta_dominante(exp_num)
        memoria.fijar("sistema", "expectativas_categoria", exp_cat)

    # -- 5. Fuzzificación de variables --------------------------------------

    def _fuzzificar_variables(self, memoria: MemoriaTrabajo) -> None:
        imc = memoria.obtener("sistema", "imc_calculado")
        flu = memoria.obtener("sistema", "fluctuacion_peso_calculada")
        cic = memoria.obtener("sistema", "cicatrizacion_valor")
        exp = memoria.obtener("sistema", "expectativas_valor")

        memoria.fijar("sistema", "fuzzificacion_imc", self.base.variable_imc.fuzzificar(imc))
        memoria.fijar("sistema", "fuzzificacion_estabilidad", self.base.variable_estabilidad.fuzzificar(flu))
        memoria.fijar("sistema", "fuzzificacion_cicatrizacion", self.base.variable_cicatrizacion.fuzzificar(cic))
        memoria.fijar("sistema", "fuzzificacion_expectativas", self.base.variable_expectativas.fuzzificar(exp))

    # -- 6..10 y 12. Aparear -> Seleccionar -> Ejecutar ---------------------

    def _ciclo_aparear_seleccionar_ejecutar(self, memoria: MemoriaTrabajo, prioridad: int) -> None:
        """
        Para un grupo de prioridad: evalúa todas las condiciones (Aparear),
        selecciona las reglas cuyas condiciones se cumplen (Seleccionar)
        y ejecuta sus acciones (Ejecutar), respetando el orden por código.
        """
        candidatas = self.base.reglas_por_prioridad(prioridad)
        # Orden estable por código (R1, R2, ...)
        candidatas = sorted(candidatas, key=lambda r: int(r["codigo"][1:]))

        aplicables: List[Dict] = []
        for regla in candidatas:
            try:
                if regla["condicion"](memoria):
                    aplicables.append(regla)
            except Exception:
                # Una regla mal evaluada no debe detener el motor;
                # en producción se registraría el error.
                continue

        for regla in aplicables:
            try:
                regla["accion"](memoria)
                memoria.registrar_regla(
                    codigo=regla["codigo"],
                    descripcion=regla["descripcion"],
                    efecto=regla["efecto"],
                )
            except Exception:
                continue

    # -- 11. Defuzzificación ------------------------------------------------

    def _defuzzificar(self, memoria: MemoriaTrabajo) -> None:
        # Si una regla crítica fijó nivel de riesgo categórico (R4), respetarlo.
        riesgo_fijo = memoria.riesgo_categorico_fijado()

        # Nivel de riesgo
        if memoria.activaciones_riesgo:
            valor_riesgo = defuzzificar_centroide(
                memoria.activaciones_riesgo,
                self.base.conjuntos_riesgo,
                self.base.universo_riesgo,
                paso=1.0,
            )
        else:
            # Sin activaciones explícitas asumimos riesgo bajo por defecto.
            valor_riesgo = 20.0
        valor_riesgo = round(valor_riesgo, 1)
        categoria_riesgo = categorizar_riesgo(valor_riesgo)

        # Si una regla crítica forzó 'alto' (R4), no degradar.
        if riesgo_fijo == "alto" and categoria_riesgo != "alto":
            categoria_riesgo = "alto"
            valor_riesgo = max(valor_riesgo, 75.0)

        memoria.fijar("sistema", "nivel_riesgo_valor", valor_riesgo)
        memoria.fijar("sistema", "nivel_riesgo_categoria", categoria_riesgo)

        # Adecuación del procedimiento
        if memoria.activaciones_adecuacion:
            valor_ade = defuzzificar_centroide(
                memoria.activaciones_adecuacion,
                self.base.conjuntos_adecuacion,
                self.base.universo_adecuacion,
                paso=1.0,
            )
        else:
            # Sin reglas de adecuación específicas, asumir parcialmente adecuado.
            valor_ade = 50.0
        valor_ade = round(valor_ade, 1)
        categoria_ade = categorizar_adecuacion(valor_ade)

        memoria.fijar("sistema", "adecuacion_valor", valor_ade)
        memoria.fijar("sistema", "adecuacion_categoria", categoria_ade)

    # ======================================================================
    # CONSTRUCCIÓN DEL RESULTADO
    # ======================================================================

    def _resultado_informacion_insuficiente(self, memoria: MemoriaTrabajo, faltantes: List[str]) -> Dict:
        """R35 (validación técnica): información insuficiente."""
        memoria.fijar_clasificacion("información insuficiente", prioridad=1, origen="R35")
        memoria.agregar_conducta("Completar la información obligatoria antes de evaluar")
        memoria.agregar_alerta(f"Faltan datos obligatorios: {', '.join(faltantes)}")
        memoria.registrar_regla(
            "R35", "Información insuficiente",
            "Clasifica como INFORMACIÓN INSUFICIENTE",
        )

        explicacion = (
            "No se puede emitir una recomendación preliminar porque faltan datos esenciales: "
            + ", ".join(faltantes) + "."
        )

        return {
            "clasificacion_preliminar": "información insuficiente",
            "nivel_riesgo": {"valor": None, "categoria": None},
            "adecuacion_procedimiento": {"valor": None, "categoria": None},
            "conducta_sugerida": list(memoria.conductas_sugeridas),
            "datos_calculados": {},
            "factores_favorables": [],
            "factores_alerta": list(memoria.factores_alerta),
            "reglas_activadas": list(memoria.reglas_activadas),
            "explicacion": explicacion,
            "hechos": memoria.listar_hechos(),
            "campos_faltantes": faltantes,
        }

    def _construir_resultado(self, memoria: MemoriaTrabajo) -> Dict:
        clasificacion = memoria.clasificacion_actual() or "candidato con optimización previa"

        nivel_riesgo = {
            "valor": memoria.obtener("sistema", "nivel_riesgo_valor"),
            "categoria": memoria.obtener("sistema", "nivel_riesgo_categoria"),
        }
        adecuacion = {
            "valor": memoria.obtener("sistema", "adecuacion_valor"),
            "categoria": memoria.obtener("sistema", "adecuacion_categoria"),
        }

        datos_calculados = {
            "imc_calculado": memoria.obtener("sistema", "imc_calculado"),
            "categoria_imc": memoria.obtener("sistema", "categoria_imc"),
            "fluctuacion_peso_calculada": memoria.obtener("sistema", "fluctuacion_peso_calculada"),
            "estabilidad_peso": memoria.obtener("sistema", "estabilidad_peso"),
            "cicatrizacion_categoria": memoria.obtener("sistema", "cicatrizacion_categoria"),
            "expectativas_categoria": memoria.obtener("sistema", "expectativas_categoria"),
        }

        # Asegurar conducta principal coherente con la clasificación final
        if clasificacion == "candidato favorable" and not any(
            "avanzar" in c.lower() for c in memoria.conductas_sugeridas
        ):
            memoria.agregar_conducta("Avanzar con evaluación preoperatoria")

        # Explicación
        explicacion = self.explicador.generar(memoria, clasificacion, nivel_riesgo, adecuacion, datos_calculados)
        reglas_descartadas = self.explicador.reglas_criticas_descartadas(memoria)

        return {
            "clasificacion_preliminar": clasificacion,
            "nivel_riesgo": nivel_riesgo,
            "adecuacion_procedimiento": adecuacion,
            "conducta_sugerida": list(memoria.conductas_sugeridas),
            "datos_calculados": datos_calculados,
            "factores_favorables": list(memoria.factores_favorables),
            "factores_alerta": list(memoria.factores_alerta),
            "reglas_activadas": list(memoria.reglas_activadas),
            "reglas_criticas_descartadas": reglas_descartadas,
            "explicacion": explicacion,
            "hechos": memoria.listar_hechos(),
        }
