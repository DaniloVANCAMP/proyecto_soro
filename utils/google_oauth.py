import os
import pickle
import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ===============================================================
# CONFIGURACIÓN
# ===============================================================

# 👇 CAMBIA ESTA RUTA según dónde guardaste tu archivo JSON
CLIENT_SECRET_FILE = "utils/client_secret_2_1081866191988-8kd49ft1ejgrc4ukomqb1vrs6o84e0p2.apps.googleusercontent.com.json"


# Permisos para acceder al Google Drive del usuario
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Archivo donde se guardan los tokens de sesión del usuario
TOKEN_FILE = "token_drive_user.pkl"

# ===============================================================
# FUNCIÓN PARA OBTENER SERVICIO DE GOOGLE DRIVE
# ===============================================================

def obtener_servicio_drive():
    """Autentica al usuario y devuelve el servicio de Google Drive."""
    creds = None

    # Verificar si ya existe un token guardado
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, ejecutar el flujo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                # 🔐 Crear flujo OAuth con el archivo de credenciales
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)

                # Si estás en la nube (Streamlit Cloud)
                if "streamlit.app" in st.server.server_address[0]:
                    creds = flow.run_local_server(port=8501)
                else:
                    creds = flow.run_local_server(port=0)

            except Exception as e:
                st.error(f"⚠️ Error de autenticación: {e}")
                return None

        # Guardar credenciales para futuras sesiones
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    # Crear el servicio de Google Drive
    try:
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Google Drive: {e}")
        return None

