import streamlit as st
from datetime import datetime
import database as db

def mostrar(perfil):
    user_id = st.session_state.get("user_id")
    
    if "editando_medidas" not in st.session_state:
        st.session_state.editando_medidas = False
        
    # --- EXTRACCIÓN DE DATOS BASE ---
    edad = perfil.get('edad', 25)
    estatura = float(perfil.get('estatura', 0))
    peso = float(perfil.get('peso', 0))
    objetivo = perfil.get('objetivo', 'Mantenerse')
    
    # --- EXTRACCIÓN DE MEDIDAS ---
    medidas = perfil.get("medidas", {})
    cuello = float(medidas.get('cuello', 0))
    hombros = float(medidas.get('hombro', 0))
    pecho = float(medidas.get('pecho', 0))
    cintura = float(medidas.get('cintura', 0))
    cadera = float(medidas.get('cadera', 0))
    brazo = float(medidas.get('brazo', 0))
    antebrazo = float(medidas.get('antebrazo', 0))
    pierna = float(medidas.get('pierna', 0))
    pantorrilla = float(medidas.get('pantorrilla', 0))
    fc_reposo = int(medidas.get('fc_reposo', 0))
    
    ultima_fecha = medidas.get('fecha_actualizacion', 'Sin registros previos')

    # --- CSS: ESTILO PLANIFICADOR ---
    st.markdown("""
    <style>
    .titulo-seccion {
        color: #ff4b4b; font-size: 1.4rem; font-weight: bold;
        margin-top: 1rem; border-bottom: 2px solid #ff4b4b; padding-bottom: 5px; margin-bottom: 15px;
    }
    .badge-fecha {
        display: inline-block; background-color: #262730; color: #aaaaaa;
        padding: 5px 10px; border-radius: 6px; font-size: 0.8rem; border: 1px solid #333; margin-bottom: 15px;
    }
    .info-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #2e2f38;
    }
    .info-row:last-child { border-bottom: none; }
    .lbl { color: #aaaaaa; font-size: 0.95rem; }
    .val { color: #ffffff; font-size: 1.05rem; font-weight: 600; text-align: right; }
    .val-fijo { color: #666666; font-size: 1.05rem; text-align: right; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👤 Perfil Medidas")
    st.markdown(f"<div class='badge-fecha'>🗓️ Última actualización: {ultima_fecha}</div>", unsafe_allow_html=True)

    if not st.session_state.editando_medidas:
        # ==========================================
        # MODO LECTURA 
        # ==========================================
        c_izq, c_der = st.columns(2)
        
        with c_izq:
            with st.container(border=True):
                st.markdown("<div class='titulo-seccion'>Datos Principales</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-row"><span class="lbl">Edad</span><span class="val-fijo">{edad} años</span></div>
                <div class="info-row"><span class="lbl">Estatura base</span><span class="val-fijo">{estatura:.0f} cm</span></div>
                <div class="info-row"><span class="lbl">Objetivo Actual</span><span class="val">{objetivo}</span></div>
                <div class="info-row"><span class="lbl">Peso Corporal</span><span class="val">{peso:.1f} kg</span></div>
                <div class="info-row"><span class="lbl">Frecuencia Cardíaca</span><span class="val">{fc_reposo} lpm</span></div>
                """, unsafe_allow_html=True)
                
        with c_der:
            with st.container(border=True):
                st.markdown("<div class='titulo-seccion'>Registro de Perímetros</div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-row"><span class="lbl">Cuello</span><span class="val">{cuello:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Hombros</span><span class="val">{hombros:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Pecho</span><span class="val">{pecho:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Cintura</span><span class="val">{cintura:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Cadera</span><span class="val">{cadera:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Brazos</span><span class="val">{brazo:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Antebrazos</span><span class="val">{antebrazo:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Piernas</span><span class="val">{pierna:.1f} cm</span></div>
                <div class="info-row"><span class="lbl">Pantorrillas</span><span class="val">{pantorrilla:.1f} cm</span></div>
                """, unsafe_allow_html=True)
            
        st.write("")
        if st.button("✏️ Modificar Medidas y Peso", use_container_width=True):
            st.session_state.editando_medidas = True
            st.rerun()
            
    else:
        # ==========================================
        # MODO EDICIÓN 
        # ==========================================
        st.info("💡 Las medidas de Cuello, Cintura y Estatura son vitales para los algoritmos de la IA.")
        
        with st.form("form_edicion_total"):
            with st.container(border=True):
                st.markdown("<div class='titulo-seccion'>Ajustes Generales</div>", unsafe_allow_html=True)
                c_obj, c_peso, c_fc = st.columns(3)
                
                lista_obj = ["Perder peso", "Mantenerse", "Ganar masa muscular"]
                idx_obj = lista_obj.index(objetivo) if objetivo in lista_obj else 1
                
                nuevo_objetivo = c_obj.selectbox("Objetivo", lista_obj, index=idx_obj)
                nuevo_peso = c_peso.number_input("Peso Total (kg)", value=float(peso), step=0.5, min_value=30.0)
                nueva_fc = c_fc.number_input("FC Reposo (lpm)", value=int(fc_reposo), step=1, min_value=0)
            
            with st.container(border=True):
                st.markdown("<div class='titulo-seccion'>Perímetros (cm)</div>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                nuevo_cuello = c1.number_input("Cuello", value=float(cuello), step=0.5)
                nuevos_hombros = c2.number_input("Hombros", value=float(hombros), step=0.5)
                nuevo_pecho = c3.number_input("Pecho", value=float(pecho), step=0.5)
                
                nueva_cintura = c1.number_input("Cintura", value=float(cintura), step=0.5)
                nueva_cadera = c2.number_input("Cadera", value=float(cadera), step=0.5)
                nuevo_brazo = c3.number_input("Brazos", value=float(brazo), step=0.5)
                
                nuevo_antebrazo = c1.number_input("Antebrazos", value=float(antebrazo), step=0.5)
                nueva_pierna = c2.number_input("Piernas", value=float(pierna), step=0.5)
                nueva_pantorrilla = c3.number_input("Pantorrillas", value=float(pantorrilla), step=0.5)
            
            st.write("")
            col_cancel, col_save = st.columns([1, 2])
            cancelar = col_cancel.form_submit_button("❌ Cancelar", use_container_width=True)
            guardar = col_save.form_submit_button("💾 Guardar Progreso", type="primary", use_container_width=True)
            
            if cancelar:
                st.session_state.editando_medidas = False
                st.rerun()
                
            if guardar:
                if user_id:
                    perfil_actualizado = perfil.copy()
                    perfil_actualizado["objetivo"] = nuevo_objetivo
                    perfil_actualizado["peso"] = nuevo_peso
                    perfil_actualizado["medidas"] = {
                        "cuello": nuevo_cuello,
                        "hombro": nuevos_hombros,
                        "pecho": nuevo_pecho,
                        "cintura": nueva_cintura,
                        "cadera": nueva_cadera,
                        "brazo": nuevo_brazo,
                        "antebrazo": nuevo_antebrazo,
                        "pierna": nueva_pierna,
                        "pantorrilla": nueva_pantorrilla,
                        "fc_reposo": nueva_fc,
                        "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    db.guardar_perfil(user_id, perfil_actualizado)
                
                st.session_state.editando_medidas = False
                st.success("✅ Progreso actualizado correctamente.")
                st.rerun()