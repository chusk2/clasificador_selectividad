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
import hmac
import streamlit as st

# =============================================================================
# Configuración
# =============================================================================

# app/pages/classifier.py → .parent = app/pages → .parent.parent = app/
APP_DIR = Path(__file__).resolve().parent.parent

CSV_TO_CLASSIFY = APP_DIR / "csv" / "ejercicios_a_clasificar.csv"
CSV_CLASSIFIED  = APP_DIR / "csv" / "ejercicios_clasificados.csv"
STATIC_DIR      = APP_DIR / "static"

EXERCISES_PER_PAGE = 5

# Orden cronológico de las convocatorias dentro de un mismo año
ORDEN_CONVOCATORIAS = ["Junio", "Reserva 1", "Reserva 2", "Reserva 3",
                       "Reserva 4", "Julio", "Septiembre", "Modelo", "Ponencia"]

CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1400px;}
header[data-testid="stHeader"] {background: transparent;}
.cabecera {
    background: linear-gradient(120deg, #047857 0%, #0D9488 55%, #0891B2 100%);
    color: white; padding: 1.6rem 2rem; border-radius: 16px;
    box-shadow: 0 8px 24px rgba(4,120,87,.25); margin-bottom: 1.4rem;
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
    '<div class="cabecera"><h1>📚 Clasificador de ejercicios Selectividad</h1>'
    "<p>Clasifica los ejercicios de Selectividad Andalucía seleccionando opciones disponibles.</p></div>"
)

# =============================================================================
# Funciones
# =============================================================================


def check_password():
    """Devuelve True si el usuario ha metido la contraseña correcta."""

    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["passwd"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # no guardamos la contraseña
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Contraseña", type="password",
                  on_change=password_entered, key="password")

    # si existe la variable de sesión "password_correct" y es False, significa que la contraseña es incorrecta
    if "password_correct" in st.session_state:
        st.error("😕 Contraseña incorrecta")
    return False


def remove_accents(texto):
    """Clave de ordenación que ignora tildes y mayúsculas ("Física" ~ "fisica")."""
    t = unicodedata.normalize("NFD", str(texto))  # "í" -> "i" + tilde suelta
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")  # quita las tildes sueltas
    return t.casefold()


def normalizar(ruta):
    """Ruta del CSV tal como está en disco: con "/" y sin tildes (ñ -> n, ü -> u).

    En el servidor se quitaron las tildes de carpetas y archivos, así que se
    eliminan también aquí. A diferencia de remove_accents, respeta mayúsculas.
    """
    t = unicodedata.normalize("NFD", str(ruta).replace("\\", "/"))
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def url(ruta):
    """URL servida por Streamlit (static serving) de un archivo del CSV (None si no hay)."""
    return None if pd.isna(ruta) else f"/app/static/{quote(normalizar(ruta))}"


def ruta_local(ruta):
    """Ruta en disco de un archivo del CSV (None si no hay)."""
    return None if pd.isna(ruta) else STATIC_DIR / normalizar(ruta)


def shorten_exercise_name(row):
    """Nombre del ejercicio para la tabla, p. ej. "2026 - Junio, Ejercicio A1"."""
    return f"{row.año} - {row.convocatoria}, {row.ejercicio}"


def generate_full_exercise_name(row):
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
def get_exercise_types(csv):
    """Devuelve un DataFrame con los tipos de ejercicio de cada asignatura y tema."""
    df = pd.read_csv(csv, dtype={"asignatura": "string",
                                 "tema": "string",
                                 "tipo_ejercicio": "string"})
    
    return df[["asignatura", "tema", "tipo_ejercicio"]].drop_duplicates()
    

def load_exercises_to_classify():
    # La fecha de modificación forma parte de la clave de caché: si el CSV se edita
    # fuera de la app, se vuelve a leer en lugar de usar datos obsoletos
    return _load_exercises_to_classify(CSV_TO_CLASSIFY.stat().st_mtime)


@st.cache_data
def _load_exercises_to_classify(mtime):
    df = pd.read_csv(CSV_TO_CLASSIFY, dtype={"tipo_ejercicio": "string",
                                   "observaciones": "string"})
    # crear las columnas tipo_ejercicio y observaciones solo si no existen
    # (si se sobrescribieran, los ejercicios ya clasificados volverían a aparecer como pendientes)
    for col in ("tipo_ejercicio", "observaciones"):
        if col not in df.columns:
            df[col] = pd.NA
    # convertir a string para que Streamlit no las infiera como float64 (NaN)
    df = df.astype({"tipo_ejercicio": "string", "observaciones": "string"})
    
    return df

# =============================================================================
# Estado de sesión y callbacks
# =============================================================================

def init_session_state():
    st.session_state.setdefault("page_table", 0)


def advance_page(delta):
    """Avanza (delta=1) o retrocede (delta=-1) una página de la tabla."""
    st.session_state.page_table += delta


def reset_filters():
    """Vuelve todos los filtros a su valor inicial."""
    st.session_state["year_selector"] = "Todos"
    st.session_state["asignatura_selector"] = None
    st.session_state["tema_selector"] = None


# =============================================================================
# Interfaz
# =============================================================================

def render_filters(remaining_to_classify_df):  # ejercicios pendientes de clasificar
    """Dibuja los filtros (año, asignatura, tema) y devuelve la máscara y lo elegido.

    Cada selector solo ofrece las opciones compatibles con los filtros anteriores.
    """
    mask = pd.Series(True, index=remaining_to_classify_df.index)
    selected_year = None

    with st.container(horizontal=True, horizontal_alignment="center", gap="medium"):
            
        years = sorted(remaining_to_classify_df["año"].unique(), reverse=True)
        
        selected_year = st.selectbox(
            label="Año",
            options=["Todos"] + [str(y) for y in years],
            index=0,
            placeholder="Selecciona año",
            key="year_selector",
        )

        if selected_year and selected_year != "Todos":
            mask &= remaining_to_classify_df.año == int(selected_year)

        # --- Asignatura
        asignaturas = sorted(remaining_to_classify_df.loc[mask, "asignatura"].unique(),
                             key=remove_accents)  # eliminar acentos para ordenar alfabéticamente
        
        selected_asignatura = st.selectbox(
            label="Asignatura",
            options=asignaturas,
            index=None,
            placeholder="Selecciona asignatura",
            key="asignatura_selector",
        )

        if selected_asignatura:
            mask &= remaining_to_classify_df.asignatura == selected_asignatura

        if selected_asignatura:
            # --- Tema (solo disponible tras elegir asignatura)
            temas = sorted(remaining_to_classify_df.loc[mask, "tema"].dropna().unique(), key=remove_accents)

            selected_tema = st.selectbox(
                label="Tema",
                options=temas,
                index=None,
                placeholder="Selecciona tema",
                disabled=selected_asignatura is None or len(temas) == 0,
                key="tema_selector",
            )
        else:
            selected_tema = None
        if selected_tema:
            mask &= remaining_to_classify_df.tema == selected_tema

    filters = (selected_year, selected_asignatura, selected_tema)
    return mask, filters



    # # dataframe filtered_df: año, asignatura, convocatoria, tema, nombre ejercicio cortoTabla a mostrar: columnas ordenada por año y convocatoria."""
    # return pd.DataFrame({
    #     "año": filtered_df["año"],
    #     "asignatura": filtered_df["asignatura"],
    #     "convocatoria": filtered_df["convocatoria"],
    #     "tema": filtered_df["tema"],
    #     # esta columna se genera a partir del dataframe filtrado
    #     "nombre_corto_ejercicio" : filtered_df.apply(shorten_exercise_name, axis=1),
    # }).sort_values(["año", "convocatoria"], ascending=[False, True],
    #                # orden personalizado de convocatorias dentro de un mismo año
    #                key=clave_orden({"convocatoria": ORDEN_CONVOCATORIAS}))


def reset_page_if_filters_changed(filters):
    """Vuelve a la primera página si ha cambiado la combinación de filtros."""
    if st.session_state.get("applied_filters") != filters:
        st.session_state.applied_filters = filters
        st.session_state.page_table = 0


def render_exercises_pager(filtered_df):
    """Muestra la página actual del pager del dataframe para clasificar. Devuelve las filas visibles del pager."""
    # filtered_df columns:
        # "id", "asignatura", "asignatura_carpeta",
        # "año", "convocatoria", "ejercicio", "tema",
        # "info_ejercicio", "enunciado",
        # "archivo", "imagen", "tipo_ejercicio", "observaciones"
    
    cols_to_show = ["año", "asignatura", "convocatoria", "ejercicio", "archivo_pdf", "enunciado_img"]
    # Página actual (se acota por si los filtros han reducido el número de filas)
    total = len(filtered_df)
    max_page = max(0, (total - 1) // EXERCISES_PER_PAGE)
    page = min(st.session_state.page_table, max_page)
    st.session_state.page_table = page
    start = page * EXERCISES_PER_PAGE
    current_rows = filtered_df.iloc[start : start + EXERCISES_PER_PAGE]
    current_rows["exercise_name"] = current_rows.apply(lambda row: " - ".join([str(row["año"]), row["convocatoria"], row["ejercicio"]]), axis=1)
    current_rows["asignatura_tema"] = current_rows.apply(lambda row: " - ".join([str(row["asignatura"]), row["tema"]]), axis=1)
    # URLs servidas por Streamlit para los enlaces de la tabla
    current_rows["archivo_url"] = current_rows["archivo"].map(url)
    current_rows["imagen_url"] = current_rows["imagen"].map(url)

    st.dataframe(
        current_rows,
        column_order=["asignatura_tema", "exercise_name", "archivo","archivo_url", "imagen_url"],
        hide_index=True,
        width="stretch",
        column_config={
            "asignatura_tema": st.column_config.Column(label="Asignatura - Tema"),
            "exercise_name": st.column_config.Column(label="Ejercicio"),
            "archivo": st.column_config.Column(label="Archivo PDF"),
            "archivo_url": st.column_config.LinkColumn("Soluciones", display_text="Abrir PDF"),
            "imagen_url": st.column_config.LinkColumn("Enunciado", display_text="Abrir imagen"),
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


def save_classification(exercise_id, tema, tipos, observaciones):
    """Escribe la clasificación en el CSV y recarga la app."""
    df = pd.read_csv(CSV_TO_CLASSIFY,
                     dtype={"tipo_ejercicio": "object", "observaciones": "string"})
    # se identifica por "id" (único); "ejercicio" ("Ejercicio A1"...) se repite entre asignaturas/años
    mask = df["id"] == exercise_id

    # tipos es una lista (multiselect) o un string (text_input), pero en el CSV se guarda como string
    if isinstance(tipos, list):
        tipos = [t.strip() for t in tipos if t.strip()]

    idx = df.loc[mask].index[0]
    # asignar los valores a las filas del ejercicio (puede haber varios tipos de ejercicio)
    df.at[idx, "tipo_ejercicio"] = tipos
    df.loc[mask, ["tema", "observaciones"]] = [tema, observaciones]

    df = df.explode("tipo_ejercicio", ignore_index=True)
    
    df.to_csv(CSV_TO_CLASSIFY, index=False, encoding="utf-8")

    # Invalida la caché para que la próxima ejecución lea el CSV actualizado
    _load_exercises_to_classify.clear()

    # Resetea el ejercicio y las observaciones para el siguiente: al cambiar la key,
    # Streamlit crea widgets nuevos (un simple pop no siempre limpia lo que muestra el navegador)
    st.session_state.form_id = st.session_state.get("form_id", 0) + 1
    st.session_state.classification_saved = True
    st.rerun()


def render_classification_widgets(filtered_df, exercise_types, subject):
    """Formulario para asignar tema, tipo de ejercicio y observaciones a un ejercicio."""
    df_to_classify = filtered_df.copy()
    df_to_classify["long_exercise_name"] = df_to_classify.apply(generate_full_exercise_name, axis=1)

    # valores por defecto: así existen aunque no se dibujen sus widgets
    tema = None
    tipo = []

    form_id = st.session_state.get("form_id", 0)
    long_names = dict(zip(df_to_classify["id"], df_to_classify["long_exercise_name"]))

    # Las opciones son los id de los ejercicios pendientes (ya filtrados por tema); se muestra el nombre largo
    selected_exercise = st.selectbox(label="Ejercicio",
                                     options=list(long_names),
                                     #format_func=long_names.get,
                                     index=0,
                                     key=f"ejercicio_selectbox_{form_id}",
                                     )

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):

        # Tema: los definidos en tipos_ejercicios.csv para la asignatura;
        # si no hay ninguno se mantiene el tema del filtro
        temas = sorted(exercise_types.loc[exercise_types.asignatura == subject, "tema"].unique())
        if temas:
            tema = st.selectbox(label="Tema", options=temas, index=None, key="tema_selectbox")

        # Tipo de ejercicio: se elige de los existentes o se escribe uno nuevo
        if tema:
            tipos = exercise_types.loc[(exercise_types.asignatura == subject) &
                                       (exercise_types.tema == tema), "tipo_ejercicio"].dropna().to_list()
            if len(tipos) > 0:
                tipo = st.multiselect(label="Tipo de ejercicio", options=tipos, default=None,
                                      key="tipo_selectbox")

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):

        # añadir nuevo tipo de ejercicio (si no está en la lista)
        if st.toggle(label="Añadir un nuevo tipo de ejercicio", key="add_new_exercise_type"):

            texto = st.text_input(label="Nuevo tipo de ejercicio",
                                  placeholder="tipos separados por comas",
                                  key="new_exercise_type_text_input")

            # varios tipos nuevos separados por comas (se descartan los vacíos)
            nuevos = [t.strip() for t in texto.split(",") if t.strip()]
            tipo = tipo + nuevos   # lista nueva: si no escribes nada, se conserva lo elegido

    with st.container(horizontal=True, vertical_alignment="center", gap="small"):
        observaciones = st.text_input(label="Observaciones",
                                      placeholder="añade una observación sobre el ejercicio",
                                      key=f"observations_text_input_{form_id}")

        # guardar la clasificación en el CSV (solo si hay ejercicio seleccionado y tipo de ejercicio indicado)
        if st.button("Guardar clasificación", key="save_classification"):
            if selected_exercise is None:
                st.warning("No hay ejercicios pendientes de clasificar")
            elif not tipo:
                st.warning("Indica el tipo de ejercicio")
            else:
                save_classification(selected_exercise, tema, tipo, observaciones)

        # El aviso se muestra tras el rerun (si se mostrase antes, se perdería)
        if st.session_state.pop("classification_saved", False):
            st.toast("Archivo clasificado con éxito")


    # show exercise image
    idx = df_to_classify[df_to_classify["id"] == selected_exercise].index[0]
    render_exercise_image(df_to_classify, idx)


def render_exercise_image(df, idx):
    """Muestra la imagen del enunciado del ejercicio a clasificar (`idx` = índice de `df`)."""
    with st.container(border=True):
        st.subheader(df.loc[idx, "long_exercise_name"])
        img_path = ruta_local(df.loc[idx, "imagen"])

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
    
    # A partir de aquí, solo lo ve quien ha entrado
    st.title("Zona privada")
    
    if not check_password():
        st.stop()
    
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(CABECERA, unsafe_allow_html=True)
    init_session_state()

    df = load_exercises_to_classify()
    df_tipos = get_exercise_types(CSV_CLASSIFIED)

    # Solo interesan los ejercicios que aún no tienen tipo asignado
    remaining_exercises_to_classify = df[df.tipo_ejercicio.isna()]

    # save filters selection to mask
    mask, filters = render_filters(remaining_exercises_to_classify)

    # save selected options from filters
    selected_year, selected_asignatura, selected_tema = filters

    # filter the dataframe with the selected options
    filtered_df = remaining_exercises_to_classify[mask].copy()

    reset_page_if_filters_changed(filters=filters)

    
    st.button(label="Borrar filtro", on_click=reset_filters)

    # El resto de la app solo se muestra con año (o rango) y asignatura elegidos
    if not (selected_year and selected_asignatura):
        return

    current_rows = render_exercises_pager(filtered_df)

    # Para clasificar hace falta haber elegido un tema en los filtros
    if selected_tema:
        render_classification_widgets(current_rows, df_tipos, selected_asignatura)

    if st.button("Guardar clasificaciones"):
        # dataframe con los ejercicios clasificados en la sesión actual (los que tienen tipo_ejercicio no nulo)
        new_classified_df = pd.read_csv(CSV_TO_CLASSIFY, encoding="utf-8")
        new_classified_df = new_classified_df[new_classified_df.tipo_ejercicio.notna()]

        # ejercicios ya clasificados (CSV_CLASSIFIED)
        classified_df = pd.read_csv(CSV_CLASSIFIED, encoding="utf-8")

        # combinar los ya clasificados con los nuevos y guardar en CSV_CLASSIFIED
        combined_df = pd.concat([new_classified_df, classified_df], ignore_index=True)
        combined_df.to_csv(CSV_CLASSIFIED, index=False, encoding="utf-8")
        
        st.toast("Clasificaciones exportadas con éxito a ejercicios_clasificados.csv")

main()
