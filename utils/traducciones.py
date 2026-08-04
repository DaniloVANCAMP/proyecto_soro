# ==========================================
# DICCIONARIOS DE TRADUCCIÓN COMPLETOS
# ==========================================

DICCIONARIO_ZONAS = {
    "back": "Espalda",
    "cardio": "Cardio / Resistencia",
    "chest": "Pecho / Pectorales",
    "lower arms": "Antebrazos",
    "lower legs": "Pantorrillas",
    "neck": "Cuello",
    "shoulders": "Hombros",
    "upper arms": "Brazos",
    "upper legs": "Piernas / Glúteos",
    "waist": "Cintura / Abdomen"
}

DICCIONARIO_EQUIPO = {
    "assisted": "Asistido / Máquina de asistencia",
    "band": "Banda de resistencia",
    "barbell": "Barra recta",
    "body weight": "Peso corporal (Calistenia)",
    "bosu ball": "Bosu",
    "cable": "Polea / Cable",
    "dumbbell": "Mancuerna",
    "elliptical machine": "Elíptica",
    "ez barbell": "Barra Z / EZ",
    "hammer": "Máquina Hammer",
    "kettlebell": "Pesa Rusa (Kettlebell)",
    "leverage machine": "Máquina de palanca",
    "medicine ball": "Balón Medicinal",
    "olympic barbell": "Barra Olímpica",
    "resistance band": "Banda de resistencia",
    "roller": "Rodillo (Foam Roller)",
    "rope": "Cuerda / Soga",
    "skierg machine": "SkiErg",
    "sled machine": "Trineo de empuje",
    "smith machine": "Máquina Smith / Multipower",
    "stability ball": "Fitball",
    "stationary bike": "Bicicleta estática",
    "stepmill machine": "Escaladora",
    "tire": "Neumático",
    "trap bar": "Barra Hexagonal",
    "upper body ergometer": "Ergómetro superior",
    "weighted": "Lastrado",
    "wheel roller": "Rueda Abdominal"
}

DICCIONARIO_MUSCULOS = {
    # --- GLÚTEOS Y CADERA ---
    "glutes": "Glúteos",
    "gluteus": "Glúteos",
    "gluteus maximus": "Glúteo Mayor",
    "gluteus medius": "Glúteo Medio",
    "gluteus minimus": "Glúteo Menor",
    "hip flexors": "Flexores de Cadera",
    "abductors": "Abductores",
    "adductors": "Aductores",

    # --- PIERNAS ---
    "quads": "Cuádriceps",
    "quadriceps": "Cuádriceps",
    "hamstrings": "Isquiotibiales / Femorales",
    "calves": "Pantorrillas / Gemelos",
    "gastrocnemius": "Gemelos",
    "soleus": "Sóleos",

    # --- CORE Y ABDOMEN ---
    "abs": "Abdominales",
    "obliques": "Oblicuos",
    "rectus abdominis": "Recto Abdominal",
    "serratus anterior": "Serrato",

    # --- ESPALDA ---
    "lats": "Dorsales",
    "latissimus dorsi": "Dorsal Ancho",
    "upper back": "Espalda Alta",
    "traps": "Trapecios",
    "rhomboids": "Romboides",
    "spine": "Erectores Espinales",
    "lower back": "Espalda Baja",

    # --- PECHO Y HOMBROS ---
    "pectorals": "Pectorales",
    "chest": "Pecho",
    "delts": "Deltoides / Hombros",
    "deltoids": "Deltoides",
    "shoulders": "Hombros",

    # --- BRAZOS Y CUELLO ---
    "biceps": "Bíceps",
    "triceps": "Tríceps",
    "forearms": "Antebrazos",
    "neck": "Cuello",
    "cardiovascular system": "Sistema Cardiovascular"
}

# ==========================================
# FUNCIONES DE FORMATEO LIGERA Y SEGURA
# ==========================================

def fmt_zona(val: str) -> str:
    if not val or val == "Todas": 
        return "Todas las zonas"
    key = str(val).lower().strip()
    traduccion = DICCIONARIO_ZONAS.get(key)
    if traduccion and traduccion.lower() != key:
        return f"{val.title()} ({traduccion})"
    return val.title()

def fmt_equipo(val: str) -> str:
    if not val or val == "Todos": 
        return "Todos los equipos"
    key = str(val).lower().strip()
    traduccion = DICCIONARIO_EQUIPO.get(key)
    if traduccion and traduccion.lower() != key:
        return f"{val.title()} ({traduccion})"
    return val.title()

def fmt_musculo(val: str) -> str:
    if not val or val == "Todos": 
        return "Todos los músculos"
    key = str(val).lower().strip()
    traduccion = DICCIONARIO_MUSCULOS.get(key)
    if traduccion and traduccion.lower() != key:
        return f"{val.title()} ({traduccion})"
    return val.title()