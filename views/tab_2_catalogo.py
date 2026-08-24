import json
import os
import requests
import time
import streamlit as st
import database as db 

# IMPORTAMOS NUESTROS TRES MÓDULOS NUEVOS
from views import tab_2_1_planificador, tab_2_2_generador, tab_2_3_catalogo_gral

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
    "assisted": "Asistido", "band": "Banda de resistencia",
    "barbell": "Barra recta", "body weight": "Peso corporal",
    "bosu ball": "Bosu", "cable": "Polea / Cable", "dumbbell": "Mancuerna",
    "elliptical machine": "Elíptica", "ez barbell": "Barra Z", "hammer": "Máquina Hammer",
    "kettlebell": "Pesa Rusa", "leverage machine": "Máquina de palanca",
    "medicine ball": "Balón Medicinal", "olympic barbell": "Barra Olímpica",
    "resistance band": "Banda de resistencia", "roller": "Rodillo",
    "rope": "Cuerda", "skierg machine": "SkiErg", "sled machine": "Trineo de empuje",
    "smith machine": "Máquina Smith", "stability ball": "Fitball",
    "stationary bike": "Bicicleta estática", "stepmill machine": "Escaladora",
    "tire": "Neumático", "trap bar": "Barra Hexagonal",
    "upper body ergometer": "Ergómetro superior", "weighted": "Lastrado",
    "wheel roller": "Rueda Abdominal"
}
DICCIONARIO_MUSCULOS = {
    "glutes": "Glúteos", "gluteus maximus": "Glúteo Mayor",
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
            return respuesta.json()[0][0][0].title()
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
            return traducir_nombre_ejercicio(desc), temp
    except Exception:
        pass
    return "Desconocido", 25

@st.cache_data(show_spinner="Cargando ejercicios desde la API...")
def cargar_ejercicios_completos():
    try:
        respuesta = requests.get(URL_JSON, timeout=10)
        respuesta.raise_for_status()
        ejercicios = respuesta.json()
        for ej in ejercicios:
            ej["body_part_trad"] = fmt_zona(ej.get("bodyPart", ej.get("body_part", "")))
            ej["target_trad"] = fmt_musculo(ej.get("target", ""))
            ej["equipment_trad"] = fmt_equipo(ej.get("equipment", ""))
            ej["gif_url_correcta"] = ej.get("gifUrl", ej.get("gif_url", ""))
        return ejercicios
    except Exception as e:
        return []

# ==========================================
# 3. INTERFAZ PRINCIPAL (ROUTER)
# ==========================================
def mostrar(exercises_param=None, base_media_url_param=None):
    st.markdown("""
    <style>
    .titulo-config { 
        color: #e74c3c; 
        font-size: 1.4rem; 
        font-weight: bold; 
        margin-bottom: 10px; 
        margin-top: 15px; 
        border-bottom: 2px solid #e74c3c;
        padding-bottom: 5px;
    }
    div[data-baseweb="tab-list"] { display: grid !important; grid-template-columns: repeat(2, 1fr) !important; gap: 12px !important; width: 100% !important; }
    div[data-testid="stTabs"] button[role="tab"] { background-color: #1a1c24 !important; border: 1px solid #2d303e !important; border-radius: 12px !important; padding: 15px 10px !important; margin: 0 !important; width: 100% !important; display: flex !important; justify-content: center !important; align-items: center !important; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { background-color: #2b2b2b !important; border: 1px solid #e74c3c !important; border-bottom: 4px solid #e74c3c !important; }
    div[data-testid="stTabs"] button[role="tab"] p { color: #aaaaaa !important; font-size: clamp(0.85rem, 3vw, 1.1rem) !important; font-weight: 600 !important; margin: 0 !important; text-align: center !important; }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p { color: #ffffff !important; font-weight: 800 !important; }
    div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px;">
        <span style="font-size: 2.2rem;">💪</span>
        <h1 style="margin: 0; padding: 0; text-align: center; font-size: 2.2rem; line-height: 1.1; color: white;">Centro Entrenamiento</h1>
        <span style="font-size: 2.2rem; display: inline-block; transform: scaleX(-1);">💪</span>
    </div>
    """, unsafe_allow_html=True)

    if exercises_param and len(exercises_param) > 10:
        ejercicios = exercises_param
    else:
        ejercicios = cargar_ejercicios_completos()

    if not ejercicios:
        st.error("No se pudieron cargar los ejercicios.")
        return

    perfil_actual = cargar_perfil()

    # ==========================================
    # SECCIÓN: CONFIGURACIÓN (BLINDADA A PRUEBA DE F5)
    # ==========================================
    st.markdown("<div class='titulo-config'>⚙️ Configuración de la Sesión</div>", unsafe_allow_html=True)
    
    presets = cargar_presets()
    opciones_perfil = list(presets.keys()) + ["➕ Crear nuevo lugar/perfil..."]
    opciones_obj = ["Hipertrofia", "Fuerza", "Resistencia", "Pérdida de Peso"]

    if "config_lugar" not in st.session_state or st.session_state.config_lugar not in opciones_perfil:
        url_lugar = st.query_params.get("lugar", opciones_perfil[0])
        st.session_state.config_lugar = url_lugar if url_lugar in opciones_perfil else opciones_perfil[0]
        
    if "config_dias" not in st.session_state:
        st.session_state.config_dias = int(st.query_params.get("dias", 4))
        
    if "config_objetivo" not in st.session_state:
        url_obj = st.query_params.get("obj", "Hipertrofia")
        st.session_state.config_objetivo = url_obj if url_obj in opciones_obj else opciones_obj[0]

    def actualizar_memoria():
        st.query_params["lugar"] = st.session_state.config_lugar
        st.query_params["dias"] = str(st.session_state.config_dias)
        st.query_params["obj"] = st.session_state.config_objetivo

    with st.container(border=True):
        perfil_elegido = st.selectbox("Lugar de entrenamiento activo:", opciones_perfil, key="config_lugar", on_change=actualizar_memoria)
        
        # --- INICIO BOTONERA DE DÍAS ESTILO APP NATIVA ---
        st.markdown("<p style='font-size: 14px; font-weight: 600; color: #ffffff; margin-bottom: 5px; margin-top: 5px;'>Días a entrenar por semana:</p>", unsafe_allow_html=True)
        
        dias_entreno = st.radio(
            "dias_entreno_radio", 
            options=[1, 2, 3, 4, 5, 6, 7], 
            horizontal=True, 
            label_visibility="collapsed",
            key="config_dias",
            on_change=actualizar_memoria
        )

        dias = st.session_state.config_dias
        
        # CSS ULTRA ESPECÍFICO QUE ANIQUILA EL CÍRCULO Y EXPANDE AL 100%
        css_botonera = """<style>
        /* Estirar el radio group al 100% de la tarjeta */
        section.main div[data-testid="stRadio"],
        section.main div[data-testid="stRadio"] > div,
        section.main div[data-testid="stRadio"] div[role="radiogroup"] {
            width: 100% !important;
            max-width: 100% !important;
            display: flex !important;
            flex-direction: row !important;
            gap: 6px !important;
            margin-bottom: 10px !important;
        }

        /* Cada tarjeta se reparte por igual en el ancho (1/7 cada una) */
        section.main div[data-testid="stRadio"] div[role="radiogroup"] > label {
            flex: 1 1 0% !important;
            width: 100% !important;
            min-width: 0 !important;
            background-color: #1a1c24 !important; 
            border: 1px solid #2d303e !important; 
            border-radius: 8px !important;
            padding: 12px 0px !important; 
            margin: 0 !important; 
            display: flex !important; 
            justify-content: center !important; 
            align-items: center !important;
            text-align: center !important;
            cursor: pointer !important; 
            transition: all 0.3s ease !important;
        }

        /* ELIMINACIÓN NUCLEAR DE LOS CÍRCULOS DEL RADIO BUTTON */
        section.main div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-of-type,
        section.main div[data-testid="stRadio"] div[role="radiogroup"] label [data-baseweb="radio"],
        section.main div[data-testid="stRadio"] div[role="radiogroup"] label input {
            display: none !important;
            width: 0px !important;
            height: 0px !important;
            opacity: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: none !important;
        }

        /* Centrar el número perfectamente */
        section.main div[data-testid="stRadio"] div[role="radiogroup"] label p { 
            color: #aaaaaa !important; 
            font-weight: 800 !important; 
            font-size: 1.1rem !important; 
            margin: 0 !important;
            padding: 0 !important;
            text-align: center !important;
            width: 100% !important;
        }
        """
        
        # Color degradado dinámico por cada opción activa
        for i in range(1, dias + 1):
            intensidad = 0.4 + (0.6 * (i / dias))
            css_botonera += f"""
            section.main div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child({i}) {{
                background-color: rgba(231, 76, 60, {intensidad:.2f}) !important;
                border-color: #e74c3c !important;
                box-shadow: 0 0 6px rgba(231, 76, 60, {intensidad/2:.2f}) !important;
            }}
            section.main div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child({i}) p {{ 
                color: #ffffff !important; 
                font-weight: 900 !important;
            }}
            """
            
        css_botonera += "</style>"
        st.markdown(css_botonera, unsafe_allow_html=True)
        # --- FIN BOTONERA DE DÍAS ESTILO APP NATIVA ---
        
        objetivo = st.selectbox("Objetivo:", opciones_obj, key="config_objetivo", on_change=actualizar_memoria)

        equipamientos_globales = sorted(list(set([ej.get("equipment_trad", "N/A") for ej in ejercicios if ej.get("equipment_trad")])))
        equipos_seleccionados = []

        if perfil_elegido == "➕ Crear nuevo lugar/perfil...":
            nuevo_nombre = st.text_input("Nombre del nuevo perfil:")
            if st.button("Crear Perfil") and nuevo_nombre:
                if nuevo_nombre not in presets:
                    presets[nuevo_nombre] = []
                    guardar_presets(presets)
                    st.session_state.config_lugar = nuevo_nombre
                    actualizar_memoria()
                    st.rerun()
        else:
            maquinas_guardadas = [eq for eq in presets.get(perfil_elegido, []) if eq in equipamientos_globales]
            
            equipos_seleccionados = st.multiselect(f"Equipamiento en {perfil_elegido}:", equipamientos_globales, default=maquinas_guardadas)
            
            if equipos_seleccionados != maquinas_guardadas:
                if st.button("💾 Guardar Equipamiento", use_container_width=True):
                    presets[perfil_elegido] = equipos_seleccionados
                    guardar_presets(presets)
                    st.rerun()

        st.session_state["config_equipo_actual"] = ", ".join(equipos_seleccionados) if equipos_seleccionados else "Ninguno"

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ENRUTAMIENTO HACIA LOS MÓDULOS HIJOS
    tab_planificador, tab_generador, tab_catalogo = st.tabs(["📅 Planificador", "⚡ Generador", "🔍 Catálogo"])

    with tab_planificador:
        tab_2_1_planificador.mostrar(ejercicios, equipos_seleccionados, perfil_elegido, BASE_MEDIA_URL, traducir_nombre_ejercicio)

    with tab_generador:
        tab_2_2_generador.mostrar(ejercicios, equipos_seleccionados, perfil_actual, perfil_elegido, objetivo, BASE_MEDIA_URL, traducir_nombre_ejercicio, obtener_clima_api, guardar_en_bitacora)

    with tab_catalogo:
        tab_2_3_catalogo_gral.mostrar(ejercicios, equipos_seleccionados, BASE_MEDIA_URL, traducir_nombre_ejercicio)