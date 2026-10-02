# %% [markdown]
# # Recorte de enunciados de PDFs de emestrada — paso a paso
# 
# Este cuaderno hace lo mismo que `enunciados_batch.py`, pero dividido en celdas para que puedas ejecutar cada paso, ver qué ocurre y experimentar.
# 
# **Recorrido:**
# 1. Preparación (imports y rutas)
# 2. Explorar un PDF con pdfplumber
# 3. Encontrar los rectángulos de una página
# 4. Detectar el recuadro del enunciado (y quitar duplicados)
# 5. Recortar, extraer texto y guardar PNG
# 6. Extraer año, convocatoria y ejercicio con una expresión regular
# 7. Componer el PDF de salida con pypdf
# 8. Juntarlo todo en una función y procesar una carpeta completa
# 
# Ejecuta las celdas en orden con `Shift + Enter`.

import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd
import pdfplumber
from pypdf import PdfReader, PdfWriter, Transformation
from IPython.display import display

# ### Rutas

# Cambia estas tres rutas por las tuyas:
# - `RUTA_PDF`: un PDF concreto para las pruebas de las secciones 2 a 7.
# - `CARPETA_ENTRADA`: la carpeta con todos los PDF (sección 8).
# - `CARPETA_SALIDA`: donde se guardarán los resultados.

# %% [markdown]
# ### Parámetros
# 
# Todas las medidas están en **puntos** (1 pt = 1/72 de pulgada ≈ 0,35 mm). Un A4 mide 595 × 842 pt.

# %%
ANCHO_MIN, ALTO_MIN = 300, 20   # tamaño mínimo para considerar un rectángulo como recuadro de enunciado
MARGEN = 2                      # holgura alrededor del borde al recortar
DPI = 200                       # resolución de los PNG
A4 = (595.28, 841.89)
MARGEN_A4 = 40                  # margen de la hoja de salida
SEPARACION = 15                 # hueco entre recuadros apilados

# %%
def detectar_recuadros(page):
    vistos = {}
    for r in page.rects:
        if r["width"] > ANCHO_MIN and r["height"] > ALTO_MIN:
            clave = tuple(round(r[k]) for k in ("x0", "top", "x1", "bottom"))
            vistos[clave] = r
    return sorted(vistos.values(), key=lambda r: r["top"])

# %%
PATRON = re.compile(
    r"(?P<anio>(19|20)\d{2})\.\s*"
    r"(?P<conv>[A-ZÁÉÍÓÚ]+(?:\s+\d)?)\.?\s*"
    r"(?:EJERCICIO\s*)?(?P<ej>[A-C]?\d+)"
    r"(?:\.?\s*OPCI[OÓ]N\s*(?P<opc>[AB]))?",
    re.IGNORECASE,
)

# %%
def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", texto).strip("_").lower()


print(slug("RESERVA 1"), "|", slug("SEPTIEMBRE"), "|", slug("2023 - Integrales"))

# %%
GUARDAR_PNG = True
UNO_POR_PAGINA = False

# %%
def procesar_pdf(ruta_pdf, carpeta_salida, png=GUARDAR_PNG, dpi=DPI, uno_por_pagina=UNO_POR_PAGINA):
    filas, recortes = [], []
    carpeta_png = carpeta_salida / "png" / ruta_pdf.stem

    # 1) Detección con pdfplumber
    with pdfplumber.open(ruta_pdf) as pdf:
        for n, page in enumerate(pdf.pages):
            cajas = detectar_recuadros(page)
            for k, r in enumerate(cajas, start=1):
                x0 = max(r["x0"] - MARGEN, 0)
                x1 = min(r["x1"] + MARGEN, page.width)
                top = max(r["top"] - MARGEN, 0)
                bottom = min(r["bottom"] + MARGEN, page.height)

                recorte = page.crop((x0, top, x1, bottom))
                texto = (recorte.extract_text() or "").replace("\n", " ")
                metadata = PATRON.search(texto)

                if metadata:
                    nombre = f"{metadata['anio']}_{slug(metadata['conv'])}_{metadata['ej']}"
                    if metadata["opc"]:
                        nombre += f"_{metadata['opc'].lower()}"
                else:
                    nombre = f"{slug(ruta_pdf.stem)}_p{n + 1:02d}"
                if len(cajas) > 1:
                    nombre += f"_r{k}"

                imagen = ""
                if png:
                    carpeta_png.mkdir(parents=True, exist_ok=True)
                    destino = carpeta_png / f"{nombre}.png"
                    i = 2
                    while destino.exists():
                        destino = carpeta_png / f"{nombre}_{i}.png"
                        i += 1
                    recorte.to_image(resolution=dpi).save(destino)
                    imagen = str(destino.relative_to(carpeta_salida))

                off_x, off_y = float(page.bbox[0]), float(page.bbox[1])
                recortes.append((n, off_x + x0, off_y + page.height - bottom,
                                 off_x + x1, off_y + page.height - top))

                aviso = ""
                if not metadata:
                    aviso = "sin metadatos"
                elif len(cajas) > 1:
                    aviso = f"{len(cajas)} recuadros en la página"

                filas.append({
                    "año": metadata["anio"] if metadata else "",
                    "convocatoria": metadata["conv"].title() if metadata else "",
                    "ejercicio": metadata["ej"] if metadata else "",
                    "opcion": (metadata["opc"] or "").upper() if metadata else "",
                    "enunciado" : texto,
                    "imagen": imagen,
                    "aviso": aviso,
                })

    if not recortes:
        return filas, "ningún recuadro detectado"

    # 2) Composición vectorial con pypdf
    salida = carpeta_salida / f"{ruta_pdf.stem}_enunciados.pdf"
    writer = PdfWriter()
    hoja, y, num_hoja = None, None, 0
    usados = set()
    reader = PdfReader(ruta_pdf)

    for fila, (n, x0, y0, x1, y1) in zip(filas, recortes):
        # si la página ya se usó (varios recuadros), se relee para no pisar el recorte anterior
        src = (PdfReader(ruta_pdf) if n in usados else reader).pages[n]
        usados.add(n)
        src.mediabox.lower_left = src.cropbox.lower_left = (x0, y0)
        src.mediabox.upper_right = src.cropbox.upper_right = (x1, y1)
        w, h = x1 - x0, y1 - y0

        if uno_por_pagina:
            hoja = writer.add_blank_page(w, h)
            hoja.merge_transformed_page(src, Transformation().translate(-x0, -y0))
            num_hoja += 1
        else:
            escala = min(1.0, (A4[0] - 2 * MARGEN_A4) / w)
            w, h = w * escala, h * escala
            if hoja is None or y - h < MARGEN_A4:
                hoja = writer.add_blank_page(*A4)
                y = A4[1] - MARGEN_A4
                num_hoja += 1
            tx, ty = (A4[0] - w) / 2, y - h
            t = Transformation().translate(-x0, -y0).scale(escala, escala).translate(tx, ty)
            hoja.merge_transformed_page(src, t)
            y -= h + SEPARACION

        # fila["pdf_salida"] = salida.name
        # fila["pagina_salida"] = num_hoja

    with open(salida, "wb") as f:
        writer.write(f)
    return filas, ""

