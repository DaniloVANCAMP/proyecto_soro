import json
import os
import sys
import streamlit as st
import database as db

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from views import (
    login,
    registro,
    tab_1_perfil,
    tab_2_catalogo,
    tab_4_bitacora,
    tab_5_nutricion
)

st.set_page_config(page_title="Fitness & Nutrición App", page_icon="🏋️‍♂️", layout="wide")
BASE_MEDIA_URL = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/"

@st.cache_data
def load_exercises():
    ruta_raiz = os.path.join(ROOT_DIR, "exercises.json")
    if not os.path.exists(ruta_raiz):
        datos_base = [{"name": "Press de banca plano", "category": "Pecho", "equipment": "Barra", "target": "Pectorales", "gif_url": "", "instructions": []}]
        with open(ruta_raiz, "w", encoding="utf-8") as f:
            json.dump(datos_base, f, ensure_ascii=False, indent=4)
    with open(ruta_raiz, "r", encoding="utf-8") as f:
        return json.load(f)

def check_perfil():
    user_id = st.session_state.get("user_id")
    if user_id:
        return db.obtener_perfil(user_id)
    return None

def main():
    if "logeado" not in st.session_state:
        st.session_state["logeado"] = False

    if not st.session_state["logeado"]:
        login.mostrar_login()
        return  
    
    try:
        exercises = load_exercises()
    except Exception as e:
        st.error(f"Error crítico irrecuperable: {e}")
        st.stop()

    perfil = check_perfil()

    if perfil is None:
        st.warning("⚠️ No tienes un perfil activo. Por favor, completa tus datos para comenzar.")
        registro.mostrar()
    else:
        usuario_actual = st.session_state.get("username", "Usuario")
        
        st.sidebar.title(f"🏋️ Smart Fitness de {usuario_actual}")
        st.sidebar.caption("Plataforma Integral de Entrenamiento")

        menu = st.sidebar.radio(
            "Menú Principal",
            ["👤 Mi Perfil y Entorno", "🏋️ Centro de Entrenamiento", "🍏 Nutrición y Suplementación", "📝 Bitácora Diaria", "⚙️ Editar Perfil"],
        )

        if menu == "👤 Mi Perfil y Entorno":
            tab_1_perfil.mostrar(exercises)
        elif menu == "🏋️ Centro de Entrenamiento":
            tab_2_catalogo.mostrar(exercises, BASE_MEDIA_URL)
        elif menu == "🍏 Nutrición y Suplementación":
            tab_5_nutricion.mostrar()
        elif menu == "📝 Bitácora Diaria":
            tab_4_bitacora.mostrar()
        elif menu == "⚙️ Editar Perfil":
            registro.mostrar()

        st.sidebar.divider()
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()