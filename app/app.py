"""App local de consulta de enunciados. Ejecutar: streamlit run app/app.py"""
import functools
import http.server
import threading
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "csv_enunciados" / "enunciados_ejercicios_clean.csv"
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


@st.cache_data
def cargar():
    return pd.read_csv(CSV)


def url(ruta):
    if pd.isna(ruta):
        return None
    return f"http://127.0.0.1:{PUERTO_ARCHIVOS}/{quote(str(ruta).replace(chr(92), '/'))}"


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
df = cargar()

st.markdown(
    '<div class="cabecera"><h1>📚 Enunciados de Selectividad</h1>'
    "<p>Busca por año, convocatoria, asignatura y tema, y abre el enunciado en imagen o PDF.</p></div>",
    unsafe_allow_html=True,
)

filtros = [("año", "Año"), ("convocatoria", "Convocatoria"), ("asignatura", "Asignatura"), ("tema", "Tema")]


def filtrar(datos, excepto=None):
    for campo, _ in filtros:
        valor = st.session_state.get(campo, TODOS)
        if campo != excepto and valor != TODOS:
            datos = datos[datos[campo] == valor]
    return datos


def opciones_de(campo):
    return [TODOS] + sorted(filtrar(df, excepto=campo)[campo].dropna().unique().tolist())


# Cada desplegable solo ofrece valores compatibles con los demás filtros.
# Si una selección deja de ser válida se reinicia; se repite hasta estabilizar.
for _ in range(len(filtros)):
    cambio = False
    for campo, _etq in filtros:
        if st.session_state.get(campo, TODOS) not in opciones_de(campo):
            st.session_state[campo] = TODOS
            cambio = True
    if not cambio:
        break

columnas = st.columns(4)
for col, (campo, etiqueta) in zip(columnas, filtros):
    col.selectbox(etiqueta, opciones_de(campo), key=campo)

res = filtrar(df)

salida = pd.DataFrame({
    "año": res["año"],
    "asignatura": res["asignatura"],
    "convocatoria": res["convocatoria"],
    "ejercicio": res["ejercicio"],
    "tema": res["tema"],
    "archivo": res["archivo"].map(url),
    "imagen": res["imagen"].map(url),
}).sort_values(["año", "asignatura", "convocatoria", "ejercicio"], ascending=[False, True, True, True])

st.markdown(f'<span class="contador">{len(salida):,} enunciados</span>'.replace(",", "."), unsafe_allow_html=True)
st.dataframe(
    salida,
    hide_index=True,
    width="stretch",
    column_config={
        "año": st.column_config.NumberColumn("año", format="%d"),
        "archivo": st.column_config.LinkColumn("archivo", display_text="Abrir PDF"),
        "imagen": st.column_config.LinkColumn("imagen", display_text="Abrir imagen"),
    },
)
