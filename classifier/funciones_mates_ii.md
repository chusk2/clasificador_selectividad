# Clasificador de ejercicios · Matemáticas II · Funciones (análisis)

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía) del bloque de **Análisis / Funciones** de Matemáticas II. El texto procede de una extracción automática de PDF, así que puede venir con espacios raros (`f ' ( x )`, `x 2` en lugar de `x²`, `sen ( x )`), fracciones partidas en varias líneas (numerador en una línea, denominador en otra), el `x → 0` de un límite separado del `lim`, saltos de línea perdidos o símbolos dañados (`∞`, `→`, `≤`, `π`). Ignora esos defectos y fíjate en las palabras y en lo que se pide.

Tu tarea es asignar **todas** las etiquetas que correspondan a lo que pide el ejercicio. Muchos ejercicios tienen dos apartados (a, b) y cada apartado suele aportar una etiqueta distinta. Además, en algunos casos debes rellenar el campo `observaciones`.

## Etiquetas y palabras clave

El diccionario siguiente tiene como **key** la etiqueta y como **value** la lista de palabras o expresiones que, si aparecen en el enunciado (sin distinguir mayúsculas/minúsculas ni tildes, y aceptando tanto la forma "tú" — *calcula, halla, estudia, determina, esboza* — como la forma "usted" — *calcule, halle, estudie, determine, esboce*), activan esa etiqueta. Las **reglas** de la sección siguiente tienen prioridad sobre el diccionario: algunas etiquetas necesitan que se cumplan varias condiciones a la vez, y otras se excluyen entre sí.

```python
ETIQUETAS = {
    "L'Hopital": [
        "lim", "límite", "el valor del límite", "es finito",
        "sabiendo que lim", "x → 0", "x→0", "x → +∞", "x → −∞", "x → -π",
        "regla de l'hôpital", "l'hôpital", "l'hopital",
    ],

    "integrales": [
        "área", "recinto", "región limitada", "región acotada",
        "región del plano", "región delimitada", "eje de abscisas y las rectas",
        "integral", "integral definida", "∫", "primitiva", "función primitiva",
        "F'(x) = f(x)", "cuya derivada es", "sabiendo que su derivada",
        "sabiendo que f'(x) =", "su función derivada es",
    ],

    "estudio continuidad / derivabilidad": [
        "estudia la continuidad", "estudia la derivabilidad",
        "continuidad y derivabilidad", "estudia si f es continua",
        "estudia si f es derivable", "es continua", "es derivable",
        "puntos de discontinuidad", "tipo de discontinuidad",
    ],

    "coeficientes continuidad / derivabilidad": [
        "función continua", "función derivable", "para que f sea continua",
        "para que f sea derivable", "sea continua y derivable",
        "continua en", "derivable en",
        "calcula a y b", "halla a y b", "determina a y b",
        "valores de a y b", "si x <", "si x ≤", "si x >", "si x ≥",
    ],

    "representación función": [
        "representa gráficamente", "representa la gráfica", "esboza",
        "esbozo", "haz un esbozo", "dibuja la gráfica", "dibuja", "traza la gráfica",
    ],

    "calcular coeficientes": [
        "calcula a", "halla a", "determina a",
        "calcula a y b", "halla a y b", "calcula a, b y c", "halla a, b y c",
        "los valores de a y b", "los valores de a, b y c", "el valor de a",
        "los coeficientes", "los parámetros",
        "sabiendo que su gráfica", "pase por el punto", "pasa por el punto",
        "tiene un extremo relativo en", "tiene un punto de inflexión en",
        "como asíntota", "como recta tangente",
    ],

    "asíntotas": [
        "asíntota", "asíntotas", "asíntota vertical", "asíntota horizontal",
        "asíntota oblicua", "estudia y calcula las asíntotas",
    ],

    "rectas tangente y normal": [
        "recta tangente", "rectas tangentes", "recta normal",
        "tangente a la gráfica", "normal a la gráfica",
        "pendiente de la recta tangente", "como recta tangente",
        "paralela a la recta", "ecuación de la recta",
    ],

    "monotonía": [
        "monotonía", "crecimiento", "decrecimiento", "creciente", "decreciente",
        "intervalos de crecimiento y de decrecimiento",
        "extremos relativos", "extremos absolutos", "extremos locales",
        "máximos y mínimos", "máximo relativo", "mínimo relativo",
        "máximo absoluto", "mínimo absoluto",
        "abscisas donde se obtienen y valores que se alcanzan",
    ],

    "curvatura": [
        "curvatura", "concavidad", "convexidad", "cóncava", "convexa",
        "punto de inflexión", "puntos de inflexión",
    ],

    "optimización": [
        "área máxima", "mayor área", "volumen máximo", "mínima", "máxima",
        "mayor", "menor", "menor distancia posible", "sea mínima", "sea máximo",
        "dimensiones", "longitudes de los lados", "halla dos números",
        "cuya suma sea", "el producto", "rectángulo", "inscrito",
        "semicircunferencia", "cilindro", "con tapas", "perímetro",
        "mayor entrada de luz", "de entre todos",
    ],
}

ETIQUETA_POR_DEFECTO = "funciones (general)"
```

