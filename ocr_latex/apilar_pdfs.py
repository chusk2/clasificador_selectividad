"""
apilar_pdfs.py — junta los PDF de cada ejercicio (tex/*.pdf) en un único PDF A4,
con los ejercicios uno debajo de otro y marcadores (bookmarks) por PDF
original y por ejercicio. Si uno no cabe en lo que queda de
página, pasa a la siguiente. Se copian como vectores: no pierden calidad.

Uso:
    python apilar_pdfs.py salida_latex                 # todos -> salida_latex/ejercicios.pdf
    python apilar_pdfs.py salida_latex --por-archivo   # un PDF por cada PDF original
"""
import argparse
import csv
from collections import defaultdict
from pathlib import Path

import pymupdf

A4 = pymupdf.paper_rect("a4")   # 595 x 842 puntos
MARGEN = 40                     # margen de la página (pt)
SEPARACION = 16                 # espacio entre ejercicios (pt)


def titulo_grupo(fl: dict) -> str:
    """Marcador de nivel 1 (un PDF original): '2001 · Matemáticas II · Integrales'."""
    partes = [fl.get("anio", ""), fl.get("asignatura", ""), fl.get("tema", "").capitalize()]
    return " · ".join(p for p in partes if p) or fl["archivo"]


def titulo_ejercicio(fl: dict) -> str:
    """Marcador de nivel 2 (un ejercicio): 'Junio · A2'."""
    partes = [fl.get("convocatoria", ""), fl.get("ejercicio", "")]
    return " · ".join(p for p in partes if p) or f"Ejercicio {fl['n']}"


def apilar(items: list[dict], salida: Path) -> None:
    """Coloca la 1ª página de cada PDF una debajo de otra en páginas A4
    y añade marcadores (bookmarks): nivel 1 = PDF original, nivel 2 = ejercicio.

    Cada item: {"ruta": Path, "grupo": str, "titulo": str}
    """
    doc = pymupdf.open()
    ancho_util = A4.width - 2 * MARGEN
    alto_util = A4.height - 2 * MARGEN
    pagina, y = None, MARGEN
    toc, grupo_actual = [], None   # toc: [nivel, título, nº de página (desde 1)]

    for item in items:
        with pymupdf.open(item["ruta"]) as src:
            r = src[0].rect
            # reduce solo si no cabe a lo ancho o es más alto que una página
            escala = min(1, ancho_util / r.width, alto_util / r.height)
            ancho, alto = r.width * escala, r.height * escala
            if pagina is None or y + alto > A4.height - MARGEN:
                pagina = doc.new_page(width=A4.width, height=A4.height)
                y = MARGEN
            x = MARGEN + (ancho_util - ancho) / 2          # centrado
            pagina.show_pdf_page(pymupdf.Rect(x, y, x + ancho, y + alto), src, 0)
            y += alto + SEPARACION

        n_pagina = doc.page_count                      # página donde ha quedado
        if item["grupo"] != grupo_actual:              # empieza un PDF original nuevo
            toc.append([1, item["grupo"], n_pagina])
            grupo_actual = item["grupo"]
        toc.append([2, item["titulo"], n_pagina])

    doc.set_toc(toc)
    doc.save(str(salida), garbage=3, deflate=True)
    doc.close()
    print(f"{salida}: {len(items)} ejercicios")


def pdfs_desde_csv(carpeta: Path) -> dict[str, list[dict]]:
    """Lee enunciados_latex.csv y devuelve {archivo: [items en orden]} (solo los que compilan)."""
    grupos = defaultdict(list)
    with (carpeta / "enunciados_latex.csv").open(encoding="utf-8-sig") as f:
        filas = [fl for fl in csv.DictReader(f) if fl["compila"] == "True"]
    for fl in sorted(filas, key=lambda fl: (fl["archivo"], int(fl["n"]))):
        ruta = carpeta / "tex" / f"{fl['archivo']}_{int(fl['n']):02d}.pdf"
        if ruta.exists():
            grupos[fl["archivo"]].append(
                {"ruta": ruta, "grupo": titulo_grupo(fl), "titulo": titulo_ejercicio(fl)})
    return grupos


def main() -> None:
    p = argparse.ArgumentParser(description="Apila los PDF de cada ejercicio en un único PDF")
    p.add_argument("carpeta", type=Path, help="carpeta de salida del pipeline (salida_latex)")
    p.add_argument("--por-archivo", action="store_true",
                   help="un PDF por cada PDF original en vez de uno solo")
    args = p.parse_args()

    grupos = pdfs_desde_csv(args.carpeta)
    if args.por_archivo:
        destino = args.carpeta / "apilados"
        destino.mkdir(exist_ok=True)
        for archivo, items in grupos.items():
            apilar(items, destino / f"{archivo}.pdf")
    else:
        todos = [it for items in grupos.values() for it in items]
        apilar(todos, args.carpeta / "ejercicios.pdf")


if __name__ == "__main__":
    main()
