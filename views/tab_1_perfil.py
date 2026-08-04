import os
import sys
import streamlit as st
import database as db  # <-- Importamos tu base de datos

def cargar_perfil_db():
    """Carga los datos biométricos directamente de la base de datos del usuario logueado."""
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil_db = db.obtener_perfil(user_id)
        if perfil_db:
            return perfil_db
    return {}

def mostrar(exercises=None):
    st.title("👤 Mi Perfil y Entorno Biométrico")
    
    # Llamamos a la función que lee de la base de datos
    perfil = cargar_perfil_db() 
    
    if not perfil:
        st.warning("No se encontró información del perfil.")
        return

    col_bio, col_env = st.columns(2)

    with col_bio:
        with st.container(border=True):
            st.subheader("📊 Datos Biométricos")
            st.write(f"**Nombre:** {perfil.get('nombre', 'N/A')}")
            st.write(f"**Edad:** {perfil.get('edad', 'N/A')} años")
            st.write(f"**Peso:** {perfil.get('peso', 'N/A')} kg")
            st.write(f"**Estatura:** {perfil.get('estatura', 'N/A')} cm")
            st.write(f"**Género:** {perfil.get('genero', 'N/A')}")
            st.write(f"**Nivel de Experiencia:** {perfil.get('nivel', 'N/A')}")

        # Mostrar medidas corporales solo si existen y son mayores a 0
        medidas = perfil.get("medidas", {})
        if medidas and any(v > 0 for v in medidas.values()):
            with st.container(border=True):
                st.subheader("📏 Medidas Corporales")
                m1, m2, m3 = st.columns(3)
                m1.metric("Pecho", f"{medidas.get('pecho', 0)} cm")
                m1.metric("Brazos", f"{medidas.get('brazo', 0)} cm")
                m2.metric("Cintura", f"{medidas.get('cintura', 0)} cm")
                m2.metric("Cadera", f"{medidas.get('cadera', 0)} cm")
                m3.metric("Piernas", f"{medidas.get('pierna', 0)} cm")
                m3.metric("Pantorrillas", f"{medidas.get('pantorrilla', 0)} cm")

    with col_env:
        with st.container(border=True):
            st.subheader("🌍 Condición Ambiental y Geolocalización")
            st.metric("Ubicación Actual", "Cali, Colombia")
            st.metric("Clima Local", "28 °C | Humedad 65%")
            st.caption("Ajuste automático: Incremento de descansos +20s por fatiga térmica.")

        # --- CONTENEDOR PARA LIMITACIONES MÉDICAS ---
        with st.container(border=True):
            st.subheader("🏥 Salud y Prevención")
            
            # Mostramos Limitaciones / Lesiones sin mencionar IA
            limitaciones = perfil.get('limitaciones', [])
            if limitaciones:
                st.write("**Condiciones registradas:**")
                for lim in limitaciones:
                    st.markdown(f"- 🔴 {lim}")
            else:
                st.write("**Condiciones registradas:** Ninguna reportada ✅")

    st.divider()
    
    if exercises:
        st.info(f"💡 Base de datos sincronizada: **{len(exercises)}** ejercicios disponibles.")