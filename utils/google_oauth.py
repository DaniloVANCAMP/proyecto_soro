import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json, os

# ---------------------------------------------------------------
# Función principal: conectar y devolver el servicio de Google Drive
# ---------------------------------------------------------------
def obtener_servicio_drive():
    try:
        # 1️⃣ Cargar la configuración del cliente desde Streamlit secrets
        client_config = st.secrets["web"]

        flow = Flow.from_client_config(
            {"web": client_config},
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        flow.redirect_uri = client_config["redirect_uris"][0]

     # 2️⃣ Si Google ya devolvió el token (en la URL)
        query_params = st.query_params
           if "code" in query_params:
                code = query_params["code"]
                flow.fetch_token(code=code)
                creds = flow.credentials
            
                # Guardar credenciales
                st.session_state["credentials"] = {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes,
                }
    
                st.success("✅ Autenticado con Google Drive correctamente.")
                st.query_params.clear()
                return build("drive", "v3", credentials=creds)
            
    
            # 3️⃣ Si ya tenemos credenciales en la sesión
            elif "credentials" in st.session_state:
                creds_data = st.session_state["credentials"]
                creds = Credentials(**creds_data)
                return build("drive", "v3", credentials=creds)

        # 4️⃣ Si no hay credenciales, generar el enlace de autorización
        else:
            auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
            st.markdown(f"🔗 [Haz clic aquí para autorizar Google Drive]({auth_url})")
            return None

    except Exception as e:
        st.error(f"⚠️ Error de autenticación: {e}")
        return None


