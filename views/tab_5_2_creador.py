import database as db
import streamlit as st
from views.tab_5_1_ia_engine import analizar_alimento_ia


def mostrar(user_id, fecha_str):
    st.caption(
        "💡 **Base de datos:** Registra alimentos empaquetados o recetas frecuentes en tu catálogo permanente con IA o Manual."
    )

    with st.expander("📦 Guardar en Catálogo", expanded=False):
        tab_ia, tab_manual = st.tabs(
            ["🤖 Analizador IA", "✍️ Registro Manual"]
        )

        with tab_ia:
            st.caption("Escanea la tabla o dicta la información del producto:")
            opcion_ia = st.radio(
                "Entrada:",
                ["📝 Texto", "🎙️ Voz", "📸 Foto"],
                horizontal=True,
                key=f"rad_ia_cat_{fecha_str}",
            )

            resultado_ia = None
            error_ia = None

            if opcion_ia == "📝 Texto":
                desc = st.text_area(
                    "Descripción:",
                    placeholder="Ej: Atún en agua marca D1 170g con 24g de proteína",
                    height=70,
                    key=f"txt_desc_cat_{fecha_str}",
                )
                if desc and st.button(
                    "✨ Analizar con IA",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_ia_txt_cat_{fecha_str}",
                ):
                    with st.status("Analizando...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(
                            texto_usuario=desc
                        )
                        if error_ia:
                            status.update(label="❌ Error", state="error")
                        else:
                            status.update(label="✅ Completado", state="complete")

            elif opcion_ia == "🎙️ Voz":
                audio_file = st.audio_input(
                    "Graba tu nota de voz:", key=f"audio_input_cat_{fecha_str}"
                )
                if audio_file and st.button(
                    "✨ Analizar Audio",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_ia_audio_cat_{fecha_str}",
                ):
                    with st.status("Procesando...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(
                            archivo_audio=audio_file
                        )
                        if error_ia:
                            status.update(label="❌ Error", state="error")
                        else:
                            status.update(label="✅ Completado", state="complete")

            elif opcion_ia == "📸 Foto":
                foto = st.camera_input(
                    "Foto de la tabla nutricional:",
                    key=f"cam_input_cat_{fecha_str}",
                )
                if foto and st.button(
                    "✨ Escanear Foto",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_ia_foto_cat_{fecha_str}",
                ):
                    with st.status("Escaneando...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(
                            archivo_imagen=foto
                        )
                        if error_ia:
                            status.update(label="❌ Error", state="error")
                        else:
                            status.update(label="✅ Completado", state="complete")

            if error_ia:
                st.error(f"⚠️ Error: {error_ia}")

            if resultado_ia:
                st.session_state["ia_cat_nom"] = resultado_ia.get("nombre", "")
                st.session_state["ia_cat_porc"] = str(
                    resultado_ia.get("porcion", "1 porción")
                )
                st.session_state["ia_cat_cal"] = int(
                    resultado_ia.get("calorias", 0)
                )
                st.session_state["ia_cat_pro"] = float(
                    resultado_ia.get("proteina", 0.0)
                )
                st.session_state["ia_cat_car"] = float(
                    resultado_ia.get("carbohidratos", 0.0)
                )
                st.session_state["ia_cat_gra"] = float(
                    resultado_ia.get("grasas", 0.0)
                )

                st.markdown(
                    f"""
                <div style="background: #181a20; border: 1px solid #2ecc71; border-radius: 8px; padding: 10px; margin-top: 8px;">
                    <div style="font-size: 0.95rem; font-weight: 700; color: #2ecc71;">🎉 {st.session_state['ia_cat_nom']} ({st.session_state['ia_cat_porc']})</div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; text-align: center; margin-top: 6px;">
                        <span class="badge-macro badge-kcal">{st.session_state['ia_cat_cal']} kcal</span>
                        <span class="badge-macro badge-pro">P: {st.session_state['ia_cat_pro']}g</span>
                        <span class="badge-macro badge-car">C: {st.session_state['ia_cat_car']}g</span>
                        <span class="badge-macro badge-gra">G: {st.session_state['ia_cat_gra']}g</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.caption(
                    "👉 Ve a '✍️ Registro Manual' para guardar el producto."
                )

        with tab_manual:
            with st.form(f"form_nuevo_alimento_cat_{fecha_str}"):
                nom_alim = st.text_input(
                    "Nombre del alimento:",
                    value=st.session_state.get("ia_cat_nom", ""),
                )
                porc_alim = st.text_input(
                    "Porción base (Ej: 100g, 1 lata):",
                    value=st.session_state.get("ia_cat_porc", ""),
                )

                c_cal, c_pro, c_car, c_gra = st.columns(4)
                cal_val = c_cal.number_input(
                    "Kcal",
                    min_value=0,
                    value=st.session_state.get("ia_cat_cal", 0),
                )
                pro_val = c_pro.number_input(
                    "Prot (g)",
                    min_value=0.0,
                    value=st.session_state.get("ia_cat_pro", 0.0),
                    step=0.1,
                )
                car_val = c_car.number_input(
                    "Carb (g)",
                    min_value=0.0,
                    value=st.session_state.get("ia_cat_car", 0.0),
                    step=0.1,
                )
                gra_val = c_gra.number_input(
                    "Grasa (g)",
                    min_value=0.0,
                    value=st.session_state.get("ia_cat_gra", 0.0),
                    step=0.1,
                )

                es_pub = st.checkbox(
                    "🌐 Compartir con la comunidad", value=True
                )
                btn_crear = st.form_submit_button(
                    "💾 Guardar en Catálogo",
                    type="primary",
                    use_container_width=True,
                )

                if btn_crear:
                    if not nom_alim or not porc_alim:
                        st.warning("⚠️ Completa el nombre y la porción.")
                    else:
                        nuevo_doc = {
                            "nombre": nom_alim,
                            "porcion": porc_alim,
                            "calorias": int(cal_val),
                            "proteina": float(pro_val),
                            "carbohidratos": float(car_val),
                            "grasas": float(gra_val),
                        }
                        if db.guardar_alimento_personalizado(
                            user_id, nuevo_doc, es_publico=es_pub
                        ):
                            st.success("✅ Guardado en catálogo")
                            for k in [
                                "ia_cat_nom",
                                "ia_cat_porc",
                                "ia_cat_cal",
                                "ia_cat_pro",
                                "ia_cat_car",
                                "ia_cat_gra",
                            ]:
                                st.session_state.pop(k, None)
                            st.rerun()