## Reglas de clasificación

1. **Multi-etiqueta.** Si el enunciado activa varias etiquetas, devuélvelas todas separadas por `" | "`, en el **mismo orden en que aparecen en el diccionario**.

2. **L'Hopital** solo se asigna si en el enunciado aparece **escrito un límite** (`lim ...`), ya sea como enunciado completo o dentro de un apartado (p. ej. `b) Calcula lim x→−π arctg(x+π)/sen(x)`). Que el alumno tenga que calcular límites para obtener asíntotas o para estudiar la continuidad **no** cuenta: si no aparece `lim` escrito, no pongas L'Hopital. Ojo: `lim` debe ser la notación del límite, no parte de otra palabra (`región limitada` no activa L'Hopital).
   - Si el límite contiene un parámetro y se pide su valor, escribe en `observaciones`:
     - `"L'Hopital calcular a/b"` si el límite viene **igualado a un número** (`... = 1`, `... = −1/7`), tanto si se pide solo `a` como si se piden `a` y `b`.
     - `"L'Hopital calcular a"` si se pide `a` pero el límite **no** viene igualado a un número (p. ej. `sabiendo que lim ... es finito, calcula a y el valor del límite`).
   - Si el límite no tiene parámetros (solo hay que calcularlo), deja `observaciones` vacío para esta etiqueta.
   - Cuando la `a` (o `b`) se obtiene del límite, **no** añadas `calcular coeficientes`.

3. **Continuidad / derivabilidad: estudio vs. coeficientes.**
   - `estudio continuidad / derivabilidad`: se pide **estudiar** la continuidad y/o derivabilidad de una función (normalmente a trozos o con valor absoluto `|x|`), sin parámetros que calcular.
   - `coeficientes continuidad / derivabilidad`: hay una **función a trozos** (aparece `si x < ...`, `si x ≥ ...`) **y** se piden parámetros (normalmente `a` y `b`) **y** se menciona que la función es (o debe ser) **continua** y/o **derivable**. Basta con que el enunciado diga "Considera la función continua f definida por ..." y luego "Calcula a y b". En este caso escribe en `observaciones` `"2 ramas"` o `"3 ramas"` según el número de trozos de la función.
   - Si se asigna `coeficientes continuidad / derivabilidad`, **no** añadas `calcular coeficientes` ni `estudio continuidad / derivabilidad` por los mismos parámetros.
   - Una función a trozos en la que solo se piden extremos, tangentes, etc. (sin hablar de continuidad ni derivabilidad) **no** lleva ninguna de estas dos etiquetas.

4. **Calcular coeficientes** se asigna cuando se piden parámetros (`a`, `b`, `c`) a partir de condiciones del enunciado (pasa por un punto, tiene una asíntota dada, tiene una recta tangente dada, tiene un extremo o un punto de inflexión en cierto punto, la pendiente de la tangente vale ...) **sin** que se mencione continuidad o derivabilidad y **sin** que los parámetros salgan de un límite escrito. Se combina con la etiqueta de la condición usada: p. ej. "calcula a y b para que y = x + 4 sea asíntota oblicua" → `calcular coeficientes | asíntotas`.
   - **Excepción:** si `a` es la **abscisa de un punto** (`en el punto (a, f(a))`, `calcula a ≠ 0 de forma que en el punto (a, f(a)) ...`) no es un coeficiente de la función: no pongas `calcular coeficientes`.
   - Si los valores de los parámetros **vienen dados** (`Para a = 0, ...`, `En el caso a = 5 y b = 4, ...`) eso no activa la etiqueta.

5. **Rectas tangente y normal**: se asigna siempre que se pida una recta tangente o normal, su pendiente, o puntos donde la tangente es paralela a una recta dada.

6. **Curvatura**: concavidad, convexidad, curvatura o puntos de inflexión. También se asigna cuando hay que **hallar el punto de inflexión** para otro fin (p. ej. "la recta tangente a la gráfica de f en el punto de inflexión" → `rectas tangente y normal | curvatura`). **No** se asigna si el punto de inflexión viene dado como dato para calcular coeficientes ("tiene un punto de inflexión en x = 1") → eso es `calcular coeficientes`.

7. **Monotonía vs. optimización.**
   - `monotonía`: se da la función `f(x)` explícitamente y se pide crecimiento/decrecimiento o extremos (relativos o absolutos) de esa función.
   - `optimización`: problema verbal o geométrico (ventana, rectángulo inscrito, lata cilíndrica, dos números, distancia mínima a una curva...) en el que **el alumno tiene que construir la función** a maximizar o minimizar. Palabras como "máxima", "mínima", "mayor", "menor", "dimensiones" en ese contexto → `optimización`, y **no** añadas `monotonía`.

8. **Integrales**: se pide un área, una integral definida o una primitiva, o se da como dato la derivada de una función (`f'(x) = ...`, `F'(x) = f(x)`) y hay que recuperar la función original. "Área máxima" o "mayor área" en un problema de optimización **no** es `integrales`.

9. **Representación función**: se pide representar, esbozar o dibujar la gráfica de la función (también si es a trozos). Si lo que se pide representar es un recinto para calcular su área, es `integrales`, no `representación función`.

10. Si no encaja ninguna etiqueta, usa `funciones (general)`.

## Campo `observaciones`

- Rellénalo solo en estos casos:
  - `L'Hopital` con parámetro: `"L'Hopital calcular a"` o `"L'Hopital calcular a/b"` (regla 2).
  - `coeficientes continuidad / derivabilidad`: `"2 ramas"` o `"3 ramas"` (regla 3).
- Si aplican ambos, únelos con `"; "`.
- En cualquier otro caso, devuelve `""` (cadena vacía).

## Nivel de confianza

- **alta:** aparecen palabras clave claras de todas las etiquetas asignadas y el contexto no deja dudas.
- **media:** el contexto encaja pero faltan palabras clave en alguna etiqueta, o hay dudas razonables (p. ej. si una `a` es un coeficiente o la abscisa de un punto, si el límite está igualado a un número porque el texto está dañado, o cuántas ramas tiene la función a trozos).
- **baja:** se ha usado la etiqueta por defecto, o el texto está demasiado dañado para interpretarlo con seguridad.

## Ejemplos

Enunciado: «Sabiendo que lim x→0 (sen(x) − ax + 2 − 2cos(x)) / (e^x − x cos(x) − 1) es finito, calcula a y el valor del límite»
{"tipo_ejercicio": "L'Hopital", "observaciones": "L'Hopital calcular a", "confianza": "alta"}

Enunciado: «Calcula a y b sabiendo que lim x→0 (x sen(x) + a(e^x − 1) + sen(x)) / (bx² + x − sen(x)) = 1»
{"tipo_ejercicio": "L'Hopital", "observaciones": "L'Hopital calcular a/b", "confianza": "alta"}

Enunciado: «Sabiendo que lim x→0 (sen(x) − ln(1 + x)) / (ax² − x + e^x − cos(2x)) = −1/7, calcula a (ln denota la función logaritmo neperiano)»
{"tipo_ejercicio": "L'Hopital", "observaciones": "L'Hopital calcular a/b", "confianza": "alta"}

Enunciado: «Considera la función f : ℝ → ℝ definida por f(x) = arctg(x + π). a) Calcula los intervalos de concavidad y de convexidad de f. Estudia y halla, si existen, los puntos de inflexión de f. b) Calcula lim x→−π arctg(x + π) / sen(x).»
{"tipo_ejercicio": "L'Hopital | curvatura", "observaciones": "", "confianza": "alta"}

