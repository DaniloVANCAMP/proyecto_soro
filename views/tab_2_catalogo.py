import json
import math
import os
import random
import requests
import uuid
import time
import streamlit as st
from datetime import datetime
import database as db  # <-- CONEXIÓN A LA BASE DE DATOS

URL_JSON = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/data/exercises.json"
BASE_MEDIA_URL = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/"
ARCHIVO_PRESETS = "presets_equipo.json"

# ==========================================
# 1. DICCIONARIOS DE TRADUCCIÓN
# ==========================================
DICCIONARIO_ZONAS = {
    "back": "Espalda", "cardio": "Cardio / Resistencia", "chest": "Pecho / Pectorales",
    "lower arms": "Antebrazos", "lower legs": "Pantorrillas", "neck": "Cuello",
    "shoulders": "Hombros", "upper arms": "Brazos", "upper legs": "Piernas / Glúteos",
    "waist": "Cintura / Abdomen"
}

DICCIONARIO_EQUIPO = {
    "assisted": "Asistido / Máquina de asistencia", "band": "Banda de resistencia",
    "barbell": "Barra recta", "body weight": "Peso corporal (Calistenia)",
    "bosu ball": "Bosu", "cable": "Polea / Cable", "dumbbell": "Mancuerna",
    "elliptical machine": "Elíptica", "ez barbell": "Barra Z / EZ", "hammer": "Máquina Hammer",
    "kettlebell": "Pesa Rusa (Kettlebell)", "leverage machine": "Máquina de palanca",
    "medicine ball": "Balón Medicinal", "olympic barbell": "Barra Olímpica",
    "resistance band": "Banda de resistencia", "roller": "Rodillo (Foam Roller)",
    "rope": "Cuerda / Soga", "skierg machine": "SkiErg", "sled machine": "Trineo de empuje",
    "smith machine": "Máquina Smith / Multipower", "stability ball": "Fitball",
    "stationary bike": "Bicicleta estática", "stepmill machine": "Escaladora",
    "tire": "Neumático", "trap bar": "Barra Hexagonal",
    "upper body ergometer": "Ergómetro superior", "weighted": "Lastrado",
    "wheel roller": "Rueda Abdominal"
}

DICCIONARIO_MUSCULOS = {
    "glutes": "Glúteos", "gluteus": "Glúteos", "gluteus maximus": "Glúteo Mayor",
    "gluteus medius": "Glúteo Medio", "gluteus minimus": "Glúteo Menor", "hip flexors": "Flexores de Cadera",
    "abductors": "Abductores", "adductors": "Aductores", "quads": "Cuádriceps", "quadriceps": "Cuádriceps",
    "hamstrings": "Isquiotibiales / Femorales", "calves": "Pantorrillas / Gemelos",
    "gastrocnemius": "Gemelos", "soleus": "Sóleos", "abs": "Abdominales", "obliques": "Oblicuos",
    "rectus abdominis": "Recto Abdominal", "serratus anterior": "Serrato", "lats": "Dorsales",
    "latissimus dorsi": "Dorsal Ancho", "upper back": "Espalda Alta", "traps": "Trapecios",
    "rhomboids": "Romboides", "spine": "Erectores Espinales", "lower back": "Espalda Baja",
    "pectorals": "Pectorales", "chest": "Pecho", "delts": "Deltoides / Hombros",
    "deltoids": "Deltoides", "shoulders": "Hombros", "biceps": "Bíceps", "triceps": "Tríceps",
    "forearms": "Antebrazos", "neck": "Cuello", "cardiovascular system": "Sistema Cardiovascular"
}

def fmt_zona(val: str) -> str:
    if not val or val == "Todas": return "Todas las zonas"
    key = str(val).lower().strip()
    return DICCIONARIO_ZONAS.get(key, val.title())

def fmt_equipo(val: str) -> str:
    if not val or val == "Todos": return "Todos los equipos"
    key = str(val).lower().strip()
    return DICCIONARIO_EQUIPO.get(key, val.title())

def fmt_musculo(val: str) -> str:
    if not val or val == "Todos": return "Todos los músculos"
    key = str(val).lower().strip()
    return DICCIONARIO_MUSCULOS.get(key, val.title())

