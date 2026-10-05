# emestrada_parser — Memoria del proyecto

## Contexto

Pipeline para extraer y clasificar los ejercicios de Selectividad (EBAU/PEvAU) de Andalucía a partir de los PDFs de problemas resueltos de **emestrada.org**. Asignatura principal: Química (unos 400 PDFs, 25 años). También Matemáticas II.

- Repositorio: `chusk2/emestrada_parser`
- Frontend: Streamlit, con base de datos SQLite, desplegado en VPS.
- Uso final: material docente. El profesor trabaja haciendo capturas de los enunciados, así que **solo necesita los enunciados como imagen**, no las soluciones.

## Estructura de los PDFs de origen

Cada PDF corresponde a una asignatura, un año y un tema.

- **Portada (página 1)**: sin recuadro. Contiene en texto limpio la asignatura, el año, el tema (p. ej. `TEMA 5: EQUILIBRIO QUÍMICO`) y la lista de ejercicios.
- **Páginas de ejercicio**: el enunciado va dentro de un **recuadro vectorial** en la parte superior (unos 500 pt de ancho). Debajo, `R E S O L U C I Ó N` y la solución. Fondo con watermark y logo.
- **Última línea del recuadro**: metadatos en texto limpio, p. ej. `QUÍMICA. 2026. JUNIO. EJERCICIO 3A` o `MATEMÁTICAS II. 2023. JUNIO. EJERCICIO 4`.
- Algunas soluciones largas continúan en páginas sin recuadro.
- El tema de la portada **no es una clasificación fiable**: p. ej. el 2B de Química 2026 (cinética) aparece en el PDF de Equilibrio Químico.

## Hechos comprobados

- **El recuadro es un objeto vectorial**, no una imagen: `pdfplumber` lo devuelve en `page.rects`. Aparece duplicado (relleno + borde) con las mismas coordenadas, hay que deduplicar.
- En las soluciones hay **recuadros pequeños** (p. ej. integrales por partes) que se descartan por tamaño.
- **Las fórmulas son MathType / editor de ecuaciones de Word** (fuente Symbol, caracteres de uso privado). En el texto extraído salen rotas: `\uf0f2` = ∫, `\uf0ae` = →, `\uf03d` = =; subíndices sueltos (`CO 2`), corchetes perdidos, la flecha de equilibrio ⇄ desaparece. Se pierde la estructura de fracciones, límites y exponentes.
- **`page.crop()` de pdfplumber filtra los caracteres por coordenadas**: el texto extraído del recorte en el PDF original contiene solo el enunciado.
- **El recorte vectorial con pypdf (`Transformation` + caja de recorte) NO elimina contenido**: solo aplica una máscara. El PDF resultante conserva todo el texto de las soluciones, el watermark y los objetos de fórmulas. Al extraer texto de él aparecen las soluciones, y `pdftotext` las mezcla línea a línea con los enunciados. Además pesa más que el original (185 KB frente a 131 KB en el PDF de prueba).
- **Un PDF de imágenes PNG es mucho más ligero**: en el PDF de prueba, 23 KB (PNG en gris, 200 dpi) frente a 185 KB del PDF de crops vectoriales.
  - 150 dpi: 16 KB · 200 dpi: 23 KB · 300 dpi: 39 KB.
  - Blanco y negro puro (1 bit) apenas ahorra (23 → 18 KB) y puede perder trazos finos.
  - Pillow guardando directamente a PDF en gris usa JPEG: 208 KB y texto emborronado. **No usarlo.**

## Decisiones tomadas

1. **Solo interesan los enunciados.** Las soluciones se ignoran por completo.
2. **El enunciado se trabaja como imagen.** El texto no es necesario para el uso docente; se guarda igualmente (en bruto) por si sirve para buscar o clasificar.
3. **Detección por recuadro + confirmación por metadatos** (ver criterio abajo).
4. **Imágenes en PNG, escala de grises, 200 dpi, sin pérdida.** El PDF de enunciados se compone a partir de los PNG, no con crops vectoriales.
5. **El CSV es la pieza central.** El PDF apilado es un producto derivado del CSV y los PNG.

## Criterio de detección de enunciados

Un recuadro se considera enunciado en dos niveles:

| Condición | Resultado |
|---|---|
| Rectángulo con ancho > 300 pt y alto > 20 pt | Candidato |
| Candidato + línea de metadatos completa | **Enunciado** |
| Candidato sin línea de metadatos | **Aviso** (revisión manual) |
| Resto | Se ignora |

Línea de metadatos: `ASIGNATURA. AÑO. CONVOCATORIA. EJERCICIO N[opción]`.

- Exigir también la palabra `EJERCICIO`, no solo asignatura + año.
- **Asignaturas como lista configurable** (QUÍMICA, MATEMÁTICAS II, FÍSICA, MATEMÁTICAS APLICADAS A LAS CC.SS. II…).
- **Normalizar el texto antes de la regex**: mayúsculas, sin tildes (NFKD), espacios variables. Las tildes pueden salir descompuestas.
- La **portada** es la excepción: no se le aplica la detección; se lee su texto para obtener el tema.

