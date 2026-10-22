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
#PUERTO_ARCHIVOS = 8599
PUERTO_ARCHIVOS = 8501
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

def ordenar_personalizado(lista, lista_ordenada):
    """Primero los de la lista, en ese orden; el resto, al final y alfabético."""
    return sorted(lista,
                  key=lambda valor: (lista_ordenada.index(valor) if valor in lista_ordenada else len(lista_ordenada),
                                     str(valor))
                                     )

@st.cache_data
def cargar():
    return pd.read_csv(CSV)

# inicializar widget selector año
# if "dropdown_year" not in st.session_state:
#     st.session_state.dropdown_year = ""
if "use_year_range" not in st.session_state:
    st.session_state.use_year_range = False

if "all_years" not in st.session_state:
    st.session_state.all_years = False

# ejercicios por página
EXERCISES_PER_PAGE = 5
if "page_table" not in st.session_state:
    st.session_state.page_table = 0

# pasar página de dataframe
def advance_page(delta):
    st.session_state.page_table += delta

def borrar_filtro():
    for filtro in ["year_selector", "asignatura_selector",
                   "tema_selector", "tipo_ejercicio_selector"]:
        st.session_state[filtro] = None
    st.session_state["year_selector"] = "Todos"
    st.session_state.pop("year_slider", None)
    st.session_state["use_year_range"] = False

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

def ruta_local(ruta):
    """Ruta absoluta en disco de un archivo del CSV (None si no hay)."""
    if pd.isna(ruta):
        return None
    ruta = unicodedata.normalize("NFC", str(ruta).replace(chr(92), "/"))
    return RAIZ / ruta

st.set_page_config(page_title="Ejercicios de Selectividad Andalucía", page_icon="📚", layout="wide")
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
    '<div class="cabecera"><h1>📚 Ejercicios de Selectividad Andalucía</h1>'
    "<p>Filtra por año, asignatura, tema y tipo de ejercicio, y abre la imagen del enunciado.</p></div>",
    unsafe_allow_html=True,
)


filtered_df = df.copy()
mask = pd.Series(True, index = filtered_df.index)
# definir valores del rango de año
selected_min_year, selected_max_year = None, None

with st.container(horizontal = True, horizontal_alignment = "center", gap = "medium"):

    with st.container(horizontal=False, vertical_alignment="center", gap = "small"):
        years = sorted(filtered_df.loc[mask, "año"].unique(), reverse=True)
        selected_year, selected_min_year, selected_max_year = None, None, None        


        if st.session_state.use_year_range:
            selected_min_year, selected_max_year = st.slider(
                            label = "Rango de años",
                            min_value=min(years),
                            max_value=max(years),
                            value = (min(years), max(years)),
                            key = "year_slider"
                            )
        # selección año
        else:
            years_selectbox = ["Todos"] + [str(i) for i in years]
            selected_year = st.selectbox(label = "Año",
                                        options = years_selectbox,
                                        index = 0,
                                        placeholder= "Selecciona año",
                                        key = "year_selector")
                

    if selected_year and selected_year != "Todos":
        selected_year = int(selected_year)
        mask &= filtered_df.año == selected_year
    elif selected_min_year and selected_max_year:
        mask &= filtered_df.año.between(selected_min_year, selected_max_year)

    # selección asignatura
    asignaturas = sorted(filtered_df.loc[mask, "asignatura"].unique())
    selected_asignatura = st.selectbox(label = "Asignatura",
                                       options = asignaturas,
                                       index = None,
                                       placeholder= "Selecciona asignatura",
                                       key = "asignatura_selector")

    if selected_asignatura:
            mask &= filtered_df.asignatura == selected_asignatura

    # selección tema
    temas = sorted(filtered_df.loc[mask, "tema"].dropna().unique())
    selected_tema = st.selectbox(label = "Tema",
                                 options = temas,
                                 index = None,
                                 placeholder= "Selecciona tema",
                                 disabled=selected_asignatura is None or len(temas) == 0,
                                 key = "tema_selector")

    if selected_tema:
            mask &= filtered_df.tema == selected_tema

    # seleccionar tipo de ejercicio
    def remove_accents(texto):
        t = unicodedata.normalize("NFD", str(texto))  # "í" -> "i" + tilde suelta
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")  # quita las tildes sueltas
        return t.casefold()  # ignora mayúsculas

    tipos_ejercicios = sorted(filtered_df.loc[mask, "tipo_ejercicio"].dropna().unique(),
                              key=remove_accents)
    selected_tipo_ejercicio = st.selectbox(label = "Tipo de ejercicio",
                                 options = tipos_ejercicios,
                                 index = None,
                                 placeholder= "Selecciona tipo de ejercicio",
                                 # desabilita elegir tipo de ejercicio
                                 # si no hay tema seleccionado o no hay tipos disponibles
                                 disabled=selected_tema is None or len(tipos_ejercicios) == 0,
                                 key = "tipo_ejercicio_selector")
    
    if selected_tipo_ejercicio:
            mask &= filtered_df.tipo_ejercicio == selected_tipo_ejercicio

