# equilibrio químico

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo según lo que **pide** el enunciado.

- **Asignatura:** Mates II
- **Tema:** Geometría

## Cómo clasificar

1. **No resuelvas el ejercicio ni hagas cálculos.** Basta con leer qué se pide y qué datos se dan. La clasificación es directa: decide rápido.
2. Asigna la etiqueta que mejor describe el ejercicio. Si el enunciado tiene varios apartados que encajan claramente en etiquetas distintas, añádelas también, como **máximo 3**, de la más a la menos relevante.
3. Las palabras clave son indicios, no requisitos: si el contexto del enunciado encaja claramente con una etiqueta, asígnala aunque no aparezca ninguna palabra clave literal.
4. Si ninguna etiqueta encaja, usa `sin clasificar`. Es una respuesta válida: no le des más vueltas.
5. El texto procede de PDFs y puede tener errores de extracción (subíndices, superíndices o símbolos perdidos, palabras partidas, espacios de más). No los tengas en cuenta al clasificar. Si el texto está tan dañado que no se entiende, usa `sin clasificar`.

## Etiquetas

- Etiqueta:

## Nivel de confianza

- **alta:** aparecen palabras clave de la etiqueta y el contexto no deja dudas.
- **media:** el contexto encaja, pero faltan palabras clave o el ejercicio mezcla aspectos de varias etiquetas.
- **baja:** se ha asignado `sin clasificar`, o el texto está demasiado dañado para interpretarlo con seguridad.

## Formato de respuesta

Responde SOLO con un JSON en una línea, sin texto adicional ni bloques de código. Usa siempre este formato, también para `sin clasificar`:

{"tipo_ejercicio": "<etiqueta> | <etiqueta>", "observaciones": "<motivo breve o vacío>", "confianza": "alta|media|baja"}

- `tipo_ejercicio`: los nombres exactos de las etiquetas, separados por " | ".
- `observaciones`: vacío ("") si la clasificación es clara. Con `sin clasificar`, el motivo en pocas palabras.

Ejemplos:

{"tipo_ejercicio": "Cálculo de Kc y Kp | Grado de disociación (cálculo)", "observaciones": "", "confianza": "alta"}

{"tipo_ejercicio": "sin clasificar", "observaciones": "pregunta teórica sobre catalizadores", "confianza": "baja"}
