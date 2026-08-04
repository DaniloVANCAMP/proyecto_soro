import streamlit as st
import time
import database as db  # Importamos nuestro nuevo motor de base de datos

def mostrar_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso a Smart Fitness</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # Columnas para centrar el formulario
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Pestañas de Acceso
        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Usuario Nuevo"])
        
        # --- PESTAÑA: INICIAR SESIÓN ---
        with tab_login:
            with st.form("form_login"):
                usuario = st.text_input("👤 Usuario", placeholder="ej. juan123")
                clave = st.text_input("🔑 Contraseña", type="password")
                submit = st.form_submit_button("Entrar", type="primary", use_container_width=True)
                
                if submit:
                    # Llama a database.py para verificar
                    user_id = db.verificar_usuario(usuario, clave)
                    
                    if user_id:
                        # ¡ÉXITO! Guardamos quién es el usuario en la memoria temporal
                        st.success("¡Acceso concedido! Entrando a tu perfil... 🏋️‍♂️")
                        st.session_state["logeado"] = True
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = usuario
                        time.sleep(1) # Pequeña pausa para que se vea el mensaje de éxito
                        st.rerun() # Esto recarga la página instantáneamente
                    else:
                        st.error("❌ Usuario o contraseña incorrectos.")
                        
        # --- PESTAÑA: CREAR USUARIO ---
        with tab_registro:
            with st.form("form_registro"):
                st.info("Crea tu cuenta para comenzar a registrar tus microdatos. 🧠")
                
                nuevo_usuario = st.text_input("👤 Nuevo Usuario (Alias)")
                correo = st.text_input("📧 Correo Electrónico", placeholder="ejemplo@correo.com")
                nueva_clave = st.text_input("🔑 Nueva Contraseña", type="password")
                confirmar_clave = st.text_input("🔑 Confirmar Contraseña", type="password")
                
                submit_reg = st.form_submit_button("Registrar", type="primary", use_container_width=True)
                
                if submit_reg:
                    # Validaciones estrictas
                    if len(nuevo_usuario) < 3 or len(nueva_clave) < 3:
                        st.warning("⚠️ El usuario y la contraseña deben tener al menos 3 caracteres.")
                    elif not correo or "@" not in correo:
                        st.warning("⚠️ Por favor, ingresa un correo electrónico válido.")
                    elif nueva_clave != confirmar_clave:
                        st.error("❌ Las contraseñas no coinciden. Inténtalo de nuevo.")
                    else:
                        # Llama a database.py para guardarlo
                        try:
                            # Intentamos mandar el correo también, asumiendo que db.crear_usuario fue actualizado
                            exito = db.crear_usuario(nuevo_usuario, nueva_clave, correo)
                        except TypeError:
                            # Fallback de seguridad por si tu database.py actual solo recibe 2 argumentos
                            exito = db.crear_usuario(nuevo_usuario, nueva_clave)

                        if exito:
                            st.success(f"✅ ¡Usuario '{nuevo_usuario}' creado! Ya puedes iniciar sesión en la pestaña de al lado.")
                        else:
                            st.error("⚠️ Ese nombre de usuario o correo ya está en uso. Elige otro.")