import os
from datetime import date, datetime, timedelta, timezone
import pandas as pd
import streamlit as st

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
import database as db


def cargar_perfil():
    user_id = st.session_state.get("user_id")
    if user_id:
        perfil = db.obtener_perfil(user_id)
        if perfil:
            return perfil
    return {}


def cargar_bitacora_microdatos():
    user_id = st.session_state.get("user_id")
    if user_id:
        return db.obtener_bitacora(user_id)
    return []


def extraer_macro(datos_comida, clave_principal, clave_secundaria=""):
    """
    Función blindada: Busca la clave principal (ej. 'calorias') y si no la halla 
    busca la secundaria (ej. 'cal') para respetar el historial de Firebase sin fallar.
    """
    def obtener_valor(item):
        return float(item.get(clave_principal, item.get(clave_secundaria, 0.0)))

    if isinstance(datos_comida, dict):
        if "totales" in datos_comida:
            return obtener_valor(datos_comida["totales"])
        return obtener_valor(datos_comida)
    elif isinstance(datos_comida, list):
        # Si Firebase devuelve una lista de alimentos (como en Desayuno, Almuerzo), los suma
        return sum(obtener_valor(item) for item in datos_comida if isinstance(item, dict))
    return 0.0


def mostrar():
    st.markdown(
        """
        <style>
        .bitacora-title { font-size: clamp(1.8rem, 6vw, 2.4rem); font-weight: 800; color: #ffffff; margin-bottom: 2px; }
        .bitacora-subtitle { font-size: clamp(1.0rem, 3.5vw, 1.3rem); font-weight: 600; color: #2ecc71; margin-bottom: 6px; }
        .bitacora-desc { font-size: 0.85rem; color: #aaaaaa; margin-bottom: 20px; }
        .section-title { font-size: clamp(1.1rem, 4vw, 1.4rem); font-weight: 700; color: #ffffff; margin-top: 15px; margin-bottom: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='bitacora-title'>📅 Mi Bitácora</div>
        <div class='bitacora-subtitle'>Entrenamiento y Nutrición en Firebase</div>
        <div class='bitacora-desc'>Consulta tus microdatos unificados directamente desde la nube.</div>
        """,
        unsafe_allow_html=True,
    )

    user_id_actual = st.session_state.get("user_id")
    if not user_id_actual:
        st.warning("⚠️ Inicia sesión para consultar tus registros de entrenamiento.")
        return

    perfil = cargar_perfil()
    medidas = perfil.get("medidas", {})
    nombre_atleta = perfil.get("nombre", "Usuario ML")

    # HORA COLOMBIA (UTC -5)
    zona_colombia = timezone(timedelta(hours=-5))
    hoy_colombia = datetime.now(zona_colombia).date()

    col1, col2 = st.columns(2)
    with col1:
        tipo_vista = st.radio(
            "⚙️ Tipo de Vista:",
            ["Un Día Específico", "Semana Completa"],
            horizontal=True,
        )
    with col2:
        fecha_ref = st.date_input("Selecciona una fecha de referencia:", hoy_colombia)

    st.markdown(
        f"<div class='section-title'>🏋️‍♂️ Entrenamientos: {tipo_vista}</div>",
        unsafe_allow_html=True,
    )

    todos_los_datos = cargar_bitacora_microdatos()

    # FILTRO SEGURO Y RIGUROSO: Solo datos pertenecientes al usuario actual y excluyendo registros netos de comida
    datos_del_usuario = []
    for d in todos_los_datos:
        uid_doc = d.get("user_id")
        if uid_doc is not None and str(uid_doc) == str(user_id_actual):
            # Garantiza que sea un entrenamiento (tenga objeto ejercicio o métricas de sesión)
            if d.get("ejercicio") or d.get("metrica_sesion"):
                datos_del_usuario.append(d)

    datos_filtrados = []
    if tipo_vista == "Un Día Específico":
        fecha_str = fecha_ref.strftime("%Y-%m-%d")
        datos_filtrados = [
            d
            for d in datos_del_usuario
            if (d.get("timestamp") or "").startswith(fecha_str)
        ]
    else:
        inicio_semana = fecha_ref - timedelta(days=fecha_ref.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        for d in datos_del_usuario:
            ts = (d.get("timestamp") or "")[:10]
            if ts:
                try:
                    fecha_d = datetime.strptime(ts, "%Y-%m-%d").date()
                    if inicio_semana <= fecha_d <= fin_semana:
                        datos_filtrados.append(d)
                except ValueError:
                    pass

    tab_resumen, tab_detalle = st.tabs(["📊 Resumen", "🔬 Microdatos (Detalle)"])

    with tab_resumen:
        st.info(
            f"👤 Atleta: {nombre_atleta} | Mostrando {len(datos_filtrados)} registros en Firebase."
        )
        if not datos_filtrados:
            st.warning(
                f"No hay entrenamientos registrados para la fecha o semana seleccionada ({fecha_ref})."
            )
        else:
            filas_resumen = []
            for d in datos_filtrados:
                ctx = d.get("contexto_ambiental") or {}
                met = d.get("metrica_sesion") or {}
                ej = d.get("ejercicio") or {}
                ejec = d.get("ejecucion") or {}

                nombre_ejercicio = str(ej.get("nombre") or "Desconocido").title()

                filas_resumen.append({
                    "Fecha": (d.get("timestamp") or "")[:10],
                    "Lugar": ctx.get("lugar_entrenamiento") or "No Registrado",
                    "Objetivo": met.get("objetivo_entrenamiento") or "Planificación Manual",
                    "Ejercicio": nombre_ejercicio,
                    "Músculo": ej.get("musculo_objetivo") or "N/A",
                    "Series": ejec.get("series") or 0,
                    "Reps": ejec.get("reps") or 0,
                    "Peso (kg)": ejec.get("peso_levantado_kg") or 0.0,
                    "RPE": ejec.get("esfuerzo_rpe") or met.get("esfuerzo_rpe") or 0,
                    "Equipamiento": (ctx.get("equipamiento") or ej.get("equipo_usado") or "N/A"),
                })
            st.dataframe(
                pd.DataFrame(filas_resumen),
                use_container_width=True,
                hide_index=True,
            )

    with tab_detalle:
        st.markdown(
            "<div class='section-title'>🧬 Dataset Consolidado para Machine Learning</div>",
            unsafe_allow_html=True,
        )
        if not datos_filtrados:
            st.warning("No hay datos para construir el dataset en este periodo.")
        else:
            filas_ml = []
            for d in datos_filtrados:
                # LA FECHA DE CRUCE PARA EL MERGE
                fecha_str = (d.get("timestamp") or "")[:10]

                # EXTRACCIÓN CORRECTA DE LA RUTA EN FIREBASE
                nutricion_hoy = db.obtener_nutricion(user_id_actual, fecha_str) or {}
                totales_nut = nutricion_hoy.get("totales") or {}
                
                comidas_db = nutricion_hoy.get("comidas") or {}
                desayuno = comidas_db.get("Desayuno") or []
                almuerzo = comidas_db.get("Almuerzo") or []
                cena = comidas_db.get("Cena") or []
                snacks = comidas_db.get("Snacks") or []

                ctx = d.get("contexto_ambiental") or {}
                met = d.get("metrica_sesion") or {}
                ej = d.get("ejercicio") or {}
                ejec = d.get("ejecucion") or {}
                bio = (d.get("biometria_diaria") or {}).get("medidas_cm") or {}

                fila = {
                    "Timestamp": d.get("timestamp") or "Sin Fecha",
                    "Lugar": ctx.get("lugar_entrenamiento") or "No Registrado",
                    "Objetivo": met.get("objetivo_entrenamiento") or "Planificación Manual",
                    "Equipamiento": (ctx.get("equipamiento") or ej.get("equipo_usado") or "No Registrado"),
                    "Temperatura (°C)": ctx.get("temperatura_c") or 25.0,
                    "Peso Corporal (kg)": ((d.get("biometria_diaria") or {}).get("peso_kg") or perfil.get("peso", 0.0)),
                    "Cuello (cm)": bio.get("cuello") or medidas.get("cuello", 0.0),
                    "Cintura (cm)": bio.get("cintura") or medidas.get("cintura", 0.0),
                    "Cadera (cm)": bio.get("cadera") or medidas.get("cadera", 0.0),
                    "Brazos (cm)": (bio.get("biceps") or bio.get("brazo") or medidas.get("brazo", 0.0)),
                    "Piernas (cm)": (bio.get("cuadriceps") or bio.get("pierna") or medidas.get("pierna", 0.0)),
                    "Pantorrillas (cm)": (bio.get("pantorrilla") or medidas.get("pantorrilla", 0.0)),
                    "Ejercicio": ej.get("nombre") or "Sin Especificar",
                    "Músculo": ej.get("musculo_objetivo") or "Sin Especificar",
                    "Series": ejec.get("series") or 0,
                    "Repeticiones": ejec.get("reps") or 0,
                    "Peso Levantado (kg)": ejec.get("peso_levantado_kg") or 0.0,
                    "Esfuerzo (RPE)": (ejec.get("esfuerzo_rpe") or met.get("esfuerzo_rpe") or 0),
                    
                    # LECTURA BLINDADA (Clave histórica, Clave actual)
                    "Nut_Total_Calorias": extraer_macro(totales_nut, "calorias", "cal"),
                    "Nut_Total_Proteina(g)": extraer_macro(totales_nut, "proteina", "pro"),
                    "Nut_Total_Carbos(g)": extraer_macro(totales_nut, "carbohidratos", "carbos"),
                    
                    "Desayuno_Calorias": extraer_macro(desayuno, "calorias", "cal"),
                    "Desayuno_Proteina(g)": extraer_macro(desayuno, "proteina", "pro"),
                    "Desayuno_Carbos(g)": extraer_macro(desayuno, "carbohidratos", "carbos"),
                    
                    "Almuerzo_Calorias": extraer_macro(almuerzo, "calorias", "cal"),
                    "Almuerzo_Proteina(g)": extraer_macro(almuerzo, "proteina", "pro"),
                    
                    "Cena_Calorias": extraer_macro(cena, "calorias", "cal"),
                    "Cena_Proteina(g)": extraer_macro(cena, "proteina", "pro"),
                    
                    "Snacks_Calorias": extraer_macro(snacks, "calorias", "cal"),
                    "Snacks_Proteina(g)": extraer_macro(snacks, "proteina", "pro"),
                }
                filas_ml.append(fila)

            df_ml = pd.DataFrame(filas_ml)
            st.dataframe(df_ml, use_container_width=True, hide_index=True)

            csv = df_ml.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Descargar Dataset Full (CSV)",
                data=csv,
                file_name=f"dataset_ml_avanzado_{fecha_ref}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )