# Sistema Experto de Evaluación Prequirúrgica Inicial

Sistema experto **híbrido** (reglas + lógica difusa) para la evaluación
prequirúrgica inicial en cirugía plástica estética corporal
(abdominoplastía, liposucción o ambos procedimientos).

> ⚠️ Este sistema **no reemplaza** la decisión médica. Funciona como apoyo
> preliminar para el cirujano plástico durante la consulta.

---

## Estructura del proyecto

```
sistema_experto_cirugia/
│
├── app.py                       # Interfaz Streamlit (recomendada)
├── main.py                      # Interfaz por consola
├── requirements.txt
├── README.md
│
├── experto/
│   ├── __init__.py
│   ├── modelos.py               # DatosPaciente, opciones, validación
│   ├── logica_difusa.py         # Triangular, trapezoidal, centroide
│   ├── base_conocimientos.py    # Conjuntos difusos + reglas R1..R34
│   ├── memoria_trabajo.py       # Hechos objeto-atributo-valor
│   ├── motor_inferencias.py     # Encadenamiento hacia adelante
│   └── subsistema_explicacion.py# Explicación en lenguaje natural
│
└── tests/
    ├── __init__.py
    ├── casos_prueba.py          # 6 casos definidos en la consigna
    └── test_casos.py            # Runner que verifica los 6 casos
```

---

## Instalación

El sistema usa **únicamente la librería estándar de Python**.
La única dependencia opcional es **Streamlit** para la interfaz gráfica.

Requisitos:

- Python 3.9 o superior.

Instalación opcional de Streamlit:

```bash
pip install -r requirements.txt
```

---

## Cómo ejecutar

### Opción 1: Interfaz gráfica (recomendada)

```bash
cd sistema_experto_cirugia
streamlit run app.py
```

Streamlit abrirá una página web con un formulario dividido en secciones
(datos generales, antropométricos, evaluación corporal, estado clínico y
hábitos, antecedentes y expectativas). Al presionar **Evaluar paciente**
se muestra el resultado completo con colores:

- 🟢 verde: factores favorables.
- 🟡 amarillo: factores de alerta.
- 🔴 rojo: condiciones críticas / clasificaciones desfavorables.
- 🔵 azul / neutro: datos calculados.

### Opción 2: Interfaz por consola

```bash
cd sistema_experto_cirugia
python main.py
```

El programa pregunta cada campo, valida la entrada y al final imprime
clasificación, riesgo, adecuación, conductas sugeridas, factores
favorables, alertas y reglas activadas.

### Opción 3: Casos de prueba

```bash
cd sistema_experto_cirugia
python -m tests.test_casos
```

Ejecuta los 6 casos descritos en la consigna y reporta cuáles pasan.

---

## Cómo está implementado el sistema experto

### 1. Base de Conocimientos (`experto/base_conocimientos.py`)

Contiene:

- **Conjuntos difusos** para `IMC` (universo 16-45), `estabilidad de peso`
  (0-20 %), `cicatrización` (0-10), `expectativas` (0-10), `nivel de
  riesgo` (0-100) y `adecuación del procedimiento` (0-100).
- **Reglas expertas** R1..R34 con su prioridad, condición, acción y
  efecto. Están agrupadas en 6 niveles de prioridad:
  1. Reglas críticas de seguridad (R1..R6).
  2. Hábitos y disposición a optimizar (R7..R10).
  3. Adecuación del procedimiento (R11..R18).
  4. Riesgo difuso (R19..R26).
  5. Expectativas (R27..R29).
  6. Clasificación final (R30..R34).
- R35 (información insuficiente) se trata como validación técnica en el
  motor, no como regla médica.

### 2. Memoria de Trabajo (`experto/memoria_trabajo.py`)

Almacena hechos en formato `objeto - atributo - valor`. Por ejemplo:

```
paciente - edad                  - 36
paciente - procedimiento_deseado - abdominoplastía
sistema  - imc_calculado         - 28.65
sistema  - estabilidad_peso      - inestable
sistema  - regla_activada        - R23
sistema  - clasificacion_preliminar - postergar
```

Además guarda activaciones difusas, reglas activadas, factores favorables,
factores de alerta, conductas sugeridas y maneja prioridades para que las
reglas críticas no sean sobrescritas por reglas de menor prioridad.

### 3. Motor de Inferencias (`experto/motor_inferencias.py`)

Implementa **encadenamiento hacia adelante** con el ciclo
**Aparear → Seleccionar → Ejecutar**:

