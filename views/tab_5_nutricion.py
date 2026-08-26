import json
import os
from datetime import datetime, timedelta, timezone
import database as db
import streamlit as st

# IMPORTACIÓN DE SUBMÓDULOS INDEPENDIENTES
from views import tab_5_2_creador, tab_5_3_platos, tab_5_4_hidratacion


@st.cache_data
def cargar_alimentos_base():
    ruta_json = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "alimentos_base.json"
    )
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


def mostrar():
    # CSS GLOBAL Y ENCABEZADO
    st.markdown(
        """
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
    
    .agua-box {
        background: #121926;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .agua-val { font-size: 2.2rem; font-weight: 900; color: #38bdf8; line-height: 1.1; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 15px;">
        <span style="font-size: 2rem;">🍏</span>
        <h1 style="margin: 0; padding: 0; text-align: center; font-size: 2rem; color: white;">Nutrición & Macros</h1>
    </div>
    """,
        unsafe_allow_html=True,
    )

    user_id = st.session_state.get("user_id")

    # ZONA HORARIA COLOMBIA (UTC-5)
    zona_colombia = timezone(timedelta(hours=-5))
    hoy = datetime.now(zona_colombia).date()

    with st.container(border=True):
        fecha_act = st.date_input("📅 Selecciona la fecha:", value=hoy)
    fecha_str = fecha_act.strftime("%Y-%m-%d")

    registro_dia = db.obtener_nutricion(user_id, fecha_str) or {}
    comidas_guardadas = registro_dia.get(
        "comidas",
        {"Desayuno": [], "Almuerzo": [], "Cena": [], "Snacks": []},
    )

    CATALOGO_ALIMENTOS = obtener_catalogo_completo(user_id)
    totales_dia = calcular_totales_dia(comidas_guardadas)

    # RESUMEN DIARIO DE MACROS
    st.markdown(
        "<div class='titulo-nutricion'>📊 Resumen Diario</div>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='metric-container'><div class='metric-value val-cal'>{int(totales_dia['cal'])}</div><div class='metric-label'>Kcal</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='metric-container'><div class='metric-value val-pro'>{round(totales_dia['pro'],1)}g</div><div class='metric-label'>Prot</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='metric-container'><div class='metric-value val-car'>{round(totales_dia['car'],1)}g</div><div class='metric-label'>Carbs</div></div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<div class='metric-container'><div class='metric-value val-gra'>{round(totales_dia['gra'],1)}g</div><div class='metric-label'>Grasas</div></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # SUBMÓDULO 1: CREADOR DEL CATÁLOGO GENERAL (D1, MARCAS)
    tab_5_2_creador.mostrar(user_id, fecha_str)

    st.divider()

    # SUBMÓDULO 2: CONSTRUCTOR DE PLATOS CON IA CONTEXTUAL RÁPIDA
    tab_5_3_platos.mostrar(
        user_id=user_id,
        fecha_str=fecha_str,
        comidas_guardadas=comidas_guardadas,
        catalogo_alimentos=CATALOGO_ALIMENTOS,
        calcular_totales_dia_func=calcular_totales_dia,
        zona_colombia=zona_colombia,
    )

    st.divider()

    # SUBMÓDULO 3: HIDRATACIÓN Y SUPLEMENTOS
    tab_5_4_hidratacion.mostrar(
        user_id=user_id,
        fecha_str=fecha_str,
        registro_dia=registro_dia,
        comidas_guardadas=comidas_guardadas,
        calcular_totales_dia_func=calcular_totales_dia,
    )