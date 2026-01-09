import pandas as pd
import numpy as np

def calcular_factor_climatico(fila, params):
    """
    Función Auxiliar:
    Determina el % de rendimiento del día (0.1 a 1.0).
    Prioridad 1: Columna 'Lluvia_mm' en el Excel.
    Prioridad 2: Valor manual configurado en la App.
    """
    # 1. Buscamos si existe la columna en el Excel y si tiene dato
    if "Lluvia_mm" in fila.index and pd.notna(fila["Lluvia_mm"]):
        mm = float(fila["Lluvia_mm"])
        if mm <= 2: return 1.00       # Seco / Rocío
        elif mm <= 10: return 0.85    # Húmedo
        elif mm <= 25: return 0.60    # Barro pesado
        else: return 0.10             # Inundado
    
    # 2. Si no hay dato en el Excel, usamos el simulador manual
    return params.get("clima_proyectado", 0.90)

def procesar_datos(params, df_bitacora):
    """
    Toma los parámetros configurados y la bitácora (Excel),
    y calcula el avance financiero y técnico día a día.
    """
    resultados = []
    
    # Aseguramos que los nombres de columnas estén limpios (sin espacios extra)
    df_bitacora.columns = [c.strip() for c in df_bitacora.columns]
    
    # Variables acumuladas
    costo_acumulado = 0
    avance_fisico_acumulado = 0
    dias_trabajados = 0
    
    # --- CÁLCULOS DÍA A DÍA ---
    for index, row in df_bitacora.iterrows():
        dias_trabajados += 1
        
        # 1. Recurso Humano y Maquinaria (Leemos del Excel)
        # Usamos .get(0) por si la celda está vacía, que asuma 0
        n_ayud = row.get("Ayud", 0)
        n_mae = row.get("Mae", 0)
        n_retro = row.get("Retro", 0)
        n_roto = row.get("Roto", 0) if "Roto" in row else 0
        
        # 2. Costos del Día (Nómina + Equipos)
        costo_mano_obra = (n_ayud * params["jornal_ayudante"]) + (n_mae * params["jornal_maestro"])
        costo_equipos = (n_retro * params["mq_retroexcavadora"]) + (n_roto * params["mq_rotomartillo"])
        
        # Costos fijos diarios (Ingeniero + Arriendos prorrateados por día)
        costo_admin = (params["salario_ingeniero"] / 30) + \
                      (params["arriendo_bodega"] / 30) + \
                      (params["arriendo_vivienda"] / 30) + \
                      (params["alim_diaria"] * (n_ayud + n_mae)) # Alimentación
                      
        costo_dia = costo_mano_obra + costo_equipos + costo_admin
        costo_acumulado += costo_dia

        # 3. PRODUCCIÓN (Aquí aplicamos el CLIMA)
        
        # A. Calculamos el Factor Clima (Excel o Manual)
        factor_clima = calcular_factor_climatico(row, params)
        
        # B. Capacidad Teórica (Sin lluvia)
        # Asumimos rendimientos estándar (puedes ajustar estos números):
        # - Retroexcavadora: 200 m3/día (teórico)
        # - Ayudante a pico y pala: 3 m3/día (apoyo)
        rendimiento_retro = 200 
        rendimiento_humano = 3
        
        avance_teorico = (n_retro * rendimiento_retro) + (n_ayud * rendimiento_humano)
        
        # C. Avance Real (Castigado por clima)
        avance_real_dia = avance_teorico * factor_clima
        
        # Ajuste por esponjamiento (Volumen en banco vs suelto)
        # Si medimos en banco, dividimos. Si pagamos volúmenes sueltos, multiplicamos.
        # Asumiremos avance en banco para la meta:
        avance_real_dia = avance_real_dia / params.get("factor_esponjamiento", 1.3)
        
        avance_fisico_acumulado += avance_real_dia
        
        # Guardamos el registro del día
        resultados.append({
            "Día": dias_trabajados,
            "Costo Día": costo_dia,
            "Costo Acum": costo_acumulado,
            "Avance (m3)": avance_real_dia,
            "Avance Acum": avance_fisico_acumulado,
            "Factor Clima": factor_clima,  # Guardamos esto para verlo en gráficas
            "Lluvia (mm)": row.get("Lluvia_mm", 0)
        })

    # Convertimos a DataFrame
    df_res = pd.DataFrame(resultados)
    
    # --- RESULTADOS GERENCIALES (KPIs) ---
    
    # Proyección
    if dias_trabajados > 0:
        promedio_diario = avance_fisico_acumulado / dias_trabajados
        dias_faltantes = (params["meta_metros"] - avance_fisico_acumulado) / promedio_diario if promedio_diario > 0 else 999
    else:
        dias_faltantes = 0

    # Dashboard resumen
    dashboard = pd.DataFrame({
        "Concepto (Día)": ["Personal", "Maquinaria", "Clima Promedio", "Avance Hoy"],
        "Valor (Día)": [
            f"{int(n_ayud)} Ayud + {int(n_mae)} Mae",
            f"{int(n_retro)} Retro",
            f"{df_res['Factor Clima'].mean()*100:.0f}%",
            f"{df_res['Avance (m3)'].iloc[-1]:.1f} m3" if not df_res.empty else "0"
        ],
        "Concepto Acum": ["Días Trabajados", "Costo Total", "Avance Total", "Proyección Fin"],
        "Valor Acum": [
            dias_trabajados,
            f"$ {costo_acumulado:,.0f}",
            f"{avance_fisico_acumulado:,.1f} / {params['meta_metros']} m3",
            f"Termina en {dias_faltantes:.1f} días"
        ]
    })
    
    # Logística (Volquetas)
    # Cuánta tierra movemos hoy (esponjada) para saber cuántas volquetas necesitamos
    tierra_a_mover_hoy = (df_res['Avance (m3)'].iloc[-1] * params.get("factor_esponjamiento", 1.3)) if not df_res.empty else 0
    capacidad_volqueta = params.get("capacidad_volqueta", 7)
    ciclo_minutos = params.get("tiempo_cargue", 15) + params.get("tiempo_transporte", 60)
    viajes_por_dia_volqueta = (480 / ciclo_minutos) # 480 min = 8 horas
    
    viajes_necesarios = tierra_a_mover_hoy / capacidad_volqueta
    volquetas_necesarias = viajes_necesarios / viajes_por_dia_volqueta

    flota = {
        "num_volquetas": int(np.ceil(volquetas_necesarias)),
        "viajes_dia": int(viajes_necesarios)
    }

    # Comparativa simple y Balance
    comparativa = pd.DataFrame({
        "Indicador": ["Costo Final Est.", "Días Totales"],
        "Actual": [f"$ {costo_acumulado + (dias_faltantes*costo_dia):,.0f}", int(dias_trabajados + dias_faltantes)],
        "Optimizado": ["Calculando...", "Calculando..."] # Placeholder
    })
    
    balance = pd.DataFrame([
        ["Ingresos (Contrato)", f"$ {params['precio_contrato']:,.0f}"],
        ["Egresos (Costo Real)", f"$ {costo_acumulado:,.0f}"],
        ["UTILIDAD ACTUAL", f"$ {params['precio_contrato'] - costo_acumulado:,.0f}"]
    ])

    # Top 5 (Datos dummy para ejemplo, se puede refinar)
    top5 = df_res.tail(5).copy()
    top5["Ayud"] = top5["Costo Día"] / 1000 # Dummy logic
    top5["Mae"] = 1
    top5["Retro"] = 1
    top5["Días"] = top5["Día"]
    top5["Utilidad_Show"] = "Alta"

    return {
        "dashboard": dashboard,
        "flota": flota,
        "comparativa": comparativa,
        "balance": balance,
        "top5": top5,
        "df_diario": df_res
    }