Enunciado: «Considera la función continua f definida por: f(x) = { (x·cos(x) − a·sen(x)) / x³ si x < 0 ; b·cos(x) − 1 si x ≥ 0 }. Calcula a y b»
{"tipo_ejercicio": "coeficientes continuidad / derivabilidad", "observaciones": "2 ramas", "confianza": "alta"}

Enunciado: «Sea f : [0, 2] → ℝ la función definida por f(x) = { 1 − e^x si 0 ≤ x < 1 ; 2x − 1 − e si 1 ≤ x ≤ 2 }. a) Estudia la derivabilidad de f. b) Halla los extremos absolutos de f (abscisas donde se obtienen y valores que se alcanzan)»
{"tipo_ejercicio": "estudio continuidad / derivabilidad | monotonía", "observaciones": "", "confianza": "alta"}

Enunciado: «Sea f la función definida por f(x) = (ax³ + bx² + x − 1) / (x² − 1), para x ≠ ±1. Sabiendo que su gráfica tiene una asíntota oblicua que pasa por el punto (0, 1) y es paralela a la recta y = 2x, calcula la asíntota oblicua y los valores de a y b.»
{"tipo_ejercicio": "calcular coeficientes | asíntotas", "observaciones": "", "confianza": "alta"}

Enunciado: «Sea f : ℝ → ℝ la función definida por f(x) = a + b cos(x) + c sen(x). Halla a, b y c sabiendo que su gráfica tiene en el punto de abscisa x = π/2 a la recta y = 1 como recta tangente, y que la recta y = x − 1 corta a la gráfica de f en el punto de abscisa x = 0»
{"tipo_ejercicio": "calcular coeficientes | rectas tangente y normal", "observaciones": "", "confianza": "alta"}

