import streamlit as st
import random

def mostrar(perfil):
    st.markdown("### 🧠 Tu Dosis Diaria de Sabiduría")
    tips = [
        "🔥 **Nutrición:** Un déficit calórico excesivo quema músculo. Mantén un déficit moderado (300-500 kcal).",
        "🏋️ **Entrenamiento:** La sobrecarga progresiva es la regla de oro.",
        "🛌 **Recuperación:** Los músculos crecen durmiendo, no entrenando.",
        "💧 **Hidratación:** El músculo es 70% agua."
    ]
    st.info(random.choice(tips))
    
    st.markdown("---")
    st.markdown("#### 🤖 Pregúntale a tu Coach")
    st.text_input("¿Tienes dudas sobre nutrición o técnica? Pregúntale a la IA aquí:")
    st.button("Consultar IA ✨", disabled=True)