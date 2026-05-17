"""
test_casos.py
-------------
Runner sencillo de los casos de prueba. No depende de pytest: se ejecuta
directamente con:

    python -m tests.test_casos

Imprime por consola los resultados de cada caso y verifica que la
clasificación, el nivel de riesgo y la adecuación coincidan con lo
esperado (los campos con `None` se omiten de la comparación).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permitir ejecutar este script directamente como `python tests/test_casos.py`.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from experto.motor_inferencias import MotorInferencias
from tests.casos_prueba import CASOS


def _ok(actual, esperado) -> bool:
    if esperado is None:
        return True
    return actual == esperado


def _contiene_alguna(conductas, claves) -> bool:
    if not claves:
        return True
    texto = " ".join(conductas).lower()
    return all(clave.lower() in texto for clave in claves)


def ejecutar_caso(caso: dict, motor: MotorInferencias) -> bool:
    print("=" * 72)
    print(caso["nombre"])
    print("-" * 72)

    resultado = motor.evaluar(caso["datos"])

    esp = caso["esperado"]
    clas_ok = _ok(resultado["clasificacion_preliminar"], esp.get("clasificacion_preliminar"))
    riesgo_ok = _ok(resultado["nivel_riesgo"]["categoria"], esp.get("nivel_riesgo"))
    ade_ok = _ok(resultado["adecuacion_procedimiento"]["categoria"], esp.get("adecuacion_procedimiento"))
    conducta_ok = _contiene_alguna(resultado["conducta_sugerida"], esp.get("conductas_clave", []))

    print(f"  Clasificación  : {resultado['clasificacion_preliminar']}"
          f"   (esperado: {esp.get('clasificacion_preliminar')}) -> {'OK' if clas_ok else 'FAIL'}")
    print(f"  Nivel riesgo   : {resultado['nivel_riesgo']['categoria']} "
          f"(valor {resultado['nivel_riesgo']['valor']})"
          f"   (esperado: {esp.get('nivel_riesgo')}) -> {'OK' if riesgo_ok else 'FAIL'}")
    print(f"  Adecuación     : {resultado['adecuacion_procedimiento']['categoria']} "
          f"(valor {resultado['adecuacion_procedimiento']['valor']})"
          f"   (esperado: {esp.get('adecuacion_procedimiento')}) -> {'OK' if ade_ok else 'FAIL'}")
    print(f"  Conductas      : {resultado['conducta_sugerida']}"
          f"   claves: {esp.get('conductas_clave', [])} -> {'OK' if conducta_ok else 'FAIL'}")
    print("  Datos calc.    :", resultado["datos_calculados"])
    print("  Reglas activ.  :", [r["codigo"] for r in resultado["reglas_activadas"]])
    print("  Explicación    :", resultado["explicacion"])

    todo_ok = clas_ok and riesgo_ok and ade_ok and conducta_ok
    print(f"  --> RESULTADO  : {'PASA' if todo_ok else 'NO PASA'}")
    return todo_ok


def main() -> int:
    motor = MotorInferencias()
    aprobados = 0
    for caso in CASOS:
        if ejecutar_caso(caso, motor):
            aprobados += 1
    total = len(CASOS)
    print()
    print("=" * 72)
    print(f"Casos aprobados: {aprobados} / {total}")
    print("=" * 72)
    return 0 if aprobados == total else 1


if __name__ == "__main__":
    sys.exit(main())