# ==========================================
# 2. GESTIÓN DE DATOS Y API
# ==========================================

@st.cache_data(show_spinner=False)
def traducir_nombre_ejercicio(texto_ingles):
    if not texto_ingles: return "Desconocido"
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "es", "dt": "t", "q": texto_ingles}
        respuesta = requests.get(url, params=params, timeout=2)
        if respuesta.status_code == 200:
            texto_traducido = respuesta.json()[0][0][0]
            return texto_traducido.title()
    except Exception:
        pass
    return texto_ingles.title()

def cargar_presets():
    if os.path.exists(ARCHIVO_PRESETS):
        with open(ARCHIVO_PRESETS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return {"🏠 Casa": [], "🏋️ Gym Frecuente": []}

def guardar_presets(presets):
    with open(ARCHIVO_PRESETS, "w", encoding="utf-8") as archivo:
        json.dump(presets, archivo, indent=4)

def cargar_perfil():
    user_id = st.session_state.get("user_id")
    default = {
        "nombre": "Usuario ML", "sexo": "Masculino", "edad": 30, "estatura_cm": 175.0,
        "peso_kg": 70.0, "biceps": 35.0, "abdomen": 85.0, "cintura": 80.0,
        "cadera": 95.0, "gluteos": 100.0, "cuadriceps": 55.0, "pantorrilla": 38.0
    }
    
    if user_id:
        perfil_db = db.obtener_perfil(user_id)
        if perfil_db:
            m = perfil_db.get('medidas', {})
            return {
                "nombre": perfil_db.get('nombre') or default["nombre"],
                "sexo": perfil_db.get('genero') or default["sexo"],
                "edad": perfil_db.get('edad') or default["edad"],
                "estatura_cm": perfil_db.get('estatura') or default["estatura_cm"],
                "peso_kg": perfil_db.get('peso') or default["peso_kg"],
                "biceps": m.get('brazo') or default["biceps"],
                "abdomen": m.get('cintura') or default["abdomen"],
                "cintura": m.get('cintura') or default["cintura"],
                "cadera": m.get('cadera') or default["cadera"],
                "gluteos": m.get('cadera') or default["gluteos"],
                "cuadriceps": m.get('pierna') or default["cuadriceps"],
                "pantorrilla": m.get('pantorrilla') or default["pantorrilla"]
            }
    return default

def guardar_perfil(datos_ml):
    user_id = st.session_state.get("user_id")
    if user_id:
        datos_db = {
            "nombre": datos_ml["nombre"], "edad": datos_ml["edad"], "genero": datos_ml["sexo"],
            "nivel": "Intermedio", "estatura": datos_ml["estatura_cm"], "peso": datos_ml["peso_kg"],
            "medidas": {
                "pecho": 0.0, "cintura": datos_ml["cintura"], "pierna": datos_ml["cuadriceps"],
                "brazo": datos_ml["biceps"], "cadera": datos_ml["cadera"], "pantorrilla": datos_ml["pantorrilla"]
            }
        }
        db.guardar_perfil(user_id, datos_db)

def guardar_en_bitacora(nuevos_datos):
    archivo = "bitacora_microdatos.json"
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            datos_historicos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        datos_historicos = []
    datos_historicos.extend(nuevos_datos)
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(datos_historicos, f, indent=4)

def obtener_clima_api(ciudad):
    try:
        url = f"https://wttr.in/{ciudad}?format=j1"
        respuesta = requests.get(url, timeout=5)
        if respuesta.status_code == 200:
            datos = respuesta.json()
            condicion = datos['current_condition'][0]
            temp = int(condicion['temp_C'])
            desc = condicion.get('weatherDesc', [{'value': 'Desconocido'}])[0]['value']
            desc_traducida = traducir_nombre_ejercicio(desc)
            return desc_traducida, temp
    except Exception:
        pass
    return "Desconocido", 25

@st.cache_data(show_spinner="Cargando 1300+ ejercicios desde la API...")
def cargar_ejercicios_completos():
    try:
        respuesta = requests.get(URL_JSON, timeout=10)
        respuesta.raise_for_status()
        ejercicios = respuesta.json()
        for ej in ejercicios:
            bp = ej.get("bodyPart", ej.get("body_part", ""))
            tg = ej.get("target", "")
            eq = ej.get("equipment", "")
            
            ej["body_part_trad"] = fmt_zona(bp)
            ej["target_trad"] = fmt_musculo(tg)
            ej["equipment_trad"] = fmt_equipo(eq)
            ej["gif_url_correcta"] = ej.get("gifUrl", ej.get("gif_url", ""))
        return ejercicios
    except Exception as e:
        return []

# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================
def mostrar(exercises_param=None, base_media_url_param=None):
    st.title("💪 Centro de Entrenamiento")

    if exercises_param and len(exercises_param) > 10:
        ejercicios = exercises_param
    else:
        ejercicios = cargar_ejercicios_completos()

    if not ejercicios:
        st.error("No se pudieron cargar los ejercicios. Verifica tu conexión a internet.")
        return

    # Perfil Biométrico
    perfil_actual = cargar_perfil()
    with st.expander("🧬 Mi Perfil Biométrico (Actualiza tus medidas aquí)", expanded=False):
        st.info("Estos datos se guardarán y se adjuntarán automáticamente a CADA ejercicio para tu modelo de ML.")
        with st.form("form_biometria"):
            st.subheader("Datos Demográficos")
            col_d1, col_d2, col_d3 = st.columns(3)
            nombre = col_d1.text_input("Nombre", value=perfil_actual["nombre"])
            
            sexo_db = perfil_actual.get("sexo", "Masculino")
            sexo_idx = ["Masculino", "Femenino", "Otro"].index(sexo_db) if sexo_db in ["Masculino", "Femenino", "Otro"] else 0
            sexo = col_d2.selectbox("Sexo", ["Masculino", "Femenino", "Otro"], index=sexo_idx)
            edad = col_d3.number_input("Edad", min_value=10, max_value=100, value=int(perfil_actual["edad"]))
            
            st.subheader("Física General y Medidas (cm / kg)")
            col_f1, col_f2 = st.columns(2)
            estatura = col_f1.number_input("Estatura (cm)", min_value=100.0, max_value=250.0, value=float(perfil_actual["estatura_cm"]), step=1.0)
            peso = col_f2.number_input("Peso Actual (kg)", min_value=30.0, max_value=200.0, value=float(perfil_actual["peso_kg"]), step=0.1)
            
            st.markdown("**Perímetros Musculares (cm)**")
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            biceps = col_m1.number_input("Bíceps", value=float(perfil_actual["biceps"]), step=0.5)
            abdomen = col_m2.number_input("Abdomen", value=float(perfil_actual["abdomen"]), step=0.5)
            cintura = col_m3.number_input("Cintura", value=float(perfil_actual["cintura"]), step=0.5)
            cadera = col_m4.number_input("Cadera", value=float(perfil_actual["cadera"]), step=0.5)
            
            col_m5, col_m6, col_m7, _ = st.columns(4)
            gluteos = col_m5.number_input("Glúteos", value=float(perfil_actual["gluteos"]), step=0.5)
            cuadriceps = col_m6.number_input("Cuádriceps", value=float(perfil_actual["cuadriceps"]), step=0.5)
            pantorrilla = col_m7.number_input("Pantorrilla", value=float(perfil_actual["pantorrilla"]), step=0.5)
            
            if st.form_submit_button("💾 Guardar Biometría", use_container_width=True):
                nuevos_datos = {
                    "nombre": nombre, "sexo": sexo, "edad": edad, "estatura_cm": estatura,
                    "peso_kg": peso, "biceps": biceps, "abdomen": abdomen, "cintura": cintura,
                    "cadera": cadera, "gluteos": gluteos, "cuadriceps": cuadriceps, "pantorrilla": pantorrilla
                }
                guardar_perfil(nuevos_datos)
                st.success("¡Perfil biométrico actualizado! Tu modelo de ML te lo agradece. 🧠")
                time.sleep(1.5)
                st.rerun()

    perfil_actual = cargar_perfil()

    st.markdown("### 📍 Configuración de la Sesión")
    col_perfil, col_dias, col_obj = st.columns([2, 1, 1], vertical_alignment="bottom")

    presets = cargar_presets()
    opciones_perfil = list(presets.keys()) + ["➕ Crear nuevo lugar/perfil..."]

    with col_perfil:
        perfil_elegido = st.selectbox("Lugar de entrenamiento activo:", opciones_perfil)
    with col_dias:
        dias_entreno = st.slider("Días a entrenar por semana:", 1, 7, 4)
    with col_obj:
        objetivo = st.selectbox("Objetivo:", ["Hipertrofia", "Fuerza", "Resistencia", "Pérdida de Peso"])

    equipamientos_globales = sorted(list(set([ej.get("equipment_trad", "N/A") for ej in ejercicios if ej.get("equipment_trad")])))
    equipos_seleccionados = []

    if perfil_elegido == "➕ Crear nuevo lugar/perfil...":
        nuevo_nombre = st.text_input("Nombre del nuevo perfil:")
        if st.button("Crear Perfil") and nuevo_nombre:
            if nuevo_nombre not in presets:
                presets[nuevo_nombre] = []
                guardar_presets(presets)
                st.rerun()
    else:
        maquinas_guardadas = [eq for eq in presets.get(perfil_elegido, []) if eq in equipamientos_globales]
        col_equipo, col_btn_guardar = st.columns([5, 1], vertical_alignment="bottom")
        with col_equipo:
            equipos_seleccionados = st.multiselect(f"Equipamiento en {perfil_elegido}:", equipamientos_globales, default=maquinas_guardadas)
        with col_btn_guardar:
            if equipos_seleccionados != maquinas_guardadas:
                if st.button("💾 Guardar Eq.", use_container_width=True):
                    presets[perfil_elegido] = equipos_seleccionados
                    guardar_presets(presets)
                    st.rerun()

    st.divider()
    
    # NUEVO ORDEN DE PESTAÑAS (Planificador -> Generador -> Catálogo)
    tab_planificador, tab_generador, tab_catalogo = st.tabs(["📅 Planificador Semanal", "⚡ Generador de Rutinas", "🔍 Catálogo de Consulta"])

# --- PESTAÑA 1: PLANIFICADOR SEMANAL (HORARIO ESCOLAR OPTIMIZADO) ---
    with tab_planificador:
        st.header("📅 Planificador de Entrenamientos")
        st.write("Selecciona una fecha. Tu semana se organizará automáticamente en la cuadrícula inferior.")
        
        # 1. OBTENEMOS EL USUARIO Y LA FECHA
        user_id = st.session_state.get("user_id")
        fecha_seleccionada = st.date_input("🗓️ Selecciona la fecha a planificar:")
        
        # Diccionario ultraligero de Emojis para que NO se pegue la app
        EMOJIS_MUSCULOS = {
            "Abdominales": "🍫", "Pecho": "🦍", "Dorsales": "🦇", "Espalda": "🐢",
            "Cuádriceps": "🦵", "Isquiotibiales / Femorales": "🍗", "Piernas / Glúteos": "🦵",
            "Glúteos": "🍑", "Pantorrillas / Gemelos": "🦿", "Bíceps": "💪", 
            "Tríceps": "🐴", "Brazos": "💪", "Antebrazos": "🔧", 
            "Deltoides / Hombros": "🥥", "Hombros": "🥥", "Sistema Cardiovascular": "🫀",
            "Cardio / Resistencia": "🏃", "Cuello": "🦒"
        }

        # 2. CONSTRUCCIÓN DE LA CUADRÍCULA SEMANAL (TIPO HORARIO ESCOLAR)
        if user_id:
            st.divider()
            st.markdown("### 🗓️ Tu Semana de Entrenamiento")
            
            from datetime import timedelta
            # Calculamos el Lunes de la semana seleccionada
            lunes = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
            dias_semana = [lunes + timedelta(days=i) for i in range(7)]
            nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            
            # Dibujamos las 7 columnas
            cols_semana = st.columns(7)
            
            for i, col in enumerate(cols_semana):
                fecha_dia = dias_semana[i]
                fecha_str_dia = fecha_dia.strftime("%Y-%m-%d")
                
                # Resaltar el día que el usuario tiene seleccionado en el calendario
                es_hoy_seleccionado = (fecha_dia == fecha_seleccionada)
                color_fondo = "background-color: #ff4b4b20;" if es_hoy_seleccionado else ""
                
                with col:
                    st.markdown(f"**{nombres_dias[i]}**")
                    st.caption(fecha_dia.strftime("%d/%m"))
                    
                    # Consultamos rápido a la BD qué hay este día
                    rutina_dia_grid = db.obtener_plan_dia(user_id, fecha_str_dia)
                    musculos_dia = list(set([r["musculo"] for r in rutina_dia_grid if r.get("musculo")]))
                    
                    # Tarjeta del día
                    st.markdown(f"""
                    <div style="border: 1px solid #444; border-radius: 8px; padding: 10px; min-height: 100px; {color_fondo}">
                    """, unsafe_allow_html=True)
                    
                    if not musculos_dia:
                        st.markdown("<div style='text-align: center; color: #888;'>Descanso 😴</div>", unsafe_allow_html=True)
                    else:
                        for m in musculos_dia:
                            emoji = EMOJIS_MUSCULOS.get(m, "🔥")
                            st.markdown(f"<div style='font-size: 14px; margin-bottom: 4px;'>{emoji} {m}</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div><br>", unsafe_allow_html=True)
                    
        else:
            st.error("⚠️ Inicia sesión para guardar y visualizar tu plan.")

        st.divider()

        # 3. OBTENER LA RUTINA DEL DÍA SELECCIONADO PARA EDITARLA
        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        rutina_dia = db.obtener_plan_dia(user_id, fecha_str) if user_id else []

        # 4. APLICAMOS EL FILTRO MAESTRO DE MÁQUINAS
        ejercicios_plan = ejercicios
        if equipos_seleccionados:
            ejercicios_plan = [ej for ej in ejercicios if ej.get("equipment_trad") in equipos_seleccionados]
        else:
            ejercicios_plan = []

        if perfil_elegido != "➕ Crear nuevo lugar/perfil...":
            equipos_str = ", ".join(equipos_seleccionados) if equipos_seleccionados else "Ningún equipo seleccionado"
            st.info(f"📍 **Lugar activo para agregar:** {perfil_elegido} | ⚙️ **Filtro:** {equipos_str}")

        # --- SECCIÓN A: AGREGAR EJERCICIOS ---
        with st.container(border=True):
            st.subheader(f"Añadir ejercicio al {fecha_str}")
            
            if not ejercicios_plan:
                st.warning("⚠️ Selecciona al menos un equipo en la Configuración de Sesión.")
            else:
                todos_los_musculos = sorted(list(set([ej.get("target_trad") for ej in ejercicios_plan if ej.get("target_trad")])))
                musculos_elegidos = st.multiselect("1️⃣ Selecciona el Músculo:", todos_los_musculos)
                
                if musculos_elegidos:
                    st.markdown("### Catálogo de Ejercicios Disponibles")
                    for musculo in musculos_elegidos:
                        st.markdown(f"<h3 style='color: #FF4B4B;'>🎯 {musculo}</h3>", unsafe_allow_html=True)
                        ejercicios_por_musculo = [ej for ej in ejercicios_plan if ej.get("target_trad") == musculo]
                        equipos_viables = sorted(list(set([ej.get("equipment_trad") for ej in ejercicios_por_musculo if ej.get("equipment_trad")])))
                        
                        for equipo in equipos_viables:
                            st.markdown(f"#### ⚙️ {equipo}")
                            ejercicios_finales = [ej for ej in ejercicios_por_musculo if ej.get("equipment_trad") == equipo]
                            
                            cols = st.columns(2)
                            for idx, ej_data in enumerate(ejercicios_finales):
                                col_actual = cols[idx % 2]
                                with col_actual:
                                    with st.container(border=True):
                                        nombre_ej = traducir_nombre_ejercicio(ej_data.get("name", ""))
                                        st.markdown(f"**{nombre_ej}**")
                                        
                                        if ej_data.get("gif_url_correcta"):
                                            st.image(f"{BASE_MEDIA_URL}{ej_data.get('gif_url_correcta').lstrip('/')}", use_container_width=True)
                                        
                                        instrucciones = ej_data.get("instructions", [])
                                        if isinstance(instrucciones, list) and instrucciones:
                                            with st.expander("📖 Ver instrucciones"):
                                                for paso in instrucciones:
                                                    st.write(f"- {paso}")
                                        
                                        c_ser, c_rep = st.columns(2)
                                        ej_id = ej_data.get("id", str(uuid.uuid4()))
                                        series_plan = c_ser.number_input("Series", min_value=1, value=3, key=f"s_{fecha_str}_{ej_id}_{idx}")
                                        reps_plan = c_rep.number_input("Reps", min_value=1, value=10, key=f"r_{fecha_str}_{ej_id}_{idx}")
                                        
                                        if st.button("➕ Añadir", key=f"b_{fecha_str}_{ej_id}_{idx}", use_container_width=True, type="primary"):
                                            if user_id:
                                                nuevo_item = {
                                                    "id_unico": str(uuid.uuid4()),
                                                    "nombre": nombre_ej, "musculo": musculo, "equipo": equipo,
                                                    "series": series_plan, "reps": reps_plan,
                                                    "gif_url": ej_data.get("gif_url_correcta", ""),
                                                    "instrucciones": instrucciones
                                                }
                                                nueva_rutina = rutina_dia.copy()
                                                nueva_rutina.append(nuevo_item)
                                                db.guardar_plan_dia(user_id, fecha_str, nueva_rutina)
                                                st.toast("¡Añadido!")
                                                time.sleep(0.5)
                                                st.rerun()

        # --- SECCIÓN B: VER RUTINA DEL DÍA ---
        st.subheader(f"📋 Rutina planificada para el {fecha_str}")
        if not rutina_dia:
            st.info("No hay ejercicios para este día.")
        else:
            for idx, item in enumerate(rutina_dia):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1.5, 3, 1], vertical_alignment="center")
                    with c1:
                        if item.get("gif_url"):
                            st.image(f"{BASE_MEDIA_URL}{item['gif_url'].lstrip('/')}", use_container_width=True)
                    with c2:
                        st.markdown(f"**{idx + 1}. {item['nombre']}**")
                        st.caption(f"🎯 {item['musculo']} | ⚙️ {item['equipo']}")
                        st.write(f"💪 {item['series']} Series x {item['reps']} Reps")
                    with c3:
                        if st.button("❌ Quitar", key=f"d_{fecha_str}_{item['id_unico']}", use_container_width=True):
                            nueva_rutina = rutina_dia.copy()
                            nueva_rutina.pop(idx)
                            db.guardar_plan_dia(user_id, fecha_str, nueva_rutina)
                            st.rerun()
