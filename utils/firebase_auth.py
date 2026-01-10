import streamlit as st
import requests
import urllib.parse

# Configuración base
def get_config():
    return st.secrets["web"]

def get_redirect_uri():
    return st.secrets["server"]["redirect_uri"]

# -------------------------------------------------------
# A. URL PARA SOLO ENTRAR (Login Básico)
# -------------------------------------------------------
def get_login_url():
    params = {
        "client_id": get_config()["client_id"],
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": "email profile",  # SOLO pedimos identidad
        "access_type": "online",
        "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

# -------------------------------------------------------
# B. URL PARA VINCULAR DRIVE (Permisos extra)
# -------------------------------------------------------
def get_drive_connect_url():
    params = {
        "client_id": get_config()["client_id"],
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/drive.file", # Pedimos DRIVE
        "access_type": "offline", # Importante para poder usarlo después
        "prompt": "consent select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

# -------------------------------------------------------
# C. CANJEAR CÓDIGO (Sirve para ambos casos)
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
# D. OBTENER INFO DEL USUARIO
# -------------------------------------------------------
def obtener_info_usuario(access_token):
    url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    return None

def cerrar_sesion():
    st.session_state.user = None
    if "drive_creds" in st.session_state:
        del st.session_state["drive_creds"]
    st.rerun()

