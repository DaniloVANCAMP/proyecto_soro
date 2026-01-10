import streamlit as st
import pandas as pd
import os
import json

# Imports de tu proyecto
try:
    from utils.calculos import procesar_datos
    from utils.pdf_generator import generar_pdf
    from utils.google_oauth import obtener_servicio_drive # Si usas esto para subir archivos
    from utils.firebase_auth import get_login_url, get_drive_connect_url, canjear_codigo, obtener_info_usuario, cerrar_sesion
    from utils.firestore_db import guardar_usuario_db # Si sigues usando la BD
except ImportError as e:
    st.error(f"⚠️ Error de importación: {e}")
    st.stop()

st.set_page_config(page_title="Control de Obra", layout="wide")

# -------------------------------------------------------------------------------------
# LÓGICA MAESTRA DE AUTENTICACIÓN
# -------------------------------------------------------------------------------------
if "user" not in st.session_state: st.session_state.user = None
if "drive_creds" not in st.session_state: st.session_state.drive_creds = None

# --- CAPTURAR EL CÓDIGO QUE DEVUELVE GOOGLE ---
if "code" in st.query_params:
    code = st.query_params["code"]
    
    # Canjeamos el código por tokens (sirve para login o para drive)
    tokens = canjear_codigo(code)
    
    if tokens:
        # CASO 1: El usuario NO estaba logueado -> Es un LOGIN
        if not st.session_state.user:
            info = obtener_info_usuario(tokens["access_token"])
            if info:
                st.session_state.user = info["email"]
                # Opcional: Guardar en Firestore
                # guardar_usuario_db({"email": info["email"]})
                st.success(f"¡Hola de nuevo, {info.get('name')}!")
        
        # CASO 2: El usuario YA estaba logueado -> Es VINCULACIÓN DE DRIVE
        else:
            st.session_state.drive_creds = tokens
            st.toast("✅ Google Drive vinculado correctamente", icon="📂")
            
    # Limpiamos la URL
    st.query_params.clear()
    st.rerun()

