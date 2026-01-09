import pandas as pd
import numpy as np

def calcular_factor_climatico(fila, params):
    """
    Busca la columna 'Lluvia_mm' en el Excel.
    - Si existe y tiene dato: Calcula el castigo (0.1 a 1.0).
    - Si NO existe o está vacía: Usa el valor manual de la App (params['clima_proyectado']).
    """
    if "Lluvia_mm" in fila.index and pd.notna(fila["Lluvia_mm"]):
        mm = float(fila["Lluvia_mm"])
        if mm <= 2: return 1.0        # Seco
        elif mm <= 10: return 0.85    # Húmedo
        elif mm <= 25: return 0.60    # Barro
        else: return 0.10             # Inundado
    
    # Si no hay dato en Excel, usa el slider manual
    return params.get("clima_proyectado", 0.90)

def procesar_datos(params, df_bitacora):
    resultados = []
    
    # Limpiamos nombres de columnas
    df_bitacora.columns = [c.strip() for c in df_bitacora.columns]
    
    costo_acum = 0
    meta_acum = 0
    dias_trabajados = 0
    
    # --- PROCESAMIENTO FILA POR FILA ---
    for index, row in df_bitacora.iterrows():
        dias_trabajados += 1
        
        # 1. Recursos
        n_ayu = row.get("Ayud", 0)
        n_mae = row.get("Mae", 0)
        n_retro = row.get("Retro", 0)
        n_roto = row.get("Roto", 0) if "Roto" in row else 0
        
        # 2. Costos
        c_mo = (n_ayu * params["jornal_ayudante"]) + (n_mae * params["jornal_maestro"])
        c_eq = (n_retro * params["mq_retroexcavadora"]) + (n_roto * params["mq_rotomartillo"])
        c_adm = (params["salario_ingeniero"]/30) + (params["arriendo_bodega"]/30) + (params["arriendo_vivienda"]/30) + (params["alim_diaria"]*(n_ayu+n_mae))
        
        costo_dia = c_mo + c_eq + c_adm
        costo_acum += costo_dia
        
        # 3. AVANCE (Aquí integramos la Lluvia sin romper nada más)
        factor_clima = calcular_factor_climatico(row, params)
        
        # Rendimientos teóricos estándar
        rend_retro = 200 # m3/dia
        rend_mano = 3    # m3/dia
        
        # Producción teórica (Sin lluvia)
        prod_teorica = (n_retro * rend_retro) + (n_ayu * rend_mano)
        
        # Producción real (Con lluvia)
        prod_real = prod_teorica * factor_clima
        
        # Ajuste por esponjamiento (Banco vs Suelto)
        # Asumimos que la meta está en banco
        avance_banco = prod_real / params.get("factor_esponjamiento", 1.3)
        
        meta_acum += avance_banco
        
        resultados.append({
            "Día": dias_trabajados,
            "Costo Real": costo_dia,
            "Costo Acum": costo_acum,
            "Avance (m3)": avance_banco,
            "Avance Acum": meta_acum,
            "Eficiencia Clima": factor_clima,
            # Guardamos datos para el Top 5
            "Ayud": n_ayu, "Mae": n_mae, "Retro": n_retro, 
            "Utilidad_Show": "Alta" if factor_clima > 0.8 else "Baja" 
        })
        
    df_res = pd.DataFrame(resultados)
    
    # --- GENERACIÓN DE TABLAS (RESTITUIDAS AL FORMATO ORIGINAL) ---
    
    # 1. DASHBOARD
    # Si no hay datos, ponemos ceros para que no falle
    ultimo_avance = df_res['Avance (m3)'].iloc[-1] if not df_res.empty else 0
    promedio_clima = df_res['Eficiencia Clima'].mean() if not df_res.empty else params.get("clima_proyectado", 0.9)
    
    dashboard = pd.DataFrame({
        "Concepto Dia": ["Personal en Obra", "Maquinaria Activa", "Eficiencia Clima", "Avance del Día"],
        "Valor Dia": [
            f"{int(n_ayu)} Of. + {int(n_mae)} Mae",
            f"{int(n_retro)} Retro",
            f"{promedio_clima*100:.0f}%",
            f"{ultimo_avance:.1f} m³"
        ],
        "Concepto Acum": ["Días Ejecutados", "Costo Acumulado", "Avance Total", "Proyección"],
        "Valor Acum": [
            dias_trabajados,
            f"$ {costo_acum:,.0f}",
            f"{meta_acum:,.1f} / {params['meta_metros']} m³",
            f"Faltan {params['meta_metros'] - meta_acum:.0f} m³"
        ]
    })
    
    # 2. LOGÍSTICA (VOLQUETAS)
    # Calculamos basado en lo que se excavó hoy (suelto)
    volumen_suelto_dia = ultimo_avance * params.get("factor_esponjamiento", 1.3)
    
    # Si no se excavó nada (0), calculamos con el potencial de la máquina
    # para recomendar cuántas se NECESITARÍAN si se trabajara a full.
    if volumen_suelto_dia == 0 and n_retro > 0:
        volumen_suelto_dia = (n_retro * 200) # Asumimos potencial full para la recomendación
    
    cap_volq = params.get("capacidad_volqueta", 7)
    t_ciclo = params.get("tiempo_cargue", 15) + params.get("tiempo_transporte", 60)
    viajes_volqueta_dia = 480 / t_ciclo # 480 min jornada
    
    viajes_req = volumen_suelto_dia / cap_volq
    num_volquetas = viajes_req / viajes_volqueta_dia
    
    flota = {
        "num_volquetas": int(np.ceil(num_volquetas)) if num_volquetas > 0 else 0,
        "viajes_dia": int(viajes_req)
    }

    # 3. COMPARATIVA (Simple)
    comparativa = pd.DataFrame([
        ["Costo Final Proyectado", f"$ {costo_acum * (params['meta_metros']/meta_acum if meta_acum > 0 else 1):,.0f}", "---"],
        ["Días Estimados Fin", f"{(dias_trabajados * params['meta_metros'] / meta_acum) if meta_acum > 0 else 0:.1f}", "---"]
    ], columns=["Indicador", "Actual", "Optimizado"])

    # 4. BALANCE
    balance = pd.DataFrame([
        ["TOTAL PAGADO (Nomina/Eq)", f"$ {costo_acum:,.0f}"],
        ["PRESUPUESTO EJECUTADO", f"{meta_acum/params['meta_metros']*100:.1f}%"],
        ["UTILIDAD A LA FECHA", f"$ {params['precio_contrato'] * (meta_acum/params['meta_metros']) - costo_acum:,.0f}"]
    ])

    return {
        "dashboard": dashboard,
        "flota": flota,
        "comparativa": comparativa,
        "balance": balance,
        "top5": df_res.tail(5), # Devolvemos las últimas 5 filas tal cual
        "df_diario": df_res
    }
