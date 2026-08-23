import streamlit as st
import uuid
import time
import json
import os
from datetime import timedelta, date, datetime
import database as db

def guardar_en_bitacora_local(nuevos_datos):
    archivo = "bitacora_microdatos.json"
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            datos_historicos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos_historicos = []
    
    datos_historicos.extend(nuevos_datos)
    
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos_historicos, f, indent=4)

def extraer_instrucciones(datos_brutos):
    """Función maestra para extraer siempre el texto correcto de las instrucciones (prioridad Español)"""
    if not datos_brutos: return []
    
    if isinstance(datos_brutos, str):
        try: datos = json.loads(datos_brutos)
        except: datos = [datos_brutos]
    else:
        datos = datos_brutos

    pasos = []
    if isinstance(datos, dict):
        pasos = datos.get("es", datos.get("en", list(datos.values())[0] if datos else []))
    elif isinstance(datos, list):
        pasos = datos
        
    if isinstance(pasos, str): pasos = [pasos]
    return pasos

def mostrar(ejercicios, equipos_seleccionados, perfil_elegido, BASE_MEDIA_URL, traducir_nombre_ejercicio):
    # CSS Premium
    st.markdown("""
    <style>
    .titulo-musculo {
        color: #ff4b4b; font-size: 1.6rem; font-weight: bold;
        margin-top: 1.5rem; border-bottom: 2px solid #ff4b4b; padding-bottom: 5px; margin-bottom: 15px;
    }
    .stExpander {
        border-radius: 8px !important; border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
    }
    [data-testid="stHorizontalBlock"] { gap: 0.1rem; }
    h2, h3, p { word-wrap: break-word; }
    </style>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")
    
    st.markdown("### 🗓️ Tu Calendario")
    hoy = date.today()
    lunes = hoy - timedelta(days=hoy.weekday())
    dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    if "dia_activo" not in st.session_state:
        st.session_state["dia_activo"] = hoy

    cols_dias = st.columns(7)
    for i, col in enumerate(cols_dias):
        fecha_iter = lunes + timedelta(days=i)
        rutina_previa = db.obtener_plan_dia(user_id, fecha_iter.strftime("%Y-%m-%d")) if user_id else []
        indicador = "🔥" if rutina_previa else "⚪"
        
        with col:
            if st.button(f"{dias_nombres[i]}\n{indicador}", key=f"btn_dia_{i}", use_container_width=True):
                st.session_state["dia_activo"] = fecha_iter

    fecha_seleccionada = st.session_state["dia_activo"]
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    fecha_corta = fecha_seleccionada.strftime("%d/%m/%Y")
    
    if st.session_state.get("ultimo_dia_visto") != fecha_str:
        st.session_state["rutina_borrador"] = db.obtener_plan_dia(user_id, fecha_str) if user_id else []
        st.session_state["ultimo_dia_visto"] = fecha_str
        st.session_state["modo_edicion"] = len(st.session_state["rutina_borrador"]) == 0

    st.divider()

    # =========================================================================
    # ESTADO A: MODO CREACIÓN / EDICIÓN 
    # =========================================================================
    if st.session_state.get("modo_edicion", True):
        st.markdown(f"### 🛠️ Armar Rutina: {fecha_corta}")
        
        if len(st.session_state["rutina_borrador"]) > 0:
            if st.button("⬅️ Volver al Entrenamiento", use_container_width=True):
                st.session_state["modo_edicion"] = False
                st.rerun()
                
        ejercicios_plan = [ej for ej in ejercicios if ej.get("equipment_trad") in equipos_seleccionados] if equipos_seleccionados else []

        with st.container(border=True):
            if not ejercicios_plan:
                st.warning("Selecciona al menos un equipo en la configuración arriba para ver opciones.")
            else:
                todos_los_musculos = sorted(list(set([ej.get("target_trad") for ej in ejercicios_plan if ej.get("target_trad")])))
                musculos_elegidos = st.multiselect("Filtra por Músculo(s):", todos_los_musculos)
                
                if musculos_elegidos:
                    nombres_usados = [ej["nombre"] for ej in st.session_state["rutina_borrador"]]
                    
                    for musculo in musculos_elegidos:
                        st.markdown(f"<div class='titulo-musculo'>{musculo}</div>", unsafe_allow_html=True)
                        ej_musculo = [ej for ej in ejercicios_plan if ej.get("target_trad") == musculo]
                        equipos_viables = sorted(list(set([ej.get("equipment_trad") for ej in ej_musculo if ej.get("equipment_trad")])))
                        
                        for equipo in equipos_viables:
                            ej_finales = [ej for ej in ej_musculo if ej.get("equipment_trad") == equipo and traducir_nombre_ejercicio(ej.get("name", "")) not in nombres_usados]
                            
                            if ej_finales:
                                with st.expander(f"⚙️ {equipo}", expanded=False):
                                    for ej_data in ej_finales:
                                        nombre_ej = traducir_nombre_ejercicio(ej_data.get("name", ""))
                                        st.markdown(f"**{nombre_ej}**")
                                        c_img, c_info = st.columns([1, 1])
                                        
                                        with c_img:
                                            url_gif = ej_data.get("gif_url_correcta")
                                            if url_gif and url_gif != "0":
                                                st.image(f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}", use_container_width=True)
                                                
                                        with c_info:
                                            pasos_mostrar = extraer_instrucciones(ej_data.get("instructions", []))
                                            if pasos_mostrar:
                                                with st.expander("📖 Explicación"):
                                                    for paso in pasos_mostrar[:3]: st.caption(f"- {paso}")
                                                        
                                            if st.button("➕ Añadir", key=f"sel_{ej_data['id']}", use_container_width=True):
                                                nuevo_item = {
                                                    "id_unico": str(uuid.uuid4()), "id_api": ej_data.get("id"),
                                                    "nombre": nombre_ej, "musculo": musculo, "equipo": equipo, 
                                                    "series": 3, "reps": 10,
                                                    "gif_url": ej_data.get("gif_url_correcta", ""),
                                                    "instrucciones": ej_data.get("instructions", [])
                                                }
                                                st.session_state["rutina_borrador"].append(nuevo_item)
                                                st.rerun()
                                        st.markdown("---")

        if st.session_state["rutina_borrador"]:
            st.markdown(f"**{len(st.session_state['rutina_borrador'])} ejercicios seleccionados.**")
            if st.button("💾 GUARDAR RUTINA SELECCIONADA", type="primary", use_container_width=True):
                if user_id:
                    db.guardar_plan_dia(user_id, fecha_str, st.session_state["rutina_borrador"])
                    st.success("¡Rutina guardada! Pasando a modo entrenamiento...")
                    time.sleep(1.5)
                    st.session_state["modo_edicion"] = False
                    st.rerun()
                else:
                    st.error("Debes iniciar sesión para guardar.")


    # =========================================================================
    # ESTADO B: MODO EJECUCIÓN (FLUJO LINEAL CORREGIDO)
    # =========================================================================
    else:
        c_title, c_edit = st.columns([2, 1], vertical_alignment="center")
        c_title.markdown(f"### 🔥 Entrenamiento: {fecha_corta}")
        if c_edit.button("✏️ Modificar Rutina", use_container_width=True):
            st.session_state["modo_edicion"] = True
            st.rerun()
            
        rutina_agrupada = {}
        for idx, item in enumerate(st.session_state["rutina_borrador"]):
            m = item.get("musculo", "Desconocido")
            e = item.get("equipo", "Desconocido")
            if m not in rutina_agrupada: rutina_agrupada[m] = {}
            if e not in rutina_agrupada[m]: rutina_agrupada[m][e] = []
            rutina_agrupada[m][e].append((idx, item))
            
        for musculo, equipos in rutina_agrupada.items():
            st.markdown(f"<div class='titulo-musculo'>{musculo}</div>", unsafe_allow_html=True)
            
            for equipo, ejercicios_lista in equipos.items():
                with st.expander(f"⚙️ {equipo} ({len(ejercicios_lista)} ejercicios)", expanded=False):
                    
                    for idx, item in ejercicios_lista:
                        hecho_key = f"done_{item['id_unico']}"
                        esta_hecho = st.session_state.get(hecho_key, False)
                        opacidad = "0.5" if esta_hecho else "1.0"
                        
                        with st.container(border=True):
                            if esta_hecho: st.success(f"✅ Completado")
                            
                            st.markdown(f"<div style='opacity: {opacidad};'>", unsafe_allow_html=True)
                            
                            # 1. Título
                            st.markdown(f"**{item['nombre']}**")
                            
                            # 2. Imagen en tamaño completo
                            url_gif = item.get("gif_url", "")
                            if url_gif and url_gif != "0": 
                                st.image(f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}", use_container_width=True)
                            
                            # 3. Instrucciones pegadas a la imagen
                            pasos_mostrar = extraer_instrucciones(item.get("instrucciones", []))
                            if pasos_mostrar:
                                with st.expander("📖 Cómo hacerlo", expanded=False):
                                    for paso in pasos_mostrar: st.write(f"- {paso}")
                            
                            st.write("") # Pequeño espacio visual
                            
                            # 4. Inputs con Nombres Completos (Series y Repeticiones)
                            c_s, c_r = st.columns(2)
                            item["series"] = c_s.number_input("Series", min_value=1, value=item["series"], key=f"s_{item['id_unico']}", disabled=esta_hecho)
                            item["reps"] = c_r.number_input("Repeticiones", min_value=1, value=item["reps"], key=f"r_{item['id_unico']}", disabled=esta_hecho)
                            st.number_input("Peso (kg)", min_value=0.0, step=1.0, value=0.0, key=f"peso_{item['id_unico']}", disabled=esta_hecho)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            st.checkbox("✅ Marcar como Realizado", key=hecho_key)
                        
                        st.write("") # Espaciado entre ejercicios
        
        st.divider()
        if st.button("🏁 GUARDAR PROGRESO EN BITÁCORA", type="primary", use_container_width=True):
            if user_id:
                db.guardar_plan_dia(user_id, fecha_str, st.session_state["rutina_borrador"])
                
                perfil = db.obtener_perfil(user_id)
                datos_ml_completados = []
                fecha_timestamp = datetime.now().isoformat()
                
                for item in st.session_state["rutina_borrador"]:
                    if st.session_state.get(f"done_{item['id_unico']}", False):
                        microdato = {
                            "id_evento": str(uuid.uuid4()), "timestamp": fecha_timestamp, "user_id": user_id,
                            "usuario": { "nombre": perfil.get("nombre", ""), "sexo": perfil.get("genero", ""), "edad": perfil.get("edad", 0), "estatura_cm": perfil.get("estatura", 0) },
                            "biometria_diaria": { "peso_kg": perfil.get("peso", 0.0), "medidas_cm": perfil.get("medidas", {}) },
                            "contexto_ambiental": { "lugar_entrenamiento": perfil_elegido, "clima": st.session_state.get("clima_actual", "Desconocido"), "temperatura_c": st.session_state.get("temp_actual", 25) },
                            "metrica_sesion": { "esfuerzo_rpe": 7, "objetivo_entrenamiento": "Planificación Manual" },
                            "ejercicio": { "id_api": item.get("id_api", ""), "nombre": item.get("nombre", ""), "musculo_objetivo": item.get("musculo", ""), "equipo_usado": item.get("equipo", "") },
                            "ejecucion": { "peso_levantado_kg": st.session_state.get(f"peso_{item['id_unico']}", 0.0), "completado": True }
                        }
                        datos_ml_completados.append(microdato)
                
                if datos_ml_completados:
                    guardar_en_bitacora_local(datos_ml_completados)
                    st.success(f"¡Brutal! {len(datos_ml_completados)} ejercicios guardados en la bitácora de ML. 🧠🏆")
                else:
                    st.info("Plan actualizado. (No marcaste ningún ejercicio como realizado).")
            else:
                st.error("Debes iniciar sesión para guardar.")