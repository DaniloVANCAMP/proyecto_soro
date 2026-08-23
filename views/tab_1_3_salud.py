import streamlit as st

def mostrar(perfil):
    st.markdown("### 🏥 Registro Clínico Activo")
    limitaciones = perfil.get('limitaciones', [])
    if limitaciones:
        for lim in limitaciones:
            st.error(f"🔴 **Condición Reportada:** {lim}")
        st.caption("Nota: El generador de IA filtrará los ejercicios basándose en esta lista.")
    else:
        st.success("✅ Estás sano. Sin condiciones médicas reportadas.")
    
    st.divider()
    st.markdown("#### 📎 Adjuntar Documentación")
    with st.form("form_certificados"):
        st.text_area("Describir nueva condición o lesión reciente:")
        st.file_uploader("Sube tu certificado o imagen (PDF/IMG)", type=["pdf", "png", "jpg"])
        if st.form_submit_button("Subir al Historial Médico", use_container_width=True):
            st.info("Archivo cargado con éxito. Pendiente revisión.")