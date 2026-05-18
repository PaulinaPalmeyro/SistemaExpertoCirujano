"""
app.py
------
Interfaz gráfica del Sistema Experto, implementada con Streamlit.

Ejecutar con:
    streamlit run app.py

Si no se desea instalar Streamlit, se puede usar la interfaz por consola en
`main.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permitir ejecutar app.py directamente desde el directorio del proyecto
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st

from experto.modelos import (
    ANTECEDENTES_OPCIONES,
    CICATRIZACION_OPCIONES,
    CONDICION_CORPORAL_OPCIONES,
    DISPUESTO_HABITOS_OPCIONES,
    EMBARAZO_OPCIONES_FORMULARIO,
    EXPECTATIVAS_OPCIONES,
    FACTORES_RIESGO_OPCIONES,
    OPCION_NINGUNO,
    PROCEDIMIENTO_OPCIONES,
    SEXO_OPCIONES,
    SI_NO_OPCIONES,
    DatosPaciente,
    resolver_dispuesto_habitos,
    resolver_embarazo,
)
from experto.motor_inferencias import MotorInferencias


RESULTADO_KEY = "resultado_evaluacion"
LIMPIAR_FLAG = "limpiar_formulario"
FORM_VERSION_KEY = "form_version"


# ---------------------------------------------------------------------------
# Limpieza del formulario / nuevo paciente
# ---------------------------------------------------------------------------

def _form_key(nombre: str) -> str:
    """Clave única por versión del formulario; al limpiar se incrementa la versión."""
    version = st.session_state.get(FORM_VERSION_KEY, 0)
    return f"form_{version}_{nombre}"


def _estado_seleccion_multiple(
    base_key: str,
    opciones: list[str],
    valores_defecto: list[str],
) -> dict[str, object]:
    seleccion = [o for o in valores_defecto if o in opciones]
    estado: dict[str, object] = {f"{base_key}_seleccion": seleccion}
    for opcion in opciones:
        estado[f"{base_key}_{opcion}"] = opcion in seleccion
    return estado


def aplicar_valores_defecto_formulario() -> None:
    """Recrea el formulario totalmente vacío (nueva versión de widgets)."""
    st.session_state.pop(RESULTADO_KEY, None)
    st.session_state[FORM_VERSION_KEY] = st.session_state.get(FORM_VERSION_KEY, 0) + 1


def _opcion_o_none(valor: str | None) -> str | None:
    if valor is None:
        return None
    return valor


def _numero_o_none(valor: float | int | None) -> float | None:
    if valor is None:
        return None
    return float(valor)


def solicitar_limpieza_formulario() -> None:
    """Marca un reinicio para aplicarlo al inicio del siguiente ciclo de Streamlit."""
    st.session_state[LIMPIAR_FLAG] = True


# ---------------------------------------------------------------------------
# Configuración de la página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SE Evaluación Prequirúrgica Inicial",
    page_icon="🩺",
    layout="wide",
)


def encabezado():
    st.title("🩺 Sistema Experto de Evaluación Prequirúrgica Inicial")
    st.caption("Cirugía plástica estética corporal — abdominoplastía, liposucción o ambos")

    st.warning(
        "**Aviso:** este sistema no reemplaza la decisión médica. "
        "Funciona como apoyo preliminar para el cirujano plástico durante la consulta."
    )


def _radio_si_no(etiqueta: str, *, key: str) -> str | None:
    """Sí/no sin selección por defecto."""
    return st.radio(
        etiqueta,
        SI_NO_OPCIONES,
        index=None,
        horizontal=True,
        key=key,
    )


def _seleccion_multiple(
    etiqueta: str,
    opciones: list[str],
    valores_defecto: list[str],
    *,
    key: str,
    opcion_exclusiva: str | None = OPCION_NINGUNO,
) -> list[str]:
    """
    Selección múltiple con casillas.
    Si `opcion_exclusiva` está presente en las opciones, no puede combinarse con otras.
    """
    estado_key = f"{key}_seleccion"
    if estado_key not in st.session_state:
        st.session_state.update(
            _estado_seleccion_multiple(key, opciones, valores_defecto),
        )

    st.markdown(f"**{etiqueta}**")
    if opcion_exclusiva and opcion_exclusiva in opciones:
        st.caption(
            f"«{opcion_exclusiva}» es excluyente: no puede marcarse junto con otras opciones."
        )

    def alternar(opcion: str) -> None:
        seleccion = list(st.session_state[estado_key])
        if opcion_exclusiva and opcion == opcion_exclusiva:
            seleccion = [] if opcion in seleccion else [opcion_exclusiva]
        else:
            seleccion = [o for o in seleccion if o != opcion_exclusiva]
            if opcion in seleccion:
                seleccion.remove(opcion)
            else:
                seleccion.append(opcion)
        st.session_state[estado_key] = seleccion
        for op in opciones:
            st.session_state[f"{key}_{op}"] = op in seleccion

    columnas = st.columns(min(len(opciones), 3))
    for indice, opcion in enumerate(opciones):
        ck_key = f"{key}_{opcion}"
        if ck_key not in st.session_state:
            st.session_state[ck_key] = opcion in st.session_state[estado_key]
        with columnas[indice % len(columnas)]:
            st.checkbox(
                opcion,
                key=ck_key,
                on_change=alternar,
                args=(opcion,),
            )

    return list(st.session_state[estado_key])


# ---------------------------------------------------------------------------
# Formulario
# ---------------------------------------------------------------------------

def construir_formulario() -> DatosPaciente | None:
    """Construye el formulario y devuelve los datos del paciente al evaluar."""

    # Sección 1: Datos generales -----------------------------------------
    st.subheader("1. Datos generales")
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        edad = st.number_input(
            "Edad (años cumplidos)",
            min_value=0,
            max_value=120,
            value=None,
            step=1,
            help="Edad del paciente en años cumplidos. Ej: 35.",
            key=_form_key("paciente_edad"),
        )
    with col_b:
        sexo = st.radio(
            "Sexo biológico",
            SEXO_OPCIONES,
            index=None,
            horizontal=True,
            help="Sexo biológico registrado.",
            key=_form_key("sexo_biologico"),
        )
    with col_c:
        if sexo == "femenino":
            embarazo_ui = st.radio(
                "Embarazo actual o futuro cercano",
                EMBARAZO_OPCIONES_FORMULARIO,
                index=None,
                horizontal=False,
                help="Estado de embarazo actual o planificado a corto plazo.",
                key=_form_key("embarazo"),
            )
        elif not sexo:
            st.markdown("**Embarazo actual o futuro cercano**")
            st.caption("Seleccione primero el sexo biológico.")
            embarazo_ui = None
        else:
            st.markdown("**Embarazo actual o futuro cercano**")
            st.caption("No aplica — asignado automáticamente.")
            embarazo_ui = None
    with col_d:
        procedimiento = st.selectbox(
            "Procedimiento deseado",
            PROCEDIMIENTO_OPCIONES,
            index=None,
            help="Procedimiento que el paciente desea: abdominoplastía, liposucción o ambos.",
            key=_form_key("procedimiento_deseado"),
        )

    embarazo = resolver_embarazo(sexo, embarazo_ui)

    # Sección 2: Datos antropométricos -----------------------------------
    st.subheader("2. Datos antropométricos")
    col1, col2, col3 = st.columns(3)
    with col1:
        peso_actual = st.number_input(
            "Peso actual (kg)",
            min_value=0.0,
            max_value=300.0,
            value=None,
            step=0.5,
            help="Peso actual del paciente en kilogramos. Ej: 72.5",
            key=_form_key("peso_actual"),
        )
    with col2:
        altura = st.number_input(
            "Altura (metros)",
            min_value=0.0,
            max_value=2.5,
            value=None,
            step=0.01,
            format="%.2f",
            help="Altura en metros. Ej: 1.68",
            key=_form_key("altura"),
        )
    with col3:
        peso_6m = st.number_input(
            "Peso hace 6 meses (kg)",
            min_value=0.0,
            max_value=300.0,
            value=None,
            step=0.5,
            help="Peso del paciente 6 meses atrás. Sirve para evaluar estabilidad.",
            key=_form_key("peso_6m"),
        )

    # Sección 3: Evaluación corporal -------------------------------------
    st.subheader("3. Evaluación corporal")
    condicion = _seleccion_multiple(
        "Condición corporal observada (marque todas las que apliquen)",
        CONDICION_CORPORAL_OPCIONES,
        [],
        key=_form_key("condicion_corporal"),
    )
    cicatrizacion = st.selectbox(
        "Cicatrización (estimada por antecedentes / examen)",
        CICATRIZACION_OPCIONES,
        index=None,
        help="Calidad estimada de cicatrización del paciente.",
        key=_form_key("cicatrizacion"),
    )

    # Sección 4: Estado clínico y hábitos --------------------------------
    st.subheader("4. Estado clínico y hábitos")
    factores = _seleccion_multiple(
        "Factores de riesgo específicos",
        FACTORES_RIESGO_OPCIONES,
        [],
        key=_form_key("factores_riesgo"),
    )
    col_e, col_f, col_g, col_h = st.columns(4)
    with col_e:
        enf = _radio_si_no(
            "Enfermedad no controlada",
            key=_form_key("enfermedad_no_controlada"),
        )
    with col_f:
        fuma = _radio_si_no("Fuma actualmente", key=_form_key("fuma"))
    with col_g:
        consumo = _radio_si_no(
            "Consumo problemático de sustancias",
            key=_form_key("consumo_sustancias"),
        )
    with col_h:
        aplica_habitos = fuma == "sí" or consumo == "sí"
        if aplica_habitos:
            dispuesto_ui = st.radio(
                "Dispuesto a dejar hábitos de riesgo",
                DISPUESTO_HABITOS_OPCIONES,
                index=None,
                horizontal=True,
                help="Compromiso de abandono de tabaco y/o sustancias.",
                key=_form_key("dispuesto_habitos"),
            )
        elif not fuma or not consumo:
            st.markdown("**Dispuesto a dejar hábitos de riesgo**")
            st.caption("Indique primero tabaco y consumo de sustancias.")
            dispuesto_ui = None
        else:
            st.markdown("**Dispuesto a dejar hábitos de riesgo**")
            st.caption("No aplica — asignado automáticamente.")
            dispuesto_ui = None

    dispuesto = resolver_dispuesto_habitos(fuma, consumo, dispuesto_ui)

    # Sección 5: Antecedentes y expectativas -----------------------------
    st.subheader("5. Antecedentes y expectativas")
    col_i, col_j = st.columns(2)
    with col_i:
        antecedentes = st.selectbox(
            "Antecedentes quirúrgicos",
            ANTECEDENTES_OPCIONES,
            index=None,
            help="Cirugías previas y su evolución.",
            key=_form_key("antecedentes_quirurgicos"),
        )
    with col_j:
        expectativas = st.selectbox(
            "Expectativas",
            EXPECTATIVAS_OPCIONES,
            index=None,
            help="Coherencia entre lo que el paciente espera y lo que la cirugía puede ofrecer.",
            key=_form_key("expectativas"),
        )

    col_evaluar, col_limpiar = st.columns([3, 1])
    with col_evaluar:
        evaluar = st.button(
            "🔎 Evaluar paciente", use_container_width=True, type="primary",
        )
    with col_limpiar:
        limpiar = st.button(
            "🗑️ Nuevo paciente",
            use_container_width=True,
            help="Borra los datos del formulario y el último resultado para cargar otro paciente.",
        )

    if limpiar:
        solicitar_limpieza_formulario()
        st.rerun()

    if not evaluar:
        return None

    return DatosPaciente(
        edad=_numero_o_none(edad),
        sexo_biologico=_opcion_o_none(sexo),
        embarazo_actual_o_futuro_cercano=embarazo,
        procedimiento_deseado=_opcion_o_none(procedimiento),
        peso_actual=_numero_o_none(peso_actual),
        altura=_numero_o_none(altura),
        peso_hace_6_meses=_numero_o_none(peso_6m),
        condicion_corporal_observada=condicion,
        cicatrizacion=_opcion_o_none(cicatrizacion),
        factores_riesgo_especificos=factores,
        enfermedad_no_controlada=_opcion_o_none(enf),
        fuma=_opcion_o_none(fuma),
        consumo_problematico_sustancias=_opcion_o_none(consumo),
        dispuesto_a_dejar_habitos_riesgo=dispuesto,
        antecedentes_quirurgicos=_opcion_o_none(antecedentes),
        expectativas=_opcion_o_none(expectativas),
    )


# ---------------------------------------------------------------------------
# Visualización del resultado
# ---------------------------------------------------------------------------

def _color_clasificacion(clasificacion: str) -> str:
    mapa = {
        "candidato favorable": "green",
        "candidato con optimización previa": "orange",
        "postergar": "red",
        "no recomendado por el momento": "red",
        "información insuficiente": "gray",
        "fuera del dominio": "gray",
    }
    return mapa.get(clasificacion, "blue")


def mostrar_resultado(resultado: dict):
    if resultado["clasificacion_preliminar"] == "información insuficiente":
        st.error("⚠️ No se puede emitir una recomendación preliminar porque faltan datos esenciales.")
        st.write("Campos faltantes:", ", ".join(resultado.get("campos_faltantes", [])))
        return

    color = _color_clasificacion(resultado["clasificacion_preliminar"])

    st.markdown("---")
    st.header("Resultado")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"### Clasificación preliminar\n"
            f"<span style='color:{color}; font-size:1.4em; font-weight:bold'>"
            f"{resultado['clasificacion_preliminar']}</span>",
            unsafe_allow_html=True,
        )
    with col2:
        riesgo = resultado["nivel_riesgo"]
        st.markdown(
            f"### Nivel de riesgo\n"
            f"**{riesgo['categoria']}** (valor difuso ≈ {riesgo['valor']})"
        )
    with col3:
        ade = resultado["adecuacion_procedimiento"]
        st.markdown(
            f"### Adecuación del procedimiento\n"
            f"**{ade['categoria']}** (valor difuso ≈ {ade['valor']})"
        )

    st.markdown("#### 🩹 Conductas sugeridas")
    if resultado["conducta_sugerida"]:
        for c in resultado["conducta_sugerida"]:
            st.write(f"• {c}")
    else:
        st.write("Sin conductas adicionales sugeridas.")

    # Datos calculados
    st.markdown("#### 📊 Datos calculados")
    dc = resultado["datos_calculados"]
    st.info(
        f"IMC: **{dc.get('imc_calculado')}** ({dc.get('categoria_imc')}) — "
        f"Fluctuación peso: **{dc.get('fluctuacion_peso_calculada')}%** "
        f"({dc.get('estabilidad_peso')})."
    )

    # Factores
    col_fa, col_al = st.columns(2)
    with col_fa:
        st.markdown("#### ✅ Factores favorables")
        if resultado["factores_favorables"]:
            for f in resultado["factores_favorables"]:
                st.success(f)
        else:
            st.write("—")
    with col_al:
        st.markdown("#### ⚠️ Factores de alerta")
        if resultado["factores_alerta"]:
            for f in resultado["factores_alerta"]:
                st.warning(f)
        else:
            st.write("—")

    # Reglas activadas
    st.markdown("#### 📜 Reglas activadas")
    if resultado["reglas_activadas"]:
        for r in resultado["reglas_activadas"]:
            st.write(f"• **{r['codigo']}** — {r['descripcion']}: _{r['efecto']}_")
    else:
        st.write("No se activaron reglas.")

    # Reglas críticas descartadas
    if resultado.get("reglas_criticas_descartadas"):
        with st.expander("Reglas críticas descartadas (no detectadas)"):
            for r in resultado["reglas_criticas_descartadas"]:
                st.write(f"• {r['codigo']} — {r['descripcion']}")

    # Explicación
    st.markdown("#### 🧠 Explicación")
    st.write(resultado["explicacion"])

    with st.expander("Hechos en la memoria de trabajo (trazabilidad)"):
        for obj, atr, val in resultado.get("hechos", []):
            st.write(f"`{obj}` — `{atr}` — `{val}`")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    if st.session_state.pop(LIMPIAR_FLAG, False):
        aplicar_valores_defecto_formulario()

    encabezado()
    datos = construir_formulario()
    if datos is not None:
        motor = MotorInferencias()
        st.session_state[RESULTADO_KEY] = motor.evaluar(datos)
    if RESULTADO_KEY in st.session_state:
        mostrar_resultado(st.session_state[RESULTADO_KEY])


if __name__ == "__main__":
    main()
