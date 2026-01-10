# utils/google_oauth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

def obtener_servicio_drive():
    """Autentica al usuario con OAuth 2.0 y devuelve el servicio de Google Drive"""
    try:
        # 1️⃣ Cargar configuración desde Secrets
        secrets = st.secrets["web"]
        client_config = {
            "web": {
                "client_id": secrets["client_id"],
                "project_id": secrets["project_id"],
                "auth_uri": secrets["auth_uri"],
                "token_uri": secrets["token_uri"],
                "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
                "client_secret": secrets["client_secret"],
                "redirect_uris": secrets["redirect_uris"],
                "javascript_origins": secrets["javascript_origins"]
            }
        }

        redirect_uri = st.secrets["server"]["redirect_uri"]

        # 2️⃣ Si ya hay credenciales, reutilízalas
        if "google_credentials" in st.session_state:
            creds = st.session_state.google_credentials
        else:
            flow = Flow.from_client_config(
                client_config,
                scopes=["https://www.googleapis.com/auth/drive.file"],
                redirect_uri=redirect_uri
            )

            # 3️⃣ URL para autorizar
            auth_url, _ = flow.authorization_url(prompt="consent")

            st.markdown(f"🔗 [Haz clic aquí para autorizar acceso a tu Google Drive]({auth_url})")

            auth_code = st.text_input("🔑 Pega aquí el código de autorización:")

            if auth_code:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                st.session_state.google_credentials = creds
                st.success("✅ Autenticación completada correctamente.")

        # 4️⃣ Crear servicio si ya hay credenciales
        if "google_credentials" in st.session_state:
            service = build("drive", "v3", credentials=st.session_state.google_credentials)
            return service

    except Exception as e:
        st.error(f"⚠️ Error de autenticación: {e}")
        return None


