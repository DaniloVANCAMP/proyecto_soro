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

# --- FUNCIONES DE TRADUCCIÓN Y FORMATO ---
def traducir_equipo(eq):
    return EQUIPMENT_SPANISH.get(str(eq).lower(), str(eq).title())

def obtener_nombre_equipo_es(eq_raw):
    return f"{str(eq_raw).title()} ({traducir_equipo(eq_raw)})"

# --- LÓGICA DE FILTRADO (A PRUEBA DE BALAS) ---
def obtener_ejercicios_candidatos(exercises, categoria_en, equipo_disponible, limitaciones="", ids_excluidos=None):
    """
    Retorna la lista de ejercicios candidatos compatibles que NO están en ids_excluidos.
    """
    if ids_excluidos is None:
        ids_excluidos = set()
    else:
        ids_excluidos = set(ids_excluidos)

    equipo_clean = [str(eq).lower().strip() for eq in equipo_disponible]
    limitaciones_clean = [l.strip().lower() for l in limitaciones.split(',') if l.strip()]

    candidatos = []
    for ex in exercises:
        ex_id = ex.get('id')
        if ex_id in ids_excluidos:
            continue

        # Compatibilidad ampliada: busca la categoría en distintos formatos posibles de la API
        cat_ex = ex.get('category') or ex.get('bodyPart') or ex.get('body_part') or ""
        if cat_ex.lower() != categoria_en.lower():
            continue

        # Verificar equipo (siempre permitiendo peso corporal como fallback)
        eq_ex = str(ex.get('equipment', '')).lower().strip()
        if eq_ex not in equipo_clean and eq_ex not in ['body weight', 'bodyweight']:
            continue

        # Verificar limitaciones/lesiones
        name_ex = str(ex.get('name', '')).lower()
        target_ex = str(ex.get('target', '')).lower()
        
        limitado = False
        for lim in limitaciones_clean:
            if lim in name_ex or lim in target_ex:
                limitado = True
                break
        if limitado:
            continue

        candidatos.append(ex)

    return candidatos

# --- GENERACIÓN Y SUSTITUCIÓN DE EJERCICIOS ---
def cambiar_ejercicio_individual(exercises, ejercicio_actual, todos_ejercicios_rutina, equipo_disponible, limitaciones=""):
    """
    Cambia un ejercicio individual por otro aleatorio que NO esté presente en la rutina activa.
    """
    ids_usados = {ex['id'] for ex in todos_ejercicios_rutina if 'id' in ex}
    # Aseguramos extraer la categoría correctamente
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

def generar_rutina_personalizada(exercises, equipo_disponible, limitaciones, datos_entorno, ejercicios_por_grupo, grupos_seleccionados):
    """
    Genera una rutina de entrenamiento excluyendo duplicados entre todos los grupos.
    """
    rutina = {}
    notas_entorno = []
    ids_usados = set()

    # --- AJUSTES DE PARÁMETROS POR ENTORNO (Features para ML) ---
    descanso_seg = 60
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

        # Intento 2: Si no hay opciones, relajamos la exclusión de IDs para no dejar el grupo muscular vacío
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
        "notas_entorno": notas_entorno
    }, None