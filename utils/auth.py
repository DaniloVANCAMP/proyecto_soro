import streamlit as st
import hashlib
import json
import os

DATA_FILE = "users.json"

def cargar_usuarios():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_usuarios(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def registrar_usuario(email, password):
    users = cargar_usuarios()
    if email in users:
        return False, "Ya existe una cuenta con ese correo."
    users[email] = {"password": hash_password(password), "proyectos": {}}
    guardar_usuarios(users)
    return True, "Usuario registrado con éxito."

def autenticar(email, password):
    users = cargar_usuarios()
    if email in users and users[email]["password"] == hash_password(password):
        return True
    return False
