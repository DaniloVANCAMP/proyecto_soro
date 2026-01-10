# utils/google_oauth.py
import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import pickle

# Ruta del archivo de credenciales descargado desde Google Cloud Console
CLIENT_SECRET_FILE = "utils/client_secret_2_1081866191988-8kd49ft1ejgrc4ukomqb1vrs6o84e0p2.apps.googleusercontent.com.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def obtener_servicio_drive():
    """Autentica al usuario con OAuth y devuelve el servicio de Google Drive"""
    try:
        # Si ya hay credenciales guardadas en sesión, reutilízalas
        if "google_credentials" in st.session_state:
            creds = st.session_state.google_credentials
        else:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=SCOPES,
                redirect_uri="https://proyectosoro-greluzdxmhpwwzsvnxzuxp.streamlit.app"  # cambia esto si estás en la nube
            )

            auth_url, _ = flow.authorization_url(prompt="consent")

            st.markdown(
                f"🔗 [Haz clic aquí para autorizar acceso a Google Drive]({auth_url})"
            )

            # Esperar a que el usuario pegue el código de autorización
            auth_code = st.text_input("🔑 Ingresa el código de autorización de Google:")

            if auth_code:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                st.session_state.google_credentials = creds
                st.success("✅ Autenticación completada correctamente.")

        # Si ya tenemos credenciales, construimos el servicio
        if "google_credentials" in st.session_state:
            service = build("drive", "v3", credentials=st.session_state.google_credentials)
            return service

    except Exception as e:
        st.error(f"⚠️ Error de autenticación: {e}")
        return None

