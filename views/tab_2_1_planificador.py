import json
import os
import time
import uuid
from datetime import date, datetime, timedelta, timezone
import streamlit as st
import database as db


def extraer_instrucciones(datos_brutos):
    if not datos_brutos:
        return []
    if isinstance(datos_brutos, str):
        try:
            datos = json.loads(datos_brutos)
        except:
            datos = [datos_brutos]
    else:
        datos = datos_brutos

    pasos = []
    if isinstance(datos, dict):
        pasos = datos.get(
            "es", datos.get("en", list(datos.values())[0] if datos else [])
        )
    elif isinstance(datos, list):
        pasos = datos

    if isinstance(pasos, str):
        pasos = [pasos]
    return pasos


def obtener_plan_con_recurrencia(user_id, fecha_obj):
    if not user_id:
        return []
    fecha_str = fecha_obj.strftime("%Y-%m-%d")
    plan = db.obtener_plan_dia(user_id, fecha_str)

    if not plan:
        for sem in range(1, 5):
            fecha_pasada = (fecha_obj - timedelta(weeks=sem)).strftime("%Y-%m-%d")
            plan_pasado = db.obtener_plan_dia(user_id, fecha_pasada)
            if plan_pasado:
                return plan_pasado
    return plan or []


def mostrar(
    ejercicios,
    equipos_seleccionados,
    perfil_elegido,
    BASE_MEDIA_URL,
    traducir_nombre_ejercicio,
):
    # CSS UI PREMIUM: Tarjetas, Encabezados Flexibles y Delimitadores Limpios
    st.markdown(
        """
        <style>
        /* Encabezado Principal Flex de Sesión */
        .header-card {
            background: #1a1c24;
            border: 1px solid #2d303e;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        .header-title {
            color: #ffffff;
            font-size: 1.25rem;
            font-weight: 800;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .header-date {
            background: #252836;
            border: 1px solid #3d4154;
            color: #e74c3c;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.95rem;
        }

        /* Delimitador de Secciones de Músculo */
        .titulo-musculo-card {
            background: rgba(231, 76, 60, 0.08);
            border-left: 4px solid #e74c3c;
            border-radius: 0px 8px 8px 0px;
            padding: 8px 14px;
            margin-top: 18px;
            margin-bottom: 12px;
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id")

    st.markdown("### 🗓️ Tu Calendario Semanal")
    
    # HORA COLOMBIA SIN LIBRERÍAS EXTERNAS (UTC -5)
    zona_colombia = timezone(timedelta(hours=-5))
    hoy = datetime.now(zona_colombia).date()
    
    lunes = hoy - timedelta(days=hoy.weekday())
    dias_nombres = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"]

    if "dia_activo" not in st.session_state:
        st.session_state["dia_activo"] = hoy

    cols_dias = st.columns(7)
    for i, col in enumerate(cols_dias):
        fecha_iter = lunes + timedelta(days=i)
        rutina_previa = obtener_plan_con_recurrencia(user_id, fecha_iter)

        es_hoy = fecha_iter == hoy
        es_activo = fecha_iter == st.session_state["dia_activo"]

        num_dia = fecha_iter.strftime("%d")
        indicador = "🔥" if rutina_previa else "⚪"
        subtexto = "📍 HOY" if es_hoy else indicador

        texto_boton = f"{dias_nombres[i]} {num_dia}\n{subtexto}"

        # Colores nativos en vez de CSS forzado
        tipo_boton = "primary" if es_activo else "secondary"

        with col:
            if st.button(
                texto_boton, key=f"btn_dia_{i}", use_container_width=True, type=tipo_boton
            ):
                st.session_state["dia_activo"] = fecha_iter
                st.rerun()

    fecha_seleccionada = st.session_state["dia_activo"]
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    fecha_corta = fecha_seleccionada.strftime("%d/%m/%Y")

    if st.session_state.get("ultimo_dia_visto") != fecha_str:
        st.session_state["rutina_borrador"] = obtener_plan_con_recurrencia(
            user_id, fecha_seleccionada
        )
        st.session_state["ultimo_dia_visto"] = fecha_str
        st.session_state["modo_edicion"] = (
            len(st.session_state["rutina_borrador"]) == 0
        )

    st.markdown("---")

    # =========================================================================
    # ESTADO A: MODO CREACIÓN / EDICIÓN
    # =========================================================================
    if st.session_state.get("modo_edicion", True):
        # Tarjeta Header Delimitada
        st.markdown(
            f"""
            <div class="header-card">
                <div class="header-title">🛠️ Armar Rutina</div>
                <div class="header-date">📅 {fecha_corta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if len(st.session_state["rutina_borrador"]) > 0:
            if st.button("⬅️ Volver al Entrenamiento", use_container_width=True):
                st.session_state["modo_edicion"] = False
                st.rerun()

        ejercicios_plan = (
            [
                ej
                for ej in ejercicios
                if ej.get("equipment_trad") in equipos_seleccionados
            ]
            if equipos_seleccionados
            else []
        )

        with st.container(border=True):
            if not ejercicios_plan:
                st.warning(
                    "Selecciona al menos un equipo en la configuración superior para"
                    " ver opciones."
                )
            else:
                todos_los_musculos = sorted(
                    list(
                        set([
                            ej.get("target_trad")
                            for ej in ejercicios_plan
                            if ej.get("target_trad")
                        ])
                    )
                )
                musculos_elegidos = st.multiselect(
                    "🎯 Filtra por Músculo(s):", todos_los_musculos
                )

                if musculos_elegidos:
                    nombres_usados = [
                        ej["nombre"] for ej in st.session_state["rutina_borrador"]
                    ]

                    for musculo in musculos_elegidos:
                        st.markdown(
                            f"<div class='titulo-musculo-card'>💪 {musculo}</div>",
                            unsafe_allow_html=True,
                        )
                        ej_musculo = [
                            ej
                            for ej in ejercicios_plan
                            if ej.get("target_trad") == musculo
                        ]
                        equipos_viables = sorted(
                            list(
                                set([
                                    ej.get("equipment_trad")
                                    for ej in ej_musculo
                                    if ej.get("equipment_trad")
                                ])
                            )
                        )

                        for equipo in equipos_viables:
                            ej_finales = [
                                ej
                                for ej in ej_musculo
                                if ej.get("equipment_trad") == equipo
                                and traducir_nombre_ejercicio(ej.get("name", ""))
                                not in nombres_usados
                            ]

                            if ej_finales:
                                with st.expander(f"⚙️ {equipo}", expanded=False):
                                    for ej_data in ej_finales:
                                        nombre_ej = traducir_nombre_ejercicio(
                                            ej_data.get("name", "")
                                        )
                                        st.markdown(f"**{nombre_ej}**")
                                        c_img, c_info = st.columns([1, 1])

                                        with c_img:
                                            url_gif = ej_data.get("gif_url_correcta")
                                            if url_gif and url_gif != "0":
                                                st.image(
                                                    f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}",
                                                    use_container_width=True,
                                                )

                                        with c_info:
                                            pasos_mostrar = extraer_instrucciones(
                                                ej_data.get("instructions", [])
                                            )
                                            if pasos_mostrar:
                                                with st.expander("📖 Explicación"):
                                                    for paso in pasos_mostrar[:3]:
                                                        st.caption(f"- {paso}")

                                            if st.button(
                                                "➕ Añadir",
                                                key=f"sel_{ej_data['id']}",
                                                use_container_width=True,
                                            ):
                                                nuevo_item = {
                                                    "id_unico": str(uuid.uuid4()),
                                                    "id_api": ej_data.get("id"),
                                                    "nombre": nombre_ej,
                                                    "musculo": musculo,
                                                    "equipo": equipo,
                                                    "series": 3,
                                                    "reps": 10,
                                                    "gif_url": ej_data.get("gif_url_correcta", ""),
                                                    "instrucciones": ej_data.get("instructions", []),
                                                }
                                                st.session_state["rutina_borrador"].append(nuevo_item)
                                                st.rerun()
                                        st.markdown("---")

        if st.session_state["rutina_borrador"]:
            st.markdown(
                f"**{len(st.session_state['rutina_borrador'])} ejercicios"
                " seleccionados.**"
            )
            if st.button(
                "💾 GUARDAR RUTINA SELECCIONADA",
                type="primary",
                use_container_width=True,
            ):
                if user_id:
                    db.guardar_plan_dia(
                        user_id, fecha_str, st.session_state["rutina_borrador"]
                    )
                    st.success("¡Rutina guardada! Pasando a modo entrenamiento...")
                    time.sleep(1.2)
                    st.session_state["modo_edicion"] = False
                    st.rerun()
                else:
                    st.error("Debes iniciar sesión para guardar.")

    # =========================================================================
    # ESTADO B: MODO EJECUCIÓN (CON TARJETAS Y CONTENEDORES DELIMITADOS)
    # =========================================================================
    else:
        # Header Tarjeta Delimitada
        st.markdown(
            f"""
            <div class="header-card">
                <div class="header-title">🔥 Entrenamiento</div>
                <div class="header-date">📅 {fecha_corta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("✏️ Modificar Rutina", use_container_width=True):
            st.session_state["modo_edicion"] = True
            st.rerun()

        rutina_agrupada = {}
        for idx, item in enumerate(st.session_state["rutina_borrador"]):
            m = item.get("musculo", "Desconocido")
            e = item.get("equipo", "Desconocido")
            
            # EL CAMBIO ESTÁ AQUÍ (Línea 337 original): se inicializa como {} en vez de []
            if m not in rutina_agrupada:
                rutina_agrupada[m] = {}
            if e not in rutina_agrupada[m]:
                rutina_agrupada[m][e] = []
                
            rutina_agrupada[m][e].append((idx, item))

        for musculo, equipos in rutina_agrupada.items():
            st.markdown(
                f"<div class='titulo-musculo-card'>💪 {musculo}</div>",
                unsafe_allow_html=True,
            )

            for equipo, ejercicios_lista in equipos.items():
                with st.expander(
                    f"⚙️ {equipo} ({len(ejercicios_lista)} ejercicios)", expanded=True
                ):

                    for idx, item in ejercicios_lista:
                        hecho_key = f"done_{item['id_unico']}"
                        esta_hecho = st.session_state.get(hecho_key, False)
                        opacidad = "0.5" if esta_hecho else "1.0"

                        with st.container(border=True):
                            if esta_hecho:
                                st.success("✅ Completado")

                            st.markdown(
                                f"<div style='opacity: {opacidad};'>", unsafe_allow_html=True
                            )
                            st.markdown(f"#### {item['nombre']}")

                            url_gif = item.get("gif_url", "")
                            if url_gif and url_gif != "0":
                                st.image(
                                    f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}",
                                    use_container_width=True,
                                )

                            pasos_mostrar = extraer_instrucciones(
                                item.get("instrucciones", [])
                            )
                            if pasos_mostrar:
                                with st.expander("📖 Cómo hacerlo", expanded=False):
                                    for paso in pasos_mostrar:
                                        st.write(f"- {paso}")

                            st.markdown("<br>", unsafe_allow_html=True)

                            # Inputs de Rendimiento Organizadamente Enmarcados
                            with st.container(border=True):
                                st.caption("📊 **Métricas de Ejecución Real**")
                                c_s, c_r = st.columns(2)
                                item["series"] = c_s.number_input(
                                    "Series",
                                    min_value=1,
                                    value=int(item.get("series", 3)),
                                    key=f"s_{item['id_unico']}",
                                )
                                item["reps"] = c_r.number_input(
                                    "Repeticiones",
                                    min_value=1,
                                    value=int(item.get("reps", 10)),
                                    key=f"r_{item['id_unico']}",
                                )

                                c_p, c_e = st.columns(2)
                                peso_val = c_p.number_input(
                                    "Peso (kg)",
                                    min_value=0.0,
                                    step=1.0,
                                    value=float(
                                        st.session_state.get(f"peso_{item['id_unico']}", 0.0)
                                    ),
                                    key=f"peso_{item['id_unico']}",
                                )
                                rpe_val = c_e.number_input(
                                    "Esfuerzo (RPE 1-10)",
                                    min_value=0,
                                    max_value=10,
                                    step=1,
                                    value=int(
                                        st.session_state.get(f"rpe_{item['id_unico']}", 0)
                                    ),
                                    help="1=Muy Suave, 10=Fallo Muscular",
                                    key=f"rpe_{item['id_unico']}",
                                )

                            st.markdown("</div>", unsafe_allow_html=True)

                            es_valido = (
                                (peso_val > 0.0)
                                and (rpe_val >= 1)
                                and (item["series"] >= 1)
                                and (item["reps"] >= 1)
                            )

                            # LA SOLUCIÓN AL BUG: Permitir marcar libremente si es válido
                            if not es_valido:
                                st.caption(
                                    "⚠️ Ingresa el Peso (> 0 kg) y el RPE (1 a 10) para"
                                    " habilitar el registro."
                                )
                                st.checkbox(
                                    "✅ Marcar como Realizado",
                                    key=hecho_key,
                                    value=False,
                                    disabled=True,
                                )
                            else:
                                st.checkbox(
                                    "✅ Marcar como Realizado",
                                    key=hecho_key,
                                )

                        st.write("")

        st.divider()
        if st.button(
            "🏁 GUARDAR PROGRESO EN BITÁCORA",
            type="primary",
            use_container_width=True,
        ):
            if user_id:
                db.guardar_plan_dia(
                    user_id, fecha_str, st.session_state["rutina_borrador"]
                )

                perfil = db.obtener_perfil(user_id) or {}
                datos_ml_completados = []
                
                # HORA COLOMBIA AL GUARDAR EN BITÁCORA
                hora_actual = datetime.now(zona_colombia).strftime("%H:%M:%S.%f")
                fecha_timestamp = f"{fecha_str}T{hora_actual}"

                for item in st.session_state["rutina_borrador"]:
                    if st.session_state.get(f"done_{item['id_unico']}", False):
                        peso_cargado = st.session_state.get(
                            f"peso_{item['id_unico']}", 0.0
                        )
                        rpe_cargado = st.session_state.get(f"rpe_{item['id_unico']}", 0)

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
                                "equipamiento": st.session_state.get(
                                    "config_equipo_actual", "Ninguno"
                                ),
                                "clima": st.session_state.get(
                                    "clima_actual", "Desconocido"
                                ),
                                "temperatura_c": st.session_state.get("temp_actual", 25),
                            },
                            "metrica_sesion": {
                                "esfuerzo_rpe": rpe_cargado,
                                "objetivo_entrenamiento": st.session_state.get(
                                    "config_objetivo", "Planificación Manual"
                                ),
                            },
                            "ejercicio": {
                                "id_api": item.get("id_api", ""),
                                "nombre": item.get("nombre", ""),
                                "musculo_objetivo": item.get("musculo", ""),
                                "equipo_usado": item.get("equipo", ""),
                            },
                            "ejecucion": {
                                "series": item.get("series", 3),
                                "reps": item.get("reps", 10),
                                "peso_levantado_kg": peso_cargado,
                                "esfuerzo_rpe": rpe_cargado,
                                "completado": True,
                            },
                        }
                        datos_ml_completados.append(microdato)

                if datos_ml_completados:
                    db.guardar_en_bitacora(datos_ml_completados)
                    st.success(
                        f"¡Brutal! {len(datos_ml_completados)} ejercicios guardados"
                        " directamente en Firebase. 🧠🏆"
                    )
                else:
                    st.info(
                        "Plan actualizado. (No marcaste ningún ejercicio como"
                        " realizado)."
                    )
            else:
                st.error("Debes iniciar sesión para guardar.")