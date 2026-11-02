"""App local de consulta de enunciados. Ejecutar: streamlit run app/app.py"""

import streamlit as st


home  = st.Page("pages/list_exercises.py",  title="Inicio",  icon="🏠", default=True)
classifier  = st.Page("pages/classifier.py",  title="Clasificador",  icon="⚛️")

# navigation panel
nav = st.navigation([home, classifier], expanded=False)
st.set_page_config(page_title="Clasificador", layout="wide")

# al salir del clasificador se vuelve a bloquear: pedirá la contraseña al volver
if nav.url_path != classifier.url_path:
    st.session_state.pop("password_correct", None)

nav.run()