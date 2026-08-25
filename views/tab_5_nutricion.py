import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
import database as db
import google.generativeai as genai
from PIL import Image
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE IA (GEMINI MULTIMODAL)
# ==========================================
def analizar_alimento_ia(texto_usuario="", archivo_imagen=None, archivo_audio=None):
    if "GEMINI_API_KEY" not in st.secrets: 
        return None, "La clave GEMINI_API_KEY no está configurada en st.secrets."
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    prompt_sistema = """
    Eres un nutricionista experto en cálculo preciso de macros y matemática de recetas.
    Analiza la descripción en texto, la imagen de la tabla nutricional o la nota de voz del usuario.
    
    REGLAS DE CÁLCULO DE RECETAS Y PORCIONES:
    1. Si el usuario describe una preparación completa con sus ingredientes totales y luego indica la porción que se comió, debes calcular la regla de tres matemática para extraer ÚNICAMENTE las calorías y macronutrientes de la porción efectivamente consumida.
    2. Considera métodos de cocción (frijoles cocidos, pechuga frita con aceite, etc.).
    3. Si el usuario no especifica la porción consumida, asume que consumió la preparación descrita.

    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta, sin código markdown extra ni texto explicativo:
    {
        "nombre": "Nombre claro del plato o alimento consumido",
        "porcion": "Descripción de la porción consumida (Ej: 100g de 500g preparados)",
        "calorias": 0,
        "proteina": 0.0,
        "carbohidratos": 0.0,
        "grasas": 0.0
    }
    """
    
    contenido = [prompt_sistema]
    try:
        if archivo_imagen:
            img = Image.open(archivo_imagen)
            contenido.append(img)
        elif archivo_audio:
            audio_bytes = archivo_audio.read()
            mime_type = archivo_audio.type or "audio/wav"
            contenido.append({"mime_type": mime_type, "data": audio_bytes})
        else:
            contenido.append(texto_usuario)
    except Exception as err_prep:
        return None, f"Error al procesar el archivo de entrada: {err_prep}"

    modelos_candidatos = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-3.6-flash',
        'gemini-2.5-flash'
    ]
    
    ultimo_error = None

    for nombre_modelo in modelos_candidatos:
        try:
            modelo = genai.GenerativeModel(
                nombre_modelo, 
                generation_config={"response_mime_type": "application/json"}
            )
            respuesta = modelo.generate_content(contenido)
            texto_limpio = respuesta.text.replace("```json", "").replace("```", "").strip()
            return json.loads(texto_limpio), None
        except Exception as e:
            ultimo_error = str(e)
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            else:
                break

    return None, ultimo_error

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
    # ==========================================
    # CSS UI PREMIUM REDISEÑADO
    # ==========================================
    st.markdown("""
    <style>
    .titulo-nutricion { color: #2ecc71; font-size: 1.3rem; font-weight: 800; margin-bottom: 12px; margin-top: 10px;}
    .metric-container {
        background-color: #1a1c24; border: 1px solid #2d303e; border-radius: 10px;
        padding: 10px 4px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .metric-value { font-size: 1.3rem; font-weight: 800; color: #ffffff; }
    .metric-label { font-size: 0.7rem; color: #aaaaaa; text-transform: uppercase; font-weight: 600; }
    .val-cal { color: #e74c3c; } .val-pro { color: #3498db; }
    .val-car { color: #f1c40f; } .val-gra { color: #e67e22; }

    /* Tarjetas de Alimentos Guardados */
    .item-guardado-card {
        background: #181a20;
        border: 1px solid #2a2d3d;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
    }
    .item-title { font-size: 0.95rem; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
    .badge-macro {
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-right: 4px;
        margin-bottom: 2px;
    }
    .badge-kcal { background: rgba(231, 76, 60, 0.15); color: #e74c3c; border: 1px solid rgba(231, 76, 60, 0.3); }
    .badge-pro { background: rgba(52, 152, 219, 0.15); color: #3498db; border: 1px solid rgba(52, 152, 219, 0.3); }
    .badge-car { background: rgba(241, 196, 15, 0.15); color: #f1c40f; border: 1px solid rgba(241, 196, 15, 0.3); }
    .badge-gra { background: rgba(230, 126, 34, 0.15); color: #e67e22; border: 1px solid rgba(230, 126, 34, 0.3); }

    .carrito-item { font-size: 0.88rem; color: #eee; background-color: #212431; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #2ecc71; }
    
    /* Widget Hidratación */
    .agua-box {
        background: #121926;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .agua-val { font-size: 2.2rem; font-weight: 900; color: #38bdf8; line-height: 1.1; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 15px;">
        <span style="font-size: 2rem;">🍏</span>
        <h1 style="margin: 0; padding: 0; text-align: center; font-size: 2rem; color: white;">Nutrición & Macros</h1>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state.get("user_id")

    # HORA COLOMBIA (UTC -5)
    zona_colombia = timezone(timedelta(hours=-5))
    hoy = datetime.now(zona_colombia).date()

    with st.container(border=True):
        fecha_act = st.date_input("📅 Selecciona la fecha:", value=hoy)
    fecha_str = fecha_act.strftime("%Y-%m-%d")

    registro_dia = db.obtener_nutricion(user_id, fecha_str) or {}
    comidas_guardadas = registro_dia.get("comidas", {
        "Desayuno": [], "Almuerzo": [], "Cena": [], "Snacks": []
    })
    
    CATALOGO_ALIMENTOS = obtener_catalogo_completo(user_id)
    totales_dia = calcular_totales_dia(comidas_guardadas)

    # DASHBOARD PRINCIPAL
    st.markdown("<div class='titulo-nutricion'>📊 Resumen Diario</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-container'><div class='metric-value val-cal'>{int(totales_dia['cal'])}</div><div class='metric-label'>Kcal</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-container'><div class='metric-value val-pro'>{round(totales_dia['pro'],1)}g</div><div class='metric-label'>Prot</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-container'><div class='metric-value val-car'>{round(totales_dia['car'],1)}g</div><div class='metric-label'>Carbs</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-container'><div class='metric-value val-gra'>{round(totales_dia['gra'],1)}g</div><div class='metric-label'>Grasas</div></div>", unsafe_allow_html=True)

    st.divider()

    # ==========================================
    # 1. CREADOR DE ALIMENTOS (IA & MANUAL)
    # ==========================================
    with st.expander("✨ Creador de Alimentos & Recetas (IA / Manual)", expanded=False):
        tab_ia, tab_manual = st.tabs(["🤖 Analizador Multimodal IA", "✍️ Registro Manual"])
        
        with tab_ia:
            st.caption("Escribe, narra o fotografía una receta. Gemini calculará porciones exactas.")
            opcion_ia = st.radio("Método de captura:", ["📝 Texto / Receta", "🎙️ Audio / Voz", "📸 Foto Tabla Nutricional"], horizontal=True, key=f"rad_ia_{fecha_str}")
            
            resultado_ia = None
            error_ia = None
            
            if opcion_ia == "📝 Texto / Receta":
                desc = st.text_area(
                    "Describe la preparación y tu porción:", 
                    placeholder="Ej: Preparé 500g de arroz blanco con 20ml de aceite. De eso me comí 150g acompañados con 120g de pechuga a la plancha.",
                    height=90,
                    key=f"txt_desc_{fecha_str}"
                )
                if desc and st.button("✨ Calcular Receta con IA", type="primary", use_container_width=True, key=f"btn_ia_txt_{fecha_str}"):
                    with st.status("🧠 Analizando receta...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(texto_usuario=desc)
                        if error_ia: status.update(label="❌ Error en procesamiento", state="error")
                        else: status.update(label="✅ Cálculo completado", state="complete")

            elif opcion_ia == "🎙️ Audio / Voz":
                st.caption("🎙️ Narra los ingredientes y porciones (máx. 45s).")
                audio_file = st.audio_input("Graba tu voz:", key=f"audio_input_{fecha_str}")
                if audio_file and st.button("✨ Analizar Nota de Voz", type="primary", use_container_width=True, key=f"btn_ia_audio_{fecha_str}"):
                    with st.status("🧠 Escuchando audio...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(archivo_audio=audio_file)
                        if error_ia: status.update(label="❌ Error de audio", state="error")
                        else: status.update(label="✅ Audio interpretado", state="complete")

            elif opcion_ia == "📸 Foto Tabla Nutricional":
                foto = st.camera_input("Toma foto del producto o tabla:", key=f"cam_input_{fecha_str}")
                if foto and st.button("✨ Escanear Foto con IA", type="primary", use_container_width=True, key=f"btn_ia_foto_{fecha_str}"):
                    with st.status("🧠 Escaneando imagen...", expanded=True) as status:
                        resultado_ia, error_ia = analizar_alimento_ia(archivo_imagen=foto)
                        if error_ia: status.update(label="❌ Error en imagen", state="error")
                        else: status.update(label="✅ Tabla leída con éxito", state="complete")

            if error_ia:
                st.error(f"⚠️ Error: {error_ia}")

            if resultado_ia:
                st.session_state['ia_nom'] = resultado_ia.get('nombre', '')
                st.session_state['ia_porc'] = str(resultado_ia.get('porcion', '1 porción'))
                st.session_state['ia_cal'] = int(resultado_ia.get('calorias', 0))
                st.session_state['ia_pro'] = float(resultado_ia.get('proteina', 0.0))
                st.session_state['ia_car'] = float(resultado_ia.get('carbohidratos', 0.0))
                st.session_state['ia_gra'] = float(resultado_ia.get('grasas', 0.0))
                
                st.markdown(f"""
                <div style="background: #181a20; border: 1px solid #2ecc71; border-radius: 10px; padding: 12px; margin-top: 10px;">
                    <div style="font-size: 1rem; font-weight: 800; color: #2ecc71;">🎉 {st.session_state['ia_nom']}</div>
                    <div style="font-size: 0.8rem; color: #aaa; margin-bottom: 8px;">📍 <b>Porción:</b> {st.session_state['ia_porc']}</div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; text-align: center;">
                        <span class="badge-macro badge-kcal">{st.session_state['ia_cal']} kcal</span>
                        <span class="badge-macro badge-pro">P: {st.session_state['ia_pro']}g</span>
                        <span class="badge-macro badge-car">C: {st.session_state['ia_car']}g</span>
                        <span class="badge-macro badge-gra">G: {st.session_state['ia_gra']}g</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.info("👉 Cambia a la pestaña **✍️ Registro Manual** para guardar este alimento en tu catálogo.")

        with tab_manual:
            with st.form(f"form_nuevo_alimento_{fecha_str}"):
                nom_alim = st.text_input("Nombre del alimento / plato:", value=st.session_state.get('ia_nom', ''))
                porc_alim = st.text_input("Porción base (Ej: 100g, 1 plato, 1 unidad):", value=st.session_state.get('ia_porc', ''))
                
                c_cal, c_pro, c_car, c_gra = st.columns(4)
                cal_val = c_cal.number_input("Kcal", min_value=0, value=st.session_state.get('ia_cal', 0))
                pro_val = c_pro.number_input("Prot (g)", min_value=0.0, value=st.session_state.get('ia_pro', 0.0), step=0.1)
                car_val = c_car.number_input("Carb (g)", min_value=0.0, value=st.session_state.get('ia_car', 0.0), step=0.1)
                gra_val = c_gra.number_input("Grasa (g)", min_value=0.0, value=st.session_state.get('ia_gra', 0.0), step=0.1)
                
                es_pub = st.checkbox("🌐 Compartir alimento con la comunidad", value=True)
                btn_crear = st.form_submit_button("💾 Guardar Alimento en Catálogo", type="primary", use_container_width=True)
                
                if btn_crear:
                    if not nom_alim or not porc_alim:
                        st.warning("⚠️ Ingresa el nombre y la porción base.")
                    else:
                        nuevo_doc = {
                            "nombre": nom_alim, "porcion": porc_alim,
                            "calorias": int(cal_val), "proteina": float(pro_val),
                            "carbohidratos": float(car_val), "grasas": float(gra_val)
                        }
                        if db.guardar_alimento_personalizado(user_id, nuevo_doc, es_publico=es_pub):
                            st.success(f"✅ ¡'{nom_alim}' guardado en catálogo!")
                            for k in ['ia_nom', 'ia_porc', 'ia_cal', 'ia_pro', 'ia_car', 'ia_gra']:
                                st.session_state.pop(k, None)
                            st.rerun()

    st.divider()

    # ==========================================
    # 2. CONSTRUCTOR DE PLATOS REDISEÑADO
    # ==========================================
    st.markdown("<div class='titulo-nutricion'>🍲 Constructor de Platos</div>", unsafe_allow_html=True)
    
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

        with st.expander(f"{label_ui} ({len(items_consolidados)} guardados)", expanded=False):
            # LECTURA ELEGANTE DE ALIMENTOS YA GUARDADOS EN FIREBASE
            if items_consolidados:
                st.markdown("<p style='font-size: 0.8rem; color: #888; margin-bottom: 6px;'><b>Alimentos registrados en este plato:</b></p>", unsafe_allow_html=True)
                
                indices_guardados_borrar = []
                for idx_g, it in enumerate(items_consolidados):
                    col_info_g, col_btn_g = st.columns([5, 1], vertical_alignment="center")
                    
                    hora_txt = f"[{it['hora']}] " if "hora" in it else ""
                    
                    with col_info_g:
                        st.markdown(f"""
                        <div class="item-guardado-card">
                            <div class="item-title">• {hora_txt}<b>{it['nombre']}</b> ({it['porciones']}x)</div>
                            <div>
                                <span class="badge-macro badge-kcal">🔥 {it['calorias']} kcal</span>
                                <span class="badge-macro badge-pro">💪 P: {it['proteina']}g</span>
                                <span class="badge-macro badge-car">🌾 C: {it['carbohidratos']}g</span>
                                <span class="badge-macro badge-gra">🥑 G: {it['grasas']}g</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col_btn_g:
                        if st.button("🗑️", key=f"del_db_{clave_comida}_{fecha_str}_{idx_g}", help="Eliminar de Firebase"):
                            indices_guardados_borrar.append(idx_g)

                if indices_guardados_borrar:
                    for i in sorted(indices_guardados_borrar, reverse=True):
                        comidas_guardadas[clave_comida].pop(i)
                    db.guardar_nutricion(user_id, fecha_str, {
                        "user_id": user_id, 
                        "fecha": fecha_str, 
                        "comidas": comidas_guardadas, 
                        "totales": calcular_totales_dia(comidas_guardadas)
                    })
                    st.toast(f"🗑️ Ítem eliminado de {clave_comida}", icon="✅")
                    st.rerun()

                st.divider()

            # FORMULARIO DE BÚSQUEDA Y ADICIÓN
            alimento_sel = st.selectbox(f"Añadir ingrediente a {clave_comida}:", [""] + list(CATALOGO_ALIMENTOS.keys()), key=sel_key)
            
            if alimento_sel != "":
                datos_base = CATALOGO_ALIMENTOS[alimento_sel]
                hora_snack_str = ""
                
                c_porc, c_add = st.columns([2, 1], vertical_alignment="bottom")
                porciones = c_porc.number_input("Cantidad / Porciones", min_value=0.5, value=1.0, step=0.5, key=cant_key)
                
                if clave_comida == "Snacks":
                    hora_snack_str = st.time_input("⏰ Hora del snack:", value=datetime.now(zona_colombia).time(), key=f"hora_{fecha_str}_{len(items_consolidados)}").strftime("%I:%M %p")

                if c_add.button("➕ Añadir", key=f"btn_add_{clave_comida}_{fecha_str}", use_container_width=True):
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

            # CARRITO TEMPORAL DE PREPARACIÓN
            if st.session_state[carrito_key]:
                st.markdown(f"<p style='font-size:0.85rem; font-weight:700; color:#2ecc71; margin-top:10px;'>🥣 En preparación ({len(st.session_state[carrito_key])} ítems por guardar):</p>", unsafe_allow_html=True)
                indices_a_borrar = []
                
                for idx, temp_item in enumerate(st.session_state[carrito_key]):
                    col_txt, col_del = st.columns([5, 1], vertical_alignment="center")
                    with col_txt: 
                        st.markdown(f"<div class='carrito-item'>• <b>{temp_item['nombre']}</b> x{temp_item['porciones']} ({temp_item['calorias']} kcal)</div>", unsafe_allow_html=True)
                    with col_del:
                        if st.button("🗑️", key=f"del_cart_{clave_comida}_{fecha_str}_{idx}"): 
                            indices_a_borrar.append(idx)

                if indices_a_borrar:
                    for i in sorted(indices_a_borrar, reverse=True): 
                        st.session_state[carrito_key].pop(i)
                    st.rerun()

                if st.button(f"💾 Guardar {clave_comida} en Firebase", key=f"btn_save_{clave_comida}_{fecha_str}", type="primary", use_container_width=True):
                    microdatos_ml = []
                    ahora_col = datetime.now(zona_colombia)
                    
                    for item in st.session_state[carrito_key]:
                        comidas_guardadas[clave_comida].append(item)
                        microdatos_ml.append({
                            "id_evento": item["id"], "timestamp": ahora_col.isoformat(), "user_id": user_id,
                            "categoria": "nutricion", "tipo_comida": clave_comida, "alimento": item["nombre"],
                            "porciones": item["porciones"], "hora_registro": item.get("hora", ahora_col.strftime("%H:%M")),
                            "macros": {"calorias": item["calorias"], "proteina_g": item["proteina"], "carbohidratos_g": item["carbohidratos"], "grasas_g": item["grasas"]}
                        })
                    
                    db.guardar_nutricion(user_id, fecha_str, {
                        "user_id": user_id, "fecha": fecha_str, 
                        "comidas": comidas_guardadas, 
                        "totales": calcular_totales_dia(comidas_guardadas)
                    })
                    db.guardar_en_bitacora(microdatos_ml)
                    
                    st.session_state[carrito_key] = []
                    st.toast(f"✅ ¡{clave_comida} guardado exitosamente!", icon="☁️")
                    st.rerun()

    st.divider()

    # ==========================================
    # 3. HIDRATACIÓN GRADUABLE Y EXTRAS
    # ==========================================
    with st.container(border=True):
        st.markdown("<div class='titulo-nutricion'>💧 Hidratación Graduable & Suplementos</div>", unsafe_allow_html=True)
        datos_hidra = registro_dia.get("hidratacion_suplementos", {})
        
        # Estado local de agua en litros
        agua_key = f"val_agua_{fecha_str}"
        if agua_key not in st.session_state:
            st.session_state[agua_key] = float(datos_hidra.get("agua_litros", 0.0))

        agua_actual = st.session_state[agua_key]
        meta_agua = 3.0
        progreso = min(agua_actual / meta_agua, 1.0)

        # WIDGET VISUAL DE AGUA
        st.markdown(f"""
        <div class="agua-box">
            <div style="font-size:0.8rem; color:#94a3b8; font-weight:700; text-transform:uppercase;">Agua Consumida Hoy</div>
            <div class="agua-val">{agua_actual:.2f} <span style="font-size:1.1rem; color:#94a3b8;">/ {meta_agua:.1f} L</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.progress(progreso)

        # BOTONES RÁPIDOS DE ADICIÓN GRADUABLE
        st.markdown("<p style='font-size:0.8rem; color:#94a3b8; font-weight:600; margin-top:10px; margin-bottom:4px;'>Ajuste rápido:</p>", unsafe_allow_html=True)
        c_w1, c_w2, c_w3, c_w4 = st.columns(4)
        if c_w1.button("+200 ml", use_container_width=True, key=f"w200_{fecha_str}"):
            st.session_state[agua_key] = round(st.session_state[agua_key] + 0.20, 2)
            st.rerun()
        if c_w2.button("+300 ml", use_container_width=True, key=f"w300_{fecha_str}"):
            st.session_state[agua_key] = round(st.session_state[agua_key] + 0.30, 2)
            st.rerun()
        if c_w3.button("+500 ml", use_container_width=True, key=f"w500_{fecha_str}"):
            st.session_state[agua_key] = round(st.session_state[agua_key] + 0.50, 2)
            st.rerun()
        if c_w4.button("➖ 200ml", use_container_width=True, key=f"w_sub_{fecha_str}"):
            st.session_state[agua_key] = max(0.0, round(st.session_state[agua_key] - 0.20, 2))
            st.rerun()

        # CAMPO DE DIGITACIÓN MANUAL PERSONALIZADA
        st.markdown("<p style='font-size:0.8rem; color:#94a3b8; font-weight:600; margin-top:10px; margin-bottom:4px;'>O digita la cantidad exacta (ml):</p>", unsafe_allow_html=True)
        c_custom_val, c_custom_btn = st.columns([2, 1], vertical_alignment="bottom")
        
        ml_custom = c_custom_val.number_input(
            "Cantidad manual en ml", 
            min_value=0, 
            max_value=3000, 
            value=250, 
            step=50, 
            key=f"input_custom_ml_{fecha_str}",
            label_visibility="collapsed"
        )
        
        if c_custom_btn.button("➕ Sumar ML", use_container_width=True, key=f"btn_custom_ml_{fecha_str}"):
            if ml_custom > 0:
                litros_a_sumar = ml_custom / 1000.0
                st.session_state[agua_key] = round(st.session_state[agua_key] + litros_a_sumar, 2)
                st.toast(f"💧 +{ml_custom} ml agregados", icon="✅")
                st.rerun()

        st.divider()

        # SUPLEMENTOS
        c_sup1, c_sup2 = st.columns(2)
        toma_prote = c_sup1.checkbox("🥤 Batido Proteína", value=datos_hidra.get("proteina", False), key=f"chk_pro_{fecha_str}")
        toma_creatina = c_sup2.checkbox("⚡ Creatina (5g)", value=datos_hidra.get("creatina", False), key=f"chk_cre_{fecha_str}")

        if st.button("💾 Guardar Hidratación & Suplementos", key=f"btn_hidra_{fecha_str}", type="primary", use_container_width=True):
            db.guardar_nutricion(user_id, fecha_str, {
                "user_id": user_id, 
                "fecha": fecha_str, 
                "comidas": comidas_guardadas, 
                "totales": calcular_totales_dia(comidas_guardadas), 
                "hidratacion_suplementos": {
                    "agua_litros": st.session_state[agua_key], 
                    "proteina": toma_prote, 
                    "creatina": toma_creatina
                }
            })
            st.toast("✅ Hidratación y extras guardados en Firebase", icon="💧")
            st.rerun()