import numpy as np

def f_cop(x):
    """Formato visual de moneda ($ 1.000.000)"""
    return f"$ {int(x):,}".replace(",", ".")

def calcular_metabolismo(peso, estatura, edad, sexo, nivel_actividad="moderado", objetivo="Mantenimiento"):
    """
    Calcula Tasa Metabólica Basal (BMR) con Mifflin-St Jeor
    y distribuye Macronutrientes (Proteínas, Carbohidratos, Grasas).
    """
    # 1. BMR (Mifflin-St Jeor)
    s = 5 if str(sexo).lower() == "hombre" else -161
    bmr = (10 * peso) + (6.25 * estatura) - (5 * edad) + s
    
    # 2. Factores de Actividad
    factores = {
        "sedentario": 1.2,      # Poco o ningún ejercicio
        "ligero": 1.375,        # 1-3 días a la semana
        "moderado": 1.55,       # 3-5 días a la semana
        "fuerte": 1.725,        # 6-7 días a la semana
        "atleta": 1.9           # Entrenamientos dobles / trabajo físico
    }
    key_act = str(nivel_actividad).lower()
    factor = factores.get(key_act, 1.55)
    tdee = bmr * factor
    
    # 3. Ajuste por Objetivo
    obj_str = str(objetivo)
    if "Perder" in obj_str or "Déficit" in obj_str:
        target_cal = tdee - 500  # Déficit de 500 kcal
    elif "Ganar" in obj_str or "Superávit" in obj_str:
        target_cal = tdee + 300  # Superávit de 300 kcal
    else:
        target_cal = tdee        # Mantenimiento
        
    # 4. Distribución de Macros
    factor_prot = 2.2 if ("Ganar" in obj_str or "Superávit" in obj_str) else 2.0
    proteina_g = peso * factor_prot
    proteina_kcal = proteina_g * 4
    
    grasa_g = peso * 0.9
    grasa_kcal = grasa_g * 9
    
    carbos_kcal = max(0, target_cal - (proteina_kcal + grasa_kcal))
    carbos_g = carbos_kcal / 4
    
    return {
        "bmr": int(bmr),
        "tdee": int(tdee),
        "target_cal": int(target_cal),
        "macros": {
            "proteinas_g": int(proteina_g),
            "carbos_g": int(carbos_g),
            "grasas_g": int(grasa_g)
        }
    }

def filtrar_ejercicios_por_equipo(exercises, equipos_disponibles):
    """
    Filtra los ejercicios del dataset según las máquinas/equipos que tiene el usuario.
    """
    if not equipos_disponibles:
        return exercises
        
    equipos_clean = [str(eq).lower().strip() for eq in equipos_disponibles]
    
    filtrados = []
    for ex in exercises:
        eq = str(ex.get('equipment', '')).lower().strip()
        if eq in equipos_clean or eq in ['body weight', 'bodyweight']:
            filtrados.append(ex)
            
    return filtrados