# Clasificador de ejercicios · Matemáticas Aplicadas a las CCSS II · Funciones (análisis)

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía) del bloque de **Análisis / Funciones** de Matemáticas CCSS II. El texto procede de una extracción automática de PDF, así que puede venir con espacios raros (`f ' ( x )`, `x 2` en lugar de `x²`, `2 ' 5` en lugar de `2,5`), saltos de línea perdidos o símbolos dañados. Ignora esos defectos y fíjate en las palabras.

Tu tarea es asignar **todas** las etiquetas que correspondan a lo que pide el ejercicio. Casi todos los ejercicios de este bloque tienen varios apartados (a, b, c, d) y cada apartado suele aportar una etiqueta distinta.

## Etiquetas y palabras clave

El diccionario siguiente tiene como **key** la etiqueta y como **value** la lista de palabras o expresiones que, si aparecen en el enunciado (sin distinguir mayúsculas/minúsculas ni tildes), activan esa etiqueta.

```python
ETIQUETAS = {
    "continuidad y derivabilidad": [
        "continua", "continuidad", "discontinuidad", "tipo de discontinuidad",
        "derivable", "derivabilidad",
        "sea continua y derivable", "estudie la continuidad",
    ],

    "cálculo de parámetros": [
        "valores de a y b", "valor de a", "valor de b", "valores de b y c",
        "valores a, b y c", "a, b y c", "halle a y b", "calcule a y b",
        "determine a, b y c", "con a y b números reales",
        "siendo a y b números reales", "parámetros",
    ],

    "monotonía y extremos": [
        "monotonía", "crecimiento", "decrecimiento", "creciente", "decreciente",
        "intervalos de crecimiento", "extremos", "extremos relativos",
        "extremos absolutos", "máximo", "mínimo", "puntos críticos",
        "va aumentando", "comience a decrecer", "niveles más alto y más bajo",
    ],

    "curvatura": [
        "curvatura", "concavidad", "convexidad", "cóncava", "convexa",
        "punto de inflexión", "puntos de inflexión",
    ],

    "asíntotas y límites": [
        "asíntota", "asíntotas", "límite", "tendería", "tendencia",
        "transcurrieran los años de manera indefinida", "están limitados",
    ],

    "dominio y puntos de corte": [
        "dominio de la función", "halle el dominio", "determine el dominio",
        "puntos de corte", "corte con los ejes", "cortes con los ejes",
    ],

    "representación gráfica": [
        "represente gráficamente la función", "represente la gráfica",
        "represente gráficamente f", "esboce la gráfica", "esboce",
        "esbozo", "dibuje la gráfica", "dibuje",
    ],

    "recta tangente": [
        "recta tangente", "rectas tangentes", "tangente a la gráfica",
        "pendiente", "sea horizontal la recta tangente", "paralelas a la recta",
    ],

    "cálculo de derivadas": [
        "calcule la derivada", "calcule las derivadas",
        "derivada de las siguientes funciones", "derivadas de las funciones",
        "función derivada de cada una",
    ],

    "función a partir de su derivada": [
        "variación instantánea", "su derivada es", "cuya expresión es",
        "f ' ( t ) =", "f '(t) =", "f'(x) =", "v ' ( t )", "c ' ( t )", "b ' ( t )",
        "f ' ( x ) = f ( x )", "f'(x) = f(x)", "halle la función",
        "obtenga la expresión de la función", "expresión analítica de la función",
        "la gráfica de su derivada", "primitiva",
    ],

    "integral definida": [
        "calcule ∫", "integral", "integrales definidas", "∫",
        "interprete el resultado",
    ],

    "área de recinto": [
        "área", "recinto", "región acotada", "región limitada",
        "región del plano", "región delimitada", "superficie",
        "eje de abscisas y las rectas", "eje ox y las rectas",
    ],

    "problema contextualizado": [
        "beneficio", "beneficios", "ingresos", "costes", "gastos", "euros", "€",
        "ventas", "cotización", "acciones", "empresa", "capital", "intereses",
        "población", "habitantes", "bacterias", "audiencia", "glucosa",
        "paciente", "temperatura", "velocidad", "concentración", "noticia",
        "cesio", "diagnosticados", "hectáreas", "kilogramos", "siembra",
        "medido en horas", "en años", "en meses", "en minutos",
    ],
}

ETIQUETA_POR_DEFECTO = "funciones (general)"
```

