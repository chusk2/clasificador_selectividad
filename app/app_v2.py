"""App local de consulta de enunciados. Ejecutar: streamlit run app/app.py"""
import functools
import http.server
import threading
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
import datetime
from generate_pdf import df_to_pdf

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "csv" / "ejercicios_clasificados.csv"
PUERTO_ARCHIVOS = 8599
TODOS = "Todos"


@st.cache_resource
def servidor_archivos():
    """Sirve el proyecto por HTTP en local: el navegador no abre file:// desde una página http."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Handler, directory=str(RAIZ))
    try:
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO_ARCHIVOS), handler)
    except OSError:
        return None  # puerto ya ocupado (otra sesión): se asume que sirve lo mismo
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def servidor_sirve_raiz():
    """Comprueba que lo que escucha en el puerto sirve este proyecto (pide el CSV por HTTP)."""
    prueba = f"http://127.0.0.1:{PUERTO_ARCHIVOS}/{quote(CSV.relative_to(RAIZ).as_posix())}"
    try:
        with urllib.request.urlopen(urllib.request.Request(prueba, method="HEAD"), timeout=2):
            return True
    except (urllib.error.URLError, OSError):
        return False


@st.cache_data
def cargar():
    return pd.read_csv(CSV)

def borrar_filtro():
    for filtro in ["selected_year", "selected_asignatura",
                   "selected_tema", "selected_tipo_ejercicio"]:
        st.session_state[filtro] = ""

def export_dataframe(df):
# columnas de filtered_df:
# año
# asignatura
# convocatoria
# ejercicio
# tema
# nombre_ejercicio
# tipo_ejercicio
# observaciones
# archivo_pdf
# enunciado_img

    renamed_cols = {
        "nombre_ejercicio" : "nombre de ejercicio",
        "observaciones" : "comentario",
        "tipo_ejercicio" : "tipo de ejercicio"
        }
    # eliminar columnas innecesarias
    export_df = df.drop(["convocatoria", "ejercicio",
                                  "archivo_pdf", "enunciado_img"], axis = 1)
    export_df = export_df.rename(columns = renamed_cols)

    return export_df

def url(ruta):
    if pd.isna(ruta):
        return None
    # Las rutas del CSV vienen de macOS (NFD) y en disco los nombres están en NFC.
    ruta = unicodedata.normalize("NFC", str(ruta).replace(chr(92), "/"))
    return f"http://127.0.0.1:{PUERTO_ARCHIVOS}/{quote(ruta)}"


st.set_page_config(page_title="Enunciados de Selectividad", page_icon="📚", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1400px;}
    header[data-testid="stHeader"] {background: transparent;}
    .cabecera {
        background: linear-gradient(120deg, #4F46E5 0%, #7C3AED 55%, #0EA5E9 100%);
        color: white; padding: 1.6rem 2rem; border-radius: 16px;
        box-shadow: 0 8px 24px rgba(79,70,229,.25); margin-bottom: 1.4rem;
    }
    .cabecera h1 {margin: 0; font-size: 2rem; font-weight: 700; color: white; padding: 0;}
    .cabecera p {margin: .3rem 0 0; opacity: .85; font-size: 1rem;}
    div[data-testid="stHorizontalBlock"]:has(div[data-baseweb="select"]) {
        background: white; padding: 1rem 1.2rem .6rem; border-radius: 14px;
        box-shadow: 0 2px 10px rgba(30,41,59,.08); margin-bottom: 1rem;
    }
    div[data-testid="stSelectbox"] label p {font-weight: 600; color: #475569; font-size: .85rem;}
    .contador {
        display: inline-block; background: #EEF2FF; color: #4338CA; font-weight: 600;
        padding: .3rem .9rem; border-radius: 999px; margin-bottom: .6rem; font-size: .9rem;
    }
    div[data-testid="stDataFrame"] {
        border-radius: 14px; overflow: hidden; box-shadow: 0 2px 10px rgba(30,41,59,.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
servidor_archivos()
if not servidor_sirve_raiz():
    st.warning(
        f"El puerto {PUERTO_ARCHIVOS} está ocupado por un servidor que no sirve `{RAIZ}`, "
        "así que los enlaces a PDF e imágenes no funcionarán. Cierra la otra sesión de Streamlit "
        "(o reinicia esta) y vuelve a cargar la página.",
        icon="⚠️",
    )
df = cargar()

st.markdown(
    '<div class="cabecera"><h1>📚 Enunciados de Selectividad</h1>'
    "<p>Busca por año, convocatoria, asignatura, tema y tipo de ejercicio, y abre el enunciado en imagen o PDF.</p></div>",
    unsafe_allow_html=True,
)


filtered_df = df.copy()
mask = pd.Series(True, index = filtered_df.index)

col1, col2, col3, col4 = st.columns([2 for _ in range(1,5)])

with col1:
    selected_year = st.selectbox(label = "Año",
                                 options = filtered_df["año"].unique(),
                                 key = "selected_year",
                                 index = None,
                                 placeholder= "Selecciona año")

    if selected_year:
        mask &= filtered_df.año == selected_year

with col2:
    selected_asignatura = st.selectbox(label = "Asignatura",
                                       options = filtered_df.loc[mask, "asignatura"].unique(),
                                       index = None,
                                       placeholder= "Selecciona asignatura",
                                       key = "selected_asignatura")

    if selected_asignatura:
            mask &= filtered_df.asignatura == selected_asignatura

with col3:
    temas = filtered_df.loc[mask, "tema"].unique()
    selected_tema = st.selectbox(label = "Tema",
                                 options = temas,
                                 index = None,
                                 placeholder= "Selecciona tema",
                                 disabled=selected_asignatura is None or all(pd.isna(temas)),
                                 key = "selected_tema")

    if selected_tema:
            mask &= filtered_df.tema == selected_tema

with col4:
    tipos_ejercicios = filtered_df.loc[mask, "tipo_ejercicio"].unique()
    selected_tipo_ejercicio = st.selectbox(label = "Tipo de ejercicio",
                                 options = filtered_df.loc[mask, "tipo_ejercicio"].unique(),
                                 index = None,
                                 placeholder= "Selecciona tipo de ejercicio",
                                 # desabilita elegir tipo de ejercicio
                                 # si no hay tema seleccionado o no hay tipos disponibles
                                 disabled=selected_tema is None or pd.isna(tipos_ejercicios)[0],
                                 key = "selected_tipo_ejercicio")
    
    if selected_tipo_ejercicio:
            mask &= filtered_df.tipo_ejercicio == selected_tipo_ejercicio

filtered_df = filtered_df[mask]

def exercise_name(row):
     return f"{row.año} - {row.convocatoria}, {row.ejercicio}"

filtered_df["nombre_ejercicio"] = filtered_df.apply(exercise_name, axis = 1)

salida = pd.DataFrame({
    "año": filtered_df["año"],
    "asignatura": filtered_df["asignatura"],
    "convocatoria": filtered_df["convocatoria"],
    "ejercicio": filtered_df["ejercicio"],
    "tema": filtered_df["tema"],
    "nombre_ejercicio" : filtered_df["nombre_ejercicio"],
    "tipo_ejercicio": filtered_df["tipo_ejercicio"],
    "observaciones": filtered_df["observaciones"],
    "archivo_pdf": filtered_df["archivo"].map(url),
    "enunciado_img": filtered_df["imagen"].map(url),
}).sort_values("año", ascending=False)

if salida["observaciones"].isna().all():
    salida = salida.drop(columns="observaciones")

with st.container(horizontal=True, horizontal_alignment="left", gap="small"):
    st.markdown(f'<span class="contador">{len(salida):,} enunciados</span>'.replace(",", "."), unsafe_allow_html=True)
    
    st.button(label = "Borrar filtro", on_click=borrar_filtro)
    
    st.download_button(
    "⬇️ Exportar a CSV",
    data=export_dataframe(salida).to_csv(index=False).encode("utf-8-sig"),
    file_name=f"ejercicios_{selected_asignatura}_filtrados_{datetime.date.today()}.csv",
    mime="text/csv",
    )

    st.download_button(
    "📄 Exportar a PDF",
    data=df_to_pdf(export_dataframe(salida)),
    file_name=f"ejercicios_{selected_asignatura}_filtrados_{datetime.date.today().strftime("%d-%m-%Y")}.pdf",
    mime="application/pdf",
    )

# ocultar asignatura, convocatoria, tema y ejercicio
cols_to_hide = ["asignatura", "convocatoria", "tema", "ejercicio"]
cols_to_show = [col for col in salida.columns if col not in cols_to_hide]

if any([selected_asignatura, selected_year]):
    st.dataframe(
        salida,
        column_order=cols_to_show,
        hide_index=True,
        width="stretch",
        column_config={
            "año": st.column_config.NumberColumn(label = "Año", format="%d"),
            "nombre_ejercicio": st.column_config.Column(label="Ejercicio"),
            "tipo_ejercicio": st.column_config.Column(label="Tipo de ejercicio"),
            "observaciones": st.column_config.Column(label="Comentario"),
            "archivo_pdf": st.column_config.LinkColumn("Soluciones", display_text="Abrir PDF"),
            "enunciado_img": st.column_config.LinkColumn("Enunciado", display_text="Abrir imagen"),
        },
    )
