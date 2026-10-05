# Explicación del script `enunciados_batch.py`

Este documento recorre el script bloque a bloque. Supone que conoces Python a nivel intermedio (funciones, diccionarios, comprensiones, f-strings, `with`) y explica con más detalle todo lo relacionado con **pdfplumber** y **pypdf**, que es la parte nueva.

---

## 1. Qué hace el script, en una frase

Abre cada PDF, busca en cada página un rectángulo grande (el recuadro del enunciado), lee el texto que hay dentro para sacar año/convocatoria/ejercicio, y construye un PDF nuevo que solo contiene esos recuadros. Opcionalmente, guarda cada recuadro como imagen PNG.

Usa dos librerías con papeles distintos:

| Librería | Para qué se usa | Por qué esta |
|---|---|---|
| **pdfplumber** | *Leer* el PDF: encontrar los rectángulos, recortar, extraer texto, generar PNG | Expone los objetos gráficos de la página (líneas, rectángulos, curvas, caracteres) con sus coordenadas |
| **pypdf** | *Escribir* el PDF de salida | Permite copiar trozos de una página a otra sin rasterizar, conservando la calidad vectorial |

---

## 2. Conceptos previos imprescindibles

### 2.1. Un PDF no es un documento de texto, es un dibujo

Una página PDF es una lista de instrucciones de dibujo: "pon la letra *C* en esta posición con esta fuente", "traza un rectángulo de aquí a aquí", "dibuja esta curva". No hay párrafos ni "recuadros" como concepto; hay **objetos con coordenadas**.

Por eso el recuadro se puede detectar: el autor de los PDF lo dibujó como un objeto *rectángulo*, y pdfplumber nos da la lista de todos los rectángulos de la página.

### 2.2. Unidades: puntos (pt)

Todas las medidas se expresan en **puntos tipográficos**: 1 pt = 1/72 de pulgada ≈ 0,35 mm. Una página A4 mide **595 × 842 pt**. Por eso en el script aparecen números como `300` (ancho mínimo del recuadro) o `40` (margen).

### 2.3. Dos sistemas de coordenadas (¡importante!)

Este es el detalle que más confunde:

```
      pdfplumber                         PDF "real" (pypdf)
  (0,0) ───────────► x              y ▲
    │                                 │
    │   top = distancia               │   y = distancia
    │   desde ARRIBA                  │   desde ABAJO
    ▼                                 │
    y                              (0,0) ───────────► x
```

- **pdfplumber** mide la posición vertical desde el **borde superior** (como una pantalla). Por eso sus rectángulos tienen `top` y `bottom`.
- **El formato PDF** (y por tanto pypdf) mide desde el **borde inferior** (como en matemáticas).

Para pasar de uno a otro: `y_pdf = alto_pagina − y_pdfplumber`. Lo verás aplicado en la sección 6.4.

### 2.4. Qué es un rectángulo para pdfplumber

`page.rects` es una lista de diccionarios. Cada uno describe un rectángulo dibujado en la página. Las claves que usamos:

| Clave | Significado |
|---|---|
| `x0` | Coordenada x del borde izquierdo |
| `x1` | Coordenada x del borde derecho |
| `top` | Distancia desde arriba de la página al borde superior del rectángulo |
| `bottom` | Distancia desde arriba de la página al borde inferior del rectángulo |
| `width`, `height` | Ancho y alto |

Hay más claves (color de relleno, grosor de línea…), pero no las necesitamos.

---

## 3. Importaciones (líneas 20–29)

```python
import argparse
import csv
import os
import re
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter, Transformation
```

- `argparse`: leer los argumentos de la línea de comandos (`--png`, `--dpi`…).
- `csv`: escribir `indice.csv`.
- `os`: solo para `os.cpu_count()`, el número de núcleos.
- `re`: expresiones regulares, para extraer año/convocatoria/ejercicio.
- `unicodedata`: quitar tildes al generar nombres de archivo.
- `ProcessPoolExecutor`, `as_completed`: procesar varios PDF a la vez (sección 8).
- `Path`: manejo de rutas como objetos (`carpeta / "archivo.png"`).
- `PdfReader` / `PdfWriter`: abrir un PDF existente / crear uno nuevo.
- `Transformation`: describe un movimiento (traslación, escala) para colocar un trozo de página en otro sitio.

---

## 4. Constantes de configuración (líneas 31–35)

```python
ANCHO_MIN, ALTO_MIN = 300, 20
MARGEN = 2
A4 = (595.28, 841.89)
MARGEN_A4 = 40
SEPARACION = 15
```

