import streamlit as st
import json
import os
import time
from datetime import date

# Blindaje de ruta absoluta (apunta a la carpeta raíz)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def mostrar():
    st.title("🍏 Nutrición y Suplementación")
    st.write("Registra tu ingesta diaria. Estos datos alimentarán automáticamente tu Bitácora para los modelos de Machine Learning.")

    # Usamos la fecha actual como llave principal
    fecha_hoy = date.today().strftime("%Y-%m-%d")
    st.subheader(f"📅 Registro del día: {fecha_hoy}")

    # Contenedor principal estilo tarjeta
    with st.container(border=True):
        col1, col2 = st.columns(2)

        # --- COLUMNA 1: MACRONUTRIENTES ---
        with col1:
            st.markdown("### 🍽️ Macros de Hoy")
            carbos = st.number_input("Carbohidratos (g)", min_value=0.0, step=1.0, help="Ingresa el total de carbohidratos consumidos.")
            proteina = st.number_input("Proteína (g)", min_value=0.0, step=1.0, help="Ingresa el total de proteína consumida.")
            grasas = st.number_input("Grasas (g)", min_value=0.0, step=1.0, help="Necesario para el cálculo exacto de calorías.")
            
            # Cálculo automático de calorías
            calorias_totales = (carbos * 4) + (proteina * 4) + (grasas * 9)
            
            st.info(f"**🔥 Calorías Totales Estimadas:** {calorias_totales} kcal")

        # --- COLUMNA 2: HIDRATACIÓN Y SUPLEMENTOS ---
        with col2:
            st.markdown("### 💧 Hidratación y Extras")
            agua = st.slider("Hidratación (Litros)", min_value=0.0, max_value=6.0, step=0.25, value=2.0)
            
            st.markdown("**Suplementación Diaria**")
            toma_prote = st.radio("¿Tomaste batido de Proteína?", ["Sí", "No"], horizontal=True)
            toma_creatina = st.radio("¿Tomaste Creatina?", ["Sí", "No"], horizontal=True)
            
            marca_suples = st.text_input("Marca de Suplementos (Opcional)", placeholder="Ej. Optimum Nutrition, MuscleTech...")

    st.divider()

    # --- BOTÓN DE GUARDADO ---
    if st.button("💾 Guardar Registro Nutricional", use_container_width=True, type="primary"):
        # Obtenemos el usuario de la sesión actual
        user_id = st.session_state.get("user_id", "anonimo")
        
        # Estructuramos los datos para guardarlos
        datos_nutricion = {
            "fecha": fecha_hoy,
            "carbohidratos": carbos,
            "proteina": proteina,
            "grasas": grasas,
            "calorias_totales": calorias_totales,
            "hidratacion": agua,
            "toma_proteina": toma_prote,
            "toma_creatina": toma_creatina,
            "marca_suplementos": marca_suples
        }
        
        # Guardar en un JSON independiente
        ruta_nutricion = os.path.join(ROOT_DIR, "nutricion.json")
        
        # Leemos datos previos si existen, para no sobreescribir el historial global
        historial = {}
        if os.path.exists(ruta_nutricion):
            try:
                with open(ruta_nutricion, "r", encoding="utf-8") as f:
                    historial = json.load(f)
            except Exception:
                pass
                
        # Aseguramos que exista la llave del usuario en el diccionario
        if user_id not in historial:
            historial[user_id] = {}
            
        # Actualizamos el historial asignando los datos a la fecha de hoy, dentro del perfil del usuario
        historial[user_id][fecha_hoy] = datos_nutricion
        
        # Guardamos el archivo
        with open(ruta_nutricion, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4)
            
        st.success("¡Datos guardados con éxito! La Bitácora Diaria ya puede procesar esta información para tu modelo. 🧠🥦")
        time.sleep(1.5)
        st.rerun()