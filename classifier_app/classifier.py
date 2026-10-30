"""Clasificador de ejercicios de Selectividad Andalucía.

App de Streamlit para asignar un tipo de ejercicio (y observaciones opcionales)
a los enunciados del CSV que todavía no están clasificados.

Ejecutar desde la carpeta classifier_app (las rutas son relativas):
    streamlit run classifier.py
"""
import unicodedata
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st

# =============================================================================
# Configuración
# =============================================================================

CSV = Path("./csv/ejercicios_a_clasificar.csv")
TIPOS_EJERCICIOS = Path("./csv/tipos_ejercicios.csv")
STATIC_DIR = Path("./static")

EXERCISES_PER_PAGE = 5

# Orden cronológico de las convocatorias dentro de un mismo año
ORDEN_CONVOCATORIAS = ["Junio", "Reserva 1", "Reserva 2", "Reserva 3",
                       "Reserva 4", "Julio", "Septiembre", "Modelo", "Ponencia"]

CSS = """
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
"""

CABECERA = (
    '<div class="cabecera"><h1>📚 Ejercicios de Selectividad Andalucía</h1>'
    "<p>Filtra por año, asignatura, tema y tipo de ejercicio, y abre la imagen del enunciado.</p></div>"
)


# =============================================================================
# Utilidades
# =============================================================================

def remove_accents(texto):
    """Clave de ordenación que ignora tildes y mayúsculas ("Física" ~ "fisica")."""
    t = unicodedata.normalize("NFD", str(texto))  # "í" -> "i" + tilde suelta
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")  # quita las tildes sueltas
    return t.casefold()


def normalizar(ruta):
    """Normaliza una ruta del CSV para que coincida con el nombre en disco.

    Las rutas del CSV vienen de macOS (NFD) y en disco los nombres están en NFC.
    """
    return unicodedata.normalize("NFC", str(ruta).replace("\\", "/"))


def url(ruta):
    """URL servida por Streamlit (static serving) de un archivo del CSV (None si no hay)."""
    return None if pd.isna(ruta) else f"/app/static/{quote(normalizar(ruta))}"


def ruta_local(ruta):
    """Ruta en disco de un archivo del CSV (None si no hay)."""
    return None if pd.isna(ruta) else STATIC_DIR / normalizar(ruta)


def nombre_corto(row):
    """Nombre del ejercicio para la tabla, p. ej. "2026 - Junio, Ejercicio A1"."""
    return f"{row.año} - {row.convocatoria}, {row.ejercicio}"


def nombre_completo(row):
    """Nombre del ejercicio para el selector de clasificación."""
    columnas = ["año", "asignatura", "tema", "convocatoria", "ejercicio"]
    return " - ".join(str(row[col]) for col in columnas)


def clave_orden(ordenes):
    """Devuelve una función `key` para `sort_values` con órdenes personalizados.

    ordenes: diccionario {columna: lista con el orden deseado}. Los valores que
    no estén en la lista van al final; el resto de columnas se ordena normal.
    """
    posiciones = {col: {v: i for i, v in enumerate(lista)}
                  for col, lista in ordenes.items()}

    def key(s):
        if s.name in posiciones:
            return s.map(posiciones[s.name]).fillna(len(posiciones[s.name]))
        return s
    return key


# =============================================================================
# Carga de datos
# =============================================================================

@st.cache_data
def load_exercises():
    return pd.read_csv(CSV, dtype={"tipo_ejercicio": "string",
                                   "observaciones": "string"})


@st.cache_data
def load_exercise_types():
    return pd.read_csv(TIPOS_EJERCICIOS)


# =============================================================================
# Estado de sesión y callbacks
# =============================================================================

def init_session_state():
    st.session_state.setdefault("use_year_range", False)
    st.session_state.setdefault("page_table", 0)


def advance_page(delta):
    """Avanza (delta=1) o retrocede (delta=-1) una página de la tabla."""
    st.session_state.page_table += delta


def borrar_filtro():
    """Vuelve todos los filtros a su valor inicial."""
    st.session_state["year_selector"] = "Todos"
    st.session_state["asignatura_selector"] = None
    st.session_state["tema_selector"] = None
    st.session_state["use_year_range"] = False
    st.session_state.pop("year_slider", None)


# =============================================================================
# Interfaz
# =============================================================================

