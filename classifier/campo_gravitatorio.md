# Clasificador de ejercicios · Física · Campo gravitatorio

Vas a recibir el enunciado de un ejercicio de selectividad (PEvAU/EBAU de Andalucía). Clasifícalo en **una sola** de las etiquetas definidas abajo.

- **Asignatura:** Física
- **Tema:** Campo gravitatorio

## Cómo clasificar

1. Revisa las etiquetas **en el orden en que aparecen** y asigna la primera cuyos criterios se cumplan.
2. Las palabras clave son indicios, no requisitos: si el contexto del enunciado encaja claramente con una etiqueta, asígnala aunque no aparezca ninguna palabra clave literal.
3. Si ninguna etiqueta encaja, usa la etiqueta por defecto: `{{ETIQUETA_POR_DEFECTO}}`.
4. El texto procede de PDFs y puede tener errores de extracción (subíndices, superíndices o símbolos perdidos, palabras partidas, espacios de más). No los tengas en cuenta al clasificar.

## Etiquetas

### plano_inclinado
- contiene las palabras plano horizontal, plano inclinado, rozamiento, bloque

### distribución_masas
- contiene la palabra partícula, se mencionan masas puntuales, se mencionan coordenadas como: A(5,0) y B(5,0), se pide calcular el campo gravitatorio, el potencial gravitatorio o el trabajo realizado para desplazar una masa.

### satélites
- si el ejercicio no coincide con alguno de los criterios anteriores, se puede clasificar como ejercicio de tipo "satélites". Además, este tipo de ejercicios suele contener las siguientes keywords: satélite, periodo, velocidad orbital, planeta, órbita.

### verdadero / falso
- En el enunciado aparecen las palabras veracidad o verdadero, falsedad o falso.

Responde SOLO con un JSON: {"id", "tipo_ejercicio": "...", "confianza": "alta|media|baja"}, sin texto adicional ni bloques de código.

Usa para la columna "id" los valores proporcionados en el archivo .csv de entrada.