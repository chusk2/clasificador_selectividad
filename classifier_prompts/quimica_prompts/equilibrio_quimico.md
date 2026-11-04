# equilibrio químico

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo según lo que **pide** el enunciado.

- **Asignatura:** Química
- **Tema:** Equilibrio Químico

## Cómo clasificar

1. **No resuelvas el ejercicio ni hagas cálculos.** Basta con leer qué se pide y qué datos se dan. La clasificación es directa: decide rápido.
2. Asigna la etiqueta que mejor describe el ejercicio. Si el enunciado tiene varios apartados que encajan claramente en etiquetas distintas, añádelas también, como **máximo 3**, de la más a la menos relevante.
3. Las palabras clave son indicios, no requisitos: si el contexto del enunciado encaja claramente con una etiqueta, asígnala aunque no aparezca ninguna palabra clave literal.
4. Si ninguna etiqueta encaja, usa `sin clasificar`. Es una respuesta válida: no le des más vueltas.
5. El texto procede de PDFs y puede tener errores de extracción (subíndices, superíndices o símbolos perdidos, palabras partidas, espacios de más). No los tengas en cuenta al clasificar. Si el texto está tan dañado que no se entiende, usa `sin clasificar`.

## Etiquetas

- Cociente de reacción: se pregunta cómo evoluciona el sistema, o se pregunta si el sistema está en equilibrio.
  
- Principio de LeChatelier: se pregunta cómo afectan los cambios al equilibrio. De forma típica se pregunta cómo le afecta un cambio de temperatura y se da como dato la entalpía de la reacción. Suelen empezar con "cómo afectan los siguientes cambios al equilibrio". A veces se pregunta cómo le influye un cambio al rendimiento de la reacción. En algunos ejercicios se pide comentar si la cantidad de una especie química aumenta, disminuye o no varía cuando se produce un cambio en las condiciones de presión, volumen, temperatura o adición de un catalizador.

- Equilibrio heterogéneo: en la reacción de equilibrio aparece un sólido ( "(s)" ). Se pregunta la cantidad de sólido que ha quedado sin reaccionar en el reactor. Se pregunta por la masa sin reacciónar de un reactivo sólido.

- Cálculo de Kc y Kp: se pide calcular estas dos constantes.

- Ley de Dalton: se pide calcular las presiones parciales en el equilibrio o se da como dato del enunciado.

- Grado disociación (dato): el enunciado da como dato el porcentaje de un reactivo que ha reaccionado.

- Equilibrio en función de alfa: en el equilibrio solo hay un único reactivo gaseoso. Todas las especies del equilibrio son gases ("(g)") y no se menciona la cantidad inicial de reactivo. Solo se da como dato el grado de disociación (porcentaje de reactivo que ha reaccionado / descompuesto).

- Grado de disociación (cálculo): se pide calcular el valor del grado de disociación.

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
