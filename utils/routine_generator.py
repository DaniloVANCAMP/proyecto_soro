import random

# --- DICCIONARIOS DE TRADUCCIÓN ---
EQUIPMENT_SPANISH = {
    "barbell": "Barra estándar",
    "dumbbell": "Mancuerna",
    "body weight": "Peso corporal",
    "cable": "Polea / Cable",
    "machine": "Máquina guiada",
    "ez barbell": "Barra EZ",
    "kettlebell": "Pesa rusa (Kettlebell)",
    "band": "Banda de resistencia",
    "smith machine": "Máquina Smith",
    "leverage machine": "Máquina de palanca",
    "assisted": "Máquina asistida",
    "medicine ball": "Balón medicinal",
    "stability ball": "Pelota de estabilidad",
    "weighted": "Con peso añadido",
    "bosu ball": "Bosu",
    "roller": "Rodillo rodante",
    "rope": "Cuerda"
}

CATEGORY_SPANISH = {
    "back": "Espalda",
    "chest": "Pecho",
    "shoulders": "Hombros",
    "upper arms": "Brazos (Bíceps / Tríceps)",
    "lower arms": "Antebrazos",
    "upper legs": "Piernas (Cuádriceps / Isquios)",
    "lower legs": "Pantorrillas",
    "waist": "Abdomen / Core",
    "cardio": "Cardio"
}

# --- DICCIONARIO MÉDICO (IA) ---
# Mapea las lesiones en español con los músculos/zonas en inglés de la API que se deben evitar.
RESTRICCIONES_MEDICAS = {
    "dolor lumbar": ["spine", "lower back"],
    "lesión de rodilla": ["knees", "quads", "calves"],
    "lesión de hombro": ["shoulders", "delts"],
    "muñecas sensibles": ["forearms", "wrists", "lower arms"]
}

# --- MATRIZ CIENTÍFICA DE PRESCRIPCIÓN DE CARGA (NSCA / ACSM) ---
MATRIZ_NSCA = {
    "Fuerza Maxima": {
        "Principiante": {"series": "3", "reps": "5", "rpe": "7 - 8", "descanso_base": 120},
        "Intermedio":   {"series": "4", "reps": "3 - 5", "rpe": "8 - 9", "descanso_base": 180},
        "Avanzado":     {"series": "5", "reps": "1 - 3", "rpe": "9 - 10", "descanso_base": 240}
    },
    "Hipertrofia": {
        "Principiante": {"series": "3", "reps": "10 - 12", "rpe": "7", "descanso_base": 60},
        "Intermedio":   {"series": "3 - 4", "reps": "8 - 12", "rpe": "8", "descanso_base": 90},
        "Avanzado":     {"series": "4 - 5", "reps": "6 - 10", "rpe": "8 - 9", "descanso_base": 90}
    },
    "Definición / Resistencia": {
        "Principiante": {"series": "2 - 3", "reps": "12 - 15", "rpe": "6 - 7", "descanso_base": 45},
        "Intermedio":   {"series": "3", "reps": "15 - 20", "rpe": "7 - 8", "descanso_base": 45},
        "Avanzado":     {"series": "3 - 4", "reps": "15 - 25", "rpe": "8", "descanso_base": 30}
    }
}

# --- FUNCIONES DE TRADUCCIÓN Y FORMATO ---
def traducir_equipo(eq):
    return EQUIPMENT_SPANISH.get(str(eq).lower(), str(eq).title())

def obtener_nombre_equipo_es(eq_raw):
    return f"{str(eq_raw).title()} ({traducir_equipo(eq_raw)})"

def obtener_dosificacion_nsca(objetivo, nivel):
    """Calcula las series, repeticiones, RPE y descanso base según el estándar NSCA."""
    obj_dict = MATRIZ_NSCA.get(objetivo, MATRIZ_NSCA["Hipertrofia"])
    return obj_dict.get(nivel, obj_dict["Intermedio"])

