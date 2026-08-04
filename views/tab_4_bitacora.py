import streamlit as st
import pandas as pd
import json
import os
from datetime import date, datetime, timedelta

# Blindaje de ruta absoluta
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

import database as db  # <-- CONEXIÓN A LA BASE DE DATOS

def cargar_perfil():
    """Carga los datos biométricos del usuario desde la base de datos SQL."""
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil = db.obtener_perfil(user_id)
        if perfil:
            return perfil
    return {}

def cargar_bitacora_microdatos():
    """Carga el dataset de entrenamientos guardado por las otras pestañas."""
    ruta = "bitacora_microdatos.json"
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def mostrar():
    st.title("📅 Mi Bitácora de Entrenamiento")
    st.write("Consulta tus microdatos de entrenamiento filtrados por día o por semana.")

    # Obtenemos el ID del usuario actual
    user_id_actual = st.session_state.get("user_id")

    # Cargar datos del perfil
    perfil = cargar_perfil()
    medidas = perfil.get("medidas", {})
    nombre_atleta = perfil.get('nombre', 'Usuario ML')

    # -------------------------------------------------------------
    # CONTROLES SUPERIORES
    # -------------------------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        tipo_vista = st.radio("⚙️ Tipo de Vista:", ["Un Día Específico", "Semana Completa"], horizontal=True)
    with col2:
        fecha_ref = st.date_input("Selecciona una fecha de referencia:", date.today())

    st.subheader(f"Entrenamientos: {tipo_vista}")

    # --- LÓGICA DE FILTRADO ---
    todos_los_datos = cargar_bitacora_microdatos()
    
    # 1. FILTRO DE PRIVACIDAD: Solo dejamos los registros que le pertenecen al usuario actual
    # Si por alguna razón el registro viejo no tiene user_id, se ignora por seguridad.
    datos_del_usuario = [d for d in todos_los_datos if d.get("user_id") == user_id_actual]

    # 2. FILTRO DE FECHAS
    datos_filtrados = []
    if tipo_vista == "Un Día Específico":
        fecha_str = fecha_ref.strftime("%Y-%m-%d")
        datos_filtrados = [d for d in datos_del_usuario if d.get("timestamp", "").startswith(fecha_str)]
    else:
        # Lógica para semana completa (Lunes a Domingo)
        inicio_semana = fecha_ref - timedelta(days=fecha_ref.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        
        for d in datos_del_usuario:
            ts = d.get("timestamp", "")[:10]
            if ts:
                try:
                    fecha_d = datetime.strptime(ts, "%Y-%m-%d").date()
                    if inicio_semana <= fecha_d <= fin_semana:
                        datos_filtrados.append(d)
                except ValueError:
                    pass

    # -------------------------------------------------------------
    # PESTAÑAS: RESUMEN VS DETALLE (ML)
    # -------------------------------------------------------------
    tab_resumen, tab_detalle = st.tabs(["📊 Resumen", "🔬 Microdatos (Detalle)"])

    # --- PESTAÑA 1: RESUMEN (Vista Limpia) ---
    with tab_resumen:
        st.info(f"👤 Atleta: {nombre_atleta} | Mostrando {len(datos_filtrados)} registros encontrados.")
        st.subheader("🏆 Detalle de Ejecución")
        
        if not datos_filtrados:
            st.warning(f"No hay entrenamientos registrados para la fecha o semana seleccionada ({fecha_ref}).")
        else:
            filas_resumen = []
            for d in datos_filtrados:
                filas_resumen.append({
                    "Fecha": d.get("timestamp", "")[:10],
                    "Ejercicio": d.get("ejercicio", {}).get("nombre", "Desconocido").title(),
                    "Músculo": d.get("ejercicio", {}).get("musculo_objetivo", "N/A"),
                    "Peso (kg)": d.get("ejecucion", {}).get("peso_levantado_kg", 0.0)
                })
            df_resumen = pd.DataFrame(filas_resumen)
            st.dataframe(df_resumen, use_container_width=True)

    # --- PESTAÑA 2: DETALLE (Dataset para Machine Learning) ---
    with tab_detalle:
        st.markdown("### 🧬 Dataset Consolidado para Machine Learning")
        st.markdown("Esta tabla unifica variables biométricas, ambientales, y de rendimiento para exportación.")
        
        if not datos_filtrados:
            st.warning("No hay datos para construir el dataset en este periodo.")
        else:
            filas_ml = []
            for d in datos_filtrados:
                # Extraemos de forma segura la info del JSON
                ctx = d.get("contexto_ambiental", {})
                met = d.get("metrica_sesion", {})
                ej = d.get("ejercicio", {})
                ejec = d.get("ejecucion", {})
                bio = d.get("biometria_diaria", {}).get("medidas_cm", {})
                
                fila = {
                    # 1. Variables Temporales y Ambientales
                    "Timestamp": d.get("timestamp", ""),
                    "Lugar": ctx.get("lugar_entrenamiento", "N/A"),
                    "Clima": ctx.get("clima", "N/A"),
                    "Temperatura (°C)": ctx.get("temperatura_c", 25.0),
                    
                    # 2. Biometría y Perfil
                    "Nombre": d.get("usuario", {}).get("nombre", nombre_atleta),
                    "Edad": d.get("usuario", {}).get("edad", perfil.get("edad", 0)),
                    "Género": d.get("usuario", {}).get("sexo", perfil.get("genero", "N/A")),
                    "Estatura (cm)": d.get("usuario", {}).get("estatura_cm", perfil.get("estatura", 0)),
                    "Peso Corporal (kg)": d.get("biometria_diaria", {}).get("peso_kg", perfil.get("peso", 0.0)),
                    
                    # 3. Medidas Corporales (Si están en el JSON, si no, del perfil)
                    "Cintura (cm)": bio.get("cintura", medidas.get("cintura", 0.0)),
                    "Piernas (cm)": bio.get("cuadriceps", medidas.get("pierna", 0.0)),
                    "Brazos (cm)": bio.get("biceps", medidas.get("brazo", 0.0)),
                    "Cadera (cm)": bio.get("cadera", medidas.get("cadera", 0.0)),
                    "Pantorrillas (cm)": bio.get("pantorrilla", medidas.get("pantorrilla", 0.0)),
                    
                    # 4. Datos de Entrenamiento
                    "Ejercicio": ej.get("nombre", "N/A"),
                    "Músculo": ej.get("musculo_objetivo", "N/A"),
                    "Equipo Usado": ej.get("equipo_usado", "N/A"),
                    "Peso Levantado (kg)": ejec.get("peso_levantado_kg", 0.0),
                    "Esfuerzo (RPE)": met.get("esfuerzo_rpe", 0),
                    "Objetivo Sesión": met.get("objetivo_entrenamiento", met.get("objetivo", "N/A")),
                }
                filas_ml.append(fila)
            
            df_ml = pd.DataFrame(filas_ml)
            
            # Mostrar la tabla con scroll horizontal
            st.dataframe(df_ml, use_container_width=True, hide_index=True)
            
            # Botón para descargar el dataset y usarlo en modelos de Python/Scikit-Learn
            csv = df_ml.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Dataset (CSV)",
                data=csv,
                file_name=f"dataset_ml_{fecha_ref}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )