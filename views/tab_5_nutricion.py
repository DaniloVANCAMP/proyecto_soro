import streamlit as st
import uuid
import json
import os
from datetime import date, datetime
import database as db
import google.generativeai as genai
from PIL import Image

# ==========================================
# CONFIGURACIÓN DE IA (GEMINI)
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Forzamos a la IA a responder SOLO en formato JSON estructurado
    modelo_ia = genai.GenerativeModel(
        'gemini-1.5-flash', 
        generation_config={"response_mime_type": "application/json"}
    )
except Exception as e:
    modelo_ia = None
    st.error(f"⚠️ Error al configurar IA: {e}")

def analizar_alimento_ia(texto_usuario, archivo_imagen=None):
    if not modelo_ia: return None
    
    prompt_sistema = """
    Eres un nutricionista experto. Analiza el texto o la imagen de la tabla nutricional. 
    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta, calculando los totales de la porción principal. No incluyas markdown, solo el JSON:
    {
        "nombre": "Nombre del producto o plato",
        "porcion": "Ej: 100g, 1 paquete, 1 unidad",
        "calorias": 0,
        "proteina": 0.0,
        "carbohidratos": 0.0,
        "grasas": 0.0
    }
    Si no es exacto, haz tu mejor estimación profesional.
    """
    try:
        if archivo_imagen:
            img = Image.open(archivo_imagen)
            respuesta = modelo_ia.generate_content([prompt_sistema, img])
        else:
            respuesta = modelo_ia.generate_content([prompt_sistema, texto_usuario])
            
        return json.loads(respuesta.text)
    except Exception as e:
        print(f"Error IA: {e}")
        return None

# ==========================================
# CARGA HÍBRIDA DE ALIMENTOS
# ==========================================
@st.cache_data
def cargar_alimentos_base():
    ruta_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alimentos_base.json")
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Faltó crear el archivo 'alimentos_base.json'.")
        return {}

