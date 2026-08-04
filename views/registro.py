import time
import streamlit as st
import database as db

def mostrar():
    st.title("👤 Mi Perfil Biométrico")
    st.write("Ingresa o actualiza tus datos biométricos para recalcular tus planes y alimentar tu Bitácora.")
    
    # Validar que exista una sesión activa antes de cargar la UI
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("⚠️ No se encontró una sesión activa. Por favor, inicia sesión primero.")
        return

    # Cargar datos existentes si los hay para pre-llenar el formulario
    perfil_actual = db.obtener_perfil(user_id)
    if not perfil_actual:
        perfil_actual = {"medidas": {}}

    # Contenedor 1: Datos Generales
    with st.container(border=True):
        st.markdown("### 📋 Datos Generales")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo:", value=perfil_actual.get('nombre', ''))
            edad = st.number_input("Edad:", min_value=10, max_value=100, value=int(perfil_actual.get('edad', 25)))
            genero = st.selectbox("Género:", ["Masculino", "Femenino"], index=0 if perfil_actual.get('genero') == 'Masculino' else 1)
        with col2:
            peso = st.number_input("Peso (kg):", min_value=30.0, max_value=200.0, value=float(perfil_actual.get('peso', 70.0)))
            estatura = st.number_input("Estatura (cm):", min_value=100, max_value=250, value=int(perfil_actual.get('estatura', 170)))
            
            # Manejo seguro del índice del nivel de experiencia
            nivel_actual = perfil_actual.get('nivel', 'Principiante')
            opciones_nivel = ["Principiante", "Intermedio", "Avanzado"]
            indice_nivel = opciones_nivel.index(nivel_actual) if nivel_actual in opciones_nivel else 0
            nivel = st.selectbox("Nivel de experiencia:", opciones_nivel, index=indice_nivel)
    
    # Contenedor 2: Medidas
    with st.container(border=True):
        st.markdown("### 📏 Medidas Corporales (cm) - Opcional")
        medidas = perfil_actual.get('medidas', {})
        col3, col4, col5 = st.columns(3)
        with col3:
            pecho = st.number_input("Pecho/Dorsal:", min_value=0.0, value=float(medidas.get('pecho', 0.0)))
            brazos = st.number_input("Brazos (Bíceps):", min_value=0.0, value=float(medidas.get('brazo', 0.0)))
        with col4:
            cintura = st.number_input("Cintura:", min_value=0.0, value=float(medidas.get('cintura', 0.0)))
            cadera = st.number_input("Cadera/Glúteos:", min_value=0.0, value=float(medidas.get('cadera', 0.0)))
        with col5:
            piernas = st.number_input("Piernas (Cuádriceps):", min_value=0.0, value=float(medidas.get('pierna', 0.0)))
            pantorrillas = st.number_input("Pantorrillas:", min_value=0.0, value=float(medidas.get('pantorrilla', 0.0)))

    # Contenedor 3: Salud y Prevención (Limpiado y Profesional)
    with st.container(border=True):
        st.markdown("### 🏥 Salud y Prevención de Lesiones")
        st.write("Selecciona si tienes alguna condición actual para que el sistema adapte tus rutinas automáticamente y evite ejercicios de riesgo.")
        
        opciones_lesiones = ["Dolor Lumbar", "Lesión de Rodilla", "Lesión de Hombro", "Muñecas Sensibles"]
        lesiones_actuales = perfil_actual.get('limitaciones', [])
        lesiones_default = [l for l in lesiones_actuales if l in opciones_lesiones]
        
        limitaciones = st.multiselect("Condiciones médicas o lesiones activas:", opciones_lesiones, default=lesiones_default)

    st.divider()
    
    # Botón de guardado
    if st.button("💾 Guardar Cambios del Perfil", use_container_width=True, type="primary"):
        datos_nuevos = {
            "nombre": nombre,
            "edad": edad,
            "genero": genero,
            "nivel": nivel,
            "estatura": estatura,
            "peso": peso,
            "limitaciones": limitaciones, # <-- Solo guardamos las lesiones, nada de equipo
            "medidas": {
                "pecho": pecho,
                "cintura": cintura,
                "pierna": piernas,
                "brazo": brazos,
                "cadera": cadera,
                "pantorrilla": pantorrillas
            }
        }
        
        # Guardar en base de datos usando el user_id de la sesión
        db.guardar_perfil(user_id, datos_nuevos)
        st.success("¡Datos guardados exitosamente! Tu ecosistema ya está actualizado. 🧬")
        time.sleep(1.5)
        st.rerun()