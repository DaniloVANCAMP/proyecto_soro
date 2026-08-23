import streamlit as st
import uuid
from datetime import date, datetime
import database as db

# Base de datos de alimentos
BASE_ALIMENTOS = {
    "Huevo cocido (1 ud)": {"cal": 78, "carbos": 0.6, "proteina": 6.0, "grasas": 5.0},
    "Huevo frito (1 ud)": {"cal": 90, "carbos": 0.4, "proteina": 6.3, "grasas": 7.0},
    "Arroz blanco cocido (100g)": {"cal": 130, "carbos": 28.0, "proteina": 2.7, "grasas": 0.3},
    "Pechuga a la plancha (100g)": {"cal": 165, "carbos": 0.0, "proteina": 31.0, "grasas": 3.6},
    "Frijoles cocidos (100g)": {"cal": 127, "carbos": 22.8, "proteina": 8.7, "grasas": 0.5},
    "Arepa de maíz (1 ud)": {"cal": 150, "carbos": 30.0, "proteina": 3.0, "grasas": 1.0},
    "Plátano / Banano cocido (1 ud)": {"cal": 110, "carbos": 28.0, "proteina": 1.2, "grasas": 0.2},
    "Queso campesino (50g)": {"cal": 160, "carbos": 1.5, "proteina": 9.0, "grasas": 13.0},
    "Café con leche (Vaso 200ml)": {"cal": 90, "carbos": 10.0, "proteina": 4.0, "grasas": 3.5},
    "Avena en hojuelas (50g)": {"cal": 190, "carbos": 33.0, "proteina": 6.5, "grasas": 3.0},
    "Batido de Proteína Whey (1 scoop)": {"cal": 120, "carbos": 3.0, "proteina": 24.0, "grasas": 1.5}
}

def calcular_totales_dia(comidas_dict):
    totales = {"cal": 0, "pro": 0.0, "car": 0.0, "gra": 0.0}
    for lista_items in comidas_dict.values():
        for item in lista_items:
            totales["cal"] += item.get("calorias", 0)
            totales["pro"] += item.get("proteina", 0.0)
            totales["car"] += item.get("carbohidratos", 0.0)
            totales["gra"] += item.get("grasas", 0.0)
    return totales

def inicializar_carrito(fecha_str, clave_comida):
    key = f"carrito_{clave_comida}_{fecha_str}"
    if key not in st.session_state:
        st.session_state[key] = []
    return key

