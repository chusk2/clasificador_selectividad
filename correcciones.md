# Correcciones y sugerencias — `recortes.ipynb` y `todos_enunciados.csv`

Revisión de `jupyter notebooks/recortes.ipynb`, `csv_enunciados/todos_enunciados.csv` (413 filas) y `source_pdf_files` (585 PDFs). Hallazgos de más a menos grave.

## Errores que afectan a los datos

1. **El texto del enunciado pierde su última línea.** En `procesar_pdf` se hace `"\n".join(lineas[:-2])`, pero la línea de metadatos es solo la última, así que debería ser `[:-1]`. Se ve en el CSV: el primer registro acaba en `"...electrones situados, en cada caso, en"`. 277 de las 413 filas no terminan en puntuación. Los PNG no tienen este problema, pero el texto bruto sí.

2. **Solo se ha procesado una parte de los PDFs.** La celda 29 usa `files_to_process_limit=2`, "para pruebas". Por eso el CSV tiene 413 filas de 585 PDFs. Además, el CSV solo contiene años 2000, 2001, 2002, 2010, 2011, 2016, 2017, 2024 y 2025, que son los 2 primeros PDFs por carpeta. Para el run completo hay que quitar el límite.

3. **27 filas con `asignatura_desconocida` (6,5 %).** Es un fallo de extracción:
   - El texto sale como `'S OCIALES II. 2001 RESERVA 1...'`, con un espacio dentro de la palabra. Lo mismo pasa con `Ejercici O`, `Eje Rcicio`, `Opc Ión`, etc.
   - Los casos afectados son Mates CCSS 2001/2002 Probabilidad y Mates II 2000/2001 Geometría y Matrices, más 2025 Probabilidad y Distribución normal (ver el punto 6).
   - La solución es normalizar el texto antes de parsear, como ya dice CLAUDE.md: mayúsculas, NFKD, y quitar espacios (`re.sub(r"\s+", "", s)` para comparar contra las asignaturas).

4. **`process_exercise_info` es frágil.**
   - Si no hay convocatoria, `convocatoria` queda sin definir y lanza `UnboundLocalError` o arrastra el valor anterior.
   - `year_pattern = r"2\d{3}"` coge el primer "2xxx" que encuentre.
   - Al hacer `.title()` salen `"Ejercicio 3 Parte Ii Opción A"` e `"Ii"`.
   - Hay 40 variantes de `ejercicio`: con o sin punto final, `Opción B.` y `Opción B`, `Ejercicio 3B`, `Ejercicio C5`, `Ejercicio D6`.
   - Falta una regex con grupos con nombre, como proponía CLAUDE.md, que dé columnas separadas: `ejercicio` (número), `parte` (I/II), `opcion` (A/B). Ahora mismo se mezclan en una cadena.

5. **4 filas con `enunciado` vacío.** Por ejemplo `2001 - Conf. Electrónica` y `2016 - Ondas` Reserva 3 ej. 4A. Probablemente `page.crop` no capta el texto porque el recuadro es una imagen o está escaneado. No generan aviso, y `aviso` está vacío en las 413 filas.

6. **`asignatura` y `asignatura_carpeta` no coinciden en origen.**
   - `2025 - Distribución normal y binomial.pdf` aparece en Mates II con una asignatura desconocida.
   - Aun así, "Mates CCSS" es una etiqueta propia, mientras que el PDF dice "SOCIALES II".
   - Conviene tomar la asignatura de la carpeta como fuente fiable y la de la línea de metadatos como confirmación, avisando si discrepan.

## Aviso que no funciona

El campo `aviso` solo se rellena con `"sin info ejercicio"` o con varios recuadros por página. Faltan avisos para estos casos:

- asignatura desconocida
- enunciado vacío
- año del metadato distinto del año del archivo
- convocatoria sin reconocer

Con eso se habrían detectado los problemas 3 y 5 al instante.

## Estructura y diseño

- **No cumple lo que fija CLAUDE.md.**
  - Las carpetas son `solo_enunciados_ejercicios/<asig>/<tema>/...` y no `salida/png/...`.
  - El nombre del PNG es `Química_2000_junio_ejercicio_2_opcion_b.png`, con tilde y sin el formato `quimica_2000_junio_ej2b`.
  - No hay columna `id`, `pagina_origen` ni `opcion`.
  - Lo más importante es que el PDF apilado sigue siendo vectorial con `pypdf`, y CLAUDE.md lo descarta: pesa más y conserva las soluciones ocultas. Habría que componerlo desde los PNG con `img2pdf`.
- **Nombres de PNG con riesgo de colisión.** Si el nombre se genera solo desde `info_ejercicio`, un ejercicio duplicado en varios temas se pisa o recibe `_2`. Hoy no hay duplicados, pero con los 585 PDFs aparecerán.
- **Un mismo ejercicio puede estar en varios temas.** El tema viene de la carpeta, no de una clasificación. Antes de clasificar conviene deduplicar por `(asignatura, año, convocatoria, ejercicio)`.
- **Caracteres de MathType.** 244 filas contienen caracteres de uso privado (`` = +, `` = −). Un mapa de sustitución `→+`, `→-`, `→=`, `→→`, etc. mejoraría mucho el texto sin esfuerzo. Para fórmulas complejas seguirá siendo mejor la imagen.
- **Notebook.**
  - Hay mucho código comentado: el `PATRON` antiguo y bloques de pruebas.
  - Se usa `os.chdir` varias veces y una ruta de Linux fija, `/home/daniel/...`, dentro de un `try`.
  - `enunciados_df = pd.concat` dentro de un bucle es ineficiente, mejor `pd.concat(lista)`.
  - Las funciones deberían salir a un módulo `.py`.
  - La celda 29 itera con `export_pdf=True`, lo que repite trabajo y es lento.
- **Reanudación.** Falta lo que pedía CLAUDE.md: ahora todo se reprocesa desde cero y el CSV se sobrescribe.
- **Otros ficheros útiles.** En `source_pdf_files` hay `.csv`, `.xlsx` y `.txt` hechos a mano (`clasificacion_funciones_selectividad.csv`, `tipos_integrales.xlsx`, etc.). Parecen etiquetas manuales y servirían como conjunto de validación para la fase de clasificación. Convendría sacarlos de `source_pdf_files`: el `rglob("*.pdf")` no los toca, pero ensucian la estructura.

## Qué haría primero

1. Corregir `[:-2]` por `[:-1]`.
2. Normalizar el texto antes de parsear, con una regex con grupos con nombre.
3. Añadir los avisos que faltan.
4. Quitar el límite de 2 PDFs y relanzar con todo.
5. Después, ajustar la estructura de salida y el `img2pdf` según CLAUDE.md.
