import os
import sys
import requests
from datetime import date, datetime, timedelta, timezone
import streamlit as st
import database as db

# Importamos nuestro motor matemático central
import utils.calculos as calc

# Importamos los submódulos independientes
from views import tab_1_1_datos, tab_1_2_estadisticas, tab_1_3_salud, tab_1_4_tips


# --- MOTOR DE CLIMA Y GEOLOCALIZACIÓN DINÁMICA ---
def obtener_ip_cliente():
    """Intenta extraer la dirección IP real del cliente usando las cabeceras de Streamlit."""
    try:
        headers = getattr(st, "context", None)
        if headers and hasattr(headers, "headers"):
            x_forwarded = headers.headers.get("X-Forwarded-For")
            if x_forwarded:
                return x_forwarded.split(",")[0].strip()
    except Exception:
        pass
    return None


def obtener_bandera_pais(codigo_pais):
    """Convierte un código ISO de país (ej. 'CO') en su emoji de bandera."""
    if not codigo_pais or len(codigo_pais) != 2:
        return "🌎"
    return chr(ord(codigo_pais[0].upper()) + 127397) + chr(
        ord(codigo_pais[1].upper()) + 127397
    )


@st.cache_data(ttl=1800)
def obtener_clima_dinamico(ip_cliente=None, ciudad_perfil=None):
    """Detecta latitud/longitud por IP y consulta el clima real en Open-Meteo."""
    lat, lon = 3.4372, -76.5225  # Coordenadas de respaldo (Cali)
    nombre_ubicacion = "Cali, Colombia 🇨🇴"

    # 1. Geolocalización automática por IP
    try:
        url_ip = (
            f"http://ip-api.com/json/{ip_cliente}"
            if ip_cliente
            else "http://ip-api.com/json/"
        )
        r_geo = requests.get(url_ip, timeout=3)
        if r_geo.status_code == 200:
            data_geo = r_geo.json()
            if data_geo.get("status") == "success":
                lat = data_geo.get("lat", lat)
                lon = data_geo.get("lon", lon)
                ciudad = data_geo.get("city", "Tu Ubicación")
                pais_code = data_geo.get("countryCode", "CO")
                pais_nombre = data_geo.get("country", "Colombia")
                nombre_ubicacion = (
                    f"{ciudad}, {pais_nombre} {obtener_bandera_pais(pais_code)}"
                )
    except Exception:
        pass

    # 2. Consulta de clima en tiempo real
    try:
        url_clima = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&timezone=auto"
        r_clima = requests.get(url_clima, timeout=4)
        if r_clima.status_code == 200:
            data_clima = r_clima.json()
            temp = data_clima["current"]["temperature_2m"]
            hum = data_clima["current"]["relative_humidity_2m"]
            return nombre_ubicacion, f"{temp}°C", f"{hum}%"
    except Exception:
        pass

    return nombre_ubicacion, "25.0°C", "65%"


