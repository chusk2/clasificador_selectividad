# Clasificador de ejercicios · {{ASIGNATURA}} · {{TEMA}}

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo en **una sola** de las etiquetas definidas abajo.

- **Asignatura:** {{ASIGNATURA}}
- **Tema:** {{TEMA}}

## Cómo clasificar

1. Revisa las etiquetas **en el orden en que aparecen** y asigna la primera cuyos criterios se cumplan.
2. Las palabras clave son indicios, no requisitos: si el contexto del enunciado encaja claramente con una etiqueta, asígnala aunque no aparezca ninguna palabra clave literal.
3. Si ninguna etiqueta encaja, usa la etiqueta por defecto: `{{ETIQUETA_POR_DEFECTO}}`.
4. El texto procede de PDFs y puede tener errores de extracción (subíndices, superíndices o símbolos perdidos, palabras partidas, espacios de más). No los tengas en cuenta al clasificar.

## Etiquetas

### `{{etiqueta_1}}`

- **Palabras clave:** {{palabra_1}}, {{palabra_2}}, {{palabra_3}}
- **Qué se pide / contexto:** {{descripción de la situación física, química o matemática típica}}
- **No confundir con:** `{{otra_etiqueta}}` — {{qué las diferencia}}

### `{{etiqueta_2}}`

- **Palabras clave:** {{palabra_1}}, {{palabra_2}}, {{palabra_3}}
- **Qué se pide / contexto:** {{descripción}}
- **No confundir con:** `{{otra_etiqueta}}` — {{qué las diferencia}}

<!-- Copia el bloque anterior para añadir más etiquetas. La etiqueta por defecto va siempre la última. -->

### `{{ETIQUETA_POR_DEFECTO}}` (por defecto)

- **Palabras clave:** {{palabra_1}}, {{palabra_2}}, {{palabra_3}}
- **Qué se pide / contexto:** {{descripción}}
- Se asigna también cuando el enunciado no cumple los criterios de ninguna etiqueta anterior.

## Nivel de confianza

- **alta:** aparecen palabras clave de la etiqueta y el contexto no deja dudas.
- **media:** el contexto encaja, pero faltan palabras clave o el ejercicio mezcla aspectos de varias etiquetas.
- **baja:** se ha asignado la etiqueta por defecto sin indicios claros, o el texto está demasiado dañado para interpretarlo con seguridad.

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código:

{"asignatura": "{{ASIGNATURA}}", "tema": "{{TEMA}}", "tipo_ejercicio": "<{{etiqueta_1}}|{{etiqueta_2}}|{{ETIQUETA_POR_DEFECTO}}>", "confianza": "alta|media|baja"}
