import uuid
from datetime import datetime
import database as db
import streamlit as st
from views.tab_5_1_ia_engine import analizar_alimento_ia


def inicializar_carrito(fecha_str, clave_comida):
    key = f"carrito_{clave_comida}_{fecha_str}"
    if key not in st.session_state:
        st.session_state[key] = []
    return key


def mostrar(
    user_id,
    fecha_str,
    comidas_guardadas,
    catalogo_alimentos,
    calcular_totales_dia_func,
    zona_colombia,
):
    st.markdown(
        "<div class='titulo-nutricion'>🍲 Constructor de Platos</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Añade ingredientes desde tu **Catálogo** o usa **IA Rápida** (Voz, Foto o Texto) dentro de cada comida."
    )

    config_comidas = [
        ("☕ Desayuno", "Desayuno"),
        ("🍲 Almuerzo", "Almuerzo"),
        ("🥗 Cena", "Cena"),
        ("🍎 Snacks", "Snacks"),
    ]

    for label_ui, clave_comida in config_comidas:
        items_consolidados = comidas_guardadas.get(clave_comida, [])
        carrito_key = inicializar_carrito(fecha_str, clave_comida)

        cnt_key = f"cnt_{clave_comida}_{fecha_str}"
        if cnt_key not in st.session_state:
            st.session_state[cnt_key] = 0
        sel_key = (
            f"sel_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"
        )
        cant_key = (
            f"cant_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"
        )

        with st.expander(
            f"{label_ui} ({len(items_consolidados)} guardados)", expanded=False
        ):
            if items_consolidados:
                st.markdown(
                    "<p style='font-size: 0.8rem; color: #888; margin-bottom: 6px;'><b>Alimentos guardados:</b></p>",
                    unsafe_allow_html=True,
                )

                indices_guardados_borrar = []
                for idx_g, it in enumerate(items_consolidados):
                    col_info_g, col_btn_g = st.columns(
                        [5, 1], vertical_alignment="center"
                    )
                    hora_txt = f"[{it['hora']}] " if "hora" in it else ""

                    with col_info_g:
                        st.markdown(
                            f"""
                        <div class="item-guardado-card">
                            <div class="item-title">• {hora_txt}<b>{it['nombre']}</b> ({it['porciones']}x)</div>
                            <div>
                                <span class="badge-macro badge-kcal">🔥 {it['calorias']} kcal</span>
                                <span class="badge-macro badge-pro">💪 P: {it['proteina']}g</span>
                                <span class="badge-macro badge-car">🌾 C: {it['carbohidratos']}g</span>
                                <span class="badge-macro badge-gra">🥑 G: {it['grasas']}g</span>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with col_btn_g:
                        if st.button(
                            "🗑️",
                            key=f"del_db_{clave_comida}_{fecha_str}_{idx_g}",
                            help="Eliminar de Firebase",
                        ):
                            indices_guardados_borrar.append(idx_g)

                if indices_guardados_borrar:
                    for i in sorted(indices_guardados_borrar, reverse=True):
                        comidas_guardadas[clave_comida].pop(i)
                    db.guardar_nutricion(
                        user_id,
                        fecha_str,
                        {
                            "user_id": user_id,
                            "fecha": fecha_str,
                            "comidas": comidas_guardadas,
                            "totales": calcular_totales_dia_func(
                                comidas_guardadas
                            ),
                        },
                    )
                    st.toast(
                        f"🗑️ Ítem eliminado de {clave_comida}", icon="✅"
                    )
                    st.rerun()

                st.divider()

            tab_cat, tab_ia_fast = st.tabs(["🔍 Catálogo", "✨ IA Rápida"])

            with tab_cat:
                alimento_sel = st.selectbox(
                    f"Añadir ingrediente a {clave_comida}:",
                    [""] + list(catalogo_alimentos.keys()),
                    key=sel_key,
                )

                if alimento_sel != "":
                    datos_base = catalogo_alimentos[alimento_sel]
                    hora_snack_str = ""

                    c_porc, c_add = st.columns(
                        [2, 1], vertical_alignment="bottom"
                    )
                    porciones = c_porc.number_input(
                        "Porciones",
                        min_value=0.5,
                        value=1.0,
                        step=0.5,
                        key=cant_key,
                    )

                    if clave_comida == "Snacks":
                        hora_snack_str = st.time_input(
                            "⏰ Hora del snack:",
                            value=datetime.now(zona_colombia).time(),
                            key=f"hora_{fecha_str}_{len(items_consolidados)}",
                        ).strftime("%I:%M %p")

                    if c_add.button(
                        "➕ Añadir",
                        key=f"btn_add_{clave_comida}_{fecha_str}",
                        use_container_width=True,
                    ):
                        nuevo_item = {
                            "id": str(uuid.uuid4()),
                            "nombre": alimento_sel,
                            "porciones": porciones,
                            "calorias": int(datos_base["cal"] * porciones),
                            "proteina": round(
                                datos_base["proteina"] * porciones, 1
                            ),
                            "carbohidratos": round(
                                datos_base["carbos"] * porciones, 1
                            ),
                            "grasas": round(
                                datos_base["grasas"] * porciones, 1
                            ),
                        }
                        if clave_comida == "Snacks":
                            nuevo_item["hora"] = hora_snack_str

                        st.session_state[carrito_key].append(nuevo_item)
                        st.session_state[cnt_key] += 1
                        st.rerun()

            with tab_ia_fast:
                opcion_ia_fast = st.radio(
                    "Capturar con IA:",
                    ["📝 Texto", "🎙️ Voz", "📸 Foto"],
                    horizontal=True,
                    key=f"rad_fast_{clave_comida}_{fecha_str}",
                )

                resultado_fast = None
                error_fast = None

                if opcion_ia_fast == "📝 Texto":
                    desc_fast = st.text_input(
                        "¿Qué comiste?",
                        placeholder="Ej: 2 huevos fritos con 1 arepa y 1 café",
                        key=f"txt_fast_{clave_comida}_{fecha_str}",
                    )
                    if desc_fast and st.button(
                        "✨ Calcular Macros",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_fast_txt_{clave_comida}_{fecha_str}",
                    ):
                        with st.status("Analizando...", expanded=True) as status:
                            resultado_fast, error_fast = analizar_alimento_ia(
                                texto_usuario=desc_fast
                            )
                            if error_fast:
                                status.update(label="❌ Error", state="error")
                            else:
                                status.update(label="✅ Listo", state="complete")

                elif opcion_ia_fast == "🎙️ Voz":
                    audio_fast = st.audio_input(
                        "Narra tu comida:",
                        key=f"audio_fast_{clave_comida}_{fecha_str}",
                    )
                    if audio_fast and st.button(
                        "✨ Analizar Voz",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_fast_aud_{clave_comida}_{fecha_str}",
                    ):
                        with st.status("Escuchando...", expanded=True) as status:
                            resultado_fast, error_fast = analizar_alimento_ia(
                                archivo_audio=audio_fast
                            )
                            if error_fast:
                                status.update(label="❌ Error", state="error")
                            else:
                                status.update(label="✅ Listo", state="complete")

                elif opcion_ia_fast == "📸 Foto":
                    foto_fast = st.camera_input(
                        "Foto de la comida:",
                        key=f"cam_fast_{clave_comida}_{fecha_str}",
                    )
                    if foto_fast and st.button(
                        "✨ Analizar Foto",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_fast_img_{clave_comida}_{fecha_str}",
                    ):
                        with st.status("Escaneando...", expanded=True) as status:
                            resultado_fast, error_fast = analizar_alimento_ia(
                                archivo_imagen=foto_fast
                            )
                            if error_fast:
                                status.update(label="❌ Error", state="error")
                            else:
                                status.update(label="✅ Listo", state="complete")

                if error_fast:
                    st.error(f"⚠️ Error: {error_fast}")

                if resultado_fast:
                    st.session_state[f"res_fast_{clave_comida}_{fecha_str}"] = (
                        resultado_fast
                    )

                res_guardado = st.session_state.get(
                    f"res_fast_{clave_comida}_{fecha_str}"
                )

                if res_guardado:
                    nom_i = res_guardado.get("nombre", "Comida IA")
                    porc_i = res_guardado.get("porcion", "1 porción")
                    cal_i = int(res_guardado.get("calorias", 0))
                    pro_i = float(res_guardado.get("proteina", 0.0))
                    car_i = float(res_guardado.get("carbohidratos", 0.0))
                    gra_i = float(res_guardado.get("grasas", 0.0))

                    st.markdown(
                        f"""
                    <div style="background: #181a20; border: 1px solid #2ecc71; border-radius: 8px; padding: 10px; margin-top: 8px;">
                        <div style="font-size: 0.9rem; font-weight: 700; color: #2ecc71;">🍽️ {nom_i} ({porc_i})</div>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; text-align: center; margin-top: 5px;">
                            <span class="badge-macro badge-kcal">{cal_i} kcal</span>
                            <span class="badge-macro badge-pro">P: {pro_i}g</span>
                            <span class="badge-macro badge-car">C: {car_i}g</span>
                            <span class="badge-macro badge-gra">G: {gra_i}g</span>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        "<p style='font-size:0.75rem; font-weight:600; color:#aaa; margin-top:6px;'>Opciones de registro:</p>",
                        unsafe_allow_html=True,
                    )
                    c_b1, c_b2, c_b3 = st.columns(3)

                    if c_b1.button(
                        "🟢 Solo este plato",
                        key=f"act_only_{clave_comida}_{fecha_str}",
                        use_container_width=True,
                    ):
                        item_ia = {
                            "id": str(uuid.uuid4()),
                            "nombre": nom_i,
                            "porciones": 1.0,
                            "calorias": cal_i,
                            "proteina": pro_i,
                            "carbohidratos": car_i,
                            "grasas": gra_i,
                        }
                        if clave_comida == "Snacks":
                            item_ia["hora"] = datetime.now(
                                zona_colombia
                            ).strftime("%I:%M %p")

                        st.session_state[carrito_key].append(item_ia)
                        st.session_state.pop(
                            f"res_fast_{clave_comida}_{fecha_str}", None
                        )
                        st.toast("✅ Sumado al plato", icon="🟢")
                        st.rerun()

                    if c_b2.button(
                        "🔵 + Mi Catálogo",
                        key=f"act_priv_{clave_comida}_{fecha_str}",
                        use_container_width=True,
                    ):
                        doc_cat = {
                            "nombre": nom_i,
                            "porcion": porc_i,
                            "calorias": cal_i,
                            "proteina": pro_i,
                            "carbohidratos": car_i,
                            "grasas": gra_i,
                        }
                        db.guardar_alimento_personalizado(
                            user_id, doc_cat, es_publico=False
                        )

                        item_ia = {
                            "id": str(uuid.uuid4()),
                            "nombre": nom_i,
                            "porciones": 1.0,
                            "calorias": cal_i,
                            "proteina": pro_i,
                            "carbohidratos": car_i,
                            "grasas": gra_i,
                        }
                        if clave_comida == "Snacks":
                            item_ia["hora"] = datetime.now(
                                zona_colombia
                            ).strftime("%I:%M %p")

                        st.session_state[carrito_key].append(item_ia)
                        st.session_state.pop(
                            f"res_fast_{clave_comida}_{fecha_str}", None
                        )
                        st.toast("✅ Guardado en catálogo", icon="🔵")
                        st.rerun()

                    if c_b3.button(
                        "🌐 + Comunidad",
                        key=f"act_pub_{clave_comida}_{fecha_str}",
                        use_container_width=True,
                    ):
                        doc_cat = {
                            "nombre": nom_i,
                            "porcion": porc_i,
                            "calorias": cal_i,
                            "proteina": pro_i,
                            "carbohidratos": car_i,
                            "grasas": gra_i,
                        }
                        db.guardar_alimento_personalizado(
                            user_id, doc_cat, es_publico=True
                        )

                        item_ia = {
                            "id": str(uuid.uuid4()),
                            "nombre": nom_i,
                            "porciones": 1.0,
                            "calorias": cal_i,
                            "proteina": pro_i,
                            "carbohidratos": car_i,
                            "grasas": gra_i,
                        }
                        if clave_comida == "Snacks":
                            item_ia["hora"] = datetime.now(
                                zona_colombia
                            ).strftime("%I:%M %p")

                        st.session_state[carrito_key].append(item_ia)
                        st.session_state.pop(
                            f"res_fast_{clave_comida}_{fecha_str}", None
                        )
                        st.toast("✅ Publicado e integrado", icon="🌐")
                        st.rerun()

            if st.session_state[carrito_key]:
                st.markdown(
                    f"<p style='font-size:0.8rem; font-weight:700; color:#2ecc71; margin-top:8px;'>🥣 En preparación ({len(st.session_state[carrito_key])}):</p>",
                    unsafe_allow_html=True,
                )
                indices_a_borrar = []

                for idx, temp_item in enumerate(st.session_state[carrito_key]):
                    col_txt, col_del = st.columns(
                        [5, 1], vertical_alignment="center"
                    )
                    with col_txt:
                        st.markdown(
                            f"<div class='carrito-item'>• <b>{temp_item['nombre']}</b> x{temp_item['porciones']} ({temp_item['calorias']} kcal)</div>",
                            unsafe_allow_html=True,
                        )
                    with col_del:
                        if st.button(
                            "🗑️",
                            key=f"del_cart_{clave_comida}_{fecha_str}_{idx}",
                        ):
                            indices_a_borrar.append(idx)

                if indices_a_borrar:
                    for i in sorted(indices_a_borrar, reverse=True):
                        st.session_state[carrito_key].pop(i)
                    st.rerun()

                if st.button(
                    f"💾 Guardar {clave_comida} en Firebase",
                    key=f"btn_save_{clave_comida}_{fecha_str}",
                    type="primary",
                    use_container_width=True,
                ):
                    microdatos_ml = []
                    ahora_col = datetime.now(zona_colombia)

                    for item in st.session_state[carrito_key]:
                        comidas_guardadas[clave_comida].append(item)
                        microdatos_ml.append({
                            "id_evento": item["id"],
                            "timestamp": ahora_col.isoformat(),
                            "user_id": user_id,
                            "categoria": "nutricion",
                            "tipo_comida": clave_comida,
                            "alimento": item["nombre"],
                            "porciones": item["porciones"],
                            "hora_registro": item.get(
                                "hora", ahora_col.strftime("%H:%M")
                            ),
                            "macros": {
                                "calorias": item["calorias"],
                                "proteina_g": item["proteina"],
                                "carbohidratos_g": item["carbohidratos"],
                                "grasas_g": item["grasas"],
                            },
                        })

                    db.guardar_nutricion(
                        user_id,
                        fecha_str,
                        {
                            "user_id": user_id,
                            "fecha": fecha_str,
                            "comidas": comidas_guardadas,
                            "totales": calcular_totales_dia_func(
                                comidas_guardadas
                            ),
                        },
                    )
                    db.guardar_en_bitacora(microdatos_ml)

                    st.session_state[carrito_key] = []
                    st.toast(f"✅ ¡{clave_comida} guardado!", icon="☁️")
                    st.rerun()