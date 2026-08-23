import streamlit as st
import json

def extraer_instrucciones(datos_brutos):
    """Extrae las instrucciones en español de manera segura"""
    if not datos_brutos: return []
    
    if isinstance(datos_brutos, str):
        try: datos = json.loads(datos_brutos)
        except: datos = [datos_brutos]
    else:
        datos = datos_brutos

    pasos = []
    if isinstance(datos, dict):
        pasos = datos.get("es", datos.get("en", list(datos.values())[0] if datos else []))
    elif isinstance(datos, list):
        pasos = datos
        
    if isinstance(pasos, str): pasos = [pasos]
    return pasos

def mostrar(ejercicios, equipos_seleccionados, BASE_MEDIA_URL, traducir_nombre_ejercicio):
    # CSS Premium Estandarizado
    st.markdown("""
    <style>
    .titulo-filtro {
        color: #ff4b4b; font-size: 1.3rem; font-weight: bold;
        margin-bottom: 15px;
    }
    .stExpander {
        border-radius: 8px !important; border: 1px solid #333 !important;
        background-color: #1e1e1e !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Catálogo de Consulta")
    
    ej_filtrados = ejercicios
    if equipos_seleccionados:
        ej_filtrados = [ej for ej in ej_filtrados if ej.get("equipment_trad") in equipos_seleccionados]
    
    # 1. FILTROS EN SU PROPIA TARJETA (Como pediste en la imagen)
    with st.container(border=True):
        st.markdown("<div class='titulo-filtro'>Filtros de Búsqueda</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        
        zonas = ["Todos"] + sorted(list(set([e.get("body_part_trad") for e in ej_filtrados if e.get("body_part_trad")])))
        zona_sel = c1.selectbox("Zona del cuerpo:", zonas)
        
        if zona_sel != "Todos":
            ej_filtrados = [e for e in ej_filtrados if e.get("body_part_trad") == zona_sel]
            
        musculos = ["Todos"] + sorted(list(set([e.get("target_trad") for e in ej_filtrados if e.get("target_trad")])))
        musculo_sel = c2.selectbox("Músculo específico:", musculos)
        
        if musculo_sel != "Todos":
            ej_filtrados = [e for e in ej_filtrados if e.get("target_trad") == musculo_sel]

    st.divider()

    # 2. RENDERIZADO AGRUPADO POR EQUIPO
    if ej_filtrados:
        st.markdown(f"**Mostrando {len(ej_filtrados)} ejercicios encontrados.**")
        
        # Lógica de agrupación
        catalogo_agrupado = {}
        for ej in ej_filtrados:
            eq = ej.get("equipment_trad", "Desconocido")
            if eq not in catalogo_agrupado:
                catalogo_agrupado[eq] = []
            catalogo_agrupado[eq].append(ej)

        # Mostrar por herramienta (con un límite de seguridad para no trabar el celular)
        for equipo in sorted(catalogo_agrupado.keys()):
            ejercicios_equipo = catalogo_agrupado[equipo]
            
            with st.expander(f"⚙️ {equipo} ({len(ejercicios_equipo)} ejercicios)", expanded=False):
                for ej in ejercicios_equipo[:20]: # Mostramos máx 20 por herramienta para fluidez
                    with st.container(border=True):
                        # Título y contexto
                        nombre_cat = traducir_nombre_ejercicio(ej.get('name', ''))
                        st.markdown(f"**{nombre_cat}**")
                        st.caption(f"🎯 Músculo: {ej.get('target_trad')} | 👤 Zona: {ej.get('body_part_trad')}")
                        
                        # Imagen responsiva
                        c_img, c_espacio = st.columns([1, 1.5], vertical_alignment="center")
                        with c_img:
                            url_gif = ej.get("gif_url_correcta", "")
                            if url_gif and url_gif != "0": 
                                st.image(f"{BASE_MEDIA_URL}{url_gif.lstrip('/')}", use_container_width=True)
                                
                        # Cómo hacerlo
                        pasos_mostrar = extraer_instrucciones(ej.get("instructions", []))
                        if pasos_mostrar:
                            with st.expander("📖 Cómo hacerlo", expanded=False):
                                for paso in pasos_mostrar:
                                    st.write(f"- {paso}")
                    st.write("") # Espaciado
                
                # Aviso si hay demasiados
                if len(ejercicios_equipo) > 20:
                    st.info(f"💡 Hay {len(ejercicios_equipo) - 20} ejercicios más de {equipo}. Usa los filtros de arriba para ser más específico.")
    else:
        st.warning("⚠️ No hay resultados que coincidan con los filtros o el equipo que tienes en casa.")