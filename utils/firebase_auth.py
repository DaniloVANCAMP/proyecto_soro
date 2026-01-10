import streamlit as st
import pyrebase

# -------------------------------------------------------
# Inicializa Firebase con la configuración del secrets
# -------------------------------------------------------
def inicializar_firebase():
    firebase_config = st.secrets["firebase"]
    firebase = pyrebase.initialize_app(firebase_config)
    return firebase.auth()


# -------------------------------------------------------
# Autenticación con Google (OAuth vía Firebase)
# -------------------------------------------------------
def login_con_google():
    auth = inicializar_firebase()

    # Firebase maneja la autenticación de Google
    provider = "google.com"
    redirect_url = st.secrets["firebase"]["authDomain"]

    # URL para redirigir al login de Google
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={st.secrets['firebase']['apiKey']}&"
        f"redirect_uri=https://{redirect_url}/__/auth/handler&"
        f"response_type=token&"
        f"scope=email%20profile"
    )

    st.markdown(f"### 🔗 [Iniciar sesión con Google]({auth_url})")


# -------------------------------------------------------
# Guardar usuario autenticado en sesión
# -------------------------------------------------------
def guardar_usuario(datos_usuario):
    st.session_state.user = {
        "email": datos_usuario.get("email"),
        "nombre": datos_usuario.get("displayName", "Usuario"),
        "uid": datos_usuario.get("localId"),
    }


# -------------------------------------------------------
# Cerrar sesión
# -------------------------------------------------------
def cerrar_sesion():
    st.session_state.user = None
    st.success("👋 Sesión cerrada correctamente.")
