import pandas as pd
import numpy as np
import itertools

def f_cop(x):
    """Formato visual de moneda ($ 1.000.000)"""
    return f"$ {int(x):,}".replace(",", ".")

def procesar_datos(params, bitacora):
    # --- 1. LIMPIEZA ---
    df = bitacora.copy()
    df["gastos_varios"] = df["gastos_varios"].fillna(0)
    df["factor_clima"] = df["factor_clima"].fillna(1).replace(0, 1)
    df["fuerza_laboral"] = df["num_ayudantes"] + df["num_maestros"]
    df["uso_maquina"] = np.where(df["horas_retro"] > 0, 1, 0)
    
    # --- 2. RENDIMIENTOS ---
    mask_man = (df["uso_maquina"] == 0) & (df["fuerza_laboral"] > 0)
    val_rend = (df.loc[mask_man, "metros_avanzados"] / 
                df.loc[mask_man, "factor_clima"] / 
                df.loc[mask_man, "fuerza_laboral"]).mean()
    rend_manual = val_rend if not np.isnan(val_rend) else 1.3

    mask_maq = df["uso_maquina"] == 1
    if mask_maq.any():
        prom_maq = (df.loc[mask_maq, "metros_avanzados"] / df.loc[mask_maq, "factor_clima"]).mean()
        rend_maquina = prom_maq - (df.loc[mask_maq, "fuerza_laboral"].mean() * rend_manual)
    else:
        rend_maquina = 8.5

    # --- 3. COSTOS ACTUALES ---
    ing_dia = params["salario_ingeniero"] / 30
    arr_dia = (params["arriendo_bodega"] + params["arriendo_vivienda"]) / 30
    
    df["costo_dia"] = (
        (df["num_ayudantes"] * params["jornal_ayudante"]) +
        (df["num_maestros"] * params["jornal_maestro"]) +
        (df["fuerza_laboral"] * params["alim_diaria"]) +
        (df["uso_maquina"] * params["mq_retroexcavadora"]) +
        (df["horas_roto"] * (params["mq_rotomartillo"] / 8)) +
        ing_dia + arr_dia + df["gastos_varios"]
    )
    gasto_ejecutado = df["costo_dia"].sum()
    avance_total = df["metros_avanzados"].sum()
    metros_pendientes = max(0, params["meta_metros"] - avance_total)
    
    # --- 4. LOGÍSTICA ---
    vol_m3_lineal = params["ancho"] * params["profundidad"] * params["factor_esponjamiento"]
    cap_volq = params["capacidad_volqueta"]
    t_ciclo = params["tiempo_cargue"] + params["tiempo_transporte"]
    viajes_dia_por_volqueta = 480 / t_ciclo if t_ciclo > 0 else 1
    
    # --- 5. SIMULACIÓN ---
    escenarios = []
    clima = params["clima_proyectado"]
    
    max_ayu = int(params.get("max_ayudantes", 15))
    max_mae = int(params.get("max_maestros", 3))
    max_ret = int(params.get("max_retro", 1))

    for a, m, r in itertools.product(range(2, max_ayu + 1), range(1, max_mae + 1), range(0, max_ret + 1)):
        f = a + m
        efic = 0.85 if f > params["limite_densidad"] else 1.0
        
        rend_proy = ((f * rend_manual) + (r * rend_maquina)) * efic * clima
        dias = np.ceil(metros_pendientes / max(rend_proy, 0.5))
        
        # Logística del escenario
        vol_dia = rend_proy * vol_m3_lineal
        viajes_Nec_dia = np.ceil(vol_dia / cap_volq)
        costo_log = dias * ((viajes_Nec_dia * params["costo_viaje"]) + params["costo_pajarita"])
        
        c_var = dias * ((a * params["jornal_ayudante"]) + (m * params["jornal_maestro"]) + 
                        ((f+1)*params["alim_diaria"]) + (r * params["mq_retroexcavadora"]) + 
                        ing_dia + df["gastos_varios"].mean())
        
        c_fijo = np.ceil(dias/30) * (params["arriendo_bodega"] + params["arriendo_vivienda"])
        imprevistos = (c_var + costo_log + c_fijo) * params["pct_imprevistos"]
        
        total = gasto_ejecutado + c_var + costo_log + c_fijo + imprevistos
        
        escenarios.append({
            "Ayud": a, "Mae": m, "Retro": r, "Días": int(dias), 
            "Utilidad": params["precio_contrato"] - total,
            "C_Var": c_var, "RCD": costo_log, "C_Fijo": c_fijo, "Imp": imprevistos,
            "Viajes_Dia": viajes_Nec_dia
        })

    df_sim = pd.DataFrame(escenarios).sort_values("Utilidad", ascending=False)
    opt = df_sim.iloc[0]
    
    volq_req = np.ceil(opt["Viajes_Dia"] / viajes_dia_por_volqueta) if viajes_dia_por_volqueta > 0 else 0

    # --- 6. TENDENCIA ---
    u = df.iloc[-1]
    f_ult = u["num_ayudantes"] + u["num_maestros"]
    r_ult = 1 if u["horas_retro"] > 0 else 0
    rend_t = ((f_ult * rend_manual) + (r_ult * rend_maquina)) * clima
    dias_t = np.ceil(metros_pendientes / max(rend_t, 0.1))
    
    # Costo Tendencia
    vol_t = rend_t * vol_m3_lineal
    viajes_t = np.ceil(vol_t / cap_volq)
    costo_dia_log_t = params["costo_pajarita"] + (viajes_t * params["costo_viaje"])
    costo_dia_base_t = (u["costo_dia"] - df["gastos_varios"].mean())
    
    costo_fut_t = dias_t * (costo_dia_base_t + costo_dia_log_t)
    util_t = params["precio_contrato"] - (gasto_ejecutado + costo_fut_t)
    impacto = opt["Utilidad"] - util_t

    # --- 7. SALIDAS ---
    dashboard = pd.DataFrame({
        "Concepto (Día)": ["Avance Hoy", "Clima Hoy", "Caja Menor"],
        "Valor (Día)": [f"{u['metros_avanzados']} m", f"{u['factor_clima']}", f_cop(u['gastos_varios'])],
        "Concepto (Acum)": ["Avance %", "Ejecutado (m)", "Dinero Gastado"],
        "Valor (Acum)": [f"{(avance_total/params['meta_metros'])*100:.1f}%", f"{avance_total} m", f_cop(gasto_ejecutado)]
    })

    comparativa = pd.DataFrame({
        "Indicador": ["Equipo / Cuadrilla", "Tiempo Restante", "Utilidad Proyectada", "IMPACTO ($)"],
        "Tendencia": [f"{int(u['num_ayudantes'])} Ayudantes/{int(u['num_maestros'])} Maestros/{int(r_ult)} Retro", f"{int(dias_t)} días", f_cop(util_t), "---"],
        "Óptimo": [f"{int(opt['Ayud'])}Ayudantes/{int(opt['Mae'])} Maestros/{int(opt['Retro'])} Retro", f"{int(opt['Días'])} días", f_cop(opt['Utilidad']), f"+ {f_cop(impacto)}"]
    })

    balance = pd.DataFrame({
        "Rubro": ["1. Ejecutado", "2. Nómina y Maquinaria", "3. Logística/RCD", "4. Costos Fijos", "5. Imprevistos", "UTILIDAD FINAL"],
        "Valor": [f_cop(gasto_ejecutado), f_cop(opt['C_Var']), f_cop(opt['RCD']), f_cop(opt['C_Fijo']), f_cop(opt['Imp']), f_cop(opt['Utilidad'])]
    })

    df_top5 = df_sim.head(5).copy()
    df_top5["Utilidad_Show"] = df_top5["Utilidad"].apply(f_cop)

    return {
        "params": params, "dashboard": dashboard, "comparativa": comparativa, "balance": balance, "top5": df_top5, 
        "opt": opt, "flota": {"num_volquetas": int(volq_req), "viajes_dia": int(opt["Viajes_Dia"])},
        "viajes": int(opt["Viajes_Dia"])

    }


