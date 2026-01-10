# utils/google_oauth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pickle
import os

CLIENT_SECRETS_FILE = "utils/client_secret.json"  # usa el nombre real del tuyo si no lo renombraste
SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/spreadsheets"]
TOKEN_DIR = "tokens"

if not os.path.exists(TOKEN_DIR):
    os.makedirs(TOKEN_DIR)

def obtener_servicio_drive():
    """Devuelve un cliente autenticado de Google Drive para el usuario actual."""
    if "user" not in st.session_state or not st.session_state.user:
        st.error("⚠️ Debes iniciar sesión primero.")
        st.stop()

    user = st.session_state.user
    token_path = os.path.join(TOKEN_DIR, f"{user}.pkl")

    # Si ya existe el token
    if os.path.exists(token_path):
        creds = pickle.load(open(token_path, "rb"))
        if creds and creds.valid:
            return build("drive", "v3", credentials=creds)

    # Si no existe, iniciar flujo OAuth
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501"
    )

    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"### 🔗 [Haz clic aquí para autorizar tu Google Drive]({auth_url})")
    st.info("Una vez autorices, copia la URL final del navegador y pégala aquí abajo:")
    code_url = st.text_input("🔑 Pega aquí la URL completa después de autorizar:")

    if code_url:
        flow.fetch_token(authorization_response=code_url)
        creds = flow.credentials
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
        st.success("✅ Autorizado correctamente. Vuelve a presionar el botón para conectar.")
        st.stop()

    return None
