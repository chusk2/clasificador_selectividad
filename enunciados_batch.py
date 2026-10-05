"""
Procesa en lote los PDF de emestrada: detecta el recuadro del enunciado de
cada página y genera, por cada PDF de entrada, un PDF nuevo que contiene
SOLO los recuadros, apilados en páginas A4. El recorte es vectorial (no se
pierde calidad y el texto sigue siendo seleccionable). Opcionalmente guarda
también cada recuadro como PNG.

Uso:
    python enunciados_batch.py carpeta_pdfs carpeta_salida [opciones]

Opciones:
    --png            guarda además un PNG por enunciado (para la API con visión)
    --dpi 200        resolución de los PNG
    --uno-por-pagina cada recuadro en su propia página, del tamaño del recuadro
    --procesos N     número de PDFs procesados en paralelo (por defecto: nº de CPUs)

Requisitos:
    pip install pdfplumber pypdf
"""
import argparse
import csv
import os
import re
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter, Transformation

ANCHO_MIN, ALTO_MIN = 300, 20   # pt: tamaño mínimo para considerar un recuadro
MARGEN = 2                      # pt de holgura alrededor del borde
A4 = (595.28, 841.89)
MARGEN_A4 = 40                  # pt de margen en la página de salida
SEPARACION = 15                 # pt entre recuadros

PATRON = re.compile(
    r"(?P<anio>(19|20)\d{2})\.\s*"
    r"(?P<conv>[A-ZÁÉÍÓÚ]+(?:\s+\d)?)\.?\s*"
    r"EJERCICIO\s*(?P<ej>\d+)"
    r"(?:\.?\s*OPCI[OÓ]N\s*(?P<opc>[AB]))?",
    re.IGNORECASE,
)


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", texto).strip("_").lower()


def detectar_recuadros(page):
    """Rectángulos grandes de la página, sin duplicados (relleno + borde)."""
    vistos = {}
    for r in page.rects:
        if r["width"] > ANCHO_MIN and r["height"] > ALTO_MIN:
            clave = tuple(round(r[k]) for k in ("x0", "top", "x1", "bottom"))
            vistos[clave] = r
    return sorted(vistos.values(), key=lambda r: r["top"])


def procesar_pdf(ruta_pdf, carpeta_salida, png, dpi, uno_por_pagina):
    filas = []
    recortes = []  # (indice_pagina, x0, y0, x1, y1) en coordenadas PDF
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
                m = PATRON.search(texto)

                if m:
                    nombre = f"{m['anio']}_{slug(m['conv'])}_ej{m['ej']}"
                    if m["opc"]:
                        nombre += f"_{m['opc'].lower()}"
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

                # pdfplumber mide desde arriba; PDF mide desde abajo
                off_x, off_y = float(page.bbox[0]), float(page.bbox[1])
                recortes.append((n, off_x + x0, off_y + page.height - bottom,
                                 off_x + x1, off_y + page.height - top))

                aviso = ""
                if not m:
                    aviso = "sin metadatos"
                elif len(cajas) > 1:
                    aviso = f"{len(cajas)} recuadros en la página"

                filas.append({
                    "pdf": str(ruta_pdf),
                    "pagina_original": n + 1,
                    "anio": m["anio"] if m else "",
                    "convocatoria": m["conv"].title() if m else "",
                    "ejercicio": m["ej"] if m else "",
                    "opcion": (m["opc"] or "").upper() if m else "",
                    "pdf_salida": "",
                    "pagina_salida": "",
                    "imagen": imagen,
                    "aviso": aviso,
                })

    if not recortes:
        return filas, "ningún recuadro detectado"

    # 2) Composición vectorial con pypdf
    salida = carpeta_salida / f"{ruta_pdf.stem}_enunciados.pdf"
    writer = PdfWriter()
    pagina, y, num_pag = None, None, 0
    usados = set()

    for fila, (n, x0, y0, x1, y1) in zip(filas, recortes):
        # Si una página tiene varios recuadros, se relee para no reutilizar
        # el mismo objeto con otra caja de recorte.
        src = (PdfReader(ruta_pdf) if n in usados else lector(ruta_pdf)).pages[n]
        usados.add(n)
        src.mediabox.lower_left = src.cropbox.lower_left = (x0, y0)
        src.mediabox.upper_right = src.cropbox.upper_right = (x1, y1)
        w, h = x1 - x0, y1 - y0

        if uno_por_pagina:
            pagina = writer.add_blank_page(w, h)
            pagina.merge_transformed_page(src, Transformation().translate(-x0, -y0))
            num_pag += 1
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

        fila["pdf_salida"] = salida.name
        fila["pagina_salida"] = num_pag

    with open(salida, "wb") as f:
        writer.write(f)
    return filas, ""


_lectores = {}


def lector(ruta):
    if ruta not in _lectores:
        _lectores.clear()
        _lectores[ruta] = PdfReader(ruta)
    return _lectores[ruta]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path, help="Carpeta con PDFs (se recorre recursivamente) o un PDF")
    ap.add_argument("salida", type=Path, help="Carpeta de salida")
    ap.add_argument("--png", action="store_true", help="Guardar también un PNG por enunciado")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--uno-por-pagina", action="store_true", help="Un recuadro por página")
    ap.add_argument("--procesos", type=int, default=os.cpu_count())
    args = ap.parse_args()

    args.salida.mkdir(parents=True, exist_ok=True)
    pdfs = [args.entrada] if args.entrada.is_file() else sorted(args.entrada.rglob("*.pdf"))
    pdfs = [p for p in pdfs if not p.stem.endswith("_enunciados")]
    print(f"{len(pdfs)} PDFs encontrados\n")

    todas, problemas = [], []
    with ProcessPoolExecutor(max_workers=args.procesos) as ex:
        tareas = {ex.submit(procesar_pdf, p, args.salida, args.png, args.dpi,
                            args.uno_por_pagina): p for p in pdfs}
        for t in as_completed(tareas):
            ruta = tareas[t]
            try:
                filas, aviso = t.result()
            except Exception as e:
                problemas.append((ruta, f"ERROR: {e}"))
                print(f"ERROR   {ruta.name}: {e}")
                continue
            todas.extend(filas)
            if aviso:
                problemas.append((ruta, aviso))
                print(f"AVISO   {ruta.name}: {aviso}")
            else:
                print(f"OK      {ruta.name}: {len(filas)} enunciados")

    todas.sort(key=lambda f: (f["pdf"], f["pagina_original"]))
    campos = ["pdf", "pagina_original", "anio", "convocatoria", "ejercicio", "opcion",
              "pdf_salida", "pagina_salida", "imagen", "aviso"]
    with open(args.salida / "indice.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(todas)

    con_aviso = sum(1 for f in todas if f["aviso"])
    print(f"\nTotal: {len(todas)} enunciados de {len(pdfs)} PDFs "
          f"({con_aviso} con aviso, {len(problemas)} PDFs con problemas).")
    print(f"Índice: {args.salida / 'indice.csv'}")


if __name__ == "__main__":
    main()