## Fase actual: recortes de enunciados

Con el script basado en `pdfplumber`, recortar los recuadros que contienen los ejercicios de cada PDF. Guardar por una parte cada recuadro en su propio archivo `.png` y por otra generar un PDF con los recuadros uno debajo de otro. Guardar todo en una estructura de carpetas diseñada para ello.

### Pasos

1. **Recorte de recuadros.** Recorrer las páginas (excepto la portada), detectar los recuadros y aplicar `page.crop()` con un margen de 2 pt.
2. **Parseo del recuadro.** Del mismo recorte: extraer el texto, aplicar la regex de metadatos y escribir una fila en el CSV. Texto en bruto, sin limpiar los caracteres de MathType.
3. **Guardado del PNG.** Del mismo recorte: renderizar a 200 dpi, convertir a gris (`L`), guardar como PNG con `optimize=True`.
4. **PDF apilado.** A partir de los **PNG ya guardados** (sin volver a renderizar): pegarlos en lienzos A4 uno debajo de otro y empaquetar con `img2pdf` (no recomprime).
   - Salto de página cuando un recuadro no cabe en lo que queda de A4.
   - Decidir qué hacer si un recuadro es más alto que una página entera (raro).
   - Pendiente de decidir si es un paso fijo o una salida opcional generada a demanda desde el CSV (p. ej. todos los enunciados de un tema).

Los pasos 1 a 3 salen de un único recorrido por cada página.

### Piezas transversales

- **Validación**: avisos cuando una página no tiene recuadro (salvo portada o continuación de solución), tiene más de uno o la regex no encuentra metadatos.
- **Reanudación**: saber qué PDFs ya están procesados (consultando el CSV) para no repetirlos si el proceso se corta o se añaden PDFs nuevos.

### Rendimiento

- Saltar las páginas sin recuadro ahorra sobre todo el renderizado del PNG; detectar el recuadro ya obliga a interpretar la página. En los PDFs de emestrada casi todas las páginas tienen recuadro, así que el ahorro es modesto.
- Si la velocidad llegara a importar: detectar rectángulos con PyMuPDF (`page.get_drawings()`), más rápido que pdfplumber.
- El procesamiento en paralelo (`ProcessPoolExecutor`) funciona en script, pero da problemas en Jupyter en Windows y macOS.

## Estructura de carpetas

```
datos/
  pdfs/<asignatura>/            # PDFs originales de emestrada (solo lectura)
salida/
  png/<asignatura>/<año>/       # un PNG por enunciado
  pdf/<asignatura>/             # PDFs de enunciados apilados, uno por PDF de origen
  indice/
    enunciados.csv              # índice central
```

**Nombre del PNG = identificador del enunciado**: `<asignatura>_<año>_<convocatoria>_ej<n>[<opción>].png`, p. ej. `quimica_2026_junio_ej3a.png`. Enlaza con la fila del CSV y es reconocible a simple vista. Si hay colisión, añadir sufijo `_2`, `_3`… y registrar aviso.

## Esquema del CSV

| Columna | Contenido |
|---|---|
| `id` | Identificador (igual que el nombre del PNG sin extensión) |
| `asignatura` | De la línea de metadatos |
| `anio` | Año |
| `convocatoria` | Junio, Julio, Reserva 1… |
| `ejercicio` | Número |
| `opcion` | A / B / vacío |
| `tema_portada` | Tema según la portada del PDF de origen (referencia, no clasificación) |
| `pdf_origen` | Ruta del PDF original |
| `pagina_origen` | Página dentro del PDF original |
| `png` | Ruta del PNG |
| `texto` | Texto extraído del recuadro, en bruto |
| `aviso` | Vacío si todo es correcto |

## Siguiente fase (pendiente): clasificación

- La clasificación se hará con la API de Claude usando los `.md` de instrucciones por tema, con salida JSON estructurada.
- Coste estimado con imágenes: del orden de unos pocos euros para todo el archivo. Cada recorte a 200 dpi ocupa unos 350–550 tokens; las instrucciones, 1.000–2.000.
- Pendiente decidir entre **texto** (más barato, 50–150 tokens por enunciado, pero con fórmulas rotas) e **imagen** (más fiable). Propuesta: prueba con 30–50 enunciados etiquetados a mano, clasificados por ambas vías, y comparar aciertos. Opción mixta: texto por defecto e imagen solo en los casos dudosos.
- En Química el texto probablemente baste para clasificar por tema; en Matemáticas II depende del bloque.

## Cosas a vigilar

- Comprobar en PDFs de otros años que el recuadro sigue siendo vectorial. En PDFs antiguos escaneados sería una imagen y habría que detectarlo con OpenCV (contornos).
- Posibles páginas con dos enunciados.
- Variaciones en el formato de la línea de metadatos entre años.