def render_filtros(pendientes):
    """Dibuja los filtros (año, asignatura, tema) y devuelve la máscara y lo elegido.

    Cada selector solo ofrece las opciones compatibles con los filtros anteriores.
    """
    mask = pd.Series(True, index=pendientes.index)
    selected_year = selected_min_year = selected_max_year = None

    with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):

        # --- Año: selector único o rango (según el toggle "Usar rango de años")
        with st.container(horizontal=False, vertical_alignment="center", gap="small"):
            years = sorted(pendientes["año"].unique(), reverse=True)

            if st.session_state.use_year_range:
                selected_min_year, selected_max_year = st.slider(
                    label="Rango de años",
                    min_value=min(years),
                    max_value=max(years),
                    value=(min(years), max(years)),
                    key="year_slider",
                )
            else:
                selected_year = st.selectbox(
                    label="Año",
                    options=["Todos"] + [str(y) for y in years],
                    index=0,
                    placeholder="Selecciona año",
                    key="year_selector",
                )

        if selected_year and selected_year != "Todos":
            mask &= pendientes.año == int(selected_year)
        elif selected_min_year and selected_max_year:
            mask &= pendientes.año.between(selected_min_year, selected_max_year)

        # --- Asignatura
        asignaturas = sorted(pendientes.loc[mask, "asignatura"].unique(), key=remove_accents)
        selected_asignatura = st.selectbox(
            label="Asignatura",
            options=asignaturas,
            index=None,
            placeholder="Selecciona asignatura",
            key="asignatura_selector",
        )
        if selected_asignatura:
            mask &= pendientes.asignatura == selected_asignatura

        # --- Tema (solo disponible tras elegir asignatura)
        temas = sorted(pendientes.loc[mask, "tema"].dropna().unique(), key=remove_accents)
        selected_tema = st.selectbox(
            label="Tema",
            options=temas,
            index=None,
            placeholder="Selecciona tema",
            disabled=selected_asignatura is None or len(temas) == 0,
            key="tema_selector",
        )
        if selected_tema:
            mask &= pendientes.tema == selected_tema

    filtros = (selected_year, selected_min_year, selected_max_year,
               selected_asignatura, selected_tema)
    return mask, filtros


def build_output_df(filtered_df):
    """Tabla a mostrar: columnas útiles + enlaces, ordenada por año y convocatoria."""
    return pd.DataFrame({
        "año": filtered_df["año"],
        "asignatura": filtered_df["asignatura"],
        "convocatoria": filtered_df["convocatoria"],
        "ejercicio": filtered_df["ejercicio"],
        "tema": filtered_df["tema"],
        "nombre_ejercicio": filtered_df["nombre_ejercicio"],
        "archivo_pdf": filtered_df["archivo"].map(url),
        "enunciado_img": filtered_df["imagen"].map(url),
    }).sort_values(["año", "convocatoria"], ascending=[False, True],
                   key=clave_orden({"convocatoria": ORDEN_CONVOCATORIAS}))


def reset_page_if_filters_changed(filtros):
    """Vuelve a la primera página si ha cambiado la combinación de filtros."""
    if st.session_state.get("applied_filters") != filtros:
        st.session_state.applied_filters = filtros
        st.session_state.page_table = 0


def render_tabla(output_df):
    """Muestra la página actual de la tabla con su paginación. Devuelve las filas visibles."""
    cols_to_hide = ["asignatura", "convocatoria", "ejercicio", "archivo_pdf"]
    cols_to_show = [col for col in output_df.columns if col not in cols_to_hide]

    # Página actual (se acota por si los filtros han reducido el número de filas)
    total = len(output_df)
    max_page = max(0, (total - 1) // EXERCISES_PER_PAGE)
    page = min(st.session_state.page_table, max_page)
    st.session_state.page_table = page
    start = page * EXERCISES_PER_PAGE
    current_rows = output_df.iloc[start : start + EXERCISES_PER_PAGE]

    st.dataframe(
        current_rows,
        column_order=cols_to_show,
        hide_index=True,
        width="stretch",
        column_config={
            "año": st.column_config.NumberColumn(label="Año", format="%d"),
            "nombre_ejercicio": st.column_config.Column(label="Ejercicio"),
            "archivo_pdf": st.column_config.LinkColumn("Soluciones", display_text="Abrir PDF"),
            "enunciado_img": st.column_config.LinkColumn("Enunciado", display_text="Abrir imagen"),
        },
    )

    if total:
        count_metric, prev, info, nxt = st.columns(4, vertical_alignment="center")
        # separador de miles con punto (formato español)
        count_metric.markdown(f'<span class="contador">{total:,} enunciados</span>'.replace(",", "."),
                              unsafe_allow_html=True)
        prev.button("Anterior", on_click=advance_page, args=(-1,),
                    disabled=page == 0, width="stretch")
        info.caption(
            f"Ejercicios {start + 1} al {start + len(current_rows)} de un total de {total}"
            f" · página {page + 1} / {max_page + 1}"
        )
        nxt.button("Siguiente", on_click=advance_page, args=(1,),
                   disabled=page >= max_page, width="stretch")

    return current_rows


def render_clasificacion(df, df_tipos, filtered_df, asignatura, tema):
    """Formulario para asignar tema, tipo de ejercicio y observaciones a un ejercicio."""
    df_classify = filtered_df.copy()
    df_classify["exercise_name"] = df_classify.apply(nombre_completo, axis=1)

    # Las opciones son los índices de `df`; el nombre solo se usa para mostrarlo
    selected_exercise = st.selectbox(
        label="Ejercicio",
        options=df_classify.index,
        format_func=lambda i: df_classify.loc[i, "exercise_name"],
        index=0,
        key="ejercicio_selectbox",
    )

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):

        # Tema: los definidos en tipos_ejercicios.csv para la asignatura;
        # si no hay ninguno se mantiene el tema del filtro
        temas = sorted(df_tipos.loc[df_tipos.asignatura == asignatura, "tema"].unique())
        if temas:
            tema = st.selectbox(label="Tema", options=temas, index=0, key="tema_selectbox")

        # Tipo de ejercicio: se elige de los existentes o se escribe uno nuevo
        tipos = df_tipos.loc[(df_tipos.asignatura == asignatura) &
                             (df_tipos.tema == tema.lower()), "tipo_ejercicio"].to_list()
        if tipos:
            tipo = st.selectbox(label="tipo_ejercicio", options=tipos, index=0,
                                key="tipo_selectbox")
        else:
            tipo = st.text_input(label="Nuevo tipo ejercicio",
                                 placeholder="escribe el tipo de ejercicio",
                                 key="new_exercise_type_text_input")

        observaciones = st.text_input(label="Observaciones",
                                      placeholder="añade una observación sobre el ejercicio",
                                      key="observations_text_input")

        if st.button("Guardar clasificación", key="save_classification"):
            if selected_exercise is None:
                st.warning("No hay ejercicios pendientes de clasificar")
            elif not tipo:
                st.warning("Indica el tipo de ejercicio")
            else:
                guardar_clasificacion(df, selected_exercise, tema, tipo, observaciones)

        # El aviso se muestra tras el rerun (si se mostrase antes, se perdería)
        if st.session_state.pop("classification_saved", False):
            st.toast("Archivo clasificado con éxito")