def obtener_catalogo_completo(user_id):
    base_fija = cargar_alimentos_base()
    base_comunidad = db.obtener_alimentos_comunitarios(user_id)
    return {**base_fija, **base_comunidad}

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

    registro_dia = db.obtener_nutricion(user_id, fecha_str) or {}
    comidas_guardadas = registro_dia.get("comidas", {
        "Desayuno": [], "Almuerzo": [], "Cena": [], "Snacks": []
    })
    
    CATALOGO_ALIMENTOS = obtener_catalogo_completo(user_id)
    totales_dia = calcular_totales_dia(comidas_guardadas)

    # DASHBOARD
    st.markdown(f"<div class='titulo-nutricion'>Resumen Totales</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-container'><div class='metric-value val-cal'>{int(totales_dia['cal'])}</div><div class='metric-label'>Kcal</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-container'><div class='metric-value val-pro'>{round(totales_dia['pro'],1)}g</div><div class='metric-label'>Prot</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-container'><div class='metric-value val-car'>{round(totales_dia['car'],1)}g</div><div class='metric-label'>Carbs</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-container'><div class='metric-value val-gra'>{round(totales_dia['gra'],1)}g</div><div class='metric-label'>Grasas</div></div>", unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # CREADOR DE ALIMENTOS CON IA INTEGRADA
    # ==========================================
    with st.expander("✨ Crear alimento con IA o Manualmente"):
        
        tab_ia, tab_manual = st.tabs(["🤖 Analizador IA", "✍️ Manual"])
        
        with tab_ia:
            st.caption("Toma una foto de una tabla nutricional o describe tu comida. La IA extraerá los macros por ti.")
            opcion_ia = st.radio("Método de entrada:", ["📸 Cámara", "📝 Texto"], horizontal=True)
            
            resultado_ia = None
            
            if opcion_ia == "📸 Cámara":
                foto = st.camera_input("Toma foto de la tabla nutricional")
                if foto and st.button("Analizar Foto con IA ✨", type="primary"):
                    with st.spinner("Procesando imagen con Gemini..."):
                        resultado_ia = analizar_alimento_ia("", archivo_imagen=foto)
            else:
                desc = st.text_area("Describe qué comiste", placeholder="Ej: Me comí una hamburguesa doble con queso y tocineta")
                if desc and st.button("Calcular con IA ✨", type="primary"):
                    with st.spinner("Analizando receta con Gemini..."):
                        resultado_ia = analizar_alimento_ia(desc)

            if resultado_ia:
                st.success("¡Análisis completado! Revisa los datos y guárdalos.")
                # Pre-llenamos el session_state para el formulario manual
                st.session_state['ia_nom'] = resultado_ia.get('nombre', '')
                st.session_state['ia_porc'] = str(resultado_ia.get('porcion', '1 porción'))
                st.session_state['ia_cal'] = int(resultado_ia.get('calorias', 0))
                st.session_state['ia_pro'] = float(resultado_ia.get('proteina', 0.0))
                st.session_state['ia_car'] = float(resultado_ia.get('carbohidratos', 0.0))
                st.session_state['ia_gra'] = float(resultado_ia.get('grasas', 0.0))

        with tab_manual:
            with st.form("form_nuevo_alimento"):
                # Usamos los datos de IA si existen, si no, vacíos
                nom_alim = st.text_input("Nombre", value=st.session_state.get('ia_nom', ''))
                porc_alim = st.text_input("Porción base", value=st.session_state.get('ia_porc', ''))
                
                c_cal, c_pro, c_car, c_gra = st.columns(4)
                cal_val = c_cal.number_input("Kcal", min_value=0, value=st.session_state.get('ia_cal', 0))
                pro_val = c_pro.number_input("Prot (g)", min_value=0.0, value=st.session_state.get('ia_pro', 0.0), step=0.1)
                car_val = c_car.number_input("Carb (g)", min_value=0.0, value=st.session_state.get('ia_car', 0.0), step=0.1)
                gra_val = c_gra.number_input("Grasa (g)", min_value=0.0, value=st.session_state.get('ia_gra', 0.0), step=0.1)
                
                es_pub = st.checkbox("🌐 Compartir con la comunidad", value=True)
                btn_crear = st.form_submit_button("💾 Guardar Alimento", type="primary")
                
                if btn_crear:
                    if not nom_alim or not porc_alim:
                        st.warning("⚠️ Ingresa nombre y porción.")
                    else:
                        nuevo_doc = {
                            "nombre": nom_alim, "porcion": porc_alim,
                            "calorias": int(cal_val), "proteina": float(pro_val),
                            "carbohidratos": float(car_val), "grasas": float(gra_val)
                        }
                        if db.guardar_alimento_personalizado(user_id, nuevo_doc, es_publico=es_pub):
                            st.success(f"✅ ¡'{nom_alim}' guardado!")
                            # Limpiar memoria de IA
                            for k in ['ia_nom', 'ia_porc', 'ia_cal', 'ia_pro', 'ia_car', 'ia_gra']:
                                st.session_state.pop(k, None)
                            st.rerun()

    st.divider()

    # ==========================================
    # CONSTRUCTOR DE PLATOS
    # ==========================================
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
        
        cnt_key = f"cnt_{clave_comida}_{fecha_str}"
        if cnt_key not in st.session_state: st.session_state[cnt_key] = 0
        sel_key = f"sel_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"
        cant_key = f"cant_{clave_comida}_{fecha_str}_{st.session_state[cnt_key]}"

        with st.expander(f"{label_ui} ({len(items_consolidados)} alimentos guardados)", expanded=False):
            if items_consolidados:
                for it in items_consolidados:
                    hora_txt = f"[{it['hora']}] " if "hora" in it else ""
                    st.caption(f"• {hora_txt}**{it['nombre']}** ({it['porciones']}x) ➔ {it['calorias']} kcal | P:{it['proteina']}g | C:{it['carbohidratos']}g | G:{it['grasas']}g")
                st.divider()

            alimento_sel = st.selectbox(f"Buscar ingrediente ({clave_comida}):", [""] + list(CATALOGO_ALIMENTOS.keys()), key=sel_key)
            
            if alimento_sel != "":
                datos_base = CATALOGO_ALIMENTOS[alimento_sel]
                hora_snack_str = ""
                if clave_comida == "Snacks":
                    hora_snack_str = st.time_input("⏰ Hora:", value=datetime.now().time(), key=f"hora_{fecha_str}_{len(items_consolidados)}").strftime("%I:%M %p")

                c_cant, c_add = st.columns([2, 1], vertical_alignment="bottom")
                porciones = c_cant.number_input("Porciones", min_value=0.5, value=1.0, step=0.5, key=cant_key)
                
                if c_add.button("➕ Agregar", key=f"btn_add_{clave_comida}_{fecha_str}"):
                    nuevo_item = {
                        "id": str(uuid.uuid4()), "nombre": alimento_sel, "porciones": porciones,
                        "calorias": int(datos_base['cal'] * porciones),
                        "proteina": round(datos_base['proteina'] * porciones, 1),
                        "carbohidratos": round(datos_base['carbos'] * porciones, 1),
                        "grasas": round(datos_base['grasas'] * porciones, 1)
                    }
                    if clave_comida == "Snacks": nuevo_item["hora"] = hora_snack_str
                        
                    st.session_state[carrito_key].append(nuevo_item)
                    st.session_state[cnt_key] += 1
                    st.rerun()

            if st.session_state[carrito_key]:
                st.markdown(f"**🥣 Plato actual ({len(st.session_state[carrito_key])} ítems):**")
                indices_a_borrar = []
                for idx, temp_item in enumerate(st.session_state[carrito_key]):
                    col_txt, col_del = st.columns([5, 1], vertical_alignment="center")
                    with col_txt: st.markdown(f"<div class='carrito-item'>• <b>{temp_item['nombre']}</b> x {temp_item['porciones']} ({temp_item['calorias']} kcal)</div>", unsafe_allow_html=True)
                    with col_del:
                        if st.button("🗑️", key=f"del_{clave_comida}_{fecha_str}_{idx}"): indices_a_borrar.append(idx)

                if indices_a_borrar:
                    for i in sorted(indices_a_borrar, reverse=True): st.session_state[carrito_key].pop(i)
                    st.rerun()

                if st.button(f"💾 Guardar {clave_comida} en Firebase", key=f"btn_save_{clave_comida}_{fecha_str}", type="primary", use_container_width=True):
                    microdatos_ml = []
                    for item in st.session_state[carrito_key]:
                        comidas_guardadas[clave_comida].append(item)
                        microdatos_ml.append({
                            "id_evento": item["id"], "timestamp": datetime.now().isoformat(), "user_id": user_id,
                            "categoria": "nutricion", "tipo_comida": clave_comida, "alimento": item["nombre"],
                            "porciones": item["porciones"], "hora_registro": item.get("hora", datetime.now().strftime("%H:%M")),
                            "macros": {"calorias": item["calorias"], "proteina_g": item["proteina"], "carbohidratos_g": item["carbohidratos"], "grasas_g": item["grasas"]}
                        })
                    
                    db.guardar_nutricion(user_id, fecha_str, {"user_id": user_id, "fecha": fecha_str, "comidas": comidas_guardadas, "totales": calcular_totales_dia(comidas_guardadas)})
                    db.guardar_en_bitacora(microdatos_ml)
                    
                    st.session_state[carrito_key] = []
                    st.toast(f"✅ ¡Guardado!", icon="☁️")
                    st.rerun()

    st.divider()

    with st.container(border=True):
        st.markdown("### 💧 Hidratación y Extras")
        datos_hidra = registro_dia.get("hidratacion_suplementos", {})
        agua = st.slider("Agua (Litros)", 0.0, 6.0, float(datos_hidra.get("agua_litros", 2.0)), 0.25, key=f"sld_agua_{fecha_str}")
        c_sup1, c_sup2 = st.columns(2)
        toma_prote = c_sup1.checkbox("Batido Proteína", value=datos_hidra.get("proteina", False), key=f"chk_pro_{fecha_str}")
        toma_creatina = c_sup2.checkbox("Creatina (5g)", value=datos_hidra.get("creatina", False), key=f"chk_cre_{fecha_str}")

        if st.button("💾 Actualizar Hidratación", key=f"btn_hidra_{fecha_str}", use_container_width=True):
            db.guardar_nutricion(user_id, fecha_str, {"user_id": user_id, "fecha": fecha_str, "comidas": comidas_guardadas, "totales": calcular_totales_dia(comidas_guardadas), "hidratacion_suplementos": {"agua_litros": agua, "proteina": toma_prote, "creatina": toma_creatina}})
            st.toast("✅ Extras guardados", icon="💧")
            st.rerun()