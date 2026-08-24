import hashlib
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

# ==========================================
# INICIALIZACIÓN DEFINITIVA Y SEGURA (SECRETS)
# ==========================================
if not firebase_admin._apps:
    try:
        # Streamlit lee automáticamente de la nube o de .streamlit/secrets.toml
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise ValueError(f"⚠️ No se encontraron las credenciales en Streamlit Secrets. Por favor configura los secretos. Detalle: {e}")

db = firestore.client()

def hash_password(password):
    """Mantiene el mismo cifrado SHA-256 original."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Función para compatibilidad con app.py"""
    pass

# ==========================================
# 1. AUTENTICACIÓN Y USUARIOS
# ==========================================
def crear_usuario(username, password, correo=""):
    try:
        users_ref = db.collection("usuarios")
        
        # Verificar si existe por username o correo
        if users_ref.where("username", "==", username).get():
            return False
        if correo and users_ref.where("correo", "==", correo).get():
            return False
        
        nuevo_doc = users_ref.document()
        nuevo_doc.set({
            "username": username,
            "password": hash_password(password),
            "correo": correo
        })
        return True
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        return False

def verificar_usuario(identificador, password):
    try:
        pwd_hashed = hash_password(password)
        users_ref = db.collection("usuarios")
        
        # Buscar por username primero
        query = users_ref.where("username", "==", identificador).where("password", "==", pwd_hashed).get()
        if not query:
            # Si no coincide, buscar por correo
            query = users_ref.where("correo", "==", identificador).where("password", "==", pwd_hashed).get()
        
        if query:
            doc = query[0]
            return doc.id, doc.to_dict().get("username", identificador)
        return None, None
    except Exception as e:
        print(f"Error en verificar_usuario: {e}")
        return None, None

# ==========================================
# 2. PERFILES DE USUARIO
# ==========================================
def guardar_perfil(user_id, datos):
    if not user_id: return
    try:
        doc_ref = db.collection("perfiles").document(str(user_id))
        doc_ref.set(datos, merge=True)
        st.cache_data.clear()  # <-- Limpia el caché para ver los cambios al instante
    except Exception as e:
        print(f"Error al guardar perfil: {e}")

@st.cache_data(ttl=300)  # <-- Memoriza el perfil por 5 minutos
def obtener_perfil(user_id):
    if not user_id: return None
    try:
        doc_ref = db.collection("perfiles").document(str(user_id))
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"Error al obtener perfil: {e}")
        return None

# ==========================================
# 3. PLANIFICACIÓN Y RUTINAS
# ==========================================
def guardar_plan_dia(user_id, fecha, rutina):
    if not user_id: return
    try:
        doc_id = f"{user_id}_{fecha}"
        doc_ref = db.collection("planificacion").document(doc_id)
        doc_ref.set({
            "user_id": user_id,
            "fecha": fecha,
            "rutina": rutina
        }, merge=True)
        st.cache_data.clear()  # <-- Limpia el caché al guardar nueva rutina
    except Exception as e:
        print(f"Error al guardar plan: {e}")

@st.cache_data(ttl=60)  # <-- Memoriza la rutina por 1 minuto
def obtener_plan_dia(user_id, fecha):
    if not user_id: return []
    try:
        doc_id = f"{user_id}_{fecha}"
        doc_ref = db.collection("planificacion").document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("rutina", [])
        return []
    except Exception as e:
        print(f"Error al obtener plan: {e}")
        return []

# ==========================================
# 4. NUTRICIÓN Y BITÁCORA (NUBE)
# ==========================================
def guardar_nutricion(user_id, fecha_str, datos):
    if not user_id: return
    try:
        doc_id = f"{user_id}_{fecha_str}"
        doc_ref = db.collection("nutricion").document(doc_id)
        doc_ref.set(datos, merge=True)
        st.cache_data.clear()
    except Exception as e:
        print(f"Error al guardar nutricion: {e}")

@st.cache_data(ttl=60)
def obtener_nutricion(user_id, fecha_str):
    if not user_id: return {}
    try:
        doc_id = f"{user_id}_{fecha_str}"
        doc_ref = db.collection("nutricion").document(doc_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        print(f"Error al obtener nutricion: {e}")
        return {}

def guardar_en_bitacora(lista_microdatos):
    try:
        for item in lista_microdatos:
            doc_id = item.get("id_evento")
            if doc_id:
                db.collection("bitacora").document(str(doc_id)).set(item)
        st.cache_data.clear()  # <-- Invalida la caché para ver el entrenamiento de inmediato
    except Exception as e:
        print(f"Error al guardar en bitacora: {e}")

@st.cache_data(ttl=60)
def obtener_bitacora(user_id):
    """Extrae todo el historial de microdatos de un usuario desde Firebase."""
    if not user_id: return []
    try:
        docs = db.collection("bitacora").where("user_id", "==", str(user_id)).get()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        print(f"Error al obtener bitacora: {e}")
        return []

# ==========================================
# 5. ALIMENTOS COMUNITARIOS (CATÁLOGO GRATIS)
# ==========================================
def guardar_alimento_personalizado(user_id, datos_alimento, es_publico=True):
    try:
        doc_ref = db.collection("alimentos_comunidad").document()
        datos_alimento["creado_por"] = str(user_id)
        datos_alimento["es_publico"] = es_publico
        doc_ref.set(datos_alimento)
        st.cache_data.clear() # Invalida el caché para que aparezca de una
        return True
    except Exception as e:
        print(f"Error al guardar alimento: {e}")
        return False

@st.cache_data(ttl=300)
def obtener_alimentos_comunitarios(user_id):
    alimentos_dict = {}
    try:
        users_ref = db.collection("alimentos_comunidad")
        # Trae los alimentos públicos O los privados creados por este usuario
        docs_publicos = users_ref.where("es_publico", "==", True).get()
        docs_privados = users_ref.where("creado_por", "==", str(user_id)).where("es_publico", "==", False).get()
        
        for doc in docs_publicos + docs_privados:
            d = doc.to_dict()
            nombre_key = f"{d['nombre']} ({d['porcion']})"
            alimentos_dict[nombre_key] = {
                "cal": d.get("calorias", 0),
                "carbos": d.get("carbohidratos", 0.0),
                "proteina": d.get("proteina", 0.0),
                "grasas": d.get("grasas", 0.0)
            }
        return alimentos_dict
    except Exception as e:
        print(f"Error al obtener alimentos comunitarios: {e}")
        return {}