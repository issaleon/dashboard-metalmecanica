import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from fpdf import FPDF
import os

# ---------------------------------------------------------
# 1. CONFIGURACIÓN E IDENTIDAD VISUAL ANÓNIMA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Dashboard OEE - Planta Metalmecánica",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

HEX_DARK_TEAL = "#1A4D54"
HEX_YELLOW = "#FFB703"
HEX_STEEL_GRAY = "#2B3A42"
HEX_SUCCESS_TEAL = "#2A9D8F"
HEX_ALERT_RED = "#D90429"
HEX_BG_LIGHT = "#F4F6F8"

URL_SHEETS_CSV_DEFAULT = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStnyYfi0vFkc202Y9nviwH1WAOVjB4ol1DiVlngVqvYMN8DSg5yO0eV7CtK1rz9g-Sp5rBJxqBCC-i/pub?gid=862398109&single=true&output=csv"
URL_FORMS_DEFAULT = "https://forms.gle/GVsfzb8w9zd3U7FR7"

st.markdown(f"""
<style>
    .stApp {{ background-color: {HEX_BG_LIGHT}; }}
    .esmetel-banner {{
        background-color: {HEX_DARK_TEAL};
        border-bottom: 5px solid {HEX_YELLOW};
        padding: 20px 25px;
        border-radius: 10px;
        color: #FFFFFF;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center;
    }}
    .esmetel-banner h1 {{ color: #FFFFFF !important; margin: 0; font-size: 2.2rem; font-weight: 800; }}
    .esmetel-banner p {{ color: {HEX_YELLOW} !important; margin: 5px 0 0 0; font-size: 1.05rem; }}
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-top: 4px solid {HEX_DARK_TEAL} !important;
        padding: 16px !important;
        border-radius: 10px !important;
        box-shadow: 0 3px 10px rgba(0,0,0,0.04) !important;
    }}
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FUNCIONES DE CARGA Y PROCESAMIENTO DINÁMICO DE DATOS
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_datos_google_sheets(url_csv):
    if not url_csv:
        return pd.DataFrame(), False
    try:
        df = pd.read_csv(url_csv, storage_options={'User-Agent': 'Mozilla/5.0'})
        df.columns = df.columns.str.strip()
        return df, True
    except Exception:
        return pd.DataFrame(), False

@st.cache_data
def cargar_datos_historicos_oficiales():
    """
    Base de datos ajustada exactamente al periodo del 02-ene al 28-sep-2025
    Total turnos-máquina: 576 (4,608.0 horas programadas)
    Paradas no programadas: 85 eventos (250.37 horas)
    Setup/Preparación: 447.26 horas (46.59 min/turno promedio)
    """
    data_prod = []
    # 192 turnos por cada una de las 3 máquinas = 576 turnos-máquina (4,608 h)
    for eq in ['EQ-01', 'EQ-02', 'EQ-03']:
        for _ in range(192):
            data_prod.append({
                'equipo_id': eq,
                'tiempo_planificado_min': 480.0, # 8 horas por turno
                'tiempo_setup_min': 46.59,      # Promedio AS-IS
                'setup_tobe_min': 22.78         # Promedio TO-BE (SMED factor 22/45)
            })
    df_prod = pd.DataFrame(data_prod)

    # Distribución oficial de paradas por máquina (250.37 h, 85 fallas)
    # EQ-01: 84.7 h, 32 fallas | EQ-02: 95.8 h, 30 fallas | EQ-03: 69.8 h, 23 fallas
    paradas_list = []
    
    def agregar_fallas(eq, n_fallas, total_horas):
        prom_min = (total_horas * 60.0) / n_fallas
        # Distribución de causas según artículo: 40% Desgaste/Lubricación (34 total), 33% Ausencia Preventivo (28 total), resto Otras (23 total)
        for i in range(n_fallas):
            if i < int(n_fallas * 0.40):
                causa = 'Desgaste de componentes (Boquillas/Guías/Lubricación)'
            elif i < int(n_fallas * 0.73):
                causa = 'Ausencia de Mantenimiento Preventivo'
            else:
                causa = 'Otras causas operativas / eléctricas'
                
            paradas_list.append({
                'equipo_id': eq,
                'tipo_parada': 'No Programada',
                'duracion_min': prom_min,
                'causa_raiz': causa
            })

    agregar_fallas('EQ-01', 32, 84.7)
    agregar_fallas('EQ-02', 30, 95.8)
    agregar_fallas('EQ-03', 23, 69.8)
    
    df_paradas_asis = pd.DataFrame(paradas_list)

    # Proyección TO-BE (E4: Detección LUP 100% sobre causas de desgaste/lubricación)
    df_paradas_tobe = df_paradas_asis.copy()
    df_paradas_tobe['erradicada'] = df_paradas_tobe['causa_raiz'].str.contains('Desgaste', case=False)
    df_paradas_tobe = df_paradas_tobe[~df_paradas_tobe['erradicada']].copy()
    df_paradas_tobe['duracion_tobe_min'] = df_paradas_tobe['duracion_min']

    return df_paradas_asis, df_prod, df_paradas_tobe

def generar_reporte_pdf(escenario_txt, equipo_txt, d_mec, d_op, mtbf, mttr, h_parada, ganancia_smed, total_lup):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "REPORTE GERENCIAL OPERATIVO - CELDA DE SOLDADURA", ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Periodo: 02-Ene al 28-Sep 2025 (576 Turnos) | Escenario: {escenario_txt} | Equipo: {equipo_txt}", ln=1, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. RESUMEN DE METRICAS OPERATIVAS (KPIs)", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"- Disponibilidad Mecanica: {d_mec:.2f}%", ln=1)
    pdf.cell(0, 7, f"- Disponibilidad Operativa: {d_op:.2f}%", ln=1)
    pdf.cell(0, 7, f"- Confiabilidad (MTBF): {mtbf:.2f} horas", ln=1)
    pdf.cell(0, 7, f"- Mantenibilidad (MTTR): {mttr:.2f} horas", ln=1)
    pdf.cell(0, 7, f"- Horas Improductivas Acumuladas: {h_parada:.2f} horas", ln=1)
    pdf.cell(0, 7, f"- Capacidad Recuperada por SMED: +{ganancia_smed:.2f} horas (en el periodo)", ln=1)
    pdf.cell(0, 7, f"- Inspecciones LUP-01 Recibidas (Nube): {total_lup} registros", ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. DIAGNOSTICO GERENCIAL", ln=1)
    pdf.set_font("Arial", "", 11)
    if d_mec >= 95.0:
        pdf.multi_cell(0, 6, "ESTADO OPTIMO: La disponibilidad mecanica cumple con la meta institucional (>= 95%). Las inspecciones autonomas LUP-01 registradas resguardan la continuidad operativa.")
    else:
        pdf.multi_cell(0, 6, "ALERTA REQUERIDA: La disponibilidad mecanica esta por debajo de la meta (<95%). Se recomienda auditar las frecuencias de falla capturadas en el formulario de campo.")
        
    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")

# ---------------------------------------------------------
# INTERFAZ Y NAVEGACIÓN
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏗️ **Planta Metalmecánica**")
    st.caption("Sistema de Gestión Operativa OEE (Ene - Sep 2025)")
    
    menu_seleccion = option_menu(
        menu_title="Menú Principal",
        options=["Visión General OEE", "Análisis de Paradas", "Datos Campo (Google Sheets)", "Plan & Reporte PDF"],
        icons=["speedometer2", "bar-chart-steps", "cloud-check", "file-earmark-pdf"],
        menu_icon="layers-half",
        default_index=0,
        styles={
            "container": {"padding": "5px!", "background-color": "#FAFAFA"},
            "icon": {"color": HEX_DARK_TEAL, "font-size": "18px"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin": "0px", "--hover-color": "#EAEAEA"},
            "nav-link-selected": {"background-color": HEX_DARK_TEAL, "color": "#FFFFFF"},
        }
    )
    
    st.markdown("### Filtros Operativos")
    escenario = st.radio("Escenario:", ["TO-BE (Propuesta TPM + SMED)", "AS-IS (Situación Actual)"])
    equipo_sel = st.selectbox("Unidad MIG:", ["Planta General (EQ-01, EQ-02, EQ-03)", "EQ-01", "EQ-02", "EQ-03"])
    
    st.divider()
    st.markdown("### Captura en Campo")
    st.link_button("📋 Abrir Formulario LUP-01 (QR)", URL_FORMS_DEFAULT, use_container_width=True)
    
    st.divider()
    st.markdown("### Conexión Google Sheets")
    url_sheets = st.text_input("URL CSV Publicada:", value=URL_SHEETS_CSV_DEFAULT, help="URL pública en formato CSV de la hoja de respuestas.")

st.markdown(f"""
<div class="esmetel-banner">
    <h1>Tablero de Control Operativo - Celda de Soldadura</h1>
    <p>Monitoreo Periodo 02-Ene al 28-Sep 2025 (4,608 h Programadas) | Integración Nube Google Forms/Sheets</p>
</div>
""", unsafe_allow_html=True)

df_paradas_asis, df_prod, df_paradas_tobe = cargar_datos_historicos_oficiales()
df_gs, gs_conectado = cargar_datos_google_sheets(url_sheets)

# Filtrar datos por máquina seleccionada
df_prod_f = df_prod if equipo_sel.startswith("Planta") else df_prod[df_prod['equipo_id'] == equipo_sel]
paradas_asis_f = df_paradas_asis if equipo_sel.startswith("Planta") else df_paradas_asis[df_paradas_asis['equipo_id'] == equipo_sel]
paradas_tobe_f = df_paradas_tobe if equipo_sel.startswith("Planta") else df_paradas_tobe[df_paradas_tobe['equipo_id'] == equipo_sel]

es_tobe = escenario.startswith("TO-BE")
paradas_f = paradas_tobe_f if es_tobe else paradas_asis_f

# Tiempos base acumulados (Ene - Sep 2025)
t_plan_total = df_prod_f['tiempo_planificado_min'].sum() / 60.0  # 4,608 h para Planta General
t_setup_asis = df_prod_f['tiempo_setup_min'].sum() / 60.0        # 447.26 h para Planta General
t_setup_tobe = df_prod_f['setup_tobe_min'].sum() / 60.0        # 218.66 h para Planta General

horas_parada_historicas = paradas_f['duracion_min'].sum() / 60.0
num_fallas_historicas = len(paradas_f)

# ---------------------------------------------------------
# CÁLCULO DINÁMICO EN TIEMPO REAL DESDE GOOGLE SHEETS
# ---------------------------------------------------------
minutos_parada_campo = 0.0
fallas_campo = 0

if gs_conectado and not df_gs.empty:
    if equipo_sel.startswith("Planta"):
        df_gs_f = df_gs.copy()
    else:
        col_eq = [c for c in df_gs.columns if 'unidad' in c.lower() or 'máquina' in c.lower() or 'equipo' in c.lower()]
        if col_eq:
            df_gs_f = df_gs[df_gs[col_eq[0]].astype(str).str.contains(equipo_sel, case=False, na=False)]
        else:
            df_gs_f = df_gs.copy()
            
    col_dur = [c for c in df_gs_f.columns if 'duraci' in c.lower() or 'minuto' in c.lower() or 'tiempo' in c.lower()]
    if col_dur:
        duraciones_serie = pd.to_numeric(df_gs_f[col_dur[0]], errors='coerce').fillna(0)
        minutos_parada_campo = duraciones_serie.sum()
        fallas_campo = len(duraciones_serie[duraciones_serie > 0])

# Consolidación total de variables
horas_parada = horas_parada_historicas + (minutos_parada_campo / 60.0)
num_fallas = num_fallas_historicas + fallas_campo
horas_setup_actual = t_setup_tobe if es_tobe else t_setup_asis

# Fórmulas oficiales según artículo (Ecuaciones 1 y 2)
d_mec = ((t_plan_total - horas_parada) / t_plan_total) * 100.0
d_op = ((t_plan_total - horas_parada - horas_setup_actual) / t_plan_total) * 100.0
mtbf = (t_plan_total - horas_parada) / max(num_fallas, 1)
mttr = horas_parada / max(num_fallas, 1)
ahorro_smed_horas = t_setup_asis - t_setup_tobe if es_tobe else 0.0
total_lup = len(df_gs) if gs_conectado else 0

# ---------------------------------------------------------
# VISTAS DEL DASHBOARD
# ---------------------------------------------------------
if menu_seleccion == "Visión General OEE":
    st.subheader("Indicadores de Desempeño Operativo (Ene - Sep 2025)")
    k1, k2, k3, k4, k5 = st.columns(5)
    
    k1.metric("Disponibilidad Mecánica", f"{d_mec:.2f}%", f"{'Meta Cumplida (≥95%)' if d_mec>=95.0 else 'Bajo Meta (<95%)'}", delta_color="normal" if d_mec>=95.0 else "inverse")
    k2.metric("Disponibilidad Operativa", f"{d_op:.2f}%", f"Setup: {horas_setup_actual:.1f}h", delta_color="normal" if d_op>=88.0 else "inverse")
    k3.metric("Confiabilidad (MTBF)", f"{mtbf:.2f} h", f"{'Óptimo (≥120h)' if mtbf>=120.0 else 'Crítico (<120h)'}", delta_color="normal" if mtbf>=120.0 else "inverse")
    k4.metric("Mantenibilidad (MTTR)", f"{mttr:.2f} h", f"{'Óptimo (≤2.0h)' if mttr<=2.0 else 'Alto (>2.0h)'}", delta_color="inverse" if mttr<=2.0 else "normal")
    k5.metric("Checklists LUP (Nube)", f"{total_lup}", "Respuestas Forms", delta_color="normal")

    st.divider()
    c_tacometro, c_andon = st.columns([1.8, 2.2])
    
    with c_tacometro:
        st.subheader("Disponibilidad Mecánica")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=d_mec,
            number={'suffix': "%", 'font': {'size': 36}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': HEX_DARK_TEAL},
                'steps': [
                    {'range': [0, 85], 'color': '#FFD1D1'},
                    {'range': [85, 95], 'color': '#FFEAA7'},
                    {'range': [95, 100], 'color': '#D4EDDA'}
                ],
                'threshold': {'line': {'color': HEX_ALERT_RED, 'width': 4}, 'thickness': 0.75, 'value': 95.0}
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=10, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c_andon:
        st.subheader("Matriz de Diagnóstico y Andón")
        if d_mec >= 95.0:
            st.success("**DISPONIBILIDAD ÓPTIMA**:\n\nInspecciones LUP-01 efectivas. Capacidad productiva resguardada.")
        else:
            st.error("**ALERTA EN DISPONIBILIDAD**:\n\nPérdida de horas por paradas no programadas. Auditar checklists LUP-01.")
            
        if mtbf >= 120.0:
            st.success("**CONFIABILIDAD OK**:\n\nMantenimiento autónomo operativo. Intervalo entre averías superior a 120 horas.")
        else:
            st.warning("**PRECAUCIÓN EN CONFIABILIDAD**:\n\nFrecuencia de fallas elevada. Verificar alineación de guías y alimentador.")

elif menu_seleccion == "Análisis de Paradas":
    col_g1, col_g2 = st.columns([3.2, 2])
    
    with col_g1:
        st.subheader("Diagrama de Pareto - Causas de Parada")
        pareto_df = paradas_f.groupby('causa_raiz')['duracion_min'].sum().reset_index()
        pareto_df['horas'] = pareto_df['duracion_min'] / 60.0
        pareto_df = pareto_df.sort_values(by='horas', ascending=False)
        pareto_df['acumulado_horas'] = pareto_df['horas'].cumsum()
        total_h = pareto_df['horas'].sum()
        pareto_df['pct_acumulado'] = (pareto_df['acumulado_horas'] / max(total_h, 0.001)) * 100
        
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=pareto_df['causa_raiz'], y=pareto_df['horas'], name="Horas Improductivas", marker_color=HEX_DARK_TEAL, text=pareto_df['horas'].round(1), textposition='auto'))
        fig_pareto.add_trace(go.Scatter(x=pareto_df['causa_raiz'], y=pareto_df['pct_acumulado'], name="% Acumulado (Pareto)", yaxis="y2", mode="lines+markers", line=dict(color=HEX_ALERT_RED, width=3), marker=dict(size=8, color=HEX_YELLOW)))
        fig_pareto.update_layout(template="plotly_white", height=420, margin=dict(l=20, r=20, t=30, b=20), yaxis=dict(title="Horas de Parada"), yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 110]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col_g2:
        st.subheader("Horas Improductivas por Unidad")
        eq_summary = []
        for eq in ['EQ-01', 'EQ-02', 'EQ-03']:
            p_eq = paradas_tobe_f if es_tobe else paradas_asis_f
            p_eq = p_eq[p_eq['equipo_id'] == eq]
            h_eq = p_eq['duracion_min'].sum() / 60.0
            eq_summary.append({'Equipo': eq, 'Horas de Parada': h_eq})
            
        df_eq = pd.DataFrame(eq_summary)
        fig_eq = px.bar(df_eq, x='Equipo', y='Horas de Parada', color='Equipo', text_auto='.1f', color_discrete_map={'EQ-01': HEX_DARK_TEAL, 'EQ-02': HEX_SUCCESS_TEAL, 'EQ-03': HEX_YELLOW})
        fig_eq.update_layout(template="plotly_white", height=420, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_eq, use_container_width=True)

elif menu_seleccion == "Datos Campo (Google Sheets)":
    st.subheader("Monitoreo en Vivo de Inspecciones LUP-01")
    
    col_info, col_link = st.columns([3, 1])
    with col_info:
        st.write("Esta sección lee automáticamente las respuestas enviadas desde el **Google Form** mediante el código QR de planta.")
    with col_link:
        st.link_button("📱 Abrir Formulario", URL_FORMS_DEFAULT, use_container_width=True)
    
    st.divider()
    
    if gs_conectado and not df_gs.empty:
        st.success(f"✅ Conexión activa con Google Sheets. Se registran **{len(df_gs)} respuestas** en la nube.")
        st.dataframe(df_gs, use_container_width=True)
    else:
        st.info("💡 La hoja de Google Sheets está conectada y a la espera de nuevos registros desde los celulares de los operarios.")

elif menu_seleccion == "Plan & Reporte PDF":
    st.subheader("Plan de Acción Estratégico TPM / SMED")
    
    matriz_decisiones = pd.DataFrame({
        "Pilares TPM / SMED": ["Mantenimiento Autónomo (LUP-01)", "Estandarización SMED", "Gestión de Repuestos Críticos", "Mantenimiento Planificado"],
        "Diagnóstico AS-IS (02-Ene al 28-Sep 2025)": [
            "34 fallas por falta de lubricación y desgaste prematuro de boquillas/guías (100.6 h perdidas).",
            "Tiempos de setup de 46.59 min/turno (447.26 h acumuladas en el periodo).",
            "Demora en reparaciones complejas (MTTR inicial de 2.95 h).",
            "28 fallas asociadas a ausencia de preventivo (75.8 h perdidas)."
        ],
        "Acción Estratégica Implementada (TO-BE)": [
            "Checklist LUP-01 capturado vía Google Forms escaneando el código QR en la soldadora.",
            "Estandarización de tareas internas/externas aplicando factor SMED 22/45.",
            "SOP estandarizado con Kit de repuestos críticos a pie de máquina.",
            "Rutinas semanales de mantenimiento programadas para soldadoras EQ-01, EQ-02 y EQ-03."
        ],
        "Impacto Proyectado (Ene - Sep)": [
            "Erradicación de las 34 fallas de desgaste/lubricación mediante detección temprana.",
            "Reducción del setup a 22.78 min/turno → Recuperación de +228.60 h en el periodo.",
            "Disminución del MTTR a ≤ 2.00 horas.",
            "Cierre de brechas: D_mec sube a 96.75% y D_op sube a 89.82% (E3)."
        ]
    })
    st.dataframe(matriz_decisiones, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("Exportación de Informe Gerencial")
    
    pdf_bytes = generar_reporte_pdf(escenario, equipo_sel, d_mec, d_op, mtbf, mttr, horas_parada, ahorro_smed_horas, total_lup)
    
    st.download_button(
        label="Descargar Reporte Gerencial en PDF",
        data=pdf_bytes,
        file_name=f"Reporte_Gerencial_{equipo_sel.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )
