import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firestore una sola vez
def init_firestore():
    if not firebase_admin._apps:
        cred = credentials.Certificate(st.secrets["firestore"])
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Guardar sesión del usuario
def guardar_sesion(email, data):
    db = init_firestore()
    db.collection("sesiones").document(email).set(data)

# Cargar sesión
def cargar_sesion(email):
    db = init_firestore()
    doc = db.collection("sesiones").document(email).get()
    return doc.to_dict() if doc.exists else None

# Eliminar sesión
def eliminar_sesion(email):
    db = init_firestore()
    db.collection("sesiones").document(email).delete()
