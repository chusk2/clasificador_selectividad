# Propuesta de limpieza: `csv/`, `jupyter notebooks/` y `classifier/`

Fecha: 2026-10-13. Nada de esto está aplicado todavía.

## Diagnóstico

### Qué notebook lee y escribe cada CSV

| Archivo | Filas | Lo escribe | Lo lee | Estado |
|---|---|---|---|---|
| `csv/ejercicios.csv` | 4.774 | `recortar_pdf` | `clean_csv` | Paso 1 del pipeline (extracción de los PDFs) |
| `csv/issues.csv` | 3 | `recortar_pdf` | — | Errores de la extracción |
| `csv/ejercicios_clean.csv` | 4.774 | `clean_csv` | `clean_csv` | Paso 2 (limpieza). Nada lo convierte en la tabla principal: se hizo a mano |
| `csv/ejercicios_clasificados.csv` | 4.986 | `clean_glyphs`, `duplicated_statements`, `merge`, `optimización` | `app.py`, `api_call`, `inspector`, `clean_filenames` | **Tabla principal.** Tiene cambios sin commit |
| `csv/ejercicios_clasificados_matrices_ccss.csv` | 294 | `merge` | `merge` | Clasificación de matrices (CCSS + II) que se incorporó a la principal |
| `csv/ejercicios_matrices_ccss.csv` | 294 | — | — | Versión anterior del anterior: mismos `id`, pero con `tipo_ejercicio` distintos |
| `csv/ejercicios_matrices_ccss_claude.csv` | 117 | — | — | Prueba antigua: sin `id`, solo CCSS |
| `csv/ejercicios_optimizacion.csv` | 58 | — | `optimización` | Clasificación de optimización (Mates II, funciones) |
| `csv/enunciados_filtrados.csv` | 9 | botón de descarga de `app.py` | — | Una descarga desde la app guardada por error |
| `classifier/matrices.csv` | 294 | — | — | Entrada de matrices sin limpiar |
| `classifier/matrices_limpio.csv` | 294 | — | `api_call`, `merge` | Entrada de matrices que se envía a la API |
| `classifier/campo_gravitatorio_classified_exercises.csv` | 124 | — | — | Clasificación de campo gravitatorio. Ya está en la principal (121 de 123 filas con tipo) |
| `classifier/response.jsonl` | — | `api_call` | `api_call` | Respuesta cruda de la API |

Ninguno de los archivos marcados con «—» en ambas columnas lo usa ningún notebook ni la app.

### Notebooks

| Notebook | Qué hace | Problema |
|---|---|---|
| `emestrada_crawler` | Descarga los PDFs de emestrada | Es de junio y usa `remote_folders.txt` |
| `recortar_pdf` | Extrae los enunciados → `ejercicios.csv` | Tiene el mismo título que `enunciados_paso_a_paso` |
| `enunciados_paso_a_paso` | Versión didáctica de la extracción (genera `indice.csv`) | Duplica `recortar_pdf` |
| `clean_csv` | `ejercicios.csv` → `ejercicios_clean.csv` | — |
| `clean_glyphs` | Arregla los glifos de la fuente Symbol en la principal | — |
| `duplicated_statements` | Quita enunciados duplicados en la principal | — |
| `clean_filenames` | Quita los acentos de las rutas (nuevo, sin commit) | Se usa una sola vez |
| `api_call` | Clasifica con la API de Claude → `response.jsonl` | — |
| `merge` | Incorpora la clasificación de matrices | Nombre poco descriptivo |
| `optimización` | Incorpora la clasificación de optimización | Lleva acento en el nombre |
| `inspector` | Explorar la tabla principal | — |
| `database` | Sube los datos a una base de datos | Lee `csv/TODOS.csv`, que **ya no existe** |
| `test_classifier` | Clasificador antiguo | Lee y escribe `csv/TODOS*.csv`, que **ya no existen** |

Otros problemas:
- La carpeta `jupyter notebooks` tiene un espacio en el nombre.
- No hay forma de saber en qué orden se ejecutan los notebooks.

## Propuesta

### Criterios
1. **Nombres en ASCII**, en minúsculas y con `_`. Sin espacios ni acentos, igual que los datos.
2. **Prefijo numérico** en los notebooks del pipeline, para que el orden se vea al listarlos.
3. **Separar** la tabla principal, los pasos intermedios y las clasificaciones de cada tema.
4. **Borrar** lo que no usa nadie. Está en git, así que se puede recuperar.
5. **No cambiar** la ruta de `csv/ejercicios_clasificados.csv`: la usan la app y seis notebooks.

### Estructura final

