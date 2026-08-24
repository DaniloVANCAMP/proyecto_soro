import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database as db
import utils.calculos as calc

def mostrar(perfil):
    st.markdown("<h2 style='text-align: center; color: #2ecc71;'>📈 Evolución Clínica y Rendimiento</h2>", unsafe_allow_html=True)
    st.markdown("Analiza tu progreso histórico basado en los datos de tu bitácora de entrenamiento.")
    
    user_id = st.session_state.get("user_id")
    if not user_id: return
    
    # 1. Traer historial de Firebase
    historial_crudo = db.obtener_bitacora(user_id)
    
    if not historial_crudo:
        st.info("🏋️‍♂️ Aún no tienes entrenamientos registrados en tu bitácora. ¡Empieza a entrenar para ver tus gráficas de evolución!")
        return

    # 2. Procesamiento de Datos (Data Engineering)
    # Como hay múltiples ejercicios por día, agrupamos para sacar un solo peso y medida por día
    datos_diarios = {}
    genero = perfil.get('genero', 'Masculino')
    altura = float(perfil.get('estatura', 0))
    
    for registro in historial_crudo:
        fecha = registro.get("timestamp", "")[:10]
        if not fecha: continue
        
        bio = registro.get("biometria_diaria", {})
        peso = float(bio.get("peso_kg", 0))
        medidas = bio.get("medidas_cm", {})
        
        # Guardamos la última biometría registrada de ese día
        if peso > 0:
            datos_diarios[fecha] = {
                "fecha": fecha,
                "peso": peso,
                "cintura": float(medidas.get("cintura", 0)),
                "cuello": float(medidas.get("cuello", 0)),
                "cadera": float(medidas.get("cadera", 0))
            }
            
    if not datos_diarios:
        st.warning("Hay entrenamientos, pero no se registró el peso en ellos.")
        return

    # Convertir a DataFrame y ordenar por fecha
    df = pd.DataFrame(list(datos_diarios.values()))
    df = df.sort_values("fecha")
    
    # 3. Aplicar Motor Matemático a la Historia
    # Usamos map/apply para calcular el % de Grasa de CADA DÍA usando utils/calculos.py
    df["porcentaje_grasa"] = df.apply(
        lambda row: calc.calcular_grasa_marina(
            genero, altura, row["cuello"], row["cintura"], row["cadera"]
        ), axis=1
    )

    # ==============================================================
    # 🎨 SECCIÓN VISUAL (GRÁFICOS PLOTLY)
    # ==============================================================
    
    tab_peso, tab_grasa, tab_composicion = st.tabs(["⚖️ Peso Corporal", "📉 % de Grasa", "🧬 Composición Actual"])

    # --- PESTAÑA 1: PESO HISTÓRICO ---
    with tab_peso:
        st.subheader("Evolución de tu Peso (kg)")
        fig_peso = px.line(
            df, x="fecha", y="peso", 
            markers=True, 
            line_shape="spline", # Hace la curva suave
            color_discrete_sequence=["#3498db"]
        )
        fig_peso.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_peso, use_container_width=True)

    # --- PESTAÑA 2: GRASA CORPORAL (MARINA) ---
    with tab_grasa:
        st.subheader("Evolución de Grasa Corporal (Fórmula Marina)")
        # Filtramos los días donde sí haya cálculo mayor a 0
        df_grasa = df[df["porcentaje_grasa"] > 0]
        
        if df_grasa.empty:
            st.info("No hay suficientes medidas (Cintura, Cuello) en el historial para calcular la grasa de la Marina.")
        else:
            fig_grasa = px.line(
                df_grasa, x="fecha", y="porcentaje_grasa", 
                markers=True, 
                line_shape="spline",
                color_discrete_sequence=["#e74c3c"]
            )
            fig_grasa.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_grasa, use_container_width=True)

    # --- PESTAÑA 3: COMPOSICIÓN ACTUAL (DONA) ---
    with tab_composicion:
        st.subheader("Tu Composición Corporal Hoy")
        peso_actual = float(perfil.get('peso', 0))
        
        # Extraemos medidas actuales del perfil
        med_actual = perfil.get("medidas", {})
        cintura = float(med_actual.get("cintura", 0))
        cuello = float(med_actual.get("cuello", 0))
        cadera = float(med_actual.get("cadera", 0))
        
        # Llamamos al motor matemático
        grasa_actual = calc.calcular_grasa_marina(genero, altura, cuello, cintura, cadera)
        
        if grasa_actual <= 0:
            st.warning("⚠️ Actualiza tus medidas de cuello y cintura en tu perfil para ver tu composición corporal.")
        else:
            # Magia pura: Calculamos cuántos kilos son músculo y cuántos grasa
            kg_grasa, kg_magra = calc.analizar_composicion_corporal(peso_actual, grasa_actual)
            
            # Gráfico de Dona
            fig_dona = go.Figure(data=[go.Pie(
                labels=['Masa Magra (Músculo/Huesos)', 'Masa Grasa'],
                values=[kg_magra, kg_grasa],
                hole=.6,
                marker_colors=['#2ecc71', '#e74c3c']
            )])
            
            fig_dona.update_layout(
                annotations=[dict(text=f"{peso_actual} kg<br>Total", x=0.5, y=0.5, font_size=20, showarrow=False)],
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_dona, use_container_width=True)
            
            st.markdown(f"**💪 Masa Magra:** {kg_magra} kg")
            st.markdown(f"**🧈 Masa Grasa:** {kg_grasa} kg")