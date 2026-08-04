import os
import sys
import json
import uuid
from datetime import datetime
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from utils.traducciones import fmt_equipo
from utils.routine_generator import generar_rutina_personalizada  # <-- IMPORTAMOS EL CEREBRO
import database as db  # <-- CONEXIÓN A LA BASE DE DATOS

# --- FUNCIONES AUXILIARES PARA ML Y BD ---
def guardar_en_bitacora(nuevos_datos):
    """Guarda los datos de la sesión para el modelo de Machine Learning"""
    archivo = "bitacora_microdatos.json"
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            datos_historicos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos_historicos = []
    
    datos_historicos.extend(nuevos_datos)
    
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos_historicos, f, indent=4)

def cargar_perfil_completo():
    """Trae la información completa del usuario activo"""
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil = db.obtener_perfil(user_id)
        if perfil:
            return perfil
    return {"nombre": "Usuario ML", "genero": "N/A", "edad": 0, "peso": 0.0, "equipo": [], "limitaciones": [], "nivel": "Intermedio"}

# --- INTERFAZ DEL GENERADOR ---
def mostrar(exercises, base_media_url=""):
    st.title("🏋️ Generador de Rutina Personalizada (IA Activa - NSCA)")
    st.markdown("Diseña tu sesión de entrenamiento de forma segura según tus lesiones, nivel y herramientas disponibles.")

    if not exercises:
        st.warning("No hay ejercicios disponibles para construir la rutina.")
        return

    # Cargamos el perfil de la base de datos para pre-llenar los filtros
    perfil = cargar_perfil_completo()
    equipo_bd = perfil.get("equipo", [])
    limitaciones_bd = perfil.get("limitaciones", [])
    nivel_bd = perfil.get("nivel", "Intermedio")

    equipos_disponibles = sorted(list({str(ex.get('equipment')).lower() for ex in exercises if ex.get('equipment')}))

    col1, col2 = st.columns(2)
    with col1:
        dias = st.slider("Días a entrenar por semana:", 1, 7, 4)
        enfoque = st.selectbox("Enfoque muscular principal:", ["Glúteos & Piernas", "Torso / Pecho & Espalda", "Full Body", "Brazos & Hombros"])

    with col2:
        objetivo = st.selectbox("Objetivo:", ["Hipertrofia", "Fuerza Maxima", "Definición / Resistencia"])
        duracion = st.select_slider("Duración máxima por sesión:", options=["30 min", "45 min", "60 min", "90 min"], value="60 min")

    st.write("---")
    st.subheader("Equipamiento para esta sesión:")
    
    # Pre-seleccionamos el equipo que el usuario guardó en su perfil (o peso corporal por defecto)
    default_equipos = [e for e in equipo_bd if e.lower() in equipos_disponibles]
    if not default_equipos:
        default_equipos = [e for e in ['body weight'] if e in equipos_disponibles]

    equipos_seleccionados = st.multiselect(
        "Verifica o ajusta el material que tienes a la mano hoy:",
        options=equipos_disponibles,
        default=default_equipos,
        format_func=fmt_equipo
    )

    if st.button("⚡ Generar Rutina Segura (NSCA)", type="primary", use_container_width=True):
        if not equipos_seleccionados:
            st.error("Por favor, selecciona al menos un equipamiento.")
        else:
            # 1. Traducir el enfoque visual a las categorías en inglés que usa la API
            if enfoque == "Glúteos & Piernas":
                grupos_api = ["upper legs", "lower legs"]
            elif enfoque == "Torso / Pecho & Espalda":
                grupos_api = ["chest", "back"]
            elif enfoque == "Brazos & Hombros":
                grupos_api = ["upper arms", "shoulders"]
            else: # Full Body
                grupos_api = ["upper legs", "chest", "back", "shoulders"]

            # 2. Calcular cuántos ejercicios por grupo necesitamos (dependiendo del tiempo y los grupos)
            num_total_ej = 4 if duracion == "30 min" else 6 if duracion == "45 min" else 8 if duracion == "60 min" else 10
            ejercicios_por_grupo = max(1, num_total_ej // len(grupos_api))

            # 3. CONECTAMOS CON EL CEREBRO IA (AQUÍ OCURRE LA MAGIA DEL FILTRO MÉDICO, EQUIPO Y MATRIZ NSCA)
            resultado, _ = generar_rutina_personalizada(
                exercises=exercises,
                equipo_disponible=equipos_seleccionados,
                limitaciones=limitaciones_bd,
                datos_entorno={"temperatura_c": 28, "altitud_m": 1000}, # Geodata simulada para el ejemplo
                ejercicios_por_grupo=ejercicios_por_grupo,
                grupos_seleccionados=grupos_api,
                objetivo=objetivo,
                nivel=nivel_bd
            )

            # 4. Desempaquetamos la rutina del formato {grupo: [ejercicios]} a una sola lista plana
            rutina_final = []
            for grupo, lista_ej in resultado.get("rutina", {}).items():
                rutina_final.extend(lista_ej)

            if not rutina_final:
                st.warning("⚠️ La IA no encontró ejercicios seguros con tu combinación de equipo y restricciones médicas. ¡Intenta elegir otro enfoque o agregar más equipo!")
            else:
                # Guardamos en sesión para que persista
                st.session_state["rutina_generada"] = rutina_final
                st.session_state["dosificacion"] = resultado.get("dosificacion", {})
                st.session_state["descanso_seg"] = resultado.get("descanso_seg", 60)
                st.session_state["notas_entorno"] = resultado.get("notas_entorno", [])
                st.session_state["datos_sesion"] = {"enfoque": enfoque, "objetivo": objetivo, "duracion": duracion, "nivel": nivel_bd}
                
                st.success(f"¡Rutina estructurada correctamente para {dias} días/semana enfocada en {enfoque} (Nivel: {nivel_bd})!")
                
                # Feedback visual de que las protecciones están activas
                if limitaciones_bd:
                    st.info(f"🛡️ **Modo Seguro Activado:** Se bloqueó automáticamente la asignación de ejercicios que comprometan: **{', '.join(limitaciones_bd)}**.")

    # ==========================================
    # MOSTRAR LA RUTINA Y REGISTRAR MICRODATOS
    # ==========================================
    if "rutina_generada" in st.session_state and st.session_state["rutina_generada"]:
        st.divider()
        
        dosis = st.session_state.get("dosificacion", {})
        descanso_final = st.session_state.get("descanso_seg", 60)
        
        # --- TABLERO CIENTÍFICO NSCA ---
        st.subheader("📋 Dosificación Científica (Estándar NSCA)")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Series Recomendadas", dosis.get("series", "3"))
        m2.metric("Repeticiones", dosis.get("reps", "8-12"))
        m3.metric("Descanso entre series", f"{descanso_final} seg")
        m4.metric("RPE Objetivo", dosis.get("rpe", "7-8"))

        # Mostrar notas ambientales si la IA las calculó
        for nota in st.session_state.get("notas_entorno", []):
            st.caption(nota)
        
        st.divider()
        st.subheader("📝 Tu Rutina de Hoy")
        
        rutina = st.session_state["rutina_generada"]
        datos_sesion = st.session_state.get("datos_sesion", {})

        for idx, ej in enumerate(rutina):
            with st.container(border=True):
                col_info, col_img, col_inputs = st.columns([2.5, 1.5, 2], vertical_alignment="center")
                with col_info:
                    st.markdown(f"**{idx + 1}. {ej.get('name', 'Desconocido').title()}**")
                    st.write(f"🎯 **Músculo:** {ej.get('target', 'N/A').title()}  \n⚙️ **Equipo:** {fmt_equipo(ej.get('equipment', 'N/A'))}")
                    st.caption(f"📌 Prescripción: **{dosis.get('series', '3')} series x {dosis.get('reps', '8-12')} reps**")
                with col_img:
                    if ej.get("gif_url"):
                        img_url = f"{base_media_url}{ej.get('gif_url').lstrip('/')}"
                        st.image(img_url, use_container_width=True)
                with col_inputs:
                    st.number_input("Peso levantado (kg)", min_value=0.0, value=0.0, step=1.0, key=f"peso_gen_{idx}")
                    st.checkbox("¡Completado!", key=f"check_gen_{idx}")
        
        st.divider()
        st.markdown("#### 🧠 Alimentar Modelo de Machine Learning")
        esfuerzo_rpe = st.slider("Esfuerzo Percibido de la Sesión (RPE 1-10)", 1, 10, 7)
        
        if st.button("💾 GUARDAR ENTRENAMIENTO EN BITÁCORA", type="primary", use_container_width=True):
            datos_a_guardar = []
            fecha_actual = datetime.now().isoformat()
            
            for idx, ej in enumerate(rutina):
                if st.session_state.get(f"check_gen_{idx}"):
                    microdato = {
                        "id_evento": str(uuid.uuid4()),
                        "timestamp": fecha_actual,
                        "usuario_id": st.session_state.get("user_id", "anonimo"),
                        "metrica_sesion": {
                            "esfuerzo_rpe": esfuerzo_rpe,
                            "objetivo": datos_sesion.get("objetivo"),
                            "enfoque": datos_sesion.get("enfoque"),
                            "nivel": datos_sesion.get("nivel")
                        },
                        "ejercicio": {
                            "id_api": ej.get("id"),
                            "nombre": ej.get("name"),
                            "musculo_objetivo": ej.get("target"),
                            "equipo_usado": ej.get("equipment")
                        },
                        "ejecucion": {
                            "peso_levantado_kg": st.session_state.get(f"peso_gen_{idx}", 0.0),
                            "completado": True
                        }
                    }
                    datos_a_guardar.append(microdato)
            
            if datos_a_guardar:
                guardar_en_bitacora(datos_a_guardar)
                st.success("¡BRUTAL! Tus microdatos se han guardado y empaquetado con éxito. 🧠🤖")
            else:
                st.warning("⚠️ No marcaste ningún ejercicio como completado. ¡Asegúrate de marcar los checkboxes!")