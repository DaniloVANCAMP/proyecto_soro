import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json

# RUTA a tu archivo de credenciales descargado desde Google Cloud Console
GOOGLE_CREDENTIALS = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def conectar_gsheets(sheet_name):
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS, scopes=SCOPES)
    cliente = gspread.authorize(creds)
    try:
        sh = cliente.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = cliente.create(sheet_name)
    return sh

def guardar_proyectos_google(email, proyectos):
    sh = conectar_gsheets("ControlObra_Datos")
    try:
        ws = sh.worksheet(email)
    except:
        ws = sh.add_worksheet(title=email, rows="1000", cols="10")
    ws.clear()
    ws.update("A1", [["Proyecto", "Datos_JSON"]])
    for i, (nombre, datos) in enumerate(proyectos.items(), start=2):
        ws.update(f"A{i}", [[nombre, json.dumps(datos)]])

def cargar_proyectos_google(email):
    sh = conectar_gsheets("ControlObra_Datos")
    try:
        ws = sh.worksheet(email)
        data = ws.get_all_records()
        proyectos = {d["Proyecto"]: json.loads(d["Datos_JSON"]) for d in data}
        return proyectos
    except:
        return {}