# %%
RUTA_PDF = Path("./solubilidad/2024 - Solubilidad.pdf")
#CARPETA_ENTRADA = Path("./pdf_recortados")
CARPETA_SALIDA = Path("./pdf_recortados")

CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
print("¿Existe el PDF de prueba?", RUTA_PDF.exists())

# %%
filas, aviso = procesar_pdf(RUTA_PDF, CARPETA_SALIDA)
print("Aviso:", aviso or "ninguno")
pd.DataFrame(filas)

# %% [markdown]
# ### 8.2. Procesar la carpeta completa
# 
# `rglob("*.pdf")` busca PDF también en subcarpetas. Se excluyen los `_enunciados.pdf` que genera el propio proceso.
# 
# Aquí se procesan **uno detrás de otro**. Para lotes muy grandes, el script `enunciados_batch.py` es más rápido porque usa varios núcleos en paralelo (el procesamiento en paralelo no funciona bien dentro de Jupyter en Windows y macOS).
# 
# Si quieres probar primero con unos pocos, cambia `LIMITE` (por ejemplo, `LIMITE = 5`).

# %%
LIMITE = None   # None = todos

pdfs = sorted(p for p in CARPETA_ENTRADA.rglob("*.pdf") if not p.stem.endswith("_enunciados"))
if LIMITE:
    pdfs = pdfs[:LIMITE]
print(f"{len(pdfs)} PDFs a procesar\n")

todas, problemas = [], []
for i, ruta in enumerate(pdfs, start=1):
    try:
        filas, aviso = procesar_pdf(ruta, CARPETA_SALIDA)
    except Exception as e:
        problemas.append({"pdf": str(ruta), "problema": f"ERROR: {e}"})
        print(f"[{i}/{len(pdfs)}] ERROR  {ruta.name}: {e}")
        continue
    todas.extend(filas)
    if aviso:
        problemas.append({"pdf": str(ruta), "problema": aviso})
        print(f"[{i}/{len(pdfs)}] AVISO  {ruta.name}: {aviso}")
    else:
        print(f"[{i}/{len(pdfs)}] OK     {ruta.name}: {len(filas)} enunciados")

# %% [markdown]
# ### 8.3. Índice y revisión de problemas
# 
# Guardamos el índice en CSV y lo mostramos como DataFrame, que es cómodo para filtrar.

# %%
indice = pd.DataFrame(todas)
indice.to_csv(CARPETA_SALIDA / "indice.csv", index=False, encoding="utf-8")
print("Total enunciados:", len(indice))
indice.head(20)

# %% [markdown]
# Enunciados con aviso (sin metadatos o varios recuadros por página) y PDFs con problemas:

# %%
if len(indice):
    display(indice[indice["aviso"] != ""])
display(pd.DataFrame(problemas))

# %% [markdown]
# Un resumen rápido: cuántos enunciados hay por año y convocatoria.

# %%
if len(indice):
    display(indice.pivot_table(index="anio", columns="convocatoria", values="ejercicio",
                               aggfunc="count", fill_value=0))


