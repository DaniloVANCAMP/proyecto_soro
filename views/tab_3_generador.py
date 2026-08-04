import os
import sys
import json
import uuid
import random
from datetime import datetime
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from utils.traducciones import fmt_equipo
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

def cargar_perfil_simple():
    """Trae la información básica del usuario activo"""
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil = db.obtener_perfil(user_id)
        if perfil:
            return perfil
    return {"nombre": "Usuario ML", "genero": "N/A", "edad": 0, "peso": 0.0}

# --- INTERFAZ DEL GENERADOR ---
def mostrar(exercises, base_media_url=""):
    st.title("🏋️ Generador de Rutina Personalizada")
    st.markdown("Diseña tu sesión de entrenamiento según tus herramientas disponibles.")

    if not exercises:
        st.warning("No hay ejercicios disponibles para construir la rutina.")
        return

    equipos_disponibles = sorted(list({str(ex.get('equipment')) for ex in exercises if ex.get('equipment')}))

    col1, col2 = st.columns(2)
    with col1:
        dias = st.slider("Días a entrenar por semana:", 1, 7, 4)
        enfoque = st.selectbox("Enfoque muscular principal:", ["Glúteos & Piernas", "Torso / Pecho & Espalda", "Full Body", "Brazos & Hombros"])

    with col2:
        objetivo = st.selectbox("Objetivo:", ["Hipertrofia", "Fuerza Maxima", "Definición / Resistencia"])
        duracion = st.select_slider("Duración máxima por sesión:", options=["30 min", "45 min", "60 min", "90 min"], value="60 min")

    st.write("---")
    st.subheader("Equipamiento que posees:")
    
    equipos_seleccionados = st.multiselect(
        "Filtra la generación según tu material:",
        options=equipos_disponibles,
        default=[e for e in ['dumbbell', 'barbell', 'body weight', 'cable'] if e in equipos_disponibles],
        format_func=fmt_equipo
    )

    if st.button("⚡ Generar Rutina Ahora", type="primary", use_container_width=True):
        if not equipos_seleccionados:
            st.error("Por favor, selecciona al menos un equipamiento.")
        else:
            # 1. Filtramos por el equipo que el usuario tiene (siempre incluimos body weight por si acaso)
            candidatos = [ej for ej in exercises if ej.get("equipment") in equipos_seleccionados or "body weight" in str(ej.get("equipment")).lower()]
            
            # 2. Filtramos por la zona muscular elegida
            if enfoque == "Glúteos & Piernas":
                candidatos = [ej for ej in candidatos if any(t in str(ej.get("target")).lower() or t in str(ej.get("body_part")).lower() for t in ["glute", "leg", "quad", "hamstring", "calf", "pierna"])]
            elif enfoque == "Torso / Pecho & Espalda":
                candidatos = [ej for ej in candidatos if any(t in str(ej.get("target")).lower() or t in str(ej.get("body_part")).lower() for t in ["chest", "back", "pecho", "espalda", "lats", "pectoral"])]
            elif enfoque == "Brazos & Hombros":
                candidatos = [ej for ej in candidatos if any(t in str(ej.get("target")).lower() or t in str(ej.get("body_part")).lower() for t in ["arm", "shoulder", "bicep", "tricep", "delt", "brazo", "hombro"])]
            
            if not candidatos:
                st.warning("⚠️ No se encontraron ejercicios con ese equipo y enfoque. ¡Intenta agregar más equipo!")
            else:
                # 3. Calculamos cuántos ejercicios dar según el tiempo elegido
                num_ej = 4 if duracion == "30 min" else 6 if duracion == "45 min" else 8 if duracion == "60 min" else 10
                
                # 4. Seleccionamos aleatoriamente para dar variedad
                rutina_final = random.sample(candidatos, min(num_ej, len(candidatos)))
                
                # Guardamos la rutina en sesión para que no se borre al interactuar con los checkboxes
                st.session_state["rutina_generada"] = rutina_final
                st.session_state["datos_sesion"] = {"enfoque": enfoque, "objetivo": objetivo, "duracion": duracion}
                
                st.success(f"¡Rutina estructurada correctamente para {dias} días/semana enfocada en {enfoque}!")

    # ==========================================
    # MOSTRAR LA RUTINA Y REGISTRAR MICRODATOS
    # ==========================================
    if "rutina_generada" in st.session_state and st.session_state["rutina_generada"]:
        st.divider()
        st.subheader("📝 Tu Rutina de Hoy")
        
        rutina = st.session_state["rutina_generada"]
        datos_sesion = st.session_state.get("datos_sesion", {})

        for idx, ej in enumerate(rutina):
            with st.container(border=True):
                col_info, col_img, col_inputs = st.columns([2.5, 1.5, 2], vertical_alignment="center")
                with col_info:
                    st.markdown(f"**{idx + 1}. {ej.get('name', 'Desconocido').title()}**")
                    st.write(f"🎯 **Músculo:** {ej.get('target', 'N/A')}  \n⚙️ **Equipo:** {fmt_equipo(ej.get('equipment', 'N/A'))}")
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
            perfil_actual = cargar_perfil_simple()
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
                            "enfoque": datos_sesion.get("enfoque")
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