Enunciado: «Sean las funciones f : (−1, 0) ∪ (0, 1) → ℝ y g : ℝ → ℝ, definidas por f(x) = ln(x²/e) y g(x) = x³ + 2. a) Calcula a ≠ 0 de forma que en el punto (a, f(a)) la recta normal a la gráfica de la función f sea paralela a la recta tangente a la gráfica de g en el punto (a, g(a)). b) Determina los intervalos de crecimiento y de decrecimiento de la función f.»
{"tipo_ejercicio": "rectas tangente y normal | monotonía", "observaciones": "", "confianza": "alta"}

Enunciado: «Considera la función f : ℝ → ℝ definida por f(x) = (x − 1)·e^x. a) Determina la ecuación de la recta tangente y la ecuación de la recta normal a la gráfica de f en el punto de inflexión. b) Estudia y calcula las asíntotas de la función.»
{"tipo_ejercicio": "asíntotas | rectas tangente y normal | curvatura", "observaciones": "", "confianza": "alta"}

Enunciado: «Considera la función f(x) = 1 / (x·|x|), para |x| ≠ 0. a) Calcula los intervalos de concavidad y de convexidad de f, así como los puntos de inflexión de su gráfica, si existen. b) Estudia y calcula las asíntotas de la función. Esboza su gráfica.»
{"tipo_ejercicio": "representación función | asíntotas | curvatura", "observaciones": "", "confianza": "alta"}

Enunciado: «Sea la función f : (0, +∞) → ℝ definida por f(x) = a + ln(x)/x². a) Calcula a para que y = 1 sea una asíntota horizontal de la gráfica de f. b) Para a = 0, calcula los intervalos de crecimiento y de decrecimiento f. Estudia y halla los extremos relativos de f (abscisas donde se obtienen y valores que se alcanzan).»
{"tipo_ejercicio": "calcular coeficientes | asíntotas | monotonía", "observaciones": "", "confianza": "alta"}

Enunciado: «En una fábrica de pinturas, las latas que se utilizan para envasar la pintura tienen forma cilíndrica y una capacidad de 20 litros. Halla las dimensiones del cilindro, con tapas, para que la chapa empleada en su construcción sea mínima.»
{"tipo_ejercicio": "optimización", "observaciones": "", "confianza": "alta"}

Enunciado: «Un náufrago se encuentra en una isla situada en el punto de coordenadas (2, 0) de un plano. Se sabe que un ferry navega en el mismo plano siempre en la trayectoria dada por la gráfica de la función f(x) = √(x + 1). ¿Hacia qué punto de la trayectoria debe nadar el náufrago para recorrer la menor distancia posible? Calcula dicha distancia.»
{"tipo_ejercicio": "optimización", "observaciones": "", "confianza": "alta"}

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código:

{"tipo_ejercicio": "<etiqueta_1 | etiqueta_2 | ...>", "observaciones": "<texto o cadena vacía>", "confianza": "alta|media|baja"}