def guardar_clasificacion(df, idx, tema, tipo, observaciones):
    """Escribe la clasificación en el CSV y recarga la app."""
    df.loc[idx, ["tema", "tipo_ejercicio", "observaciones"]] = [tema, tipo, observaciones]
    df.to_csv(CSV, index=False, encoding="utf-8")
    # Invalida la caché para que la próxima ejecución lea el CSV actualizado
    load_exercises.clear()
    # Resetea el ejercicio y las observaciones para el siguiente
    st.session_state.pop("ejercicio_selectbox", None)
    st.session_state.pop("observations_text_input", None)
    st.session_state.classification_saved = True
    st.rerun()


def render_imagenes(current_rows, filtered_df):
    """Muestra las imágenes de los enunciados de la página actual (sin repetir)."""
    with st.container(border=True):
        for idx, row in current_rows.drop_duplicates("enunciado_img").iterrows():
            st.subheader(row["nombre_ejercicio"])
            img_path = ruta_local(filtered_df.loc[idx, "imagen"])

            if img_path is None:
                st.info("Este ejercicio no tiene imagen de enunciado.")
            elif img_path.exists():
                st.image(str(img_path), width="stretch")
            else:
                st.warning(f"No encuentro la imagen: {img_path.name}")


# =============================================================================
# App
# =============================================================================

def main():
    st.set_page_config(page_title="Clasificador de ejercicios de Selectividad Andalucía",
                       page_icon="📚", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(CABECERA, unsafe_allow_html=True)
    init_session_state()

    df = load_exercises()
    df_tipos = load_exercise_types()

    # Solo interesan los ejercicios que aún no tienen tipo asignado
    pendientes = df[df.tipo_ejercicio.isna()]

    mask, filtros = render_filtros(pendientes)
    selected_year, selected_min_year, _, selected_asignatura, selected_tema = filtros

    filtered_df = pendientes[mask].copy()
    filtered_df["nombre_ejercicio"] = filtered_df.apply(nombre_corto, axis=1)
    output_df = build_output_df(filtered_df)

    reset_page_if_filters_changed(filtros)

    with st.container(horizontal=True, vertical_alignment="center", gap="large"):
        st.toggle(label="Usar rango de años", key="use_year_range")
        st.button(label="Borrar filtro", on_click=borrar_filtro)

    # El resto de la app solo se muestra con año (o rango) y asignatura elegidos
    if not ((selected_year or selected_min_year) and selected_asignatura):
        return

    current_rows = render_tabla(output_df)
    st.toggle("Ver enunciados", key="show_exercises")

    # Para clasificar hace falta haber elegido un tema en los filtros
    if selected_tema:
        render_clasificacion(df, df_tipos, filtered_df, selected_asignatura, selected_tema)

    if st.session_state.get("show_exercises"):
        render_imagenes(current_rows, filtered_df)


main()
