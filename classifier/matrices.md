# Clasificador de ejercicios · Mates CCSS y Mates II · Matrices y determinantes

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo en **una sola** de las etiquetas definidas abajo.

- **Asignatura:** Mates CCSS y Mates II
- **Tema:** Matrices y determinantes

## Cómo clasificar

1. Revisa las etiquetas **en el orden en que aparecen** y asigna la primera cuyos criterios se cumplan.
2. Las palabras clave son indicios, no requisitos: si el contexto del enunciado encaja claramente con una etiqueta, asígnala aunque no aparezca ninguna palabra clave literal.
3. Si ninguna etiqueta encaja, usa la etiqueta por defecto: `sin clasificar`.
4. El texto procede de PDFs y puede tener errores de extracción (subíndices, superíndices o símbolos perdidos, palabras partidas, espacios de más). No los tengas en cuenta al clasificar.

## Etiquetas

### `ecuación matricial`

- **Palabras clave:** ecuación matricial, matriz X
- **Qué se pide / contexto:** resolver la ecuación matricial
- **No confundir con:** 

### `valores tenga inversa`

- **Palabras clave:** no tenga inversa, tenga inversa, existe la inversa
- **Qué se pide / contexto:** valores para los cuales la matriz tiene inversa o no tiene inversa
- **No confundir con:**

### `determinantes`

- **Palabras clave:** "Se sabe que", determinantes
- **Qué se pide / contexto:** 
- **No confundir con:**

### `rango`

- **Palabras clave:** rango
- **Qué se pide / contexto:** calcular el rango de la matriz
- **No confundir con:**

### `verificar`

- **Palabras clave:** verifica, todas las matrices X
- **Qué se pide / contexto:** verificar una igualdad
- **No confundir con:** 

### `potencias`

- **Palabras clave:** existe el texto A, seguido de un número (debería ser el exponente, normalmente un año)
- **Qué se pide / contexto:** calcular la potencia de una matriz
- **No confundir con:**

### `inversa`

- **Palabras clave:** inversa
- **Qué se pide / contexto:** calcular la matriz inversa
- **No confundir con:**
- 
### `sin clasificar` (por defecto)

- **Palabras clave:** 
- **Qué se pide / contexto:**
- Se asigna también cuando el enunciado no cumple los criterios de ninguna etiqueta anterior.

## Nivel de confianza

- **alta:** aparecen palabras clave de la etiqueta y el contexto no deja dudas.
- **media:** el contexto encaja, pero faltan palabras clave o el ejercicio mezcla aspectos de varias etiquetas.
- **baja:** se ha asignado la etiqueta por defecto sin indicios claros, o el texto está demasiado dañado para interpretarlo con seguridad.

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código:

Toma el valor de "id" a partir del archivo texto suministrado
{"id", "tipo_ejercicio": "<{{etiqueta_1}}|{{etiqueta_2}}|{{ETIQUETA_POR_DEFECTO}}>", "confianza": "alta|media|baja"}
