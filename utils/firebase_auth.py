import streamlit as st
import pyrebase

# -------------------------------------------------------
# Inicializa Firebase con la configuración del secrets
# -------------------------------------------------------
def inicializar_firebase():
    firebase_config = dict(st.secrets["firebase"])  # 🔹 Crea copia editable

    # Evita error si falta databaseURL
    if "databaseURL" not in firebase_config:
        firebase_config["databaseURL"] = ""

    firebase = pyrebase.initialize_app(firebase_config)
    return firebase.auth()

# -------------------------------------------------------
# Iniciar sesión con correo/contraseña
# -------------------------------------------------------
def login_con_correo(email, password):
    auth = inicializar_firebase()
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        guardar_usuario(user)
        return True
    except Exception as e:
        st.error("❌ Error al iniciar sesión. Verifica tus credenciales.")
        st.write(e)
        return False

# -------------------------------------------------------
# Crear nuevo usuario
# -------------------------------------------------------
def registrar_usuario(email, password):
    auth = inicializar_firebase()
    try:
        auth.create_user_with_email_and_password(email, password)
        return True, "✅ Usuario registrado correctamente."
    except Exception as e:
        if "EMAIL_EXISTS" in str(e):
            return False, "⚠️ El correo ya está registrado."
        else:
            st.write(e)
            return False, "❌ Error al registrar usuario."

# -------------------------------------------------------
# Guardar usuario autenticado en sesión
# -------------------------------------------------------
def guardar_usuario(datos_usuario):
    st.session_state.user = {
        "email": datos_usuario.get("email"),
        "idToken": datos_usuario.get("idToken"),
        "refreshToken": datos_usuario.get("refreshToken"),
    }

# -------------------------------------------------------
# Cerrar sesión
# -------------------------------------------------------
def cerrar_sesion():
    st.session_state.user = None
    st.success("👋 Sesión cerrada correctamente.")
