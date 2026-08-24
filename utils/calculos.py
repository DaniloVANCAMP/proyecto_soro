import math
import numpy as np

# =========================================================================
# 1. UTILIDADES GENERALES
# =========================================================================
def f_cop(x):
    """Formato visual de moneda ($ 1.000.000)"""
    return f"$ {int(x):,}".replace(",", ".")

# =========================================================================
# 2. MÓDULO: NUTRICIÓN Y METABOLISMO
# =========================================================================
def calcular_metabolismo(peso, estatura, edad, sexo, nivel_actividad="moderado", objetivo="Mantenimiento"):
    """
    Calcula Tasa Metabólica Basal (BMR) con Mifflin-St Jeor
    y distribuye Macronutrientes (Proteínas, Carbohidratos, Grasas).
    """
    s = 5 if str(sexo).lower() == "hombre" else -161
    bmr = (10 * peso) + (6.25 * estatura) - (5 * edad) + s
    
    factores = {
        "sedentario": 1.2, "ligero": 1.375, "moderado": 1.55,
        "fuerte": 1.725, "atleta": 1.9 
    }
    key_act = str(nivel_actividad).lower()
    factor = factores.get(key_act, 1.55)
    tdee = bmr * factor
    
    obj_str = str(objetivo)
    if "Perder" in obj_str or "Déficit" in obj_str: target_cal = tdee - 500 
    elif "Ganar" in obj_str or "Superávit" in obj_str: target_cal = tdee + 300 
    else: target_cal = tdee 
        
    factor_prot = 2.2 if ("Ganar" in obj_str or "Superávit" in obj_str) else 2.0
    proteina_g = peso * factor_prot
    proteina_kcal = proteina_g * 4
    
    grasa_g = peso * 0.9
    grasa_kcal = grasa_g * 9
    
    carbos_kcal = max(0, target_cal - (proteina_kcal + grasa_kcal))
    carbos_g = carbos_kcal / 4
    
    return {
        "bmr": int(bmr), "tdee": int(tdee), "target_cal": int(target_cal),
        "macros": { "proteinas_g": int(proteina_g), "carbos_g": int(carbos_g), "grasas_g": int(grasa_g) }
    }

# =========================================================================
# 3. MÓDULO: BIOMETRÍA Y COMPOSICIÓN CORPORAL
# =========================================================================
def calcular_imc(peso_kg, altura_cm):
    """Calcula el Índice de Masa Corporal."""
    if not peso_kg or not altura_cm or float(altura_cm) <= 0: return 0.0
    return round(float(peso_kg) / ((float(altura_cm) / 100) ** 2), 1)

def clasificar_imc(imc):
    """Devuelve el estado clínico según el IMC."""
    if imc == 0: return "Sin datos", "⚪"
    if imc < 18.5: return "Bajo peso", "🔵"
    elif 18.5 <= imc < 24.9: return "Peso normal", "🟢"
    elif 25 <= imc < 29.9: return "Sobrepeso", "🟡"
    else: return "Obesidad", "🔴"

def calcular_grasa_marina(genero, altura, cuello, cintura, cadera=0):
    """Calcula el % de grasa usando la fórmula logarítmica de la Marina de EE. UU."""
    if altura <= 0 or cuello <= 0 or cintura <= 0: return 0.0
    try:
        if genero == "Masculino":
            if cintura <= cuello: return 0.0
            porcentaje = 495.0 / (1.0324 - 0.19077 * math.log10(cintura - cuello) + 0.15456 * math.log10(altura)) - 450.0
        else:
            if cintura + cadera <= cuello: return 0.0
            porcentaje = 495.0 / (1.29579 - 0.35004 * math.log10(cintura + cadera - cuello) + 0.22100 * math.log10(altura)) - 450.0
        
        return max(0.0, min(porcentaje, 60.0)) 
    except ValueError:
        return 0.0

def analizar_composicion_corporal(peso, porcentaje_grasa):
    """Divide el peso total en masa grasa y masa magra (libre de grasa)."""
    kg_grasa = peso * (porcentaje_grasa / 100)
    kg_magra = peso - kg_grasa
    return round(kg_grasa, 1), round(kg_magra, 1)

