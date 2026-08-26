import json
from PIL import Image
import google.generativeai as genai
import streamlit as st


def analizar_alimento_ia(
    texto_usuario="", archivo_imagen=None, archivo_audio=None
):
    """Procesa texto, imagen o audio usando Gemini y retorna un diccionario con los macros calculados."""
    if "GEMINI_API_KEY" not in st.secrets:
        return (
            None,
            "La clave GEMINI_API_KEY no está configurada en st.secrets.",
        )

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    prompt_sistema = """
    Eres un nutricionista experto en cálculo preciso de macros y matemática de recetas.
    Analiza la descripción en texto, la imagen de la tabla nutricional o la nota de voz del usuario.
    
    REGLAS DE CÁLCULO DE RECETAS Y PORCIONES:
    1. Si el usuario describe una preparación completa con sus ingredientes totales y luego indica la porción que se comió, debes calcular la regla de tres matemática para extraer ÚNICAMENTE las calorías y macronutrientes de la porción efectivamente consumida.
    2. Considera métodos de cocción (frijoles cocidos, pechuga frita con aceite, etc.).
    3. Si el usuario no especifica la porción consumida, asume que consumió la preparación descrita.

    Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta, sin código markdown extra ni texto explicativo:
    {
        "nombre": "Nombre claro del plato o alimento consumido",
        "porcion": "Descripción de la porción consumida (Ej: 100g de 500g preparados)",
        "calorias": 0,
        "proteina": 0.0,
        "carbohidratos": 0.0,
        "grasas": 0.0
    }
    """

    contenido = [prompt_sistema]
    try:
        if archivo_imagen:
            img = Image.open(archivo_imagen)
            contenido.append(img)
        elif archivo_audio:
            audio_bytes = archivo_audio.read()
            mime_type = archivo_audio.type or "audio/wav"
            contenido.append({"mime_type": mime_type, "data": audio_bytes})
        else:
            contenido.append(texto_usuario)
    except Exception as err_prep:
        return None, f"Error al procesar el archivo de entrada: {err_prep}"

    modelos_candidatos = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-3.6-flash",
        "gemini-2.5-flash",
    ]

    ultimo_error = None

    for nombre_modelo in modelos_candidatos:
        try:
            modelo = genai.GenerativeModel(
                nombre_modelo,
                generation_config={"response_mime_type": "application/json"},
            )
            respuesta = modelo.generate_content(contenido)
            texto_limpio = (
                respuesta.text.replace("```json", "").replace("```", "").strip()
            )
            return json.loads(texto_limpio), None
        except Exception as e:
            ultimo_error = str(e)
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            else:
                break

    return None, ultimo_error