```
csv/
├── ejercicios_clasificados.csv          # principal (no cambia)
├── pipeline/
│   ├── 01_ejercicios_extraidos.csv      # antes ejercicios.csv
│   ├── 01_issues_extraccion.csv         # antes issues.csv
│   └── 02_ejercicios_limpios.csv        # antes ejercicios_clean.csv
└── clasificaciones/
    ├── matrices.csv                     # antes ejercicios_clasificados_matrices_ccss.csv
    ├── optimizacion.csv                 # antes ejercicios_optimizacion.csv
    └── campo_gravitatorio.csv           # antes classifier/campo_gravitatorio_classified_exercises.csv

classifier/                              # prompts y entradas/salidas de la API
├── plantilla_clasificador.md
├── matrices.md
├── campo_gravitatorio.md
├── matrices_entrada.csv                 # antes matrices_limpio.csv
└── matrices_respuesta.jsonl             # antes response.jsonl

notebooks/                               # antes "jupyter notebooks"
├── 01_descargar_pdfs.ipynb              # emestrada_crawler
├── 02_extraer_enunciados.ipynb          # recortar_pdf
├── 03_limpiar_csv.ipynb                 # clean_csv
├── 04_limpiar_glifos.ipynb              # clean_glyphs
├── 05_quitar_duplicados.ipynb           # duplicated_statements
├── 10_clasificar_api.ipynb              # api_call
├── 11_incorporar_matrices.ipynb         # merge
├── 12_incorporar_optimizacion.ipynb     # optimización
├── explorar.ipynb                       # inspector
└── archivo/                             # ya no se usan, se guardan como referencia
    ├── enunciados_paso_a_paso.ipynb
    ├── limpiar_nombres_archivo.ipynb    # clean_filenames, una vez aplicado
    ├── database.ipynb
    └── test_classifier.ipynb
```

Los números del 10 en adelante son la fase de clasificación. Así queda hueco para añadir pasos de limpieza (06, 07…) sin tener que renumerar.

### Archivos a borrar

| Archivo | Motivo |
|---|---|
| `csv/enunciados_filtrados.csv` | Descarga de la app, no forma parte del proyecto |
| `csv/ejercicios_matrices_ccss_claude.csv` | Prueba antigua sin `id` |
| `csv/ejercicios_matrices_ccss.csv` | Versión anterior de la clasificación de matrices *(confirmar, ver dudas)* |
| `classifier/matrices.csv` | Entrada sin limpiar, sustituida por `matrices_limpio.csv` |
| `classifier/matrices_claude.md` | Ningún notebook lo usa *(confirmar)* |

Además, conviene añadir `enunciados_filtrados.csv` al `.gitignore` para que no vuelva a colarse.

### Cambios de rutas dentro de los notebooks

| Notebook (nombre nuevo) | Cambio |
|---|---|
| `02_extraer_enunciados` | `csv/ejercicios.csv` → `csv/pipeline/01_ejercicios_extraidos.csv`; `csv/issues.csv` → `csv/pipeline/01_issues_extraccion.csv` |
| `03_limpiar_csv` | Entrada `01_ejercicios_extraidos.csv`, salida `csv/pipeline/02_ejercicios_limpios.csv` |
| `10_clasificar_api` | `classifier/matrices_limpio.csv` → `matrices_entrada.csv`; `response.jsonl` → `matrices_respuesta.jsonl` |
| `11_incorporar_matrices` | `csv/ejercicios_clasificados_matrices_ccss.csv` → `csv/clasificaciones/matrices.csv`; `classifier/matrices_limpio.csv` → `matrices_entrada.csv` |
| `12_incorporar_optimizacion` | `csv/ejercicios_optimizacion.csv` → `csv/clasificaciones/optimizacion.csv` |
| `explorar`, `limpiar_nombres_archivo` | Usan `../csv/...`. Siguen funcionando porque la carpeta sigue estando un nivel por debajo de la raíz |

`app/app.py` no necesita cambios.

## Cómo aplicarlo

1. **Antes de nada, hacer commit** de los cambios pendientes en `csv/ejercicios_clasificados.csv` y de `limpiar_nombres.py`.
2. Renombrar con `git mv` (no con `mv`), para que git conserve el historial de cada archivo.
3. Borrar con `git rm`.
4. Actualizar las rutas en los notebooks (tabla anterior). Después, buscar las rutas antiguas para comprobar que no queda ninguna.
5. Comprobar que la app arranca y que `11_incorporar_matrices` y `12_incorporar_optimizacion` leen bien sus archivos.
6. Un solo commit: «Reorganizar CSV y notebooks».
7. En el Mac: `git pull`. Como todo lo que se mueve está en git, allí no hay que hacer nada más.

## Dudas por resolver

1. **`ejercicios_matrices_ccss.csv` y `ejercicios_clasificados_matrices_ccss.csv`** tienen los mismos 294 `id` pero `tipo_ejercicio` distintos. `merge` usa el segundo, así que supongo que el primero es una versión anterior. ¿Se puede borrar?
2. **`database` y `test_classifier`** dependen de `TODOS.csv`, que ya no existe. ¿Archivarlos, como propongo, o borrarlos?
3. **`matrices_claude.md`**: ¿es un prompt que todavía quieres conservar?
4. **Carpeta de notebooks**: si cambias `jupyter notebooks` → `notebooks`, revisa si tienes accesos directos o configuración de VS Code/Jupyter que apunten a la ruta antigua.
