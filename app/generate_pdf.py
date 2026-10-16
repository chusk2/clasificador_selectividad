from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


def df_to_pdf(df, titulo="Ejercicios filtrados"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20,
    )
    estilos = getSampleStyleSheet()
    celda = estilos["BodyText"]
    celda.fontSize = 8
    celda.leading = 10

    # Paragraph hace que el texto largo se ajuste a la celda
    datos = [[Paragraph(f"<b>{escape(str(c))}</b>", celda) for c in df.columns]]
    for fila in df.fillna("").astype(str).itertuples(index=False):
        datos.append([Paragraph(escape(v), celda) for v in fila])

    tabla = Table(datos, repeatRows=1)  # repite la cabecera en cada página
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    doc.build([Paragraph(titulo, estilos["Title"]), Spacer(1, 10), tabla])
    return buffer.getvalue()