# -------------------------------------------------------------------------------------
# PANTALLA DE LOGIN (Si no ha entrado)
# -------------------------------------------------------------------------------------
if not st.session_state.user:
    st.markdown(f"""
    <div style='text-align:center; padding-top: 50px;'>
        <h1>🚧 Constructora Vanoy SAS</h1>
        <p>Sistema de Control de Obra</p>
        <br>
        <a href="{get_login_url()}" target="_self" style="
            background-color: #4285F4; color: white; padding: 12px 24px; 
            text-decoration: none; border-radius: 5px; font-weight: bold;">
            G Iniciar Sesión con Google
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# -------------------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL (Usuario ya adentro)
# -------------------------------------------------------------------------------------
usuario_actual = st.session_state.user

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{usuario_actual}**")
    
    st.divider()
    
    # --- BOTÓN PARA VINCULAR DRIVE (DENTRO DE LA APP) ---
    if not st.session_state.drive_creds:
        st.warning("⚠️ Drive no conectado")
        st.markdown(f"""
        <a href="{get_drive_connect_url()}" target="_self" style="
            display: block; text-align: center;
            background-color: #fff; color: #333; border: 1px solid #ccc;
            padding: 8px; text-decoration: none; border-radius: 4px; font-size: 0.9em;">
            🔗 Conectar Google Drive
        </a>
        """, unsafe_allow_html=True)
    else:
        st.success("✅ Drive Conectado")
        if st.button("Desconectar Drive"):
            st.session_state.drive_creds = None
            st.rerun()

    st.divider()
    if st.button("Cerrar Sesión"):
        cerrar_sesion()

# --- AQUÍ VA EL RESTO DE TU LÓGICA (TABS, CÁLCULOS, ETC) ---
st.title(f"Panel de Control")
st.info("Bienvenido al sistema. Usa el menú lateral para gestionar tus proyectos.")
# ... Pega aquí tus Tabs, cálculos, etc.
# -------------------------------------------------------------------------------------
# INTERFAZ PRINCIPAL
# -------------------------------------------------------------------------------------

# Variables iniciales del proyecto
if "proyecto_items" not in st.session_state: st.session_state.proyecto_items = {}
if "item_actual" not in st.session_state: st.session_state.item_actual = None
rgb_color = (0, 51, 102)

# -------------------------------------------------------------------------------------
# SIDEBAR (Menú Lateral)
# -------------------------------------------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"): 
        st.image("logo.png", width=180)
    else: 
        st.header("🏗️ Constructora")
    
    st.divider()
    st.subheader("Portafolio")
    
    # Crear nuevo proyecto
    nombre = st.text_input("Nuevo Proyecto:")
    if st.button("Crear / Cargar", use_container_width=True):
        if nombre:
            if nombre not in st.session_state.proyecto_items:
                st.session_state.proyecto_items[nombre] = {"params": {}, "bitacora": None}
            st.session_state.item_actual = nombre
    
    # Selector de proyectos existentes
    if st.session_state.proyecto_items:
        st.session_state.item_actual = st.selectbox("Proyecto Activo:", list(st.session_state.proyecto_items.keys()))
    
    st.divider()
    with st.expander("🎨 Color"):
        color_marca = st.color_picker("Tono Reporte", "#003366")
        h = color_marca.lstrip('#')
        rgb_color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# -------------------------------------------------------------------------------------
# PANTALLA DE BIENVENIDA (Si no hay proyecto seleccionado)
# -------------------------------------------------------------------------------------
if not st.session_state.item_actual:
    st.write("") 
    st.write("") 
    st.write("Constructora Vanoy SAS") 
    
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    with col_centro:
        st.info("👈 **Para comenzar:**")
        st.markdown("""
            <div style='text-align: center; color: #666;'>
                <h3>¡Bienvenido al Control de Obra!</h3>
                <p>Ve al menú lateral (izquierda), escribe un nombre <br>
                y presiona el botón <b>'Crear / Cargar'</b>.</p>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# -------------------------------------------------------------------------------------
# CONTENIDO DEL PROYECTO
# -------------------------------------------------------------------------------------
item_id = st.session_state.item_actual
st.write("") 
st.title(f"Control: {item_id}")

# Tabs principales
st.markdown("#### 1. Configuración de Obra")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Contrato", "🏗️ Operativo", "🏢 Admin", "Logística RCD", "🎛️ Simulación"])

# === Pestaña 1: Contrato ===
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: precio = st.number_input("Valor Contrato ($)", value=250000000.0, format="%.0f")
    with c2: meta = st.number_input("Meta Total (m)", value=1500.0)
    with c3: dias_est = st.number_input("Días Plazo", value=60)
    with c4: pct_imp = st.number_input("% Imprevistos", value=5.0, step=0.5, format="%.1f")
    clima_p = st.slider("Factor Lluvia", 0.1, 1.0, 0.9)

# === Pestaña 2: Operativo ===
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Personal")
        sc1, sc2 = st.columns(2)
        with sc1:
            j_ayu = st.number_input("Jornal Ayudante", value=120000.0, format="%.0f")
            j_mae = st.number_input("Jornal Maestro", value=160000.0, format="%.0f")
        with sc2:
            s_ing = st.number_input("Salario Ing. (Mes)", value=3500000.0, format="%.0f")
            alim  = st.number_input("Alimentación/Día", value=20000.0, format="%.0f")     
    with c2:
        st.caption("Excavación")
        sc3, sc4 = st.columns(2)
        with sc3:
            c_retro = st.number_input("Costo Retro/Día", value=500000.0, format="%.0f")
            c_roto  = st.number_input("Costo Roto/Día", value=80000.0, format="%.0f")
            factor_esp = st.number_input("Factor Esponjamiento", value=1.3, step=0.1)
        with sc4:
            ancho = st.number_input("Ancho Zanja (m)", value=2.0)
            prof  = st.number_input("Profundidad (m)", value=1.2)

# === Pestaña 3: Admin ===
with tab3:
    c1, c2 = st.columns(2)
    with c1: arr_bod = st.number_input("Arriendo Bodega (Mes)", value=2500000.0, format="%.0f")
    with c2: arr_viv = st.number_input("Arriendo Vivienda (Mes)", value=2000000.0, format="%.0f")

# === Pestaña 4: Logística ===
with tab4:
    st.info("Logística")
    c1, c2, c3 = st.columns(3)
    with c1:
        c_pajarita = st.number_input("Pajarita/Día", value=450000.0, format="%.0f")
        c_viaje = st.number_input("Costo Viaje", value=85000.0, format="%.0f")
    with c2:
        t_cargue = st.number_input("Tiempo Cargue (min)", value=15.0)
        t_ciclo = st.number_input("Ciclo Volqueta (min)", value=60.0)
    with c3:
        cap_volq = st.number_input("Capacidad Volq (m3)", value=7.0)
        st.caption(f"Ciclo Total: {t_cargue + t_ciclo} min")

# === Pestaña 5: Simulación ===
with tab5:
    c1, c2, c3 = st.columns(3)
    with c1: max_ayu = st.number_input("Max Ayu", value=15, min_value=1)
    with c2: max_mae = st.number_input("Max Mae", value=3, min_value=1)
    with c3: max_ret = st.number_input("Max Retro", value=1, min_value=0)

# --- GUARDAR PARÁMETROS EN MEMORIA ---
st.session_state.proyecto_items[item_id]["params"] = {
    "salario_ingeniero": s_ing, "jornal_ayudante": j_ayu, "jornal_maestro": j_mae,
    "alim_diaria": alim, "mq_retroexcavadora": c_retro, "mq_rotomartillo": c_roto,
    "ancho": ancho, "profundidad": prof, "meta_metros": meta, "precio_contrato": precio,
    "dias_estipulados": dias_est, "clima_proyectado": clima_p,
    "arriendo_bodega": arr_bod, "arriendo_vivienda": arr_viv,
    "factor_esponjamiento": factor_esp, "pct_imprevistos": pct_imp / 100.0,
    "max_ayudantes": max_ayu, "max_maestros": max_mae, "max_retro": max_ret,
    "costo_pajarita": c_pajarita, "costo_viaje": c_viaje,
    "tiempo_cargue": t_cargue, "tiempo_transporte": t_ciclo, "capacidad_volqueta": cap_volq
}

# -------------------------------------------------------------------------------------
# CARGA DE BITÁCORA Y RESULTADOS
# -------------------------------------------------------------------------------------
st.divider()
st.markdown("#### 2. Bitácora")
CARPETA_INPUT = "input"
nombre_safe = "".join([c for c in item_id if c.isalnum() or c in (' ', '-', '_')]).strip()
NOMBRE_ARCHIVO = f"Bitacora_{nombre_safe}.xlsx"
RUTA_COMPLETA = os.path.join(CARPETA_INPUT, NOMBRE_ARCHIVO)

if not os.path.exists(CARPETA_INPUT): os.makedirs(CARPETA_INPUT)

c1, c2 = st.columns([1, 2])
with c1:
    up = st.file_uploader("Cargar", type=["xlsx"], label_visibility="collapsed")
    if up:
        with open(RUTA_COMPLETA, "wb") as f: f.write(up.getbuffer())
        st.success("✅ Cargado correctamente")
        st.rerun()

with c2:
    if os.path.exists(RUTA_COMPLETA):
        try:
            st.session_state.proyecto_items[item_id]["bitacora"] = pd.read_excel(RUTA_COMPLETA, sheet_name="Bitacora")
            st.info(f"📂 Archivo: **{NOMBRE_ARCHIVO}**")
        except: st.error("Error al leer archivo.")
    else: st.warning("Sube archivo Excel con la hoja 'Bitacora'.")

# --- PROCESAMIENTO Y DASHBOARD ---
if st.session_state.proyecto_items[item_id]["bitacora"] is not None:
    # Llamamos a la función de cálculos
    res = procesar_datos(st.session_state.proyecto_items[item_id]["params"], st.session_state.proyecto_items[item_id]["bitacora"])
    
    st.divider()
    st.markdown("#### 3. Resultados Gerenciales")
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("📊 Estado")
        st.dataframe(res["dashboard"].set_index("Concepto (Día)").T, use_container_width=True)
   
    with c2:
        st.caption("🚚 Equipo Sugerido Eliminación de Escombros")
        st.info(f"Requieres: **{res['flota']['num_volquetas']} Volquetas** y **1 Pajarita**.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("📉 Tendencia Actual vs Optimización")
        st.dataframe(res["comparativa"], use_container_width=True, hide_index=True)
        st.caption("💰 Balance")
        st.dataframe(res["balance"], use_container_width=True, hide_index=True)
    with c2:
        st.caption("🏆 Top 5")
        st.dataframe(res["top5"][["Ayud", "Mae", "Retro", "Días", "Utilidad_Show"]], use_container_width=True, hide_index=True)

    # --- GENERACIÓN DE PDF ---
    st.divider()
    cp, _ = st.columns([1, 3])
    with cp:
        cfg = {"logo": "logo.png", "color": rgb_color}
        if st.button("📄 PDF", type="primary", use_container_width=True):
            p = generar_pdf(res, item_id, cfg)
            with open(p, "rb") as f: 
                st.download_button("Descargar", f, f"Reporte_{item_id}.pdf", "application/pdf")




































