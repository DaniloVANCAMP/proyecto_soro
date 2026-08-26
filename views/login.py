import streamlit as st
import time
import datetime
import database as db

def mostrar_login(cookie_manager=None):
    # --- CSS ESTILIZADO, SERIO Y PROFESIONAL ---
    st.markdown("""
    <style>
    .login-title {
        font-size: clamp(2.2rem, 6vw, 3rem);
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-bottom: 5px;
        line-height: 1.1;
    }
    .login-subtitle {
        font-size: clamp(0.9rem, 3vw, 1.1rem);
        font-weight: 600;
        color: #2ecc71; /* Verde Neón */
        text-align: center;
        margin-bottom: 25px;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .login-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #e74c3c, transparent); /* Degradado rojo */
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- ENCABEZADO ---
    st.markdown("<div class='login-title'>Smart Fitness</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-subtitle'>Acceso al Sistema</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-divider'></div>", unsafe_allow_html=True)
    
    # Centrar el cuadro de login usando columnas (1/4 - 2/4 - 1/4)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Envolvemos todo en un contenedor para que parezca una tarjeta de acceso
        with st.container(border=True):
            tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "📝 Crear Usuario Nuevo"])
            
            # ==========================================
            # PESTAÑA: INICIAR SESIÓN
            # ==========================================
            with tab_login:
                with st.form("form_login", border=False):
                    st.markdown("<h4 style='color: #ffffff; margin-bottom: 15px;'>Bienvenido de vuelta</h4>", unsafe_allow_html=True)
                    
                    correo = st.text_input("Correo Electrónico o Usuario", placeholder="ejemplo@correo.com")
                    clave = st.text_input("Contraseña", type="password")
                    
                    submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)
                    
                    if submit:
                        user_id, username = db.verificar_usuario(correo, clave)
                        
                        if user_id:
                            st.success("✅ Acceso autorizado. Cargando tu entorno...")
                            
                            # 1. COOKIES: Guardar por 30 días para sobrevivir al cierre de app
                            if cookie_manager:
                                exp_date = datetime.datetime.now() + datetime.timedelta(days=30)
                                cookie_manager.set("user_id", str(user_id), expires_at=exp_date)
                                cookie_manager.set("username", str(username), expires_at=exp_date)

                            # 2. Memoria de sesión tradicional
                            st.session_state["logeado"] = True
                            st.session_state["user_id"] = user_id
                            st.session_state["username"] = username
                            
                            # 3. Guardar en la URL como respaldo
                            st.query_params["user_id"] = str(user_id)
                            st.query_params["username"] = str(username)
                            
                            # Pausa ligera para asegurar que la cookie se grabe antes de recargar
                            time.sleep(1.5) 
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas. Verifica tu usuario y contraseña.")
                            
            # ==========================================
            # PESTAÑA: CREAR USUARIO
            # ==========================================
            with tab_registro:
                with st.form("form_registro", border=False):
                    st.markdown("<h4 style='color: #ffffff; margin-bottom: 5px;'>Registro de Nuevo Atleta</h4>", unsafe_allow_html=True)
                    st.markdown("<div style='font-size: 0.85rem; color: #aaaaaa; margin-bottom: 15px;'>Configura tu cuenta para comenzar a registrar tu historial de entrenamiento y nutrición.</div>", unsafe_allow_html=True)
                    
                    nuevo_usuario = st.text_input("Nombre Usuario")
                    correo_reg = st.text_input("Correo Electrónico", placeholder="ejemplo@correo.com")
                    nueva_clave = st.text_input("Nueva Contraseña", type="password")
                    confirmar_clave = st.text_input("Confirmar Contraseña", type="password")
                    
                    submit_reg = st.form_submit_button("Crear Cuenta", type="primary", use_container_width=True)
                    
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
                                st.success(f"✅ Usuario '{nuevo_usuario}' creado exitosamente. Ya puedes iniciar sesión.")
                            else:
                                st.error("⚠️ Ese nombre de usuario o correo ya está registrado en el sistema. Intenta con otro.")