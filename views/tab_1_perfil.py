import os
import sys
import streamlit as st
from datetime import date, datetime
import database as db

# Importamos los submódulos independientes
from views import tab_1_1_datos, tab_1_2_estadisticas, tab_1_3_salud, tab_1_4_tips

# --- FUNCIONES BASE ---
def calcular_imc(peso_kg, altura_cm):
    if not peso_kg or not altura_cm or float(altura_cm) <= 0: return 0.0
    return round(float(peso_kg) / ((float(altura_cm) / 100) ** 2), 1)

def clasificar_imc(imc):
    if imc == 0: return "Sin datos", "⚪"
    if imc < 18.5: return "Bajo peso", "🔵"
    elif 18.5 <= imc < 24.9: return "Peso normal", "🟢"
    elif 25 <= imc < 29.9: return "Sobrepeso", "🟡"
    else: return "Obesidad", "🔴"

def calcular_calorias_objetivo(peso, altura, edad, genero, objetivo):
    if not peso or not altura or not edad: return 2000
    peso, altura, edad = float(peso), float(altura), int(edad)
    
    if genero == "Masculino":
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) + 5
    else:
        tmb = (10 * peso) + (6.25 * altura) - (5 * edad) - 161
        
    tmb_activa = tmb * 1.3
    obj_str = str(objetivo).lower()
    
    if "perder" in obj_str or "bajar" in obj_str: return int(tmb_activa - 400)
    elif "ganar" in obj_str or "volumen" in obj_str: return int(tmb_activa + 400)
    else: return int(tmb_activa)