## Reglas de clasificación

1. **Multi-etiqueta.** Si el enunciado activa varias etiquetas, devuélvelas todas separadas por `" | "`, en el mismo orden en que aparecen en el diccionario.
2. **"Represente el recinto / la región"** → es `área de recinto`, **no** `representación gráfica`. Usa `representación gráfica` solo cuando se pide dibujar la función (`represente gráficamente f`, `esboce la gráfica de f`).
3. **"Con a y b números reales"** solo activa `cálculo de parámetros` si además se pide hallar/determinar esos valores. Si los valores vienen dados (`Para a = 2 y b = -2, ...`) y no se piden, no la añadas.
4. **"Máximo/mínimo" en problemas de beneficio** (`¿cuándo se alcanza el máximo beneficio?`) → `monotonía y extremos` **y** `problema contextualizado`.
5. **"Integral"** dentro de un cálculo de área (`calcule el área...`) → solo `área de recinto`. Usa `integral definida` cuando se pide expresamente calcular `∫` entre límites o interpretar una integral.
6. **`F'(x) = f(x)`, `h'(x) = ... y h(2) = ...`, `c'(t) = ...` con un valor inicial** → `función a partir de su derivada`.
7. **`problema contextualizado`** se añade cuando la función modela una situación real (economía, biología, física, sociedad), aunque el resto de apartados sean técnicos.
8. Si no encaja ninguna etiqueta, usa `funciones (general)`.

## Nivel de confianza

- **alta:** aparecen palabras clave claras de todas las etiquetas asignadas y el contexto no deja dudas.
- **media:** el contexto encaja pero faltan palabras clave en alguna etiqueta, o hay dudas sobre si una etiqueta aplica (p. ej. si "represente" se refiere a la función o al recinto).
- **baja:** se ha usado la etiqueta por defecto, o el texto está demasiado dañado para interpretarlo con seguridad.

## Ejemplos

Enunciado: «Se considera la función f(x) = { x² − 4x + 4 si x < 3 ; −x + 4 si x ≥ 3 }. a) Estudie la continuidad y derivabilidad de la función f en todos los puntos de su dominio. b) Represente gráficamente f. c) Calcule el área de la región limitada por la gráfica de f, el eje de abscisas y las rectas x = 2 y x = 4.»
{"tipo_ejercicio": "continuidad y derivabilidad | representación gráfica | área de recinto", "confianza": "alta"}

Enunciado: «Una empresa de fumigación sabe que los beneficios, en miles de euros, ... B(x) = −x² + 16x − 48. a) ¿Cuántas hectáreas tiene que fumigar al mes para que la empresa tenga beneficios? b) ¿Cuántas hectáreas tiene que fumigar para obtener el máximo beneficio mensual?...»
{"tipo_ejercicio": "monotonía y extremos | problema contextualizado", "confianza": "alta"}

Enunciado: «a) Calcule la derivada de las siguientes funciones: f(x) = (−5 + x²)²·e^(3x), g(x) = ln(x³ − 5x)/(1 − x²). b) Calcule el área del recinto acotado por la gráfica de h(x) = −x² + 2x + 3 y el eje de abscisas.»
{"tipo_ejercicio": "cálculo de derivadas | área de recinto", "confianza": "alta"}

Enunciado: «El número de bacterias en un determinado cultivo viene dado por la función B(t) ... La variación instantánea ... B'(t) = 50000·e^(2t). a) ¿Existe algún instante t en el que el número de bacterias comience a decrecer? b) Obtenga la expresión de la función B(t), sabiendo que en el instante t = 0 ...»
{"tipo_ejercicio": "monotonía y extremos | función a partir de su derivada | problema contextualizado", "confianza": "alta"}

Enunciado: «Se considera la función f(x) = 1 − 4/(3 + x). a) Halle el dominio de f y los puntos de corte de su gráfica con los ejes de coordenadas. b) Calcule las asíntotas de la función f. c) Obtenga los puntos donde la recta tangente a la gráfica de f tiene pendiente 1. d) Estudie la curvatura de la función f.»
{"tipo_ejercicio": "curvatura | asíntotas y límites | dominio y puntos de corte | recta tangente", "confianza": "alta"}

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código:

{"tipo_ejercicio": "<etiqueta_1 | etiqueta_2 | ...>", "confianza": "alta|media|baja"}