filtered_df = filtered_df[mask].copy()

def exercise_name(row):
     return f"{row.año} - {row.convocatoria}, {row.ejercicio}"

filtered_df["nombre_ejercicio"] = filtered_df.apply(exercise_name, axis = 1)

# ordenar por convocatoria
convocatorias_ordenadas = {"convocatoria": ["Junio",
                           "Reserva 1", "Reserva 2",
                           "Reserva 3", "Reserva 4",
                           "Julio", "Septiembre",
                           "Modelo", "Ponencia"]
}

def clave_orden(ordenes):
    """ordenes: diccionario {columna: lista con el orden deseado}."""
    posiciones = {col: {v: i for i, v in enumerate(lista)}
                  for col, lista in ordenes.items()}

    def key(s):
        if s.name in posiciones:
            return s.map(posiciones[s.name]).fillna(len(posiciones[s.name]))
        return s          # las demás columnas se ordenan de forma normal
    return key

output_df = pd.DataFrame({
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
}).sort_values(["año", "convocatoria"], ascending=[False, True],
               key = clave_orden(convocatorias_ordenadas)
)

if output_df["observaciones"].isna().all():
    output_df.drop(columns="observaciones", inplace = True)

# combinación de filtros
applied_filters = (selected_year, selected_min_year, selected_max_year,
selected_asignatura, selected_tema, selected_tipo_ejercicio)

# si se han cambiado los filtros, resetea la paginación del df
if st.session_state.get("applied_filters") != applied_filters:
    st.session_state.applied_filters = applied_filters
    st.session_state.page_table = 0


# condición para comprobar si hay filtros aplicados
filter_exists = (selected_year or selected_min_year) and selected_asignatura

with st.container(horizontal=True, vertical_alignment="center", gap = "large"):
    st.toggle(label = "Usar rango de años", key = "use_year_range")
    st.button(label = "Borrar filtro", on_click=borrar_filtro)
    
# mostrar dataframe solo si hay un año y asignatura seleccionados
if filter_exists:
    # ocultar asignatura, convocatoria, tema y ejercicio
    cols_to_hide = ["asignatura", "convocatoria", "ejercicio"]
    cols_to_show = [col for col in output_df.columns if col not in cols_to_hide]

    # cálculo del número de páginas del dataframe
    total = len(output_df)
    max_page = max(0, (total - 1) // EXERCISES_PER_PAGE)
    page = min(st.session_state.page_table, max_page)
    st.session_state.page_table = page
    # cada valor de page supone EXERCISES_PER_PAGE ejercicios (filas)
    start_page = page * EXERCISES_PER_PAGE
    current_rows = output_df.iloc[start_page : start_page + EXERCISES_PER_PAGE]
    
    st.dataframe(
        current_rows,
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
        }
    )

    if total:
        count_metric, prev, info, nxt = st.columns([1, 1, 1, 1], vertical_alignment="center")

        count_metric.markdown(f'<span class="contador">{len(output_df):,} enunciados</span>'.replace(",", "."), unsafe_allow_html=True)
        
        prev.button("Anterior", on_click=advance_page, args=(-1,),
                    disabled = page == 0, width="stretch")
        
        info.caption(
            f"Ejercicios {start_page + 1} al {start_page + len(current_rows)} de un total de {total}"
            f" · página {page + 1} / {max_page + 1}"
            )
        
        nxt.button("Siguiente", on_click=advance_page, args=(1,),
                   disabled = page >= max_page, width="stretch")

    # mostrar borrar filtros y opciones de exportación
    # solo si hay un año y asignatura seleccionados
    with st.container(horizontal = True, vertical_alignment= "center", gap = "small"):
        # fecha actual para añadir a nombre archivo
        today_date = datetime.date.today().strftime("%d-%m-%Y")
        st.toggle("Ver enunciados", key="show_exercises")
                
        st.download_button(
        "⬇️ Exportar a CSV",
        data=export_dataframe(output_df).to_csv(index=False).encode("utf-8-sig"),
        file_name=f"ejercicios_{selected_asignatura}_filtrados_{today_date}.csv",
        mime="text/csv",
        )

        st.download_button(
        "📄 Exportar a PDF",
        data=df_to_pdf(export_dataframe(output_df)),
        file_name=f"ejercicios_{selected_asignatura}_filtrados_{today_date}.pdf",
        mime="application/pdf",
        )
        
    if st.session_state.get("show_exercises"):
        with st.container(border=True):
            for idx, row in current_rows.iterrows():
                st.subheader(row["nombre_ejercicio"])
                img_path = ruta_local(filtered_df.loc[idx, "imagen"])
                
                if img_path is None:
                    st.info("Este ejercicio no tiene imagen de enunciado.")
                elif img_path.exists():
                    st.image(str(img_path), width="stretch")
                else:
                    st.warning(f"No encuentro la imagen: {img_path.name}")