- `ANCHO_MIN`, `ALTO_MIN`: un rectángulo solo cuenta como "recuadro de enunciado" si mide más de 300 pt de ancho y 20 de alto. Los recuadros de emestrada miden unos 500 pt de ancho; esto descarta rectángulos pequeños, como el de "u = ln x; du = …" que aparece en las resoluciones de integración por partes.
- `MARGEN`: al recortar se añaden 2 pt alrededor para que el borde negro del recuadro no quede cortado a la mitad.
- `A4`: tamaño de la página de salida.
- `MARGEN_A4`, `SEPARACION`: margen de la hoja de salida y hueco entre recuadros apilados.

Si algún año los recuadros son más estrechos, bastaría con bajar `ANCHO_MIN`.

---

## 5. Expresión regular y nombres de archivo

### 5.1. `PATRON` (líneas 37–43)

```python
PATRON = re.compile(
    r"(?P<anio>(19|20)\d{2})\.\s*"
    r"(?P<conv>[A-ZÁÉÍÓÚ]+(?:\s+\d)?)\.?\s*"
    r"EJERCICIO\s*(?P<ej>\d+)"
    r"(?:\.?\s*OPCI[OÓ]N\s*(?P<opc>[AB]))?",
    re.IGNORECASE,
)
```

Busca dentro del texto del recuadro la línea de referencia, por ejemplo `MATEMÁTICAS II. 2023. RESERVA 1. EJERCICIO 3` o `QUÍMICA. 2000. JUNIO EJERCICIO 4. OPCIÓN A`.

Las cadenas `r"..."` contiguas se concatenan automáticamente; se parten así solo para que sea legible. Pieza a pieza:

| Fragmento | Captura | Ejemplo |
|---|---|---|
| `(?P<anio>(19\|20)\d{2})\.` | Un año de 4 cifras seguido de punto | `2023` |
| `(?P<conv>[A-ZÁÉÍÓÚ]+(?:\s+\d)?)` | Una palabra en mayúsculas, opcionalmente seguida de un número | `JUNIO`, `RESERVA 1` |
| `\.?\s*` | Punto opcional (a veces falta) y espacios | |
| `EJERCICIO\s*(?P<ej>\d+)` | La palabra EJERCICIO y su número | `3` |
| `(?:\.?\s*OPCI[OÓ]N\s*(?P<opc>[AB]))?` | Todo el bloque "OPCIÓN A/B" es opcional (los exámenes nuevos no lo tienen) | `B` |

`(?P<nombre>...)` es un **grupo con nombre**: después se accede con `m["anio"]`, `m["conv"]`, etc. `(?:...)` es un grupo que agrupa pero no captura. `re.IGNORECASE` hace que no importen mayúsculas/minúsculas.

Por qué no se busca "MATEMÁTICAS" o "QUÍMICA": así el mismo patrón sirve para cualquier asignatura.

### 5.2. `slug()` (líneas 46–48)

```python
def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", texto).strip("_").lower()
```

Convierte un texto en algo apto para nombre de archivo: `"RESERVA 1"` → `"reserva_1"`.

1. `normalize("NFKD", ...)` separa cada letra acentuada en letra + tilde (`Ó` → `O` + `´`).
2. `.encode("ascii", "ignore")` descarta todo lo que no sea ASCII, es decir, las tildes. `.decode()` lo devuelve a `str`.
3. `re.sub(r"\W+", "_", ...)` sustituye cualquier secuencia de caracteres no alfanuméricos (espacios, puntos, guiones) por `_`.
4. `.strip("_")` quita guiones bajos sobrantes en los extremos y `.lower()` pasa a minúsculas.

---

## 6. Detección y recorte con pdfplumber

### 6.1. `detectar_recuadros()` (líneas 51–58)

```python
def detectar_recuadros(page):
    vistos = {}
    for r in page.rects:
        if r["width"] > ANCHO_MIN and r["height"] > ALTO_MIN:
            clave = tuple(round(r[k]) for k in ("x0", "top", "x1", "bottom"))
            vistos[clave] = r
    return sorted(vistos.values(), key=lambda r: r["top"])
```

Recibe una página de pdfplumber y devuelve la lista de recuadros grandes.

