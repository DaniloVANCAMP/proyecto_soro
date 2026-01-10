import streamlit as st
import requests
import urllib.parse

# -------------------------------------------------------
# 1. Generar el Link de Login (Sin intermediarios)
# -------------------------------------------------------
def login_con_google():
    # Datos de configuración
    client_id = st.secrets["web"]["client_id"]
    # Usamos la dirección de tu app como destino
    redirect_uri = st.secrets["server"]["redirect_uri"]
    
    # Construimos la URL de Google
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    
    st.markdown(f"""
        <div style="text-align: center; margin-top: 20px;">
            <a href="{auth_url}" target="_self" style="
                background-color: #ffffff; 
                color: #333; 
                padding: 12px 25px; 
                text-decoration: none; 
                border-radius: 5px; 
                border: 1px solid #ddd; 
                font-family: sans-serif; 
                font-weight: bold;
                display: inline-flex;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" 
                     style="width: 20px; margin-right: 10px;">
                Iniciar sesión con Google
            </a>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------
# 2. Canjear el código por los datos del usuario
# -------------------------------------------------------
def intercambiar_codigo_por_usuario(code):
    # Datos para el canje
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": st.secrets["web"]["client_id"],
        "client_secret": st.secrets["web"]["client_secret"],
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": st.secrets["server"]["redirect_uri"]
    }
    
    # A. Pedir el Token
    res_token = requests.post(token_url, data=payload)
    if res_token.status_code != 200:
        st.error(f"Error obteniendo token: {res_token.text}")
        return None
        
    tokens = res_token.json()
    access_token = tokens.get("access_token")
    
    # B. Pedir los datos del usuario con ese Token
    user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    res_user = requests.get(user_info_url, headers=headers)
    
    if res_user.status_code != 200:
        st.error("Error obteniendo datos del usuario")
        return None
        
    return res_user.json()  # Devuelve {email: ..., name: ..., picture: ...}

def cerrar_sesion():
    st.session_state.user = None
    st.success("👋 Sesión cerrada")