# --- LÓGICA DE FILTRADO (A PRUEBA DE BALAS) ---
def obtener_ejercicios_candidatos(exercises, categoria_en, equipo_disponible, limitaciones=None, ids_excluidos=None):
    """
    Retorna la lista de ejercicios candidatos compatibles que NO están en ids_excluidos,
    filtrando por el equipo que tiene el usuario y protegiendo sus lesiones.
    """
    if ids_excluidos is None:
        ids_excluidos = set()
    else:
        ids_excluidos = set(ids_excluidos)
        
    if limitaciones is None:
        limitaciones = []

    # 1. Limpiar lista de equipo
    equipo_clean = [str(eq).lower().strip() for eq in equipo_disponible] if equipo_disponible else []
    
    # 2. Convertir limitaciones a una lista segura y buscar qué partes del cuerpo evitar
    if isinstance(limitaciones, str):
        limitaciones_clean = [l.strip().lower() for l in limitaciones.split(',') if l.strip()]
    else:
        limitaciones_clean = [str(l).strip().lower() for l in limitaciones]

    zonas_a_evitar = set()
    for lim in limitaciones_clean:
        if lim in RESTRICCIONES_MEDICAS:
            zonas_a_evitar.update(RESTRICCIONES_MEDICAS[lim])

    candidatos = []
    for ex in exercises:
        ex_id = ex.get('id')
        if ex_id in ids_excluidos:
            continue

        # Compatibilidad ampliada: busca la categoría
        cat_ex = ex.get('category') or ex.get('bodyPart') or ex.get('body_part') or ""
        if cat_ex.lower() != categoria_en.lower():
            continue

        # Verificar equipo (siempre permitiendo peso corporal por defecto)
        eq_ex = str(ex.get('equipment', '')).lower().strip()
        if equipo_clean: # Si el usuario registró equipo, filtramos estrictamente
            if eq_ex not in equipo_clean and eq_ex not in ['body weight', 'bodyweight']:
                continue
        else: # Si no registró NADA, asumimos que solo puede hacer peso corporal
            if eq_ex not in ['body weight', 'bodyweight']:
                continue

        # Verificar lesiones (Si el ejercicio ataca una zona lesionada, lo descartamos)
        target_ex = str(ex.get('target', '')).lower()
        body_part_ex = str(ex.get('bodyPart', '')).lower()
        
        ejercicio_peligroso = any(zona in target_ex or zona in body_part_ex for zona in zonas_a_evitar)
        if ejercicio_peligroso:
            continue

        candidatos.append(ex)

    return candidatos

# --- GENERACIÓN Y SUSTITUCIÓN DE EJERCICIOS ---
def cambiar_ejercicio_individual(exercises, ejercicio_actual, todos_ejercicios_rutina, equipo_disponible, limitaciones=None):
    """
    Cambia un ejercicio individual por otro aleatorio que NO esté presente en la rutina activa.
    """
    ids_usados = {ex['id'] for ex in todos_ejercicios_rutina if 'id' in ex}
    categoria_en = ejercicio_actual.get('category') or ejercicio_actual.get('bodyPart') or ejercicio_actual.get('body_part', '')

    candidatos = obtener_ejercicios_candidatos(
        exercises=exercises,
        categoria_en=categoria_en,
        equipo_disponible=equipo_disponible,
        limitaciones=limitaciones,
        ids_excluidos=ids_usados
    )

    if candidatos:
        return random.choice(candidatos)
    return None

def generar_rutina_personalizada(exercises, equipo_disponible, limitaciones, datos_entorno, ejercicios_por_grupo, grupos_seleccionados, objetivo="Hipertrofia", nivel="Intermedio"):
    """
    Genera una rutina de entrenamiento excluyendo duplicados entre todos los grupos,
    protegiendo lesiones y aplicando la dosificación científica NSCA según objetivo y nivel.
    """
    rutina = {}
    notas_entorno = []
    ids_usados = set()

    # --- DOSIFICACIÓN CIENTÍFICA NSCA ---
    dosis = obtener_dosificacion_nsca(objetivo, nivel)
    descanso_seg = dosis.get("descanso_base", 60)

    # --- AJUSTES DE PARÁMETROS POR ENTORNO ---
    if datos_entorno:
        temp = datos_entorno.get('temperatura_c', 20)
        altitud = datos_entorno.get('altitud_m', 0)
        
        if temp > 28:
            descanso_seg += 15
            notas_entorno.append("🌡️ Alta temperatura detectada: Se incrementaron 15s de descanso para facilitar la recuperación térmica.")
        if altitud > 2000:
            descanso_seg += 15
            notas_entorno.append("⛰️ Alta altitud detectada: Se incrementaron 15s de descanso para compensar la menor presión de oxígeno.")

    # --- ENSAMBLAJE DE LA RUTINA ---
    for cat_en in grupos_seleccionados:
        cat_es = CATEGORY_SPANISH.get(cat_en, cat_en.title())
        
        # Intento 1: Buscar excluyendo lo que ya usamos
        candidatos = obtener_ejercicios_candidatos(
            exercises=exercises,
            categoria_en=cat_en,
            equipo_disponible=equipo_disponible,
            limitaciones=limitaciones,
            ids_excluidos=ids_usados
        )

        # Intento 2: Si no hay opciones por falta de equipo, relajamos la exclusión de IDs para no dejar el grupo vacío
        if not candidatos:
            candidatos = obtener_ejercicios_candidatos(
                exercises=exercises,
                categoria_en=cat_en,
                equipo_disponible=equipo_disponible,
                limitaciones=limitaciones,
                ids_excluidos=set()
            )

        if candidatos:
            num_a_tomar = min(len(candidatos), ejercicios_por_grupo)
            seleccionados = random.sample(candidatos, num_a_tomar)
            rutina[cat_es] = seleccionados
            for s in seleccionados:
                ids_usados.add(s['id'])
        else:
            rutina[cat_es] = []

    return {
        "rutina": rutina,
        "descanso_seg": descanso_seg,
        "dosificacion": dosis,  # Contiene series, reps y RPE calculados por la NSCA
        "notas_entorno": notas_entorno
    }, None