- `page.rects`: **todos** los rectángulos dibujados en la página (ver 2.4).
- El `if` filtra por tamaño.
- **El problema de los duplicados**: en estos PDF cada recuadro está dibujado dos veces en el mismo sitio (una vez el relleno blanco, otra el borde negro). Para no contarlo dos veces, se usa un diccionario cuya clave son las coordenadas redondeadas. Si llega un segundo rectángulo con las mismas coordenadas, sobrescribe al primero y en el diccionario sigue habiendo una sola entrada.
- `round()` evita que diferencias de décimas (`57.02` frente a `57.04`) hagan que dos rectángulos iguales parezcan distintos.
- Se devuelven ordenados por `top`, de arriba abajo, por si alguna página tuviera más de uno.

### 6.2. Apertura del PDF y recorrido de páginas (líneas 61–70)

```python
def procesar_pdf(ruta_pdf, carpeta_salida, png, dpi, uno_por_pagina):
    filas = []
    recortes = []
    carpeta_png = carpeta_salida / "png" / ruta_pdf.stem

    with pdfplumber.open(ruta_pdf) as pdf:
        for n, page in enumerate(pdf.pages):
            cajas = detectar_recuadros(page)
            for k, r in enumerate(cajas, start=1):
```

- `procesar_pdf` se ocupa de un único PDF de principio a fin. Devuelve las filas para el índice CSV.
- `filas` acumula una fila (diccionario) por enunciado; `recortes` guarda las coordenadas de cada recuadro para usarlas después con pypdf.
- `ruta_pdf.stem` es el nombre del archivo sin extensión (`2023_-_Integrales`). Los PNG de cada PDF van a su propia subcarpeta para que no se pisen entre sí.
- `pdfplumber.open()` abre el PDF. Se usa con `with` para que se cierre automáticamente al terminar.
- `pdf.pages` es la lista de páginas. `n` es el índice empezando en 0 (la portada es `n = 0`).
- La portada no tiene recuadro, así que `cajas` estará vacía y el `for` interior simplemente no se ejecuta.

### 6.3. Recorte, texto y metadatos (líneas 71–87)

```python
x0 = max(r["x0"] - MARGEN, 0)
x1 = min(r["x1"] + MARGEN, page.width)
top = max(r["top"] - MARGEN, 0)
bottom = min(r["bottom"] + MARGEN, page.height)

recorte = page.crop((x0, top, x1, bottom))
texto = (recorte.extract_text() or "").replace("\n", " ")
m = PATRON.search(texto)
```

- Se amplía el rectángulo `MARGEN` puntos por cada lado. `max(..., 0)` y `min(..., page.width)` evitan salirse de la página, lo que daría error.
- **`page.crop(bbox)`** es una función clave de pdfplumber. Devuelve un objeto que se comporta como una página, pero que solo "ve" lo que hay dentro de esa caja. El orden de la tupla es siempre `(x0, top, x1, bottom)`, en coordenadas de pdfplumber.
- **`recorte.extract_text()`** devuelve el texto que hay dentro del recorte. Las fórmulas salen destrozadas (como vimos), pero la última línea, `MATEMÁTICAS II. 2023. JUNIO. EJERCICIO 4`, sale limpia, y es lo único que nos interesa aquí.
- `or ""` cubre el caso de que `extract_text()` devuelva `None`. Se cambian los saltos de línea por espacios para que el patrón no falle si la referencia quedara partida.
- `PATRON.search()` devuelve un objeto *match* `m`, o `None` si no encuentra nada.

```python
if m:
    nombre = f"{m['anio']}_{slug(m['conv'])}_ej{m['ej']}"
    if m["opc"]:
        nombre += f"_{m['opc'].lower()}"
else:
    nombre = f"{slug(ruta_pdf.stem)}_p{n + 1:02d}"
if len(cajas) > 1:
    nombre += f"_r{k}"
```

Construye el nombre base: `2023_reserva_1_ej3`, o `2000_junio_ej6_b` si hay opción. Si no se pudo leer la referencia, usa el nombre del PDF y el número de página (`:02d` rellena con ceros: `p05`). Si la página tuviera varios recuadros, añade `_r1`, `_r2`…

### 6.4. Guardar el PNG (líneas 89–98)

```python
if png:
    carpeta_png.mkdir(parents=True, exist_ok=True)
    destino = carpeta_png / f"{nombre}.png"
    i = 2
    while destino.exists():
        destino = carpeta_png / f"{nombre}_{i}.png"
        i += 1
    recorte.to_image(resolution=dpi).save(destino)
    imagen = str(destino.relative_to(carpeta_salida))
```

