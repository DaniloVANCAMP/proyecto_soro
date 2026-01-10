import streamlit as st
import requests
import urllib.parse
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# -------------------------------------------------------
# CONFIGURACIÓN BÁSICA
# -------------------------------------------------------
def get_config():
    return st.secrets["web"]

def get_redirect_uri():
    # Redirección definida en Streamlit Cloud (debe estar en Google Cloud Console)
    return st.secrets["server"]["redirect_uri"]

# -------------------------------------------------------
# A. GENERAR URL DE AUTORIZACIÓN (Drive)
# -------------------------------------------------------
def get_drive_auth_url():
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
# B. CANJEAR CÓDIGO POR TOKEN
# -------------------------------------------------------
def exchange_code_for_token(code):
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
# C. CREAR SERVICIO DE GOOGLE DRIVE
# -------------------------------------------------------
def obtener_servicio_drive():
    query_params = st.query_params
    creds = None

    try:
        # 1️⃣ Si ya se devolvió el código en la URL
        if "code" in query_params:
            code = query_params["code"]
            token_data = exchange_code_for_token(code)
            if token_data:
                creds = Credentials(
                    token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=get_config()["client_id"],
                    client_secret=get_config()["client_secret"],
                    scopes=["https://www.googleapis.com/auth/drive.file"]
                )
                st.session_state["drive_creds"] = token_data
                st.query_params.clear()
                st.success("✅ Conectado correctamente con Google Drive")

        # 2️⃣ Si ya existen credenciales guardadas
        elif "drive_creds" in st.session_state:
            token_data = st.session_state["drive_creds"]
            creds = Credentials(
                token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=get_config()["client_id"],
                client_secret=get_config()["client_secret"],
                scopes=["https://www.googleapis.com/auth/drive.file"]
            )

        # 3️⃣ Si no hay nada aún, mostrar el enlace de autorización
        else:
            auth_url = get_drive_auth_url()
            st.markdown(f"🔗 [Autoriza acceso a Google Drive]({auth_url})")
            return None

        # 4️⃣ Retornar el servicio si hay credenciales
        if creds:
            return build("drive", "v3", credentials=creds)

    except Exception as e:
        st.error(f"⚠️ Error conectando con Google Drive: {e}")
        return None