def mostrar():
    st.markdown("""
    <style>
    .titulo-nutricion { color: #2ecc71; font-size: 1.4rem; font-weight: bold; margin-bottom: 10px; margin-top: 10px;}
    .metric-container {
        background-color: #1a1a1a; border: 1px solid #333; border-radius: 8px;
        padding: 12px 5px; text-align: center; margin-bottom: 10px;
    }
    .metric-value { font-size: 1.4rem; font-weight: bold; color: #ffffff; }
    .metric-label { font-size: 0.75rem; color: #aaaaaa; text-transform: uppercase; }
    .val-cal { color: #e74c3c; } .val-pro { color: #3498db; }
    .val-car { color: #f1c40f; } .val-gra { color: #e67e22; }
    .carrito-item { font-size: 0.9rem; color: #eee; background-color: #262626; padding: 6px 10px; border-radius: 5px; margin-bottom: 4px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 15px;">
        <span style="font-size: 2rem;">🍏</span>
        <h1 style="margin: 0; padding: 0; text-align: center; font-size: 2rem;">Nutrición & Macros</h1>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")
    hoy = date.today()

    with st.container(border=True):
        fecha_act = st.date_input("📅 Selecciona la fecha:", value=hoy)
    fecha_str = fecha_act.strftime("%Y-%m-%d")

    # CARGAR DATOS DE FIREBASE
    registro_dia = db.obtener_nutricion(user_id, fecha_str) or {}
    comidas_guardadas = registro_dia.get("comidas", {
        "Desayuno": [], "Almuerzo": [], "Cena": [], "Snacks": []
    })
    
    totales_dia = calcular_totales_dia(comidas_guardadas)

    # DASHBOARD
    st.markdown(f"<div class='titulo-nutricion'>Resumen Totales</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-container'><div class='metric-value val-cal'>{int(totales_dia['cal'])}</div><div class='metric-label'>Kcal</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-container'><div class='metric-value val-pro'>{round(totales_dia['pro'],1)}g</div><div class='metric-label'>Prot</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-container'><div class='metric-value val-car'>{round(totales_dia['car'],1)}g</div><div class='metric-label'>Carbs</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-container'><div class='metric-value val-gra'>{round(totales_dia['gra'],1)}g</div><div class='metric-label'>Grasas</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div class='titulo-nutricion'>Constructor de Platos</div>", unsafe_allow_html=True)
    
    config_comidas = [
        ("☕ Desayuno", "Desayuno"),
        ("🍲 Almuerzo", "Almuerzo"),
        ("🥗 Cena", "Cena"),
        ("🍎 Snacks", "Snacks")
    ]

    for label_ui, clave_comida in config_comidas:
        items_consolidados = comidas_guardadas.get(clave_comida, [])
        carrito_key = inicializar_carrito(fecha_str, clave_comida)
        
        # CONTADOR PARA REINICIAR WIDGET DE FORMA LIMPIA
        cnt_key = f"cnt_{clave_comida}_{fecha_str}"
        if cnt_key not in st.session_state:
            st.session_state[cnt_key] = 0

        sel_key = f"sel_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"
        cant_key = f"cant_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"

        with st.expander(f"{label_ui} ({len(items_consolidados)} alimentos guardados)", expanded=False):
            
            # 1. Mostrar lo que ya está guardado en Firebase para hoy
            if items_consolidados:
                st.markdown("**🍽️ Ya guardado en la nube:**")
                for it in items_consolidados:
                    hora_txt = f"[{it['hora']}] " if "hora" in it else ""
                    st.caption(f"• {hora_txt}**{it['nombre']}** ({it['porciones']}x) ➔ {it['calorias']} kcal | P:{it['proteina']}g | C:{it['carbohidratos']}g | G:{it['grasas']}g")
                st.divider()

            # 2. Buscador de Alimentos
            st.markdown(f"**Añadir ingrediente al plato:**")
            alimento_sel = st.selectbox(
                f"Buscar ingrediente ({clave_comida}):",
                [""] + list(BASE_ALIMENTOS.keys()),
                key=sel_key
            )
            
            if alimento_sel != "":
                datos_base = BASE_ALIMENTOS[alimento_sel]
                
                hora_snack_str = ""
                if clave_comida == "Snacks":
                    hora_snack = st.time_input("⏰ Hora del snack:", value=datetime.now().time(), key=f"hora_snack_{fecha_str}_{len(items_consolidados)}")
                    hora_snack_str = hora_snack.strftime("%I:%M %p")

                c_cant, c_add = st.columns([2, 1], vertical_alignment="bottom")
                porciones = c_cant.number_input("Porciones / Cantidad", min_value=0.5, value=1.0, step=0.5, key=cant_key)
                
                # BOTÓN AGREGAR INGREDIENTE
                if c_add.button("➕ Agregar al Plato", key=f"btn_add_{clave_comida}_{fecha_str}"):
                    nuevo_item = {
                        "id": str(uuid.uuid4()),
                        "nombre": alimento_sel,
                        "porciones": porciones,
                        "calorias": int(datos_base['cal'] * porciones),
                        "proteina": round(datos_base['proteina'] * porciones, 1),
                        "carbohidratos": round(datos_base['carbos'] * porciones, 1),
                        "grasas": round(datos_base['grasas'] * porciones, 1)
                    }
                    if clave_comida == "Snacks":
                        nuevo_item["hora"] = hora_snack_str
                        
                    # Añadir al plato temporal
                    st.session_state[carrito_key].append(nuevo_item)
                    
                    # Incrementar el contador para forzar un selector limpio en el próximo render
                    st.session_state[cnt_key] += 1
                    st.rerun()

            # 3. Mostrar el plato que se está armando actualmente
            if st.session_state[carrito_key]:
                st.write("")
                st.markdown(f"**🥣 Plato actual en construcción ({len(st.session_state[carrito_key])} ítems):**")
                
                indices_a_borrar = []
                for idx, temp_item in enumerate(st.session_state[carrito_key]):
                    col_txt, col_del = st.columns([5, 1], vertical_alignment="center")
                    with col_txt:
                        st.markdown(f"<div class='carrito-item'>• <b>{temp_item['nombre']}</b> x {temp_item['porciones']} ({temp_item['calorias']} kcal)</div>", unsafe_allow_html=True)
                    with col_del:
                        if st.button("🗑️", key=f"del_{clave_comida}_{fecha_str}_{idx}"):
                            indices_a_borrar.append(idx)

                # Si se hizo clic en borrar un elemento
                if indices_a_borrar:
                    for i in sorted(indices_a_borrar, reverse=True):
                        st.session_state[carrito_key].pop(i)
                    st.rerun()

                st.write("")
                # BOTÓN FINAL DE GUARDAR PLATO EN FIREBASE
                if st.button(f"💾 Guardar {clave_comida} completo en Firebase", key=f"btn_save_{clave_comida}_{fecha_str}", type="primary", use_container_width=True):
                    
                    microdatos_ml = []
                    for item in st.session_state[carrito_key]:
                        comidas_guardadas[clave_comida].append(item)
                        
                        microdatos_ml.append({
                            "id_evento": item["id"],
                            "timestamp": datetime.now().isoformat(),
                            "user_id": user_id,
                            "categoria": "nutricion",
                            "tipo_comida": clave_comida,
                            "alimento": item["nombre"],
                            "porciones": item["porciones"],
                            "hora_registro": item.get("hora", datetime.now().strftime("%H:%M")),
                            "macros": {
                                "calorias": item["calorias"], "proteina_g": item["proteina"],
                                "carbohidratos_g": item["carbohidratos"], "grasas_g": item["grasas"]
                            }
                        })
                    
                    # Guardar plato completo en Firebase
                    datos_actualizados = {
                        "user_id": user_id,
                        "fecha": fecha_str,
                        "comidas": comidas_guardadas,
                        "totales": calcular_totales_dia(comidas_guardadas)
                    }
                    db.guardar_nutricion(user_id, fecha_str, datos_actualizados)
                    db.guardar_en_bitacora(microdatos_ml)
                    
                    # Vaciar carrito
                    st.session_state[carrito_key] = []
                    
                    st.toast(f"✅ ¡{clave_comida} guardado exitosamente!", icon="☁️")
                    st.rerun()

    st.divider()

    # HIDRATACIÓN
    with st.container(border=True):
        st.markdown("### 💧 Hidratación y Extras")
        datos_hidra = registro_dia.get("hidratacion_suplementos", {})
        agua = st.slider("Agua (Litros)", 0.0, 6.0, float(datos_hidra.get("agua_litros", 2.0)), 0.25, key=f"sld_agua_{fecha_str}")
        
        c_sup1, c_sup2 = st.columns(2)
        toma_prote = c_sup1.checkbox("Batido Proteína", value=datos_hidra.get("proteina", False), key=f"chk_pro_{fecha_str}")
        toma_creatina = c_sup2.checkbox("Creatina (5g)", value=datos_hidra.get("creatina", False), key=f"chk_cre_{fecha_str}")

        if st.button("💾 Actualizar Hidratación", key=f"btn_hidra_{fecha_str}", use_container_width=True):
            datos_actualizados = {
                "user_id": user_id, "fecha": fecha_str,
                "comidas": comidas_guardadas, "totales": calcular_totales_dia(comidas_guardadas),
                "hidratacion_suplementos": {"agua_litros": agua, "proteina": toma_prote, "creatina": toma_creatina}
            }
            db.guardar_nutricion(user_id, fecha_str, datos_actualizados)
            st.toast("✅ Extras guardados en Firestore", icon="💧")
            st.rerun()