- Solo se ejecuta si se pasó `--png`.
- `mkdir(parents=True, exist_ok=True)` crea la carpeta y sus padres si no existen, sin error si ya existen.
- El `while` evita sobrescribir: si `2023_junio_ej3.png` ya existe, prueba `_2`, `_3`…
- **`recorte.to_image(resolution=dpi)`** rasteriza el recorte (lo convierte en imagen de píxeles) a la resolución indicada. A 200 dpi un recuadro de 500 pt de ancho da una imagen de unos 1400 px. `.save()` la escribe en disco.
- `relative_to()` guarda en el índice la ruta relativa (`png/2023_-_Integrales/2023_junio_ej3.png`), más portable que la absoluta.

### 6.5. Conversión de coordenadas para pypdf (líneas 100–103)

```python
off_x, off_y = float(page.bbox[0]), float(page.bbox[1])
recortes.append((n, off_x + x0, off_y + page.height - bottom,
                 off_x + x1, off_y + page.height - top))
```

Aquí se aplica lo explicado en 2.3. pypdf necesita la caja con el origen abajo, en el formato `(x0, y0, x1, y1)`:

- La **y inferior** del recuadro en PDF es `alto − bottom` (el borde que en pdfplumber está más lejos de arriba es el más cercano a abajo).
- La **y superior** es `alto − top`.

`page.bbox` contiene el origen de la página. Casi siempre es `(0, 0)`, así que `off_x` y `off_y` valen 0. Se suman por seguridad, para PDFs raros cuya página no empieza en el origen.

### 6.6. Avisos y fila del índice (líneas 105–122)

Se decide si la fila lleva aviso (no se leyó la referencia, o había varios recuadros) y se añade un diccionario a `filas`. Las claves coinciden con las columnas del CSV. `pdf_salida` y `pagina_salida` se dejan vacías porque todavía no se sabe en qué página del PDF nuevo caerá cada recuadro; se rellenan en el paso siguiente.

`m["conv"].title()` convierte `RESERVA 1` en `Reserva 1`.

```python
if not recortes:
    return filas, "ningún recuadro detectado"
```

Si en todo el PDF no hubo ningún recuadro, se termina aquí sin crear PDF de salida y se devuelve un aviso.

---

## 7. Composición del PDF de salida con pypdf

### 7.1. La idea: cajas de página y transformaciones

pypdf no "corta" contenido. Lo que hace es:

1. Tomar la página original completa.
2. Cambiarle la **caja visible** (`mediabox` / `cropbox`) para que solo sea el área del recuadro. Todo lo que queda fuera (la resolución, las gráficas, la marca de agua) deja de verse.
3. **Estampar** esa página recortada sobre una página en blanco nueva, desplazada a la posición deseada.

Como no se convierte nada en imagen, el resultado sigue siendo vectorial: nítido a cualquier zoom y con texto seleccionable.

- `mediabox`: el tamaño "físico" de la página.
- `cropbox`: la zona que se muestra e imprime. Se ajustan las dos para que coincidan con el recuadro.

### 7.2. Preparación (líneas 128–131)

```python
salida = carpeta_salida / f"{ruta_pdf.stem}_enunciados.pdf"
writer = PdfWriter()
pagina, y, num_pag = None, None, 0
usados = set()
```

- `PdfWriter()` crea un PDF vacío en memoria.
- `pagina` es la hoja A4 que estamos rellenando, `y` la altura por la que vamos (de arriba abajo) y `num_pag` el número de hoja actual.
- `usados` registra qué páginas originales ya se han utilizado (ver 7.3).

### 7.3. Obtener la página origen y recortarla (líneas 133–140)

```python
for fila, (n, x0, y0, x1, y1) in zip(filas, recortes):
    src = (PdfReader(ruta_pdf) if n in usados else lector(ruta_pdf)).pages[n]
    usados.add(n)
    src.mediabox.lower_left = src.cropbox.lower_left = (x0, y0)
    src.mediabox.upper_right = src.cropbox.upper_right = (x1, y1)
    w, h = x1 - x0, y1 - y0
```

- `zip(filas, recortes)` recorre a la vez cada fila del índice y sus coordenadas; ambas listas se construyeron en el mismo orden.
- `lector(ruta_pdf)` devuelve un `PdfReader` reutilizable para ese PDF (sección 7.6), para no abrir el archivo una vez por recuadro.
- **Por qué `usados`**: modificar `mediabox` altera el objeto página. Si una página tuviera dos recuadros y usáramos el mismo objeto dos veces, el segundo recorte pisaría al primero. Por eso, si la página ya se usó, se abre una copia nueva con `PdfReader(ruta_pdf)`. En tus PDF esto no ocurre (un recuadro por página), pero así el script es robusto.
- `lower_left` y `upper_right` son las esquinas inferior izquierda y superior derecha, en coordenadas PDF (origen abajo).
- `w`, `h`: ancho y alto del recuadro.

