import streamlit as st
import pyrebase

# -------------------------------------------------------
# Inicializa Firebase con la configuración del secrets
# -------------------------------------------------------
def inicializar_firebase():
    # Carga la configuración desde secrets
    firebase_config = dict(st.secrets["firebase"])
    
    # Pyrebase a veces necesita que databaseURL exista, aunque sea vacía
    if "databaseURL" not in firebase_config:
        firebase_config["databaseURL"] = ""

    firebase = pyrebase.initialize_app(firebase_config)
    return firebase.auth()

# -------------------------------------------------------
# Autenticación con Google (OAuth vía Firebase)
# -------------------------------------------------------
def login_con_google():
    try:
        auth = inicializar_firebase()
    except Exception as e:
        st.error(f"Error inicializando Firebase: {e}")
        return

    # TU CLIENT ID REAL (El que termina en apps.googleusercontent.com)
    # Lo ponemos directo aquí para evitar errores de lectura en secrets
    CLIENT_ID = "1081866191988-8kd49ft1ejgrc4ukomqb1vrs6o84e0p2.apps.googleusercontent.com"

    # URL de redirección (Intenta leerla de secrets, si falla usa localhost)
    try:
        redirect_url = st.secrets["firebase"]["authDomain"]
    except:
        redirect_url = "localhost:8501"

    # Construimos la URL oficial de Google
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri=https://{redirect_url}/__/auth/handler&"
        f"response_type=token&"
        f"scope=email%20profile"
    )

    st.markdown(f"### 🔗 [Iniciar sesión con Google]({auth_url})")

# -------------------------------------------------------
# Cerrar sesión
# -------------------------------------------------------
def cerrar_sesion():
    st.session_state.user = None
    if "credentials" in st.session_state:
        del st.session_state["credentials"]
    st.success("👋 Sesión cerrada correctamente.")