# --- PESTAÑA 2: GENERADOR ---
    with tab_generador:
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            enfoque = st.selectbox("Enfoque muscular para hoy:", ["Cuerpo Completo", "Tren Superior", "Tren Inferior", "Personalizado"])
        with col_gen2:
            duracion = st.slider("Duración máxima (min):", 30, 120, 60, 15)

        musculos_personalizados = []
        if enfoque == "Personalizado":
            lista_todos_musculos = sorted(list(set([ej.get("target_trad") for ej in ejercicios if ej.get("target_trad")])))
            musculos_personalizados = st.multiselect("Músculos:", lista_todos_musculos)

        btn_deshabilitado = (enfoque == "Personalizado" and len(musculos_personalizados) == 0)

        if st.button("⚡ Generar Rutina", type="primary", use_container_width=True, disabled=btn_deshabilitado):
            candidatos_equipo = ejercicios
            if equipos_seleccionados:
                # SE CORRIGIÓ EL BUG DEL PESO CORPORAL (ahora es estricto a tu selección)
                candidatos_equipo = [ej for ej in ejercicios if ej.get("equipment_trad") in equipos_seleccionados]

            candidatos_finales = []
            if enfoque == "Personalizado":
                candidatos_finales = [ej for ej in candidatos_equipo if ej.get("target_trad") in musculos_personalizados]
            elif enfoque == "Tren Superior":
                targets_upper = ["Pecho", "Dorsales", "Bíceps", "Tríceps", "Deltoides", "Espalda", "Antebrazos"]
                candidatos_finales = [ej for ej in candidatos_equipo if any(t in str(ej.get("target_trad")) for t in targets_upper)]
            elif enfoque == "Tren Inferior":
                targets_lower = ["Cuádriceps", "Glúteos", "Isquiotibiales", "Pantorrillas", "Aductores", "Abductores"]
                candidatos_finales = [ej for ej in candidatos_equipo if any(t in str(ej.get("target_trad")) for t in targets_lower)]
            else:
                candidatos_finales = candidatos_equipo

            if not candidatos_finales:
                st.error("⚠️ No hay ejercicios compatibles. Prueba agregando más equipos arriba.")
                st.session_state["rutina_generada"] = []
            else:
                num_ejercicios = max(3, min(duracion // 10, len(candidatos_finales)))
                st.session_state["rutina_generada"] = random.sample(candidatos_finales, num_ejercicios)
                st.session_state["candidatos_pool"] = candidatos_equipo

        if "rutina_generada" in st.session_state and st.session_state["rutina_generada"]:
            st.divider()
            st.subheader("📝 Tu Rutina de Hoy")
            rutina = st.session_state["rutina_generada"]

            for idx, ej in enumerate(rutina):
                with st.container(border=True):
                    col_info, col_img, col_inputs, col_btn = st.columns([2.5, 1.5, 1.5, 1])
                    with col_info:
                        nombre_traducido = traducir_nombre_ejercicio(ej.get('name', ''))
                        st.markdown(f"**{idx + 1}. {nombre_traducido}**")
                        st.write(f"🎯 {ej.get('target_trad')} | ⚙️ {ej.get('equipment_trad')}")
                    with col_img:
                        if ej.get("gif_url_correcta"):
                            st.image(f"{BASE_MEDIA_URL}{ej.get('gif_url_correcta').lstrip('/')}", use_container_width=True)
                    with col_inputs:
                        st.number_input("Peso (kg)", min_value=0.0, value=0.0, step=1.0, key=f"peso_{idx}")
                        st.checkbox("¡Hecho!", key=f"check_{idx}")
                    with col_btn:
                        if st.button("🔄 Swap", key=f"swap_{idx}"):
                            pool = st.session_state.get("candidatos_pool", ejercicios)
                            alternativas = [c for c in pool if c.get("id") != ej.get("id")]
                            if alternativas:
                                st.session_state["rutina_generada"][idx] = random.choice(alternativas)
                                st.rerun()

            st.divider()
            st.markdown("#### 🌤️ Contexto Ambiental y Esfuerzo (Features para ML)")
            col_ciudad, col_btn_clima = st.columns([3, 1], vertical_alignment="bottom")
            with col_ciudad:
                ciudad_input = st.text_input("📍 Ciudad actual:", placeholder="Ej: Cali, Madrid...")
            with col_btn_clima:
                if st.button("🔍 Detectar Clima", use_container_width=True) and ciudad_input:
                    with st.spinner("Buscando..."):
                        desc, temp = obtener_clima_api(ciudad_input)
                        st.session_state["clima_actual"] = desc
                        st.session_state["temp_actual"] = temp

            col_clima, col_temp, col_esfuerzo = st.columns(3)
            with col_clima:
                clima_actual = st.text_input("Clima", value=st.session_state.get("clima_actual", "Soleado"))
            with col_temp:
                temp_actual = st.number_input("Temp (°C)", value=st.session_state.get("temp_actual", 25))
            with col_esfuerzo:
                esfuerzo_rpe = st.slider("Esfuerzo Sesión (RPE 1-10)", 1, 10, 7)

            if st.button("💾 GUARDAR MICRODATOS COMPLETOS EN BITÁCORA", type="primary", use_container_width=True):
                datos_a_guardar = []
                fecha_actual = datetime.now().isoformat()
                
                for idx, ej in enumerate(rutina):
                    if st.session_state.get(f"check_{idx}"):
                        microdato = {
                            "id_evento": str(uuid.uuid4()),
                            "timestamp": fecha_actual,
                            "user_id": st.session_state.get("user_id"),
                            "usuario": {
                                "nombre": perfil_actual["nombre"], "sexo": perfil_actual["sexo"],
                                "edad": perfil_actual["edad"], "estatura_cm": perfil_actual["estatura_cm"]
                            },
                            "biometria_diaria": {
                                "peso_kg": perfil_actual["peso_kg"],
                                "medidas_cm": {
                                    "biceps": perfil_actual["biceps"], "abdomen": perfil_actual["abdomen"],
                                    "cintura": perfil_actual["cintura"], "cadera": perfil_actual["cadera"],
                                    "gluteos": perfil_actual["gluteos"], "cuadriceps": perfil_actual["cuadriceps"],
                                    "pantorrilla": perfil_actual["pantorrilla"]
                                }
                            },
                            "contexto_ambiental": {
                                "lugar_entrenamiento": perfil_elegido,
                                "ciudad": ciudad_input if ciudad_input else "Desconocida",
                                "clima": clima_actual, "temperatura_c": temp_actual
                            },
                            "metrica_sesion": {
                                "esfuerzo_rpe": esfuerzo_rpe, "objetivo_entrenamiento": objetivo
                            },
                            "ejercicio": {
                                "id_api": ej.get("id"),
                                "nombre": traducir_nombre_ejercicio(ej.get("name", "")),
                                "musculo_objetivo": ej.get("target_trad"),
                                "zona_cuerpo": ej.get("body_part_trad"),
                                "equipo_usado": ej.get("equipment_trad")
                            },
                            "ejecucion": {
                                "peso_levantado_kg": st.session_state.get(f"peso_{idx}", 0.0),
                                "completado": True
                            }
                        }
                        datos_a_guardar.append(microdato)
                
                if datos_a_guardar:
                    guardar_en_bitacora(datos_a_guardar)
                    st.success("¡HECHO! Microdatos granulares exportados con éxito. 🧠🤖")
                else:
                    st.warning("No marcaste ningún ejercicio como completado.")

# --- PESTAÑA 3: CATÁLOGO ---
    with tab_catalogo:
        st.header("Catálogo de Consulta")
        ej_filtrados = ejercicios
        if equipos_seleccionados:
            # SE CORRIGIÓ EL BUG DEL PESO CORPORAL (ahora es estricto a tu selección)
            ej_filtrados = [ej for ej in ej_filtrados if ej.get("equipment_trad") in equipos_seleccionados]
        
        c1, c2 = st.columns(2)
        zonas = ["Todos"] + sorted(list(set([e.get("body_part_trad") for e in ej_filtrados if e.get("body_part_trad")])))
        zona_sel = c1.selectbox("Zona", zonas)
        if zona_sel != "Todos":
            ej_filtrados = [e for e in ej_filtrados if e.get("body_part_trad") == zona_sel]
            
        musculos = ["Todos"] + sorted(list(set([e.get("target_trad") for e in ej_filtrados if e.get("target_trad")])))
        musculo_sel = c2.selectbox("Músculo", musculos)
        if musculo_sel != "Todos":
            ej_filtrados = [e for e in ej_filtrados if e.get("target_trad") == musculo_sel]
            
        if ej_filtrados:
            st.write(f"Mostrando {len(ej_filtrados)} resultados.")
            for ej in ej_filtrados[:15]:
                with st.container(border=True):
                    c_txt, c_img = st.columns([3, 1])
                    with c_txt:
                        nombre_cat = traducir_nombre_ejercicio(ej.get('name', ''))
                        st.markdown(f"**{nombre_cat}**")
                        st.write(f"🎯 Músculo: {ej.get('target_trad')}")
                        st.write(f"⚙️ Equipo: {ej.get('equipment_trad')}")
                    with c_img:
                        if ej.get("gif_url_correcta"):
                            st.image(f"{BASE_MEDIA_URL}{ej.get('gif_url_correcta').lstrip('/')}", width=100)
        else:
            st.warning("No hay resultados con la máquina o filtro que seleccionaste.")

if __name__ == "__main__":
    mostrar()