### 7.4. Modo `--uno-por-pagina`

```python
if uno_por_pagina:
    pagina = writer.add_blank_page(w, h)
    pagina.merge_transformed_page(src, Transformation().translate(-x0, -y0))
    num_pag += 1
```

- `writer.add_blank_page(w, h)` añade al PDF de salida una página en blanco del tamaño exacto del recuadro.
- **`merge_transformed_page(src, transformacion)`** estampa `src` sobre `pagina` aplicándole antes la transformación. pypdf respeta la caja de recorte de `src`, así que solo se estampa el contenido del recuadro.
- `translate(-x0, -y0)` mueve el recuadro desde su posición original (por ejemplo, x = 57, y = 690) a la esquina `(0, 0)` de la página nueva.

### 7.5. Modo por defecto: apilar en A4 (líneas siguientes)

```python
else:
    escala = min(1.0, (A4[0] - 2 * MARGEN_A4) / w)
    w, h = w * escala, h * escala
    if pagina is None or y - h < MARGEN_A4:
        pagina = writer.add_blank_page(*A4)
        y = A4[1] - MARGEN_A4
        num_pag += 1
    tx = (A4[0] - w) / 2
    ty = y - h
    t = Transformation().translate(-x0, -y0).scale(escala, escala).translate(tx, ty)
    pagina.merge_transformed_page(src, t)
    y -= h + SEPARACION
```

Funciona como ir colocando tarjetas en un folio, de arriba abajo:

1. **Escala**: si el recuadro es más ancho que el espacio útil del A4 (595 − 2·40 = 515 pt), se reduce. `min(1.0, ...)` garantiza que nunca se amplía.
2. **¿Cabe en la hoja actual?** `y` es la altura disponible más baja ocupada hasta ahora. Si no hay hoja todavía (`pagina is None`), o si al poner el recuadro se invadiría el margen inferior (`y - h < MARGEN_A4`), se crea una hoja A4 nueva y `y` vuelve arriba del todo (842 − 40).
3. **Posición**: `tx` centra el recuadro horizontalmente. `ty` es la coordenada de su borde inferior: justo debajo de `y`.
4. **La transformación encadenada**, que se aplica en orden:
   - `translate(-x0, -y0)`: lleva la esquina inferior izquierda del recuadro al origen.
   - `scale(escala, escala)`: lo reduce si hace falta. Se escala después de llevarlo al origen para que el escalado no lo desplace.
   - `translate(tx, ty)`: lo coloca en su sitio en la hoja.
5. Se estampa con `merge_transformed_page` y se baja `y` la altura del recuadro más la separación, listo para el siguiente.

Finalmente se anotan en la fila el nombre del PDF de salida y la página donde quedó:

```python
fila["pdf_salida"] = salida.name
fila["pagina_salida"] = num_pag
```

### 7.6. Escribir el archivo y la función `lector()`

```python
with open(salida, "wb") as f:
    writer.write(f)
return filas, ""
```

Hasta aquí todo estaba en memoria; `writer.write()` vuelca el PDF a disco. Se abre en modo `"wb"` (binario) porque un PDF no es texto.

```python
_lectores = {}

def lector(ruta):
    if ruta not in _lectores:
        _lectores.clear()
        _lectores[ruta] = PdfReader(ruta)
    return _lectores[ruta]
```

Es una pequeña caché: guarda el `PdfReader` del PDF que se está procesando para reutilizarlo con todos sus recuadros. Al pasar a otro PDF, `.clear()` libera el anterior para no acumular memoria cuando procesas cientos de archivos.

---

## 8. `main()`: argumentos, procesamiento en paralelo e índice

### 8.1. Argumentos de línea de comandos

```python
ap = argparse.ArgumentParser(description=__doc__, ...)
ap.add_argument("entrada", type=Path, ...)
ap.add_argument("salida", type=Path, ...)
ap.add_argument("--png", action="store_true", ...)
ap.add_argument("--dpi", type=int, default=200)
ap.add_argument("--uno-por-pagina", action="store_true", ...)
ap.add_argument("--procesos", type=int, default=os.cpu_count())
args = ap.parse_args()
```

