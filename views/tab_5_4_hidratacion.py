import database as db
import streamlit as st


def mostrar(
    user_id, fecha_str, registro_dia, comidas_guardadas, calcular_totales_dia_func
):
    with st.container(border=True):
        st.markdown(
            "<div class='titulo-nutricion'>💧 Hidratación Graduable & Suplementos</div>",
            unsafe_allow_html=True,
        )
        datos_hidra = registro_dia.get("hidratacion_suplementos", {})

        agua_key = f"val_agua_{fecha_str}"
        if agua_key not in st.session_state:
            st.session_state[agua_key] = float(
                datos_hidra.get("agua_litros", 0.0)
            )

        agua_actual = st.session_state[agua_key]
        meta_agua = 3.0
        progreso = min(agua_actual / meta_agua, 1.0)

        # WIDGET VISUAL DE AGUA
        st.markdown(
            f"""
        <div class="agua-box">
            <div style="font-size:0.8rem; color:#94a3b8; font-weight:700; text-transform:uppercase;">Agua Consumida Hoy</div>
            <div class="agua-val">{agua_actual:.2f} <span style="font-size:1.1rem; color:#94a3b8;">/ {meta_agua:.1f} L</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.progress(progreso)

        # HELPER PARA GUARDADO AUTOMÁTICO INSTANTÁNEO EN FIREBASE
        def actualizar_y_guardar_agua(
            nuevo_valor_litros, mensaje_toast="💧 Agua actualizada"
        ):
            val_final = max(0.0, round(nuevo_valor_litros, 2))
            st.session_state[agua_key] = val_final
            datos_hidra["agua_litros"] = val_final

            db.guardar_nutricion(
                user_id,
                fecha_str,
                {
                    "user_id": user_id,
                    "fecha": fecha_str,
                    "comidas": comidas_guardadas,
                    "totales": calcular_totales_dia_func(comidas_guardadas),
                    "hidratacion_suplementos": datos_hidra,
                },
            )
            st.toast(mensaje_toast, icon="⚡")
            st.rerun()

        # BOTONES RÁPIDOS DE ADICIÓN CON GUARDADO INSTANTÁNEO
        st.markdown(
            "<p style='font-size:0.8rem; color:#94a3b8; font-weight:600; margin-top:10px; margin-bottom:4px;'>Ajuste rápido (Guardado automático):</p>",
            unsafe_allow_html=True,
        )
        c_w1, c_w2, c_w3, c_w4 = st.columns(4)
        if c_w1.button(
            "+200 ml", use_container_width=True, key=f"w200_{fecha_str}"
        ):
            actualizar_y_guardar_agua(
                agua_actual + 0.20, "💧 +200 ml registrados"
            )

        if c_w2.button(
            "+300 ml", use_container_width=True, key=f"w300_{fecha_str}"
        ):
            actualizar_y_guardar_agua(
                agua_actual + 0.30, "💧 +300 ml registrados"
            )

        if c_w3.button(
            "+500 ml", use_container_width=True, key=f"w500_{fecha_str}"
        ):
            actualizar_y_guardar_agua(
                agua_actual + 0.50, "💧 +500 ml registrados"
            )

        if c_w4.button(
            "➖ 200ml", use_container_width=True, key=f"w_sub_{fecha_str}"
        ):
            actualizar_y_guardar_agua(
                agua_actual - 0.20, "💧 -200 ml ajustados"
            )

        # DIGITACIÓN MANUAL CON GUARDADO INSTANTÁNEO
        st.markdown(
            "<p style='font-size:0.8rem; color:#94a3b8; font-weight:600; margin-top:10px; margin-bottom:4px;'>O digita la cantidad exacta (ml):</p>",
            unsafe_allow_html=True,
        )
        c_custom_val, c_custom_btn = st.columns(
            [2, 1], vertical_alignment="bottom"
        )

        ml_custom = c_custom_val.number_input(
            "Cantidad manual en ml",
            min_value=0,
            max_value=3000,
            value=250,
            step=50,
            key=f"input_custom_ml_{fecha_str}",
            label_visibility="collapsed",
        )

        if c_custom_btn.button(
            "➕ Sumar ML",
            use_container_width=True,
            key=f"btn_custom_ml_{fecha_str}",
        ):
            if ml_custom > 0:
                litros_a_sumar = ml_custom / 1000.0
                actualizar_y_guardar_agua(
                    agua_actual + litros_a_sumar, f"💧 +{ml_custom} ml agregados"
                )

        st.divider()

        # SECCIÓN DE SUPLEMENTOS
        st.markdown(
            "<p style='font-size:0.85rem; font-weight:700; color:#ddd; margin-bottom:6px;'>Suplementación Diaria:</p>",
            unsafe_allow_html=True,
        )
        c_sup1, c_sup2 = st.columns(2)
        toma_prote = c_sup1.checkbox(
            "🥤 Batido Proteína",
            value=datos_hidra.get("proteina", False),
            key=f"chk_pro_{fecha_str}",
        )
        toma_creatina = c_sup2.checkbox(
            "⚡ Creatina (5g)",
            value=datos_hidra.get("creatina", False),
            key=f"chk_cre_{fecha_str}",
        )

        if st.button(
            "💾 Guardar Suplementos",
            key=f"btn_hidra_{fecha_str}",
            type="primary",
            use_container_width=True,
        ):
            datos_hidra["agua_litros"] = st.session_state[agua_key]
            datos_hidra["proteina"] = toma_prote
            datos_hidra["creatina"] = toma_creatina
            db.guardar_nutricion(
                user_id,
                fecha_str,
                {
                    "user_id": user_id,
                    "fecha": fecha_str,
                    "comidas": comidas_guardadas,
                    "totales": calcular_totales_dia_func(comidas_guardadas),
                    "hidratacion_suplementos": datos_hidra,
                },
            )
            st.toast("✅ Suplementos guardados en Firebase", icon="⚡")
            st.rerun()