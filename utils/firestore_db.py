import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Evitar que se inicialice múltiples veces y de error
def init_firestore():
    if not firebase_admin._apps:
        # Cargar credenciales desde los Secrets de Streamlit
        cred_dict = dict(st.secrets["firestore"])
        
        # Corregir los saltos de línea de la clave privada (común error de copiado)
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()
    

# Guardar o actualizar usuario
def guardar_usuario_db(user_data):
    db = init_firestore()
    # Usamos el email como ID único del documento
    doc_ref = db.collection("usuarios").document(user_data["email"])
    doc_ref.set(user_data, merge=True)

# Recuperar usuario por email
def obtener_usuario_db(email):
    db = init_firestore()
    doc_ref = db.collection("usuarios").document(email)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None