- `entrada` y `salida` son obligatorios y posicionales. `type=Path` los convierte directamente en objetos `Path`.
- `action="store_true"` crea opciones tipo interruptor: valen `False` salvo que se escriban.
- `argparse` convierte los guiones en guiones bajos: `--uno-por-pagina` se lee como `args.uno_por_pagina`.
- `description=__doc__` reutiliza el docstring del principio del archivo, que es lo que verás con `python enunciados_batch.py --help`.

### 8.2. Lista de PDFs

```python
args.salida.mkdir(parents=True, exist_ok=True)
pdfs = [args.entrada] if args.entrada.is_file() else sorted(args.entrada.rglob("*.pdf"))
pdfs = [p for p in pdfs if not p.stem.endswith("_enunciados")]
```

- Si la entrada es un archivo, se procesa solo ese. Si es una carpeta, `rglob("*.pdf")` busca todos los PDF **recursivamente** en subcarpetas.
- La segunda línea excluye los PDF que ya genera el propio script. Así, si la carpeta de salida estuviera dentro de la de entrada, no se reprocesarían en una segunda ejecución.

### 8.3. Procesamiento en paralelo

```python
with ProcessPoolExecutor(max_workers=args.procesos) as ex:
    tareas = {ex.submit(procesar_pdf, p, args.salida, args.png, args.dpi,
                        args.uno_por_pagina): p for p in pdfs}
    for t in as_completed(tareas):
        ruta = tareas[t]
        try:
            filas, aviso = t.result()
        except Exception as e:
            ...
```

- `ProcessPoolExecutor` crea varios procesos de Python (por defecto, uno por núcleo) que trabajan a la vez. Con cientos de PDF, el tiempo total se divide aproximadamente por el número de núcleos.
- `ex.submit(funcion, argumentos...)` encarga una tarea y devuelve un *future*: un objeto que representa un resultado que llegará más adelante.
- `tareas` es un diccionario *future → ruta del PDF*, construido con una comprensión de diccionario, para saber luego a qué PDF corresponde cada resultado.
- `as_completed(tareas)` va entregando los *futures* **según terminan**, no en el orden en que se lanzaron. Por eso en la consola los PDF pueden aparecer desordenados.
- `t.result()` devuelve lo que retornó `procesar_pdf`: la tupla `(filas, aviso)`. Si dentro hubo una excepción, se relanza aquí; el `try/except` la captura para que **un PDF defectuoso no detenga todo el lote**: se anota como problema y se sigue con el siguiente.

Nota: en Windows y macOS, el código que lanza procesos tiene que estar dentro de `if __name__ == "__main__":`, como está al final del script. Si lo quitas, el script fallará al intentar crear los procesos.

### 8.4. Escritura del índice

```python
todas.sort(key=lambda f: (f["pdf"], f["pagina_original"]))
...
with open(args.salida / "indice.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(todas)
```

- Como los resultados llegan desordenados, se reordenan por PDF y página.
- `csv.DictWriter` escribe una lista de diccionarios como CSV: `fieldnames` fija el orden de las columnas, `writeheader()` escribe la cabecera y `writerows()` todas las filas.
- `newline=""` evita líneas en blanco extra en Windows, y `encoding="utf-8"` garantiza que las tildes se guarden bien.

Por último se imprime un resumen con el total de enunciados, cuántos tienen aviso y cuántos PDF dieron problemas.

---

## 9. Resumen de las funciones de pdfplumber utilizadas

| Código | Qué hace |
|---|---|
| `pdfplumber.open(ruta)` | Abre un PDF (usar con `with`) |
| `pdf.pages` | Lista de páginas |
| `page.width`, `page.height` | Dimensiones de la página en puntos |
| `page.bbox` | Caja de la página `(x0, top, x1, bottom)` |
| `page.rects` | Lista de rectángulos dibujados (diccionarios con `x0`, `x1`, `top`, `bottom`, `width`, `height`…) |
| `page.crop((x0, top, x1, bottom))` | Devuelve una "subpágina" limitada a esa caja |
| `objeto.extract_text()` | Texto contenido en la página o recorte |
| `objeto.to_image(resolution=dpi)` | Rasteriza la página o recorte; `.save(ruta)` la guarda como imagen |

Otras listas parecidas a `page.rects` que pueden resultarte útiles en el futuro: `page.lines` (líneas), `page.curves` (curvas, como la marca de agua de emestrada), `page.chars` (cada carácter con su posición y fuente) y `page.images` (imágenes incrustadas).
