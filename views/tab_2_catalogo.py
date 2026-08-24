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

# Mantenemos esta función porque el Generador de Rutinas la usa internamente, pero borramos la visual.
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
    # CSS MAESTRO NUCLEAR V3: Transformando TABS en un GRID 2x2 Real
    st.markdown("""
    <style>
    /* Titulos */
    .titulo-config { 
        color: #e74c3c; 
        font-size: 1.4rem; 
        font-weight: bold; 
        margin-bottom: 10px; 
        margin-top: 15px; 
        border-bottom: 2px solid #e74c3c;
        padding-bottom: 5px;
    }
    
    /* MAGIA GRID PARA LAS PESTAÑAS (TABS) */
    /* Esto toma el contenedor original de las pestañas y lo obliga a ser una cuadrícula */
    div[data-baseweb="tab-list"] {
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 12px !important;
        width: 100% !important;
    }
    
    /* Estilo de cada pestaña para que parezca una tarjeta premium */
    div[data-testid="stTabs"] button[role="tab"] {
        background-color: #1a1c24 !important;
        border: 1px solid #2d303e !important;
        border-radius: 12px !important;
        padding: 15px 10px !important;
        margin: 0 !important;
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* Pestaña Activa (Seleccionada) */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #2b2b2b !important;
        border: 1px solid #e74c3c !important;
        border-bottom: 4px solid #e74c3c !important; /* Borde rojo imponente abajo */
    }
    
    /* Textos de las Pestañas */
    div[data-testid="stTabs"] button[role="tab"] p {
        color: #aaaaaa !important; 
        font-size: clamp(0.85rem, 3vw, 1.1rem) !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* Texto Pestaña Activa */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] p {
        color: #ffffff !important; 
        font-weight: 800 !important;
    }
    
    /* Ocultar las rayas default feas de Streamlit */
    div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # TÍTULO PRINCIPAL
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
        st.error("No se pudieron cargar los ejercicios. Verifica tu conexión.")
        return

    # Cargamos el perfil de forma invisible (sin la UI)
    perfil_actual = cargar_perfil()

    # ==========================================
    # SECCIÓN: CONFIGURACIÓN DE LA SESIÓN 
    # ==========================================
    st.markdown("<div class='titulo-config'>⚙️ Configuración de la Sesión</div>", unsafe_allow_html=True)
    
    with st.container(border=True):
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

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ENRUTAMIENTO HACIA LOS MÓDULOS HIJOS (El CSS arriba los convierte en una grilla 2x2)
    tab_planificador, tab_generador, tab_catalogo = st.tabs(["📅 Planificador", "⚡ Generador", "🔍 Catálogo"])

    with tab_planificador:
        tab_2_1_planificador.mostrar(ejercicios, equipos_seleccionados, perfil_elegido, BASE_MEDIA_URL, traducir_nombre_ejercicio)

    with tab_generador:
        tab_2_2_generador.mostrar(ejercicios, equipos_seleccionados, perfil_actual, perfil_elegido, objetivo, BASE_MEDIA_URL, traducir_nombre_ejercicio, obtener_clima_api, guardar_en_bitacora)

    with tab_catalogo:
        tab_2_3_catalogo_gral.mostrar(ejercicios, equipos_seleccionados, BASE_MEDIA_URL, traducir_nombre_ejercicio)