def mostrar(exercises=None):
    # 1. INICIALIZAR EL ENRUTADOR
    if "vista_activa" not in st.session_state:
        st.session_state.vista_activa = "dashboard"

    user_id = st.session_state.get("user_id")
    if not user_id: return
    perfil = db.obtener_perfil(user_id) or {}

    # ==========================================
    # 2. LÓGICA DE NAVEGACIÓN A SUB-PÁGINAS
    # ==========================================
    if st.session_state.vista_activa != "dashboard":
        # Botón para volver atrás
        if st.button("⬅️ Regresar al Panel Principal", type="primary", use_container_width=True):
            st.session_state.vista_activa = "dashboard"
            st.rerun()
        
        st.divider()
        
        # Carga la vista correspondiente
        if st.session_state.vista_activa == "datos":
            tab_1_1_datos.mostrar(perfil)
        elif st.session_state.vista_activa == "stats":
            tab_1_2_estadisticas.mostrar(perfil)
        elif st.session_state.vista_activa == "salud":
            tab_1_3_salud.mostrar(perfil)
        elif st.session_state.vista_activa == "tips":
            tab_1_4_tips.mostrar(perfil)
            
        # IMPORTANTE: Se detiene aquí para no dibujar el dashboard debajo
        return

    # ==========================================
    # 3. DASHBOARD PRINCIPAL (Si vista_activa == 'dashboard')
    # ==========================================
    st.markdown("""
    <style>
    .header-panel { font-size: 1.5rem; font-weight: 800; color: #ffffff; text-align: left; margin-bottom: 15px; margin-top: -15px; }
    .weather-card { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 15px 20px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #333; }
    .weather-loc { font-size: 1.1rem; font-weight: bold; margin: 0; padding: 0; color: #fff;}
    .weather-desc { font-size: 0.85rem; margin: 0; padding: 0; color: #b3cce6;}
    .weather-icon { font-size: 2.5rem; margin: 0; padding: 0;}
    .metric-card { background-color: #1a1a1a; padding: 12px 5px; border-radius: 10px; border-left: 3px solid #2ecc71; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); margin-bottom: 10px;}
    .metric-title { font-size: 0.65rem; color: #aaaaaa; text-transform: uppercase; letter-spacing: 0.5px;}
    .metric-val { font-size: 1.3rem; font-weight: bold; color: #ffffff;}
    .seccion-titulo { font-size: 1.1rem; font-weight: bold; color: #eee; margin-top: 15px; margin-bottom: 15px;}
    
    /* CSS PARA TRANSFORMAR BOTONES EN TARJETAS CUADRADAS */
    div[data-testid="stButton"] button {
        height: 80px;
        background-color: #262730;
        color: white;
        border-radius: 15px;
        border: 1px solid #3a3b45;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        font-size: 15px !important;
        font-weight: 600;
        display: flex;
        justify-content: center !important;
        align-items: center !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #2ecc71;
        border-color: #2ecc71;
        color: #111;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

    nombre = perfil.get('nombre', 'Atleta').split()[0]
    st.markdown(f"<div class='header-panel'>👋 Hola, {nombre}</div>", unsafe_allow_html=True)

    # --- CLIMA ---
    hoy = datetime.now()
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    st.markdown(f"""
    <div class='weather-card'>
        <div>
            <div class='weather-loc'>Cali, Colombia 🇨🇴</div>
            <div class='weather-desc'>{dias[hoy.weekday()]}, {hoy.day} {meses[hoy.month - 1]} | 29°C • Hum 65%</div>
            <div style='font-size: 0.75rem; margin-top: 6px; color: #ffcc00; font-weight: bold;'>⚠️ Entrena con hidratación extra.</div>
        </div>
        <div class='weather-icon'>🌤️</div>
    </div>
    """, unsafe_allow_html=True)

    # --- MÉTRICAS ---
    st.markdown("<div class='seccion-titulo'>🔥 Monitoreo Diario</div>", unsafe_allow_html=True)
    peso = float(perfil.get('peso', 0))
    altura = float(perfil.get('estatura', 0))
    imc_actual = calcular_imc(peso, altura)
    estado_imc, color_imc = clasificar_imc(imc_actual)
    meta_calorias = calcular_calorias_objetivo(peso, altura, perfil.get('edad', 25), perfil.get('genero', 'Masculino'), perfil.get('objetivo', 'Mantenerse'))
    
    registro_hoy = db.obtener_nutricion(user_id, date.today().strftime("%Y-%m-%d")) or {}
    agua_consumida = float(registro_hoy.get("hidratacion_suplementos", {}).get("agua_litros", 0.0))
    calorias_consumidas = int(registro_hoy.get("totales", {}).get("cal", 0))

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card'><div class='metric-title'>⚖️ IMC</div><div class='metric-val'>{imc_actual}</div><div style='font-size: 0.7rem; color: #ddd;'>{color_imc} {estado_imc}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card' style='border-left-color: #3498db;'><div class='metric-title'>💧 Agua</div><div class='metric-val'>{agua_consumida}L</div><div style='font-size: 0.7rem; color: #ddd;'>Meta: 3.0 L</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card' style='border-left-color: #e74c3c;'><div class='metric-title'>🎯 Calorías</div><div class='metric-val'>{calorias_consumidas}</div><div style='font-size: 0.7rem; color: #ddd;'>Meta: {meta_calorias}</div></div>", unsafe_allow_html=True)

    # --- CUADRÍCULA 2x2 REAL ---
    st.markdown("<div class='seccion-titulo'>📱 Explora tu Perfil</div>", unsafe_allow_html=True)
    
    c_btn1, c_btn2 = st.columns(2)
    
    with c_btn1:
        if st.button("👤 Datos Usuario", use_container_width=True): 
            st.session_state.vista_activa = "datos"
            st.rerun()
        if st.button("📈 Estadísticas", use_container_width=True): 
            st.session_state.vista_activa = "stats"
            st.rerun()
            
    with c_btn2:
        if st.button("🏥 Salud Médica", use_container_width=True): 
            st.session_state.vista_activa = "salud"
            st.rerun()
        if st.button("💡 Tip del Día", use_container_width=True): 
            st.session_state.vista_activa = "tips"
            st.rerun()