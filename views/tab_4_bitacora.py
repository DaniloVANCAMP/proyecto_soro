import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta

# Blindaje de ruta absoluta
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

import database as db  # <-- CONEXIÓN A LA BASE DE DATOS

def cargar_perfil():
    """Carga los datos biométricos del usuario desde la base de datos."""
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil = db.obtener_perfil(user_id)
        if perfil:
            return perfil
    return {}

def cargar_bitacora_microdatos():
    """Carga el dataset de entrenamientos DIRECTAMENTE DESDE FIREBASE."""
    user_id = st.session_state.get("user_id")
    if user_id:
        return db.obtener_bitacora(user_id)
    return []

def extraer_macro(datos_comida, llave):
    """Extrae macros de forma segura, ya sea que estén en una lista de alimentos o un diccionario totalizado."""
    if isinstance(datos_comida, dict):
        if "totales" in datos_comida: return datos_comida["totales"].get(llave, 0)
        return datos_comida.get(llave, 0)
    elif isinstance(datos_comida, list):
        return sum(float(item.get(llave, 0)) for item in datos_comida if isinstance(item, dict))
    return 0

def mostrar():
    st.title("📅 Mi Bitácora de Entrenamiento y Nutrición")
    st.write("Consulta tus microdatos cruzados (Ejercicio + Alimentación) para Machine Learning.")

    user_id_actual = st.session_state.get("user_id")
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
    datos_del_usuario = [d for d in todos_los_datos if d.get("user_id") == user_id_actual]

    datos_filtrados = []
    if tipo_vista == "Un Día Específico":
        fecha_str = fecha_ref.strftime("%Y-%m-%d")
        datos_filtrados = [d for d in datos_del_usuario if d.get("timestamp", "").startswith(fecha_str)]
    else:
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

    with tab_resumen:
        st.info(f"👤 Atleta: {nombre_atleta} | Mostrando {len(datos_filtrados)} registros encontrados.")
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
            st.dataframe(pd.DataFrame(filas_resumen), use_container_width=True)

    with tab_detalle:
        st.markdown("### 🧬 Dataset Consolidado para Machine Learning")
        st.markdown("Esta tabla unifica variables biométricas, ambientales, rendimiento **y nutrición detallada**.")
        
        if not datos_filtrados:
            st.warning("No hay datos para construir el dataset en este periodo.")
        else:
            filas_ml = []
            for d in datos_filtrados:
                fecha_str = d.get("timestamp", "")[:10]
                
                # --- MAGIA: EL JOIN CON NUTRICIÓN ---
                nutricion_hoy = db.obtener_nutricion(user_id_actual, fecha_str) or {}
                totales_nut = nutricion_hoy.get("totales", {})
                desayuno = nutricion_hoy.get("desayuno", {})
                almuerzo = nutricion_hoy.get("almuerzo", {})
                cena = nutricion_hoy.get("cena", {})
                snacks = nutricion_hoy.get("snacks", {})
                
                ctx = d.get("contexto_ambiental", {})
                met = d.get("metrica_sesion", {})
                ej = d.get("ejercicio", {})
                ejec = d.get("ejecucion", {})
                bio = d.get("biometria_diaria", {}).get("medidas_cm", {})
                
                fila = {
                    # 1. Variables Temporales y Ambientales
                    "Timestamp": d.get("timestamp", ""),
                    "Lugar": ctx.get("lugar_entrenamiento", "N/A"),
                    "Temperatura (°C)": ctx.get("temperatura_c", 25.0),
                    
                    # 2. Biometría
                    "Peso Corporal (kg)": d.get("biometria_diaria", {}).get("peso_kg", perfil.get("peso", 0.0)),
                    "Cintura (cm)": bio.get("cintura", medidas.get("cintura", 0.0)),
                    
                    # 3. Datos de Entrenamiento
                    "Ejercicio": ej.get("nombre", "N/A"),
                    "Músculo": ej.get("musculo_objetivo", "N/A"),
                    "Peso Levantado (kg)": ejec.get("peso_levantado_kg", 0.0),
                    "Esfuerzo (RPE)": met.get("esfuerzo_rpe", 0),
                    
                    # 4. NUTRICIÓN: AGREGADA
                    "Nut_Total_Calorias": totales_nut.get("cal", 0),
                    "Nut_Total_Proteina(g)": totales_nut.get("proteina", 0),
                    "Nut_Total_Carbos(g)": totales_nut.get("carbos", 0),
                    
                    # 5. NUTRICIÓN: DESAGREGADA (El oro para ML)
                    "Desayuno_Calorias": extraer_macro(desayuno, "cal"),
                    "Desayuno_Proteina(g)": extraer_macro(desayuno, "proteina"),
                    "Desayuno_Carbos(g)": extraer_macro(desayuno, "carbos"),
                    
                    "Almuerzo_Calorias": extraer_macro(almuerzo, "cal"),
                    "Almuerzo_Proteina(g)": extraer_macro(almuerzo, "proteina"),
                    
                    "Cena_Calorias": extraer_macro(cena, "cal"),
                    "Cena_Proteina(g)": extraer_macro(cena, "proteina"),
                    
                    "Snacks_Calorias": extraer_macro(snacks, "cal"),
                    "Snacks_Proteina(g)": extraer_macro(snacks, "proteina"),
                }
                filas_ml.append(fila)
            
            df_ml = pd.DataFrame(filas_ml)
            st.dataframe(df_ml, use_container_width=True, hide_index=True)
            
            csv = df_ml.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Dataset Full (CSV)",
                data=csv,
                file_name=f"dataset_ml_avanzado_{fecha_ref}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )