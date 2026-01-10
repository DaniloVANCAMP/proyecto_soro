import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

def obtener_servicio_drive():
    try:
        # 1️⃣ Configuración desde secrets.toml
        client_config = {"web": st.secrets["web"]}
        redirect_uri = st.secrets["web"]["redirect_uris"][0]

        flow = Flow.from_client_config(
            client_config,
            scopes=["https://www.googleapis.com/auth/drive.file"]
        )
        flow.redirect_uri = redirect_uri

        # 2️⃣ Verificar si Google devolvió el código en la URL
        query_params = st.experimental_get_query_params()
        if "code" in query_params:
            code = query_params["code"][0]
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Guardamos las credenciales en la sesión
            st.session_state["drive_credentials"] = {
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
            }

            st.success("✅ Google Drive conectado exitosamente.")
            st.experimental_set_query_params()  # Limpia la URL
            return build("drive", "v3", credentials=creds)

        # 3️⃣ Si ya tenemos credenciales en la sesión, reconstruirlas
        elif "drive_credentials" in st.session_state:
            creds_data = st.session_state["drive_credentials"]
            creds = Credentials(**creds_data)
            return build("drive", "v3", credentials=creds)

        # 4️⃣ Si no hay conexión previa, mostrar botón de autorización
        else:
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                prompt="consent"
            )
            st.markdown(f"🔗 [Haz clic aquí para autorizar Google Drive]({auth_url})")
            return None

    except Exception as e:
        st.error(f"⚠️ Error de autenticación: {e}")
        return None

