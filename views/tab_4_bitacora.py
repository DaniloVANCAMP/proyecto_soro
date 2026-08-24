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
    # --- CSS ESTILIZADO Y RESPONSIVO PARA MÓVIL ---
    st.markdown("""
    <style>
    .bitacora-title {
        font-size: clamp(1.8rem, 6vw, 2.4rem);
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 2px;
        line-height: 1.1;
    }
    .bitacora-subtitle {
        font-size: clamp(1.0rem, 3.5vw, 1.3rem);
        font-weight: 600;
        color: #2ecc71;
        margin-bottom: 6px;
    }
    .bitacora-desc {
        font-size: 0.85rem;
        color: #aaaaaa;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: clamp(1.1rem, 4vw, 1.4rem);
        font-weight: 700;
        color: #ffffff;
        margin-top: 15px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- ENCABEZADO REORGANIZADO ---
    st.markdown("""
    <div class='bitacora-title'>📅 Mi Bitácora</div>
    <div class='bitacora-subtitle'>Entrenamiento y Nutrición</div>
    <div class='bitacora-desc'>Consulta tus microdatos cruzados (Ejercicio + Alimentación) para Machine Learning.</div>
    """, unsafe_allow_html=True)

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

    st.markdown(f"<div class='section-title'>🏋️‍♂️ Entrenamientos: {tipo_vista}</div>", unsafe_allow_html=True)

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
                ej_resumen = d.get("ejercicio") or {}
                ejec_resumen = d.get("ejecucion") or {}
                filas_resumen.append({
                    "Fecha": d.get("timestamp", "")[:10],
                    "Ejercicio": ej_resumen.get("nombre", "Desconocido").title(),
                    "Músculo": ej_resumen.get("musculo_objetivo", "N/A"),
                    "Peso (kg)": ejec_resumen.get("peso_levantado_kg", 0.0)
                })
            st.dataframe(pd.DataFrame(filas_resumen), use_container_width=True)

    with tab_detalle:
        st.markdown("<div class='section-title'>🧬 Dataset Consolidado para Machine Learning</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.82rem; color: #aaaaaa; margin-bottom: 12px;'>Esta tabla unifica variables biométricas, ambientales, rendimiento y nutrición detallada.</div>", unsafe_allow_html=True)
        
        if not datos_filtrados:
            st.warning("No hay datos para construir el dataset en este periodo.")
        else:
            filas_ml = []
            for d in datos_filtrados:
                fecha_str = d.get("timestamp", "")[:10]
                
                # --- EXTRACCIÓN ROBUSTA DE FIREBASE ---
                nutricion_hoy = db.obtener_nutricion(user_id_actual, fecha_str) or {}
                totales_nut = nutricion_hoy.get("totales") or {}
                desayuno = nutricion_hoy.get("desayuno") or {}
                almuerzo = nutricion_hoy.get("almuerzo") or {}
                cena = nutricion_hoy.get("cena") or {}
                snacks = nutricion_hoy.get("snacks") or {}
                
                ctx = d.get("contexto_ambiental") or {}
                met = d.get("metrica_sesion") or {}
                ej = d.get("ejercicio") or {}
                ejec = d.get("ejecucion") or {}
                bio = (d.get("biometria_diaria") or {}).get("medidas_cm") or {}
                
                fila = {
                    # 1. Variables Temporales y Ambientales
                    "Timestamp": d.get("timestamp") or "Sin Fecha",
                    "Lugar": ctx.get("lugar_entrenamiento") or "No Registrado",
                    "Temperatura (°C)": ctx.get("temperatura_c") or 25.0,
                    
                    # 2. BIOMETRÍA COMPLETA (Crucial para ML)
                    "Peso Corporal (kg)": (d.get("biometria_diaria") or {}).get("peso_kg") or perfil.get("peso", 0.0),
                    "Cuello (cm)": bio.get("cuello") or medidas.get("cuello", 0.0),
                    "Cintura (cm)": bio.get("cintura") or medidas.get("cintura", 0.0),
                    "Cadera (cm)": bio.get("cadera") or medidas.get("cadera", 0.0),
                    "Brazos (cm)": bio.get("biceps") or bio.get("brazo") or medidas.get("brazo", 0.0),
                    "Piernas (cm)": bio.get("cuadriceps") or bio.get("pierna") or medidas.get("pierna", 0.0),
                    "Pantorrillas (cm)": bio.get("pantorrilla") or medidas.get("pantorrilla", 0.0),
                    
                    # 3. Datos de Entrenamiento
                    "Ejercicio": ej.get("nombre") or "Sin Especificar",
                    "Músculo": ej.get("musculo_objetivo") or "Sin Especificar",
                    "Peso Levantado (kg)": ejec.get("peso_levantado_kg") or 0.0,
                    "Esfuerzo (RPE)": met.get("esfuerzo_rpe") or 0,
                    
                    # 4. NUTRICIÓN: AGREGADA
                    "Nut_Total_Calorias": totales_nut.get("cal") or 0,
                    "Nut_Total_Proteina(g)": totales_nut.get("proteina") or 0,
                    "Nut_Total_Carbos(g)": totales_nut.get("carbos") or 0,
                    
                    # 5. NUTRICIÓN: DESAGREGADA
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