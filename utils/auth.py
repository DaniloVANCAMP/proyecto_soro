import json
import os

# utils/auth.py
USUARIOS_AUTORIZADOS = [
    "naidaluzmontero@gmail.com",
    "daniloanhelo20172@gmail.com"
]

ARCHIVO_USUARIOS = "usuarios.json"

# --- CARGAR USUARIOS ---
def cargar_usuarios():
    if os.path.exists(ARCHIVO_USUARIOS):
        with open(ARCHIVO_USUARIOS, "r") as f:
            return json.load(f)
    return {}

# --- GUARDAR USUARIOS ---
def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w") as f:
        json.dump(usuarios, f, indent=4)

# --- REGISTRAR USUARIO ---
def registrar_usuario(email, password):
    usuarios = cargar_usuarios()
    if email in usuarios:
        return False, "⚠️ El correo ya está registrado."
    usuarios[email] = password
    guardar_usuarios(usuarios)
    return True, "✅ Usuario registrado correctamente."

# --- AUTENTICAR USUARIO ---
def autenticar(email, password):
    usuarios = cargar_usuarios()
    return usuarios.get(email) == password
