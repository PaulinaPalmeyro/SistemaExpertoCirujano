"""
Paquete del Sistema Experto Híbrido para Evaluación Prequirúrgica Inicial
en Cirugía Plástica Estética Corporal (abdominoplastía / liposucción / ambos).

Módulos:
    - modelos:                 dataclasses y constantes con las variables del dominio.
    - logica_difusa:           funciones de membresía y defuzzificación por centroide.
    - base_conocimientos:      reglas expertas, prioridades y conjuntos difusos.
    - memoria_trabajo:         hechos del paciente y del sistema (objeto-atributo-valor).
    - motor_inferencias:       encadenamiento hacia adelante (Aparear -> Seleccionar -> Ejecutar).
    - subsistema_explicacion:  explicación trazable en lenguaje natural.
"""