def mostrar(exercises=None):
    if "vista_activa" not in st.session_state:
        st.session_state.vista_activa = "dashboard"

    user_id = st.session_state.get("user_id")
    if not user_id:
        return
    perfil = db.obtener_perfil(user_id) or {}

    # ==========================================
    # LÓGICA DE NAVEGACIÓN A SUB-PÁGINAS
    # ==========================================
    if st.session_state.vista_activa != "dashboard":
        if st.button(
            "⬅️ Regresar al Panel Principal",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.vista_activa = "dashboard"
            st.rerun()

        st.divider()

        if st.session_state.vista_activa == "datos":
            tab_1_1_datos.mostrar(perfil)
        elif st.session_state.vista_activa == "stats":
            tab_1_2_estadisticas.mostrar(perfil)
        elif st.session_state.vista_activa == "salud":
            tab_1_3_salud.mostrar(perfil)
        elif st.session_state.vista_activa == "tips":
            tab_1_4_tips.mostrar(perfil)

        return

    # ==========================================
    # DASHBOARD PRINCIPAL
    # ==========================================
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    nombre = perfil.get("nombre", "Atleta").split()[0]
    st.markdown(
        f"<div class='header-panel'>👋 Hola, {nombre}</div>",
        unsafe_allow_html=True,
    )

    # --- CLIMA REAL Y UBICACIÓN DINÁMICA EN HORA COLOMBIA (UTC-5) ---
    ip_cliente = obtener_ip_cliente()
    ubicacion_str, temp_real, hum_real = obtener_clima_dinamico(
        ip_cliente=ip_cliente, ciudad_perfil=perfil.get("ciudad")
    )

    zona_colombia = timezone(timedelta(hours=-5))
    hoy = datetime.now(zona_colombia)

    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    meses = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]

    st.markdown(
        f"""
    <div class='weather-card'>
        <div>
            <div class='weather-loc'>{ubicacion_str}</div>
            <div class='weather-desc'>{dias[hoy.weekday()]}, {hoy.day} {meses[hoy.month - 1]} | {temp_real} • Hum {hum_real}</div>
            <div style='font-size: 0.75rem; margin-top: 6px; color: #ffcc00; font-weight: bold;'>⚠️ Entrena con hidratación extra.</div>
        </div>
        <div class='weather-icon'>🌤️</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # --- EXTRACCIÓN Y CÁLCULOS CENTRALIZADOS ---
    st.markdown(
        "<div class='seccion-titulo'>🔥 Monitoreo Diario</div>",
        unsafe_allow_html=True,
    )

    peso = float(perfil.get("peso", 0))
    altura = float(perfil.get("estatura", 0))
    edad = int(perfil.get("edad", 25))
    genero = perfil.get("genero", "Masculino")
    objetivo = perfil.get("objetivo", "Mantenerse")

    medidas = perfil.get("medidas", {})
    cuello = float(medidas.get("cuello", 0))
    cintura = float(medidas.get("cintura", 0))
    cadera = float(medidas.get("cadera", 0))

    # Invocamos la lógica separada
    imc_actual = calc.calcular_imc(peso, altura)
    estado_imc, color_imc = calc.clasificar_imc(imc_actual)

    metabolismo = calc.calcular_metabolismo(
        peso, altura, edad, genero, objetivo=objetivo
    )
    meta_calorias = metabolismo["target_cal"]

    grasa_marina = calc.calcular_grasa_marina(
        genero, altura, cuello, cintura, cadera
    )
    texto_grasa = f"{grasa_marina:.1f}%" if grasa_marina > 0 else "Sin datos"

    registro_hoy = db.obtener_nutricion(user_id, hoy.strftime("%Y-%m-%d")) or {}
    agua_consumida = float(
        registro_hoy.get("hidratacion_suplementos", {}).get("agua_litros", 0.0)
    )
    calorias_consumidas = int(registro_hoy.get("totales", {}).get("cal", 0))

    # --- RENDERIZADO (GRID 2x2) ---
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"<div class='metric-card'><div class='metric-title'>⚖️ IMC</div><div class='metric-val'>{imc_actual}</div><div style='font-size: 0.7rem; color: #ddd;'>{color_imc} {estado_imc}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='metric-card' style='border-left-color: #f39c12;'><div class='metric-title'>📉 Grasa Corporal</div><div class='metric-val'>{texto_grasa}</div><div style='font-size: 0.7rem; color: #ddd;'>Fórmula Marina</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='metric-card' style='border-left-color: #3498db;'><div class='metric-title'>💧 Agua</div><div class='metric-val'>{agua_consumida}L</div><div style='font-size: 0.7rem; color: #ddd;'>Meta: 3.0 L</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='metric-card' style='border-left-color: #e74c3c;'><div class='metric-title'>🎯 Calorías</div><div class='metric-val'>{calorias_consumidas}</div><div style='font-size: 0.7rem; color: #ddd;'>Meta: {meta_calorias} kcal</div></div>",
            unsafe_allow_html=True,
        )

    # --- NAVEGACIÓN ---
    st.markdown(
        "<div class='seccion-titulo'>📱 Explora tu Perfil</div>",
        unsafe_allow_html=True,
    )

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