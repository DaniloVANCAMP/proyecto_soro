import streamlit as st

# Lista de correos autorizados
CORREOS_AUTORIZADOS = [
    "tuemail1@gmail.com",
    "ingenieria@constructora.com",
    "gerente@constructora.com"
]

def login_screen():
    st.markdown("""
        <style>
            body {
                background-color: #f0f2f6;
            }
            .login-box {
                background-color: rgba(255, 255, 255, 0.95);
                padding: 2rem 3rem;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 400px;
                margin: auto;
                margin-top: 12%;
            }
            .title {
                font-size: 1.5rem;
                font-weight: 700;
                color: #003366;
                margin-bottom: 1rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Fondo (GIF animado)
    st.markdown(f"""
        <style>
        .stApp {{
            background: url("app/static/fondo.gif");
            background-size: cover;
        }}
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<div class='title'>🏗️ Control de Obra</div>", unsafe_allow_html=True)
        email = st.text_input("Correo electrónico autorizado")
        btn = st.button("Iniciar sesión", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if btn:
        if email.lower() in CORREOS_AUTORIZADOS:
            st.session_state["usuario"] = email
            st.rerun()
        else:
            st.error("❌ Correo no autorizado. Contacta al administrador.")


def cerrar_sesion():
    if "usuario" in st.session_state:
        del st.session_state["usuario"]
        st.success("Has cerrado sesión correctamente.")
        st.rerun()
