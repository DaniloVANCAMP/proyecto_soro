import streamlit as st
import random
import uuid
import json
from datetime import datetime, timedelta, timezone
import database as db  # <-- IMPORTADO PARA GUARDAR DIRECTO EN FIREBASE

def extraer_instrucciones(datos_brutos):
    """Extrae las instrucciones en español de manera segura"""
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

def mostrar(ejercicios, equipos_seleccionados, perfil_actual, perfil_elegido, objetivo, BASE_MEDIA_URL, traducir_nombre_ejercicio, obtener_clima_api, guardar_en_bitacora):
    # CSS para mantener la estética Premium
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
    </style>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")

    st.markdown("### ⚡ Generador Inteligente")
    
    with st.container(border=True):
        col_gen1, col_gen2, col_gen3 = st.columns(3)
        with col_gen1:
            enfoque = st.selectbox(
                "Enfoque muscular:", 
                ["Cuerpo Completo", "Tren Superior", "Tren Inferior", "Personalizado"],
                key="gen_enfoque_muscular"
            )
        with col_gen2:
            duracion = st.number_input(
                "Duración (min):", 
                min_value=15, max_value=180, value=60, step=5,
                key="gen_duracion_min"
            )
        with col_gen3:
            ejercicios_por_musculo = st.number_input(
                "Ejercicios por músculo:", 
                min_value=1, max_value=6, value=2, step=1,
                key="gen_ej_por_musculo"
            )

        musculos_personalizados = []
        if enfoque == "Personalizado":
            lista_todos_musculos = sorted(list(set([ej.get("target_trad") for ej in ejercicios if ej.get("target_trad")])))
            musculos_personalizados = st.multiselect(
                "Selecciona los músculos:", 
                lista_todos_musculos,
                key="gen_musculos_personalizados"
            )

        btn_deshabilitado = (enfoque == "Personalizado" and len(musculos_personalizados) == 0)

        if st.button("⚡ GENERAR RUTINA", type="primary", use_container_width=True, disabled=btn_deshabilitado, key="gen_btn_generar"):
            candidatos_equipo = ejercicios
            if equipos_seleccionados:
                candidatos_equipo = [ej for ej in ejercicios if ej.get("equipment_trad") in equipos_seleccionados]

            # Definir qué músculos vamos a trabajar
            if enfoque == "Personalizado":
                musculos_objetivo = musculos_personalizados
            elif enfoque == "Tren Superior":
                musculos_objetivo = ["Pecho", "Dorsales", "Bíceps", "Tríceps", "Deltoides / Hombros", "Espalda Alta", "Antebrazos"]
            elif enfoque == "Tren Inferior":
                musculos_objetivo = ["Cuádriceps", "Glúteos", "Isquiotibiales / Femorales", "Pantorrillas / Gemelos", "Aductores", "Abductores"]
            else: # Cuerpo Completo
                musculos_objetivo = ["Pecho", "Dorsales", "Bíceps", "Tríceps", "Deltoides / Hombros", "Cuádriceps", "Isquiotibiales / Femorales", "Pantorrillas / Gemelos", "Abdominales"]

            rutina_nueva = []
            ids_seleccionados = set()

            for musculo in musculos_objetivo:
                cands = [ej for ej in candidatos_equipo if ej.get("target_trad") == musculo or musculo in str(ej.get("target_trad"))]
                cands_disponibles = [ej for ej in cands if ej.get("id") not in ids_seleccionados]
                
                if cands_disponibles:
                    seleccion = random.sample(cands_disponibles, min(ejercicios_por_musculo, len(cands_disponibles)))
                    for ej in seleccion:
                        ids_seleccionados.add(ej.get("id"))
                        nuevo_item = {
                            "id_unico": str(uuid.uuid4()),
                            "id_api": ej.get("id"),
                            "nombre": traducir_nombre_ejercicio(ej.get("name", "")),
                            "musculo": ej.get("target_trad", "Desconocido"),
                            "equipo": ej.get("equipment_trad", "Desconocido"),
                            "series": st.session_state.get("def_series", 3),
                            "reps": st.session_state.get("def_reps", 10),
                            "gif_url": ej.get("gif_url_correcta", ""),
                            "instrucciones": ej.get("instructions", [])
                        }
                        rutina_nueva.append(nuevo_item)

            if not rutina_nueva:
                st.error("⚠️ No hay ejercicios compatibles. Prueba agregando más equipos en la configuración.")
            else:
                st.session_state["rutina_generada"] = rutina_nueva
                st.session_state["candidatos_pool"] = candidatos_equipo

    # =========================================================
    # VISTA PREVIA Y EJECUCIÓN 
    # =========================================================
    if "rutina_generada" in st.session_state and st.session_state["rutina_generada"]:
        st.divider()
        st.markdown("### 📋 Tu Rutina Generada")
        
        # Agrupar por músculo y equipo
        rutina_agrupada = {}
        for idx, item in enumerate(st.session_state["rutina_generada"]):
            m = item.get("musculo", "Desconocido")
            e = item.get("equipo", "Desconocido")
            if m not in rutina_agrupada: rutina_agrupada[m] = {}
            if e not in rutina_agrupada[m]: rutina_agrupada[m][e] = []
            rutina_agrupada[m][e].append((idx, item))
            
        for musculo, equipos in rutina_agrupada.items():
            st.markdown(f"<div class='titulo-musculo'>{musculo}</div>", unsafe_allow_html=True)
            
            for equipo, ejercicios_lista in equipos.items():
                with st.expander(f"⚙️ {equipo} ({len(ejercicios_lista)} ejercicios)", expanded=True):
                    
                    for idx, item in ejercicios_lista:
                        hecho_key = f"gen_done_{item['id_unico']}"
                        esta_hecho = st.session_state.get(hecho_key, False)
                        opacidad = "0.5" if esta_hecho else "1.0"
                        
                        with st.container(border=True):
                            if esta_hecho: st.success("✅ Completado")
                            
                            st.markdown(f"<div style='opacity: {opacidad};'>", unsafe_allow_html=True)
                            
                            # 1. Título
                            st.markdown(f"**{item['nombre']}**")
                            
                            # 2. Imagen
                            url_gif = item.get("gif_url", "")
                            if url_gif and url_gif != "0": 
                                st.image(f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}", use_container_width=True)
                            
                            # 3. Instrucciones
                            pasos_mostrar = extraer_instrucciones(item.get("instrucciones", []))
                            if pasos_mostrar:
                                with st.expander("📖 Cómo hacerlo", expanded=False):
                                    for paso in pasos_mostrar: st.write(f"- {paso}")
                            
                            st.write("")
                            
                            # 4. Inputs de validación (Peso y RPE unidos)
                            c_s, c_r = st.columns(2)
                            item["series"] = c_s.number_input("Series", min_value=1, value=int(item.get("series", 3)), key=f"gs_{item['id_unico']}", disabled=esta_hecho)
                            item["reps"] = c_r.number_input("Repeticiones", min_value=1, value=int(item.get("reps", 10)), key=f"gr_{item['id_unico']}", disabled=esta_hecho)
                            
                            c_p, c_e = st.columns(2)
                            peso_val = c_p.number_input("Peso (kg)", min_value=0.0, step=1.0, value=float(st.session_state.get(f"gpeso_{item['id_unico']}", 0.0)), key=f"gpeso_{item['id_unico']}", disabled=esta_hecho)
                            rpe_val = c_e.number_input("Esfuerzo (RPE 1-10)", min_value=0, max_value=10, step=1, value=int(st.session_state.get(f"grpe_{item['id_unico']}", 0)), help="1=Muy Suave, 10=Fallo Muscular", key=f"grpe_{item['id_unico']}", disabled=esta_hecho)
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            # Validar que los datos tengan sentido antes de permitir marcar
                            es_valido = (peso_val > 0.0) and (rpe_val >= 1) and (item["series"] >= 1) and (item["reps"] >= 1)

                            # Acciones (Hecho y Cambiar)
                            col_check, col_swap = st.columns([1.5, 1], vertical_alignment="center")
                            with col_check:
                                if not es_valido:
                                    st.caption("⚠️ Ingresa el Peso (> 0 kg) y el RPE (1 a 10) para habilitar el registro.")
                                    st.checkbox("✅ Marcar Realizado", key=hecho_key, value=False, disabled=True)
                                else:
                                    st.checkbox("✅ Marcar Realizado", key=hecho_key)
                            with col_swap:
                                # Lógica de Swap Inteligente
                                if not esta_hecho:
                                    if st.button("🔄 Cambiar", key=f"swap_{item['id_unico']}", use_container_width=True):
                                        pool = st.session_state.get("candidatos_pool", ejercicios)
                                        ids_actuales = [ej["id_api"] for ej in st.session_state["rutina_generada"]]
                                        
                                        # Buscar alternativas del MISMO músculo que NO estén en la rutina actual
                                        alternativas = [c for c in pool if c.get("target_trad") == item["musculo"] and c.get("id") not in ids_actuales]
                                        
                                        if alternativas:
                                            nuevo_ej = random.choice(alternativas)
                                            item["id_api"] = nuevo_ej.get("id")
                                            item["nombre"] = traducir_nombre_ejercicio(nuevo_ej.get("name", ""))
                                            item["equipo"] = nuevo_ej.get("equipment_trad", "Desconocido")
                                            item["gif_url"] = nuevo_ej.get("gif_url_correcta", "")
                                            item["instrucciones"] = nuevo_ej.get("instructions", [])
                                            st.rerun()
                                        else:
                                            st.toast("⚠️ No hay más alternativas para este músculo con tu equipo actual.", icon="⚠️")
                        
                        st.write("")

        # === NUEVO BOTÓN INFERIOR DE GUARDADO (IGUAL QUE EN PLANIFICADOR) ===
        st.divider()
        if st.button(
            "🏁 GUARDAR PROGRESO EN BITÁCORA",
            type="primary",
            use_container_width=True,
            key="btn_guardar_generador"
        ):
            if user_id:
                perfil = db.obtener_perfil(user_id) or {}
                datos_ml_completados = []
                
                zona_colombia = timezone(timedelta(hours=-5))
                fecha_str = datetime.now(zona_colombia).strftime("%Y-%m-%d")
                hora_actual = datetime.now(zona_colombia).strftime("%H:%M:%S.%f")
                fecha_timestamp = f"{fecha_str}T{hora_actual}"

                for item in st.session_state["rutina_generada"]:
                    hecho_key = f"gen_done_{item['id_unico']}"
                    
                    if st.session_state.get(hecho_key, False):
                        peso_cargado = st.session_state.get(f"gpeso_{item['id_unico']}", 0.0)
                        rpe_cargado = st.session_state.get(f"grpe_{item['id_unico']}", 0)
                        series_cargadas = st.session_state.get(f"gs_{item['id_unico']}", int(item.get("series", 3)))
                        reps_cargadas = st.session_state.get(f"gr_{item['id_unico']}", int(item.get("reps", 10)))

                        microdato = {
                            "id_evento": str(uuid.uuid4()),
                            "timestamp": fecha_timestamp,
                            "user_id": user_id,
                            "usuario": {
                                "nombre": perfil.get("nombre", ""),
                                "sexo": perfil.get("genero", ""),
                                "edad": perfil.get("edad", 0),
                                "estatura_cm": perfil.get("estatura", 0),
                            },
                            "biometria_diaria": {
                                "peso_kg": perfil.get("peso", 0.0),
                                "medidas_cm": perfil.get("medidas", {}),
                            },
                            "contexto_ambiental": {
                                "lugar_entrenamiento": perfil_elegido,
                                "equipamiento": st.session_state.get("config_equipo_actual", "Ninguno"),
                                "clima": st.session_state.get("clima_actual", "Desconocido"),
                                "temperatura_c": st.session_state.get("temp_actual", 25),
                            },
                            "metrica_sesion": {
                                "esfuerzo_rpe": rpe_cargado,
                                "objetivo_entrenamiento": st.session_state.get("config_objetivo", objetivo),
                            },
                            "ejercicio": {
                                "id_api": item.get("id_api", ""),
                                "nombre": item.get("nombre", ""),
                                "musculo_objetivo": item.get("musculo", ""),
                                "equipo_usado": item.get("equipo", ""),
                            },
                            "ejecucion": {
                                "series": series_cargadas,
                                "reps": reps_cargadas,
                                "peso_levantado_kg": peso_cargado,
                                "esfuerzo_rpe": rpe_cargado,
                                "completado": True,
                            },
                        }
                        datos_ml_completados.append(microdato)

                if datos_ml_completados:
                    db.guardar_en_bitacora(datos_ml_completados)
                    st.success(f"¡Brutal! {len(datos_ml_completados)} ejercicios guardados directamente en Firebase. 🧠🏆")
                else:
                    st.info("Plan actualizado. (No marcaste ningún ejercicio como realizado).")
            else:
                st.error("Debes iniciar sesión para guardar.")