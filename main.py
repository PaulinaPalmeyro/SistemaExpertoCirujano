"""
main.py
-------
Interfaz por consola del Sistema Experto.

Ejecutar con:
    python main.py

Es interactiva y guía al usuario campo por campo. Si se prefiere una
interfaz gráfica, ver `app.py` (Streamlit).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Permitir ejecutar el script directamente.
sys.path.append(str(Path(__file__).resolve().parent))

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
    seleccion_valida_sin_ninguno_mixto,
)
from experto.motor_inferencias import MotorInferencias


def pedir_opcion(pregunta: str, opciones: list, multi: bool = False) -> object:
    print(f"\n{pregunta}")
    for i, op in enumerate(opciones, 1):
        print(f"  {i}. {op}")
    while True:
        crudo = input("→ ").strip()
        if multi:
            try:
                idx = [int(x) - 1 for x in crudo.replace(",", " ").split()]
                if all(0 <= i < len(opciones) for i in idx):
                    return [opciones[i] for i in idx]
            except ValueError:
                pass
            print("Ingrese uno o más números separados por espacio.")
        else:
            try:
                i = int(crudo) - 1
                if 0 <= i < len(opciones):
                    return opciones[i]
            except ValueError:
                pass
            print("Ingrese un número válido.")


def pedir_opcion_multiple(
    pregunta: str,
    opciones: list[str],
    *,
    opcion_exclusiva: str = OPCION_NINGUNO,
) -> list[str]:
    """Selección múltiple; «ninguno» no puede combinarse con otras opciones."""
    nota = (
        f"\n  (Nota: «{opcion_exclusiva}» no puede elegirse junto con otras opciones.)"
        if opcion_exclusiva in opciones
        else ""
    )
    while True:
        seleccion = pedir_opcion(f"{pregunta}{nota}", opciones, multi=True)
        if not seleccion:
            print("Debe seleccionar al menos una opción.")
            continue
        if seleccion_valida_sin_ninguno_mixto(seleccion):
            return seleccion
        print(
            f"«{opcion_exclusiva}» no puede combinarse con otras opciones. "
            "Intente de nuevo."
        )


def pedir_numero(pregunta: str, ejemplo: str = "") -> float:
    print(f"\n{pregunta}" + (f"  (ejemplo: {ejemplo})" if ejemplo else ""))
    while True:
        crudo = input("→ ").strip().replace(",", ".")
        try:
            return float(crudo)
        except ValueError:
            print("Ingrese un número válido.")


def cargar_paciente_interactivo() -> DatosPaciente:
    print("=" * 70)
    print("SISTEMA EXPERTO DE EVALUACIÓN PREQUIRÚRGICA INICIAL")
    print("Cirugía plástica estética corporal")
    print("=" * 70)
    print("Aviso: este sistema NO reemplaza la decisión médica.")
    print("Funciona como apoyo preliminar para el cirujano plástico.\n")

    edad = pedir_numero("Edad del paciente (años cumplidos)", "35")
    sexo = pedir_opcion("Sexo biológico:", SEXO_OPCIONES)
    if sexo == "femenino":
        embarazo_ui = pedir_opcion(
            "Embarazo actual o futuro cercano:", EMBARAZO_OPCIONES_FORMULARIO,
        )
    else:
        embarazo_ui = None
        print("\nEmbarazo actual o futuro cercano: no aplica (asignado automáticamente).")
    embarazo = resolver_embarazo(sexo, embarazo_ui)
    procedimiento = pedir_opcion("Procedimiento deseado:", PROCEDIMIENTO_OPCIONES)
    peso = pedir_numero("Peso actual (kg)", "72.5")
    altura = pedir_numero("Altura (m)", "1.68")
    peso_6m = pedir_numero("Peso hace 6 meses (kg)", "70.0")
    condicion = pedir_opcion_multiple(
        "Condición corporal observada (ingrese números separados por espacio):",
        CONDICION_CORPORAL_OPCIONES,
    )
    cicatrizacion = pedir_opcion("Cicatrización:", CICATRIZACION_OPCIONES)
    factores = pedir_opcion_multiple(
        "Factores de riesgo específicos (puede seleccionar varios):",
        FACTORES_RIESGO_OPCIONES,
    )
    enf = pedir_opcion("Enfermedad no controlada:", SI_NO_OPCIONES)
    fuma = pedir_opcion("Fuma actualmente:", SI_NO_OPCIONES)
    consumo = pedir_opcion("Consumo problemático de sustancias:", SI_NO_OPCIONES)
    if fuma == "sí" or consumo == "sí":
        dispuesto_ui = pedir_opcion(
            "Dispuesto a dejar hábitos de riesgo:", DISPUESTO_HABITOS_OPCIONES,
        )
    else:
        dispuesto_ui = None
        print("\nDispuesto a dejar hábitos de riesgo: no aplica (asignado automáticamente).")
    dispuesto = resolver_dispuesto_habitos(fuma, consumo, dispuesto_ui)
    antecedentes = pedir_opcion("Antecedentes quirúrgicos:", ANTECEDENTES_OPCIONES)
    expectativas = pedir_opcion("Expectativas:", EXPECTATIVAS_OPCIONES)

    return DatosPaciente(
        edad=edad,
        sexo_biologico=sexo,
        embarazo_actual_o_futuro_cercano=embarazo,
        procedimiento_deseado=procedimiento,
        peso_actual=peso,
        altura=altura,
        peso_hace_6_meses=peso_6m,
        condicion_corporal_observada=condicion,
        cicatrizacion=cicatrizacion,
        factores_riesgo_especificos=factores,
        enfermedad_no_controlada=enf,
        fuma=fuma,
        consumo_problematico_sustancias=consumo,
        dispuesto_a_dejar_habitos_riesgo=dispuesto,
        antecedentes_quirurgicos=antecedentes,
        expectativas=expectativas,
    )


def imprimir_resultado(resultado: dict) -> None:
    print("\n" + "=" * 70)
    print("RESULTADO PRELIMINAR")
    print("=" * 70)
    print(f"Clasificación preliminar : {resultado['clasificacion_preliminar']}")
    print(f"Nivel de riesgo          : {resultado['nivel_riesgo']['categoria']} "
          f"(valor difuso ≈ {resultado['nivel_riesgo']['valor']})")
    print(f"Adecuación del procedimiento : {resultado['adecuacion_procedimiento']['categoria']} "
          f"(valor difuso ≈ {resultado['adecuacion_procedimiento']['valor']})")

    print("\nDatos calculados:")
    for k, v in resultado["datos_calculados"].items():
        print(f"  - {k}: {v}")

    print("\nConductas sugeridas:")
    for c in resultado["conducta_sugerida"]:
        print(f"  • {c}")

    print("\nFactores favorables:")
    for f in resultado["factores_favorables"] or ["—"]:
        print(f"  ✓ {f}")

    print("\nFactores de alerta:")
    for f in resultado["factores_alerta"] or ["—"]:
        print(f"  ! {f}")

    print("\nReglas activadas:")
    for r in resultado["reglas_activadas"]:
        print(f"  - {r['codigo']}: {r['descripcion']} → {r['efecto']}")

    print("\nReglas críticas descartadas:")
    for r in resultado.get("reglas_criticas_descartadas", []):
        print(f"  · {r['codigo']}: {r['descripcion']}")

    print("\nExplicación:")
    print(resultado["explicacion"])
    print("=" * 70)


def main() -> None:
    datos = cargar_paciente_interactivo()
    motor = MotorInferencias()
    resultado = motor.evaluar(datos)
    imprimir_resultado(resultado)

    if "--json" in sys.argv:
        print("\nJSON:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
