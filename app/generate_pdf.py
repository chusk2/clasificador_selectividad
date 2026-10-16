from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

FUENTE = "Helvetica"
FUENTE_NEGRITA = "Helvetica-Bold"
TAM_FUENTE = 8

# Padding horizontal total de cada columna (suma de izquierda + derecha), en puntos.
# Se calcula como una fracción del ancho medio del contenido, entre un mínimo y un máximo.
PADDING_MIN = 12
PADDING_MAX = 36
PADDING_RATIO = 0.25   # 25 % del ancho medio de columna

# columnas centradas (cabecera y celdas); el resto se alinea a la izquierda
COLUMNAS_CENTRADAS = ("año", "asignatura", "tema")

MARGEN = 20  # puntos, en los cuatro lados


def _ancho_contenido(df):
    """Ancho del texto más largo de cada columna (cabecera en negrita incluida)."""
    anchos = []
    for col in df.columns:
        w_cabecera = stringWidth(str(col), FUENTE_NEGRITA, TAM_FUENTE)
        w_celdas = max(
            (stringWidth(str(v), FUENTE, TAM_FUENTE) for v in df[col].fillna("")),
            default=0,
        )
        anchos.append(max(w_cabecera, w_celdas))
    return anchos


def elegir_tamano_pagina(df):
    """A4 vertical si la tabla cabe en 21 cm sin partir texto; si no, A4 horizontal.

    "Cabe" significa que el contenido más el padding mínimo de cada columna
    entra en el ancho útil de la página vertical.
    """
    ancho_util_vertical = A4[0] - 2 * MARGEN
    necesario = sum(_ancho_contenido(df)) + PADDING_MIN * len(df.columns)
    return A4 if necesario <= ancho_util_vertical else landscape(A4)


def calcular_anchos(df, ancho_disponible, minimo=40):
    """Devuelve (anchos de columna, padding horizontal por columna).

    - La tabla mide lo que ocupa su contenido más un padding proporcional a ese
      contenido; si cabe en la página, no se estira (se centrará al construirla).
    - Si no cabe, se ensancha hasta el ancho disponible: se limitan las columnas
      más anchas (su texto se parte en varias líneas) y las estrechas conservan
      su ancho.
    """
    contenido = _ancho_contenido(df)
    n = len(contenido)

    # padding proporcional al ancho medio de columna, acotado, y que no
    # supere el hueco que queda en la página
    padding = PADDING_RATIO * sum(contenido) / n
    padding = max(PADDING_MIN, min(PADDING_MAX, padding))
    hueco_por_columna = (ancho_disponible - sum(contenido)) / n
    padding = max(PADDING_MIN, min(padding, hueco_por_columna))

    ideales = [w + padding for w in contenido]
    if sum(ideales) <= ancho_disponible:
        return ideales, padding

    # no cabe: búsqueda binaria del tope t tal que sum(min(ideal, t)) == ancho_disponible
    lo, hi = minimo, max(ideales)
    for _ in range(40):
        tope = (lo + hi) / 2
        if sum(min(w, tope) for w in ideales) > ancho_disponible:
            hi = tope
        else:
            lo = tope
    anchos = [min(w, lo) for w in ideales]
    escala = ancho_disponible / sum(anchos)
    return [w * escala for w in anchos], padding


def df_to_pdf(df, titulo="Ejercicios filtrados", centradas=COLUMNAS_CENTRADAS):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=elegir_tamano_pagina(df),
        leftMargin=MARGEN, rightMargin=MARGEN, topMargin=MARGEN, bottomMargin=MARGEN,
    )
    estilos = getSampleStyleSheet()
    celda = estilos["BodyText"]
    celda.fontSize = TAM_FUENTE
    celda.leading = 10

    # un estilo por columna: centrado o a la izquierda
    izquierda = ParagraphStyle("celda_izq", parent=celda, alignment=TA_LEFT)
    centrado = ParagraphStyle("celda_cen", parent=celda, alignment=TA_CENTER)
    estilo_col = [centrado if c in centradas else izquierda for c in df.columns]

    # Paragraph hace que el texto largo se ajuste a la celda
    datos = [[Paragraph(f"<b>{escape(str(c))}</b>", estilo_col[i])
              for i, c in enumerate(df.columns)]]
    for fila in df.fillna("").astype(str).itertuples(index=False):
        datos.append([Paragraph(escape(v), estilo_col[i]) for i, v in enumerate(fila)])

    anchos, padding = calcular_anchos(df, doc.width)
    tabla = Table(datos, colWidths=anchos, repeatRows=1, hAlign="CENTER")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), padding / 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding / 2),
    ]))

    doc.build([Paragraph(titulo, estilos["Title"]), Spacer(1, 10), tabla])
    return buffer.getvalue()
