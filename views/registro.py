import time
import streamlit as st
import database as db

def mostrar():
    # --- CSS ESTILIZADO Y COLORIDO ---
    st.markdown("""
    <style>
    .perfil-title {
        font-size: clamp(1.8rem, 6vw, 2.4rem);
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 2px;
        line-height: 1.1;
    }
    .perfil-subtitle {
        font-size: clamp(1.0rem, 3.5vw, 1.3rem);
        font-weight: 600;
        color: #2ecc71; /* Verde Neón */
        margin-bottom: 6px;
    }
    .perfil-desc {
        font-size: 0.85rem;
        color: #aaaaaa;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: clamp(1.1rem, 4vw, 1.4rem);
        font-weight: 700;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 15px;
        border-bottom: 2px solid #e74c3c; /* Línea roja vibrante */
        padding-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- ENCABEZADO ---
    st.markdown("""
    <div class='perfil-title'>👤 Mi Perfil </div>
    <div class='perfil-subtitle'>Datos de Salud y Composición Corporal</div>
    <div class='perfil-desc'>Ingresa o actualiza tu información para recalcular tus planes y mantener tu historial al día.</div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ No se encontró una sesión activa. Por favor, inicia sesión primero.")
        return

    perfil_actual = db.obtener_perfil(user_id)
    if not perfil_actual:
        perfil_actual = {"medidas": {}}

    # ==========================================
    # 🛡️ INICIO DEL FORMULARIO PROTEGIDO
    # ==========================================
    with st.form("formulario_perfil", border=False):
        
        # --- SECCIÓN 1: DATOS GENERALES ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>📋 Datos Generales</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre completo:", value=perfil_actual.get('nombre', ''))
                edad = st.number_input("Edad:", min_value=10, max_value=100, value=int(perfil_actual.get('edad', 25)))
                genero = st.selectbox("Género:", ["Masculino", "Femenino"], index=0 if perfil_actual.get('genero') == 'Masculino' else 1)
            with col2:
                peso = st.number_input("Peso (kg):", min_value=30.0, max_value=200.0, value=float(perfil_actual.get('peso', 70.0)))
                estatura = st.number_input("Estatura (cm):", min_value=100, max_value=250, value=int(perfil_actual.get('estatura', 170)))
                
                nivel_actual = perfil_actual.get('nivel', 'Principiante')
                opciones_nivel = ["Principiante", "Intermedio", "Avanzado"]
                indice_nivel = opciones_nivel.index(nivel_actual) if nivel_actual in opciones_nivel else 0
                nivel = st.selectbox("Nivel de experiencia:", opciones_nivel, index=indice_nivel)
        
        # --- SECCIÓN 2: MEDIDAS CORPORALES (FULL) ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>📏 Medidas Corporales (cm)</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 0.8rem; color: #aaaaaa; margin-bottom: 10px;'>Opcional, pero necesario para calcular tu porcentaje de grasa y progreso físico.</div>", unsafe_allow_html=True)
            
            medidas = perfil_actual.get('medidas', {})
            
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                cuello = st.number_input("Cuello:", min_value=0.0, value=float(medidas.get('cuello', 0.0)))
                pecho = st.number_input("Pecho/Dorsal:", min_value=0.0, value=float(medidas.get('pecho', 0.0)))
            with col4:
                hombros = st.number_input("Hombros:", min_value=0.0, value=float(medidas.get('hombros', 0.0))) 
                brazos = st.number_input("Brazos (Bíceps):", min_value=0.0, value=float(medidas.get('brazo', 0.0)))
            with col5:
                cintura = st.number_input("Cintura:", min_value=0.0, value=float(medidas.get('cintura', 0.0)))
                cadera = st.number_input("Cadera/Glúteos:", min_value=0.0, value=float(medidas.get('cadera', 0.0)))
            with col6:
                piernas = st.number_input("Piernas (Cuádriceps):", min_value=0.0, value=float(medidas.get('pierna', 0.0)))
                pantorrillas = st.number_input("Pantorrillas:", min_value=0.0, value=float(medidas.get('pantorrilla', 0.0)))

        # --- SECCIÓN 3: SALUD Y LESIONES ---
        with st.container(border=True):
            st.markdown("<div class='section-title'>🏥 Salud y Prevención</div>", unsafe_allow_html=True)
            st.write("Selecciona si tienes alguna condición actual para adaptar tus rutinas y evitar riesgos.")
            
            opciones_lesiones = ["Dolor Lumbar", "Lesión de Rodilla", "Lesión de Hombro", "Muñecas Sensibles"]
            lesiones_actuales = perfil_actual.get('limitaciones', [])
            lesiones_default = [l for l in lesiones_actuales if l in opciones_lesiones]
            
            limitaciones = st.multiselect("Condiciones médicas o lesiones activas:", opciones_lesiones, default=lesiones_default)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- BOTÓN DE GUARDADO DEL FORMULARIO ---
        # st.form_submit_button es la única forma de enviar los datos que están dentro de un st.form
        guardar = st.form_submit_button("💾 Guardar Perfil Biométrico", use_container_width=True, type="primary")
        
        if guardar:
            datos_nuevos = {
                "nombre": nombre,
                "edad": edad,
                "genero": genero,
                "nivel": nivel,
                "estatura": estatura,
                "peso": peso,
                "limitaciones": limitaciones,
                "medidas": {
                    "cuello": cuello,
                    "hombros": hombros,
                    "pecho": pecho,
                    "cintura": cintura,
                    "pierna": piernas,
                    "brazo": brazos,
                    "cadera": cadera,
                    "pantorrilla": pantorrillas
                }
            }
            
            db.guardar_perfil(user_id, datos_nuevos)
            st.success("¡Datos guardados exitosamente! Tu ecosistema ya está actualizado. 🧬")
            time.sleep(1.5)
            st.rerun()