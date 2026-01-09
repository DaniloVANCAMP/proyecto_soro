from fpdf import FPDF
import os
import tempfile  # <--- Importante para la nube

class PDF(FPDF):
    def __init__(self, color_rgb):
        super().__init__()
        self.col = color_rgb

    def header(self):
        # TÍTULO LIMPIO (Sin Logo)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*self.col)
        self.cell(0, 10, 'INFORME GERENCIAL DE OBRA', 0, 1, 'C')
        
        # Subtítulo
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Control Técnico, Financiero y Logístico', 0, 1, 'C')
        
        self.set_draw_color(*self.col)
        self.set_line_width(0.5)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(res, nombre, cfg):
    c = cfg.get("color", (0, 51, 102))
    pdf = PDF(c)
    pdf.add_page()
    
    # 1. INFO
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f"PROYECTO: {nombre.upper()}", ln=True)
    pdf.set_font('Arial', '', 10); pdf.set_text_color(50)
    meta = res['params']['meta_metros']
    precio = res['params']['precio_contrato']
    pdf.multi_cell(0, 6, f"Meta Física: {meta} m  |  Presupuesto Total: $ {int(precio):,}".replace(",", "."))
    pdf.ln(5)

    # 2. DASHBOARD
    pdf.set_fill_color(*c); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 7, " 1. ESTADO ACTUAL (DASHBOARD)", 0, 1, 'L', True)
    pdf.set_text_color(0); pdf.ln(2)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(47, 6, "Concepto Dia", 1, 0, 'C')
    pdf.cell(47, 6, "Valor Dia", 1, 0, 'C')
    pdf.cell(47, 6, "Concepto Acum", 1, 0, 'C')
    pdf.cell(47, 6, "Valor Acum", 1, 1, 'C')
    pdf.set_font('Arial', '', 8)
    for _, row in res['dashboard'].iterrows():
        for val in row: pdf.cell(47, 6, str(val), 1, 0, 'C')
        pdf.ln()

    # 3. COMPARATIVA
    pdf.ln(5); pdf.set_fill_color(*c); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 7, " 2. COSTO DE OPORTUNIDAD", 0, 1, 'L', True)
    pdf.set_text_color(0); pdf.ln(2)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(50, 6, "Indicador", 1)
    pdf.cell(70, 6, "Si sigues IGUAL", 1)
    pdf.cell(70, 6, "Si OPTIMIZAS", 1, 1)
    pdf.set_font('Arial', '', 8)
    for _, row in res['comparativa'].iterrows():
        pdf.cell(50, 6, str(row[0]), 1)
        pdf.cell(70, 6, str(row[1]), 1)
        pdf.cell(70, 6, str(row[2]), 1, 1)

    # 4. LOGÍSTICA
    pdf.ln(5); pdf.set_fill_color(*c); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 7, " 3. PLAN LOGÍSTICO REQUERIDO", 0, 1, 'L', True)
    pdf.set_text_color(0); pdf.ln(2); pdf.set_font('Arial', '', 9)
    
    flota = res['flota']
    pdf.cell(0, 6, f"- Maquinaria Carga: 1 Pajarita (Standby en obra)", ln=True)
    pdf.cell(0, 6, f"- Flota Transporte: {flota['num_volquetas']} Volquetas (Rotación continua)", ln=True)
    pdf.cell(0, 6, f"- Meta Diaria: {flota['viajes_dia']} viajes al botadero", ln=True)

    # 5. BALANCE
    pdf.ln(5); pdf.set_fill_color(*c); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 7, " 4. BALANCE FINANCIERO", 0, 1, 'L', True)
    pdf.set_text_color(0); pdf.ln(2); pdf.set_font('Arial', '', 9)
    for _, r in res['balance'].iterrows():
        if "UTILIDAD" in str(r[0]): pdf.set_font('Arial', 'B', 9); pdf.set_text_color(*c)
        else: pdf.set_font('Arial', '', 9); pdf.set_text_color(0)
        pdf.cell(120, 6, str(r[0]), 1); pdf.cell(70, 6, str(r[1]), 1, 1, 'R')

    # 6. TOP 5
    pdf.ln(5); pdf.set_fill_color(*c); pdf.set_text_color(255); pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 7, " 5. MEJORES ESTRATEGIAS (TOP 5)", 0, 1, 'L', True)
    pdf.set_text_color(0); pdf.ln(2)
    cols = ["Ayud", "Mae", "Retro", "Días", "Utilidad"]
    pdf.set_font('Arial', 'B', 8)
    for cx in cols: pdf.cell(38, 6, cx, 1, 0, 'C')
    pdf.ln(); pdf.set_font('Arial', '', 8)
    for _, r in res['top5'].iterrows():
        pdf.cell(38, 6, str(int(r['Ayud'])), 1, 0, 'C')
        pdf.cell(38, 6, str(int(r['Mae'])), 1, 0, 'C')
        pdf.cell(38, 6, f"{int(r['Retro'])} Und", 1, 0, 'C')
        pdf.cell(38, 6, str(int(r['Días'])), 1, 0, 'C')
        pdf.cell(38, 6, str(r['Utilidad_Show']), 1, 1, 'R')

    # --- CAMBIO CRÍTICO AQUÍ ---
    # Usamos un archivo temporal para que funcione en la nube
    # sin necesidad de crear carpetas manualmente.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name
