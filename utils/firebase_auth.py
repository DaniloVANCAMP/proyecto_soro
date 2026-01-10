import streamlit as st
import requests
import urllib.parse
import firebase_admin
from firebase_admin import credentials, firestore

# -------------------------------------------------------
# 🔥 Inicializar Firebase (si no está inicializado)
# -------------------------------------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")  # tu clave privada JSON
    firebase_admin.initialize_app(cred)
db = firestore.client()

# -------------------------------------------------------
# Configuración base de OAuth
# -------------------------------------------------------
def get_config():
    return st.secrets["web"]

def get_redirect_uri():
    return st.secrets["server"]["redirect_uri"]

# -------------------------------------------------------
# A. URL PARA LOGIN
# -------------------------------------------------------
def get_login_url():
    params = {
        "client_id": get_config()["client_id"],
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": "email profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

# -------------------------------------------------------
# B. URL PARA VINCULAR DRIVE
# -------------------------------------------------------
def get_drive_connect_url():
    params = {
        "client_id": get_config()["client_id"],
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.file",
        "access_type": "offline",
        "prompt": "consent select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

# -------------------------------------------------------
# C. CANJEAR CÓDIGO (tokens)
# -------------------------------------------------------
def canjear_codigo(code):
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": get_config()["client_id"],
        "client_secret": get_config()["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": get_redirect_uri()
    }
    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        st.error(f"Error canjeando código: {response.text}")
        return None
    return response.json()

# -------------------------------------------------------
# D. INFO DEL USUARIO
# -------------------------------------------------------
def obtener_info_usuario(access_token):
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return None

# -------------------------------------------------------
# E. GUARDAR Y OBTENER USUARIO EN FIRESTORE
# -------------------------------------------------------
def guardar_usuario_db(data: dict):
    """Guarda o actualiza usuario en Firestore."""
    try:
        ref = db.collection("usuarios").document(data["email"])
        ref.set(data, merge=True)
        return True
    except Exception as e:
        st.error(f"Error guardando usuario: {e}")
        return False

def obtener_usuario_db(email: str):
    """Obtiene datos de un usuario desde Firestore."""
    try:
        ref = db.collection("usuarios").document(email)
        doc = ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Error obteniendo usuario: {e}")
        return None

# -------------------------------------------------------
# F. CERRAR SESIÓN
# -------------------------------------------------------
def cerrar_sesion():
    st.session_state.user = None
    if "drive_creds" in st.session_state:
        del st.session_state["drive_creds"]
    st.rerun()

