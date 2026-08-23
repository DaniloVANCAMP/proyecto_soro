import streamlit as st
import pandas as pd

def mostrar(perfil):
    peso = float(perfil.get('peso', 0))
    medidas = perfil.get("medidas", {})

    st.markdown("### 📉 Evolución de Peso")
    df_historial = pd.DataFrame({
        "Semana": ["S1", "S2", "S3", "S4 (Actual)"],
        "Peso (kg)": [peso + 1.5, peso + 0.8, peso + 0.3, peso]
    }).set_index("Semana")
    st.line_chart(df_historial, color=["#2ecc71"])
    
    st.markdown("### 💪 Comparativa Muscular (Brazos vs Pecho)")
    df_medidas = pd.DataFrame({
        "Zonas": ["Bíceps", "Pecho", "Cuádriceps"],
        "cm": [medidas.get('brazo', 0), medidas.get('pecho', 0), medidas.get('pierna', 0)]
    }).set_index("Zonas")
    st.bar_chart(df_medidas, color=["#3498db"])