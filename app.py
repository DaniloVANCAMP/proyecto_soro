import json
import os
import sys
import streamlit as st
import database as db  # <-- IMPORTAMOS LA BASE DE DATOS AQUÍ

# 1. ESTO DEBE SER OBLIGATORIAMENTE LO PRIMERO DE STREAMLIT
st.set_page_config(
    page_title="Fitness & Nutrición App", page_icon="🏋️‍♂️", layout="wide", initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS PREMIUM PARA EL SIDEBAR ---
st.markdown("""
<style>
/* Estilo general del fondo del menú lateral */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important; /* Fondo ultra oscuro */
}

/* Título del Sidebar */
[data-testid="stSidebar"] h1 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin-bottom: 0px !important;
    padding-bottom: 5px !important;
    border-bottom: 2px solid #e74c3c; /* Línea roja imponente */
}

/* Subtítulo (Caption) */
[data-testid="stSidebar"] .stMarkdown p {
    color: #aaaaaa !important;
    margin-bottom: 15px;
}

/* 1. Ocultar los círculos feos nativos de los Radio Buttons */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > div[role="radio"] > div:first-child {
    display: none !important;
}

/* 2. Convertir las opciones del menú en botones premium */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    background-color: #1a1c24 !important;
    border: 1px solid #2d303e !important;
    border-radius: 8px !important;
    padding: 12px 15px !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

/* 3. Efecto al pasar el mouse (Hover) */
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background-color: #242733 !important;
    border-color: #e74c3c !important;
    border-left: 5px solid #e74c3c !important; /* Marca visual roja a la izquierda */
    transform: translateX(3px); /* Pequeño salto a la derecha */
}

/* 4. Botón de cerrar sesión (Estilo outline rojo) */
[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    border: 1px solid #e74c3c !important;
    color: #e74c3c !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #e74c3c !important;
    color: #ffffff !important;
    box-shadow: 0px 4px 10px rgba(231, 76, 60, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from views import (
    login,
    registro,
    tab_1_perfil,
    tab_2_catalogo,
    tab_3_generador,
    tab_4_bitacora,
    tab_5_nutricion
)

BASE_MEDIA_URL = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/"

@st.cache_data
def load_exercises():
    ruta_raiz = os.path.join(ROOT_DIR, "exercises.json")
    if not os.path.exists(ruta_raiz):
        datos_base = [
            {"name": "Press de banca plano", "category": "Pecho", "equipment": "Barra", "target": "Pectorales", "gif_url": "", "instructions": []},
        ]
        with open(ruta_raiz, "w", encoding="utf-8") as f:
            json.dump(datos_base, f, ensure_ascii=False, indent=4)
    with open(ruta_raiz, "r", encoding="utf-8") as f:
        return json.load(f)

def check_perfil():
    """Busca el perfil EN LA BASE DE DATOS usando el ID del usuario"""
    user_id = st.session_state.get("user_id")
    if user_id:
        return db.obtener_perfil(user_id)
    return None

def main():
    # 2. SALVAVIDAS ANTI-F5 (Login)
    if "user_id" in st.query_params:
        st.session_state["logeado"] = True
        st.session_state["user_id"] = st.query_params["user_id"]
        st.session_state["username"] = st.query_params.get("username", "Usuario")

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

    if "historial_bitacora" not in st.session_state:
        st.session_state["historial_bitacora"] = []

    perfil = check_perfil()

    if perfil is None:
        st.warning("⚠️ No tienes un perfil activo. Por favor, completa tus datos para comenzar.")
        registro.mostrar()
    else:
        usuario_actual = st.session_state.get("username", "Usuario")
        
        st.sidebar.title(f"🏋️ Smart Fitness de {usuario_actual}")
        st.sidebar.caption("Plataforma Integral de Entrenamiento")

        # 3. SALVAVIDAS DE NAVEGACIÓN (F5 para el menú)
        opciones_menu = [
            "👤 Mi Perfil y Entorno", 
            "🏋️ Rutinas y Catálogo", 
            "🍏 Nutrición y Suplementación", 
            "📝 Bitácora Diaria"
        ]
        
        menu_guardado = st.query_params.get("menu", opciones_menu[0])
        idx_menu = opciones_menu.index(menu_guardado) if menu_guardado in opciones_menu else 0

        # Ocultamos la etiqueta del menú porque el diseño ya habla por sí solo
        menu = st.sidebar.radio("Navegación", opciones_menu, index=idx_menu, label_visibility="collapsed")

        # --- NAVEGACIÓN LIMPIA SIN REEJECUCIÓN DUPLICADA ---
        if st.query_params.get("menu") != menu:
            st.query_params["menu"] = menu
            st.rerun()

        # --- ENRUTAMIENTO DIRECTO ---
        if menu == "👤 Mi Perfil y Entorno":
            tab_1_perfil.mostrar(exercises)
        elif menu == "🏋️ Rutinas y Catálogo":
            tab_2_catalogo.mostrar(exercises, BASE_MEDIA_URL)
        elif menu == "🍏 Nutrición y Suplementación":
            tab_5_nutricion.mostrar()
        elif menu == "📝 Bitácora Diaria":
            tab_4_bitacora.mostrar()

        st.sidebar.divider()
        
        # 4. CERRAR SESIÓN
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.query_params.clear()
            st.rerun()

if __name__ == "__main__":
    main()