1. Carga los datos del paciente.
2. Valida información obligatoria (R35 como validación técnica).
3. Calcula IMC, categoría de IMC, fluctuación y estabilidad de peso.
4. Fuzzifica IMC, estabilidad, cicatrización y expectativas.
5. Aplica las reglas por grupo de prioridad (1 → 5).
6. Defuzzifica el nivel de riesgo y la adecuación por **centroide**.
7. Aplica las reglas de clasificación final (grupo 6).
8. Devuelve un diccionario con clasificación, riesgo, adecuación,
   conductas, factores, reglas activadas y explicación.

### 4. Lógica difusa (`experto/logica_difusa.py`)

Implementación manual con solo la librería estándar:

- `triangular(x, a, b, c)` y `trapezoidal(x, a, b, c, d)`.
- `ConjuntoDifuso` y `VariableLinguistica`.
- `defuzzificar_centroide(activaciones, conjuntos, universo, paso)`
  que aplica `Σ(x·μ(x)) / Σ μ(x)` sobre la salida agregada de Mamdani.
- `categorizar_riesgo` y `categorizar_adecuacion` interpretan el valor
  defuzzificado (0-35: bajo / 36-70: moderado / 71-100: alto, etc.).

### 5. Subsistema de Explicación (`experto/subsistema_explicacion.py`)

A partir de la Memoria de Trabajo genera:

- Texto natural con la clasificación, riesgo, adecuación, datos calculados,
  factores favorables, factores de alerta, conductas sugeridas y reglas
  activadas.
- Lista de reglas críticas descartadas (qué condiciones críticas se
  evaluaron y no se activaron), para reforzar la trazabilidad.

### 6. Interfaz

- `app.py`: formulario Streamlit con secciones, ayudas por campo y
  resultado coloreado por gravedad.
- `main.py`: versión por consola, guía al usuario campo por campo.

---

## Estructura del resultado devuelto

```python
{
  "clasificacion_preliminar": "candidato con optimización previa",
  "nivel_riesgo": {"valor": 50.0, "categoria": "moderado"},
  "adecuacion_procedimiento": {"valor": 83.2, "categoria": "adecuado"},
  "conducta_sugerida": ["Suspender tabaquismo antes de avanzar (...)"],
  "datos_calculados": {
      "imc_calculado": 27.55,
      "categoria_imc": "normal-aceptable",
      "fluctuacion_peso_calculada": 0.67,
      "estabilidad_peso": "estable",
      "cicatrizacion_categoria": "normal",
      "expectativas_categoria": "realistas"
  },
  "factores_favorables": [...],
  "factores_alerta": [...],
  "reglas_activadas": [
      {"codigo": "R7",
       "descripcion": "Tabaquismo activo con disposición a dejar",
       "efecto": "Eleva a mínimo CANDIDATO CON OPTIMIZACIÓN PREVIA..."}
  ],
  "reglas_criticas_descartadas": [...],
  "explicacion": "El sistema clasifica al paciente como...",
  "hechos": [("paciente", "edad", 40), ...]
}
```

---

## Casos de prueba

Los 6 casos (5 obligatorios + 1 opcional) se encuentran en
`tests/casos_prueba.py`. Al ejecutar `python -m tests.test_casos` se
verifica:

| Caso                                                            | Resultado esperado                                  |
|-----------------------------------------------------------------|-----------------------------------------------------|
| 1. Liposucción + grasa localizada + peso estable + realistas    | candidato favorable / riesgo bajo / adecuado        |
| 2. Abdominoplastía + exceso de piel + tabaco dispuesto a dejar  | optimización previa / riesgo moderado / adecuado    |
| 3. Abdominoplastía + fluctuación > 10 %                         | postergar / riesgo alto / parcialmente adecuado     |
| 4. Liposucción con expectativas irreales                        | no recomendado por el momento                       |
| 5. Liposucción con grasa visceral sospechada                    | procedimiento no adecuado / redefinir técnica       |
| 6. Combinada + enfermedad no controlada                         | postergar / control clínico previo                  |

Salida esperada: `Casos aprobados: 6 / 6`.

---

## Notas de diseño

- Las reglas críticas (grupo 1) fijan la clasificación con prioridad alta;
  reglas posteriores no pueden sobrescribirla.
- Un IMC moderadamente elevado **no se descarta automáticamente**: se
  interpreta en conjunto con estabilidad, hábitos, cicatrización y
  adecuación del procedimiento, como pide el documento.
- La defuzzificación usa Mamdani agregado por máximo y centroide
  discreto (paso 1).
- El sistema mantiene una bandera para bloquear la clasificación
  "candidato favorable" cuando aparecen condiciones que la incompatibilizan
  (por ejemplo, expectativas poco claras).
