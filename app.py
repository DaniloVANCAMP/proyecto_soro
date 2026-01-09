import streamlit as st
import pandas as pd
import os
from utils.calculos import procesar_datos
from utils.pdf_generator import generar_pdf

st.set_page_config(page_title="Control Obra", layout="wide")

# CSS
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem;}
    h1 {font-size: 1.5rem !important; font-weight: 700; color: #1f1f1f; margin-bottom: 0.5rem;}
    h2 {font-size: 1.2rem !important; font-weight: 600; padding-top: 1rem;}
    .stTable {font-size: 0.85rem;}
    thead tr th:first-child {display:none}
    tbody th {display:none}
</style>
""", unsafe_allow_html=True)

# VARIABLES
if "proyecto_items" not in st.session_state: st.session_state.proyecto_items = {}
if "item_actual" not in st.session_state: st.session_state.item_actual = None
rgb_color = (0, 51, 102)

# SIDEBAR
with st.sidebar:
    if os.path.exists("logo.png"): st.image("logo.png", width=180)
    else: st.header("🏗️ Constructora")
    st.divider()
    st.subheader("Portafolio")
    nombre = st.text_input("Nuevo Proyecto:")
    if st.button("Crear / Cargar", use_container_width=True):
        if nombre:
            if nombre not in st.session_state.proyecto_items:
                st.session_state.proyecto_items[nombre] = {"params": {}, "bitacora": None}
            st.session_state.item_actual = nombre
    if st.session_state.proyecto_items:
        st.session_state.item_actual = st.selectbox("Proyecto Activo:", list(st.session_state.proyecto_items.keys()))
    st.divider()
    with st.expander("🎨 Color"):
        color_marca = st.color_picker("Tono Reporte", "#003366")
        h = color_marca.lstrip('#')
        rgb_color = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# --- PANTALLA DE BIENVENIDA (Centrada) ----
if not st.session_state.item_actual:
    st.write("") # Espacio vacío arriba
    st.write("") 
    
    # Creamos 3 columnas: Izquierda(vacía), CENTRO(contenido), Derecha(vacía)
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

item_id = st.session_state.item_actual
st.title(f"Control: {item_id}")

# 1. CONFIGURACIÓN
st.markdown("#### 1. Configuración de Obra")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Contrato", "🏗️ Operativo", "🏢 Admin", "🚛 Logística RCD", "🎛️ Simulación"])

with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1: precio = st.number_input("Valor Contrato ($)", value=250000000.0, format="%.0f")
    with c2: meta = st.number_input("Meta Total (m)", value=1500.0)
    with c3: dias_est = st.number_input("Días Plazo", value=60)
    with c4: pct_imp = st.number_input("% Imprevistos", value=5.0, step=0.5, format="%.1f")
    clima_p = st.slider("Factor Lluvia", 0.1, 1.0, 0.9)

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

with tab3:
    c1, c2 = st.columns(2)
    with c1: arr_bod = st.number_input("Arriendo Bodega (Mes)", value=2500000.0, format="%.0f")
    with c2: arr_viv = st.number_input("Arriendo Vivienda (Mes)", value=2000000.0, format="%.0f")

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

with tab5:
    st.caption("Límites")
    c1, c2, c3 = st.columns(3)
    with c1: max_ayu = st.number_input("Max Ayu", value=15, min_value=1)
    with c2: max_mae = st.number_input("Max Mae", value=3, min_value=1)
    with c3: max_ret = st.number_input("Max Retro", value=1, min_value=0)

# Guardar
st.session_state.proyecto_items[item_id]["params"] = {
    "salario_ingeniero": s_ing, "jornal_ayudante": j_ayu, "jornal_maestro": j_mae,
    "alim_diaria": alim, "mq_retroexcavadora": c_retro, "mq_rotomartillo": c_roto,
    "ancho": ancho, "profundidad": prof, "meta_metros": meta, "precio_contrato": precio,
    "dias_estipulados": dias_est, "clima_proyectado": clima_p,
    "arriendo_bodega": arr_bod, "arriendo_vivienda": arr_viv,
    "factor_esponjamiento": factor_esp, "pct_imprevistos": pct_imp / 100.0,
    "limite_densidad": 10, "max_ayudantes": max_ayu, "max_maestros": max_mae, "max_retro": max_ret,
    "costo_pajarita": c_pajarita, "costo_viaje": c_viaje,
    "tiempo_cargue": t_cargue, "tiempo_transporte": t_ciclo, "capacidad_volqueta": cap_volq
}

# 2. ARCHIVOS
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
        st.success("✅"); st.rerun()

with c2:
    if os.path.exists(RUTA_COMPLETA):
        try:
            st.session_state.proyecto_items[item_id]["bitacora"] = pd.read_excel(RUTA_COMPLETA, sheet_name="Bitacora")
            st.info(f"📂 Archivo: **{NOMBRE_ARCHIVO}**")
        except: st.error("Error archivo.")
    else: st.warning("Sube archivo.")

# 3. RESULTADOS
if st.session_state.proyecto_items[item_id]["bitacora"] is not None:
    res = procesar_datos(st.session_state.proyecto_items[item_id]["params"], st.session_state.proyecto_items[item_id]["bitacora"])
    
    st.divider()
    st.markdown("#### 3. Resultados Gerenciales")
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("📊 Estado")
        st.dataframe(res["dashboard"].set_index("Concepto (Día)").T, use_container_width=True)
    with c2:
        st.caption("🚚 Flota Sugerida")
        st.info(f"Requieres: **{res['flota']['num_volquetas']} Volquetas** y **1 Pajarita**.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.caption("📉 Inercia vs Optimización")
        st.dataframe(res["comparativa"], use_container_width=True, hide_index=True)
        st.caption("💰 Balance")
        st.dataframe(res["balance"], use_container_width=True, hide_index=True)
    with c2:
        st.caption("🏆 Top 5")
        st.dataframe(res["top5"][["Ayud", "Mae", "Retro", "Días", "Utilidad_Show"]], use_container_width=True, hide_index=True)

    st.divider()
    cp, _ = st.columns([1, 3])
    with cp:
        cfg = {"logo": "logo.png", "color": rgb_color}
        if st.button("📄 PDF", type="primary", use_container_width=True):
            p = generar_pdf(res, item_id, cfg)

            with open(p, "rb") as f: st.download_button("Descargar", f, f"Reporte_{item_id}.pdf", "application/pdf")
