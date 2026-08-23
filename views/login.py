import streamlit as st
import time
import database as db

def mostrar_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso a Smart Fitness</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Usuario Nuevo"])
        
        # --- PESTAÑA: INICIAR SESIÓN ---
        with tab_login:
            with st.form("form_login"):
                correo = st.text_input("📧 Correo Electrónico o Usuario", placeholder="ejemplo@correo.com")
                clave = st.text_input("🔑 Contraseña", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
                    user_id, username = db.verificar_usuario(correo, clave)
                    
                    if user_id:
                        st.success("¡Acceso concedido! Entrando a tu perfil... 🏋️‍♂️")
                        # 1. Guardar en memoria de sesión
                        st.session_state["logeado"] = True
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = username
                        
                        # 2. PERSISTENCIA: Guardar en la URL para sobrevivir al F5
                        st.query_params["user_id"] = str(user_id)
                        st.query_params["username"] = str(username)
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Correo o contraseña incorrectos.")
                        
        # --- PESTAÑA: CREAR USUARIO ---
        with tab_registro:
            with st.form("form_registro"):
                st.info("Crea tu cuenta para comenzar a registrar tus microdatos. 🧠")
                
                nuevo_usuario = st.text_input("👤 Nuevo Usuario (Alias)")
                correo_reg = st.text_input("📧 Correo Electrónico", placeholder="ejemplo@correo.com")
                nueva_clave = st.text_input("🔑 Nueva Contraseña", type="password")
                confirmar_clave = st.text_input("🔑 Confirmar Contraseña", type="password")
                
                submit_reg = st.form_submit_button("Registrar", type="primary", use_container_width=True)
                
                if submit_reg:
                    if len(nuevo_usuario) < 3 or len(nueva_clave) < 3:
                        st.warning("⚠️ El usuario y la contraseña deben tener al menos 3 caracteres.")
                    elif not correo_reg or "@" not in correo_reg:
                        st.warning("⚠️ Por favor, ingresa un correo electrónico válido.")
                    elif nueva_clave != confirmar_clave:
                        st.error("❌ Las contraseñas no coinciden. Inténtalo de nuevo.")
                    else:
                        exito = db.crear_usuario(nuevo_usuario, nueva_clave, correo_reg)
                        if exito:
                            st.success(f"✅ ¡Usuario '{nuevo_usuario}' creado! Ya puedes iniciar sesión en la pestaña de al lado.")
                        else:
                            st.error("⚠️ Ese nombre de usuario o correo ya está en uso. Elige otro.")