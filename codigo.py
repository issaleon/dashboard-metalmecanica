import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from fpdf import FPDF
from streamlit_option_menu import option_menu

# =========================================================
# 1. CONFIGURACIÓN E IDENTIDAD VISUAL
# =========================================================
st.set_page_config(
    page_title="Tablero de mantenimiento MIG - Modelo v9",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Paleta: se conserva el verde azulado y el amarillo del tablero original.
INK = "#14262B"
MUTED = "#5B6B72"
LINE = "#DCE2E4"
BG = "#F3F5F5"
TEAL = "#1A4D54"        # identidad y E2
TEAL_MID = "#2A9D8F"    # positivo
AMBER = "#E09F1F"       # E1 (preventivo fijo)
YELLOW = "#FFB703"      # filete del encabezado
STEEL = "#8696A0"       # E0 (referencia)
CORAL = "#C1473B"       # paradas no programadas / negativo
FONT = "IBM Plex Sans, Segoe UI, Arial, sans-serif"

URL_SHEETS_CSV_DEFAULT = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStnyYfi0vFkc202Y9nviwH1WAOVjB4ol1DiVlngVqvYMN8DSg5yO0eV7CtK1rz9g-Sp5rBJxqBCC-i/pub?gid=862398109&single=true&output=csv"
URL_FORMS_DEFAULT = "https://forms.gle/GVsfzb8w9zd3U7FR7"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

.stApp { background-color: @BG@; font-family: @FONT@; color: @INK@; font-variant-numeric: tabular-nums; }
.block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1320px; }
h1, h2, h3, h4, h5 { font-family: @FONT@; color: @INK@; letter-spacing: -0.01em; }
h3 { font-size: 1.25rem; font-weight: 600; margin-bottom: .2rem; }
h4 { font-size: 1.02rem; font-weight: 600; }
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid @LINE@; }
section[data-testid="stSidebar"] h3 { font-size: 1.0rem; margin-top: .4rem; }

/* Encabezado */
.banner { background: @TEAL@; border-bottom: 4px solid @YELLOW@; border-radius: 6px; padding: 22px 28px 20px 28px; margin-bottom: 14px; }
.banner h1 { color: #FFFFFF !important; font-size: 1.65rem; font-weight: 600; margin: 0 0 4px 0; padding: 0; }
.banner p { color: #CFE3E2; margin: 0 0 14px 0; font-size: .95rem; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { border: 1px solid rgba(255,255,255,.35); color: #FFFFFF; border-radius: 4px; padding: 3px 10px; font-size: .82rem; }
.chip b { color: @YELLOW@; font-weight: 600; }

/* Franja de indicadores */
.kpi-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); background: #FFFFFF; border: 1px solid @LINE@; border-radius: 6px; margin: 6px 0 18px 0; }
.kpi { padding: 16px 20px; border-left: 1px solid @LINE@; }
.kpi:first-child { border-left: none; }
.kpi .lbl { font-size: .82rem; color: @MUTED@; margin-bottom: 4px; }
.kpi .val { font-size: 1.85rem; font-weight: 600; line-height: 1.15; color: @INK@; }
.kpi .nota { font-size: .82rem; margin-top: 4px; color: @MUTED@; }
.kpi .nota.ok { color: #1B7F72; }
.kpi .nota.bad { color: @CORAL@; }

/* Veredicto */
.veredicto { background: #FFFFFF; border: 1px solid @LINE@; border-left: 6px solid @STEEL@; border-radius: 6px; padding: 14px 18px; margin-bottom: 18px; }
.veredicto.e2 { border-left-color: @TEAL_MID@; }
.veredicto.e1 { border-left-color: @AMBER@; }
.veredicto .t { font-weight: 600; font-size: 1.05rem; margin-bottom: 2px; }
.veredicto .d { color: @MUTED@; font-size: .92rem; }

/* Bloques de texto */
.bloque { background: #FFFFFF; border: 1px solid @LINE@; border-radius: 6px; padding: 14px 18px; font-size: .92rem; line-height: 1.55; }
.bloque .g { display: flex; gap: 10px; align-items: baseline; margin: 4px 0; }
.bloque .sw { width: 10px; height: 10px; border-radius: 2px; flex: none; position: relative; top: 1px; }

/* Botones */
div[data-testid="stLinkButton"] a, div[data-testid="stDownloadButton"] button {
    border-radius: 4px; border: 1px solid @TEAL@; color: @TEAL@; background: #FFFFFF; font-weight: 500;
}
div[data-testid="stLinkButton"] a:hover, div[data-testid="stDownloadButton"] button:hover { background: @TEAL@; color: #FFFFFF; }
</style>
"""
for _k, _v in {
    "@BG@": BG, "@FONT@": FONT, "@INK@": INK, "@LINE@": LINE, "@TEAL@": TEAL, "@YELLOW@": YELLOW,
    "@MUTED@": MUTED, "@CORAL@": CORAL, "@STEEL@": STEEL, "@TEAL_MID@": TEAL_MID, "@AMBER@": AMBER,
}.items():
    CSS = CSS.replace(_k, _v)
st.markdown(CSS, unsafe_allow_html=True)


# =========================================================
# 2. DATOS: TABLA 1 v9 Y GOOGLE SHEETS
# =========================================================
@st.cache_data(ttl=60)
def cargar_datos_google_sheets(url_csv):
    if not url_csv:
        return pd.DataFrame(), False
    try:
        df = pd.read_csv(url_csv, storage_options={"User-Agent": "Mozilla/5.0"})
        df.columns = df.columns.str.strip()
        return df, True
    except Exception:
        return pd.DataFrame(), False


@st.cache_data
def obtener_tabla1_v9():
    """Tabla 1 de la v9: 85 paradas y 250 horas estimadas por jefatura de planta."""
    df = pd.DataFrame([
        {"Causa": "Sin preventivo", "Eventos": 28, "Horas": 76.0, "Política Objetivo": "E1 (Preventivo fijo)"},
        {"Causa": "Desgaste", "Eventos": 28, "Horas": 79.0, "Política Objetivo": "E2 (Inspección con alerta)"},
        {"Causa": "Lubricación", "Eventos": 6, "Horas": 21.0, "Política Objetivo": "E2 (Inspección con alerta)"},
        {"Causa": "Otras causas", "Eventos": 23, "Horas": 74.0, "Política Objetivo": "No intervenido en modelo"},
    ])
    df["Porcentaje (%)"] = df["Horas"] / df["Horas"].sum() * 100.0
    return df


# ==== INICIO MOTOR ANALÍTICO ================================
# Supuestos de calendario (v9)
DIAS = 192
HORAS_TURNO = 8
N_EQUIPOS = 3
INTERVALO_E1 = 120.0                      # horas entre preventivos fijos
T_REF = float(DIAS * HORAS_TURNO * N_EQUIPOS)   # 4,608 h-máquina
N_REF = float(DIAS * N_EQUIPOS)                 # 576 turnos-máquina
HORAS_POR_EQUIPO = DIAS * HORAS_TURNO           # 1,536 h


def parametros_desde_tabla1(df):
    """Deriva de la Tabla 1 todas las constantes que usa el modelo (P0, 76 h, 100 h, 34 eventos)."""
    e1 = df[df["Política Objetivo"].str.startswith("E1")]
    e2 = df[df["Política Objetivo"].str.startswith("E2")]
    return {
        "P0": float(df["Horas"].sum()),            # 250 h
        "EV_TOTAL": int(df["Eventos"].sum()),      # 85 eventos
        "H_E1": float(e1["Horas"].sum()),          # 76 h
        "EV_E1": int(e1["Eventos"].sum()),         # 28 eventos
        "H_E2": float(e2["Horas"].sum()),          # 100 h
        "EV_E2": int(e2["Eventos"].sum()),         # 34 eventos
    }


DF_T1 = obtener_tabla1_v9()
PAR = parametros_desde_tabla1(DF_T1)
INTERVENCIONES_E1 = N_EQUIPOS * int(HORAS_POR_EQUIPO // INTERVALO_E1)   # 3 x 12 = 36


def calcular_modelo_v9(d, m, h, T=T_REF, N=N_REF):
    """
    Ecuaciones de la Guía de Cálculos v9 (mismos resultados que la versión anterior):
      E0: P0 = 250, H0 = 0, L0 = 250
      E1: P1 = 250 - 76 = 174; H1 = 36 h; L1 = P1 + H1
      E2: P2 = 250 - 100 d; H2 = (N m / 60) + 34 d h; L2 = P2 + H2
      Balance: dL = L1 - L2
      Equilibrio: m* = [100 d - 76 + (36 - 34 d) h] / (N / 60)
    """
    P0, H_E1, H_E2, EV_E2 = PAR["P0"], PAR["H_E1"], PAR["H_E2"], PAR["EV_E2"]
    factor_inspeccion = N / 60.0   # 9.6 h por cada minuto de inspección por turno-máquina

    P0_ = P0
    L0 = P0_
    Dmec0 = (T - P0_) / T * 100.0

    P1 = P0 - H_E1
    H1 = INTERVENCIONES_E1 * h
    L1 = P1 + H1
    Dmec1 = (T - P1) / T * 100.0

    P2 = P0 - H_E2 * d
    H2_insp = factor_inspeccion * m
    H2_interv = EV_E2 * d * h
    H2 = H2_insp + H2_interv
    L2 = P2 + H2
    Dmec2 = (T - P2) / T * 100.0

    delta_L = L1 - L2
    m_star = (H_E2 * d - H_E1 + (INTERVENCIONES_E1 - EV_E2 * d) * h) / factor_inspeccion

    d_meta_95 = max(0.0, (P0 - 0.05 * T) / H_E2)
    d_igual_E1 = (P0 - P1) / H_E2

    return {
        "T": T, "N": N, "d": d, "m": m, "h": h,
        "E0": {"nombre": "E0 (Referencia)", "P": P0_, "H": 0.0, "L": L0, "Dmec": Dmec0},
        "E1": {"nombre": "E1 (Preventivo fijo)", "P": P1, "H": H1, "L": L1, "Dmec": Dmec1},
        "E2": {"nombre": "E2 (Inspección con alerta)", "P": P2, "H": H2, "H_insp": H2_insp,
               "H_interv": H2_interv, "L": L2, "Dmec": Dmec2},
        "delta_L": delta_L,
        "m_star": m_star,
        "d_meta_95": d_meta_95,
        "d_igual_E1": d_igual_E1,
    }


def generar_tabla3_sensibilidad():
    """Reproduce los 18 resultados de la Tabla 3 de la v9."""
    filas = []
    for d_pct in [50, 100]:
        for h_val in [0.5, 1.0, 2.0]:
            fila = {"Detección d (%)": f"{d_pct}%", "Intervención h (h)": f"{h_val:g}"}
            for m_val in [1.0, 2.0, 3.0]:
                dl = calcular_modelo_v9(d=d_pct / 100.0, m=m_val, h=h_val)["delta_L"]
                fila[f"ΔL con m = {m_val:g} min (h)"] = round(dl, 1)
            filas.append(fila)
    return pd.DataFrame(filas)
# ==== FIN MOTOR ANALÍTICO ===================================

M_STAR_REF = calcular_modelo_v9(d=1.0, m=0.0, h=2.0)["m_star"]   # 2.92 min con d = 100 %, h = 2 h


# =========================================================
# 3. UTILIDADES DE PRESENTACIÓN
# =========================================================
def kpi_strip(items):
    """items: lista de (etiqueta, valor, nota, tono) con tono en {'ok','bad',''}."""
    celdas = "".join(
        f'<div class="kpi"><div class="lbl">{lbl}</div><div class="val">{val}</div>'
        f'<div class="nota {tono}">{nota}</div></div>'
        for lbl, val, nota, tono in items
    )
    st.markdown(f'<div class="kpi-strip">{celdas}</div>', unsafe_allow_html=True)


def base_layout(height, **extra):
    layout = dict(
        height=height,
        font=dict(family=FONT, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=12)),
        xaxis=dict(showgrid=False, linecolor=LINE, tickfont=dict(size=12)),
        yaxis=dict(gridcolor="#E6EBED", zeroline=False, linecolor=LINE),
    )
    layout.update(extra)
    return layout


def _t(s):
    return str(s).encode("latin-1", "replace").decode("latin-1")


def _linea(pdf, txt, alto=6, align="L"):
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, alto, _t(txt), align=align)


def generar_reporte_pdf(res, escenario_sel, total_lup):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 15)
    _linea(pdf, "REPORTE ANALITICO DE MANTENIMIENTO MIG - MODELO v9", 10, "C")
    pdf.set_font("Arial", "", 10)
    _linea(pdf, f"Calendario T = {res['T']:,.1f} h-maquina (N = {int(res['N'])} turnos) | Escenario activo: {escenario_sel}", 7, "C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    _linea(pdf, "1. PARAMETROS EVALUADOS", 8)
    pdf.set_font("Arial", "", 10)
    _linea(pdf, f"- Fraccion de deteccion supuesta (d): {res['d']*100:.1f}% ({res['d']:.3f})")
    _linea(pdf, f"- Duracion de inspeccion por turno-maquina (m): {res['m']:.2f} min")
    _linea(pdf, f"- Duracion de cada intervencion (h): {res['h']:.2f} h/intervencion")
    _linea(pdf, f"- Registros LUP-01 capturados en nube (Google Sheets): {total_lup} respuestas")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    _linea(pdf, "2. COMPARATIVA DE ESCENARIOS (TABLA 2 v9)", 8)
    pdf.set_font("Arial", "", 10)
    for k in ["E0", "E1", "E2"]:
        e = res[k]
        _linea(pdf, f"- {e['nombre']}: Pi = {e['P']:.1f} h | Hi = {e['H']:.1f} h | Dmec = {e['Dmec']:.2f}% | Li = {e['L']:.1f} h")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    _linea(pdf, "3. BALANCE DE HORAS Y PUNTO DE EQUILIBRIO", 8)
    pdf.set_font("Arial", "", 10)
    dl = round(res["delta_L"], 6)
    if dl > 0:
        criterio = "FAVORECE A E2 (la inspeccion con alerta consume menos horas totales)"
    elif dl < 0:
        criterio = "FAVORECE A E1 (el preventivo fijo consume menos horas totales)"
    else:
        criterio = "EMPATE TECNICO (L1 = L2)"
    _linea(pdf, f"- Diferencia de balance (Delta L = L1 - L2): {dl:+.1f} h -> {criterio}")
    _linea(pdf, f"- Duracion de inspeccion de equilibrio (m*): {res['m_star']:.2f} min/turno-maquina")
    _linea(pdf, f"- Deteccion minima para Dmec >= 95%: {res['d_meta_95']*100:.1f}% | Para igualar E1: {res['d_igual_E1']*100:.1f}%")

    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin-1")


# =========================================================
# 4. BARRA LATERAL
# =========================================================
with st.sidebar:
    st.markdown("### Celda de soldadura MIG")
    st.caption("Modelo analítico v9. Tres soldadoras (EQ-01 a EQ-03).")

    escenario_sel = st.radio(
        "Escenario destacado",
        ["E2 (Inspección con alerta)", "E1 (Preventivo fijo)", "E0 (Referencia)"],
        index=0,
    )

    st.markdown("### Parámetros del modelo")
    d_pct = st.slider(
        "Fracción de detección d (%)", 0, 100, 100, 5,
        help="Fracción de detección supuesta en E2 sobre 34 eventos y 100 h (desgaste más lubricación). Referencia v9: 100 %.",
    )
    m_min = st.slider(
        "Inspección m (min por turno-máquina)", 0.0, 15.0, 10.0, 0.5,
        help=f"Referencia conservadora de diseño v9: 10 min. Punto de equilibrio con d = 100 % y h = 2 h: {M_STAR_REF:.2f} min.",
    )
    h_hora = st.select_slider(
        "Duración de la intervención h (h)",
        options=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0], value=2.0,
        help="Duración de cada intervención planificada en E1 y E2. Referencia v9: 2.0 h.",
    )
    T_opcion = st.selectbox(
        "Calendario supuesto T (h-máquina)",
        [
            "Referencia: 4,608.0 h (192 días × 8 h × 3 eq.)",
            "Sensibilidad -10%: 4,147.2 h",
            "Sensibilidad +10%: 5,068.8 h",
        ],
    )
    T_val = T_REF * (0.9 if "-10%" in T_opcion else 1.1 if "+10%" in T_opcion else 1.0)

    st.divider()
    st.markdown("### Captura en campo")
    st.link_button("Abrir formulario LUP-01", URL_FORMS_DEFAULT, use_container_width=True)
    with st.expander("Conexión de datos (Google Sheets)"):
        url_sheets = st.text_input("URL del CSV publicado", value=URL_SHEETS_CSV_DEFAULT)

# =========================================================
# 5. CÁLCULO Y ENCABEZADO
# =========================================================
res = calcular_modelo_v9(d=d_pct / 100.0, m=m_min, h=h_hora, T=T_val, N=N_REF)
df_gs, gs_conectado = cargar_datos_google_sheets(url_sheets)
total_lup = len(df_gs) if gs_conectado else 0

clave_esc = escenario_sel[:2]
esc_actual = res[clave_esc]
delta_L = round(res["delta_L"], 6)   # evita falsos "no empate" por redondeo de punto flotante

st.markdown(
    f'<div class="banner"><h1>Tablero de mantenimiento de soldadoras MIG</h1>'
    f'<p>Inspección con alerta frente a preventivo fijo, comparadas por balance de horas</p>'
    f'<div class="chips">'
    f'<span class="chip">T = <b>{res["T"]:,.1f}</b> h-máquina</span>'
    f'<span class="chip">N = <b>{int(N_REF)}</b> turnos-máquina</span>'
    f'<span class="chip">Criterio: <b>Lᵢ = Pᵢ + Hᵢ</b></span>'
    f'<span class="chip">Base: <b>{PAR["EV_TOTAL"]}</b> paradas y <b>{PAR["P0"]:.0f}</b> h (Tabla 1)</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

menu_seleccion = option_menu(
    menu_title=None,
    options=[
        "Comparativa (E0, E1, E2)",
        "Causas de Parada (Tabla 1)",
        "Sensibilidad y Equilibrio (m*)",
        "Datos Campo (Google Sheets)",
        "Ecuaciones & Reporte PDF",
    ],
    icons=["speedometer2", "bar-chart-steps", "sliders", "cloud-check", "file-earmark-pdf"],
    orientation="horizontal",
    styles={
        "container": {"padding": "4px", "background-color": "#FFFFFF", "border": f"1px solid {LINE}", "border-radius": "6px"},
        "icon": {"color": TEAL, "font-size": "15px"},
        "nav-link": {"font-size": "13.5px", "text-align": "center", "margin": "0 2px", "--hover-color": "#EEF2F3", "border-radius": "4px"},
        "nav-link-selected": {"background-color": TEAL, "color": "#FFFFFF", "font-weight": "500"},
    },
)
st.write("")

# =========================================================
# VISTA 1: COMPARATIVA
# =========================================================
if menu_seleccion == "Comparativa (E0, E1, E2)":
    st.subheader(f"Indicadores de {esc_actual['nombre']}")

    cumple = esc_actual["Dmec"] >= 95.0
    kpi_strip([
        ("Disponibilidad mecánica (Dmec)", f"{esc_actual['Dmec']:.2f}%",
         "Cumple la meta de 95 %" if cumple else "Por debajo de la meta de 95 %", "ok" if cumple else "bad"),
        ("Paradas no programadas (Pᵢ)", f"{esc_actual['P']:.1f} h",
         f"{esc_actual['P'] - PAR['P0']:+.1f} h frente a E0", "ok" if esc_actual["P"] < PAR["P0"] else ""),
        ("Carga planificada (Hᵢ)", f"{esc_actual['H']:.1f} h",
         "Inspección más intervención" if esc_actual["H"] > 0 else "Sin carga planificada", ""),
        ("Balance total (Lᵢ)", f"{esc_actual['L']:.1f} h",
         f"{esc_actual['L'] - res['E0']['L']:+.1f} h frente a E0", "ok" if esc_actual["L"] < res["E0"]["L"] else "bad"),
        ("Balance E1 − E2 (ΔL)", f"{delta_L:+.1f} h",
         "Gana E2" if delta_L > 0 else ("Gana E1" if delta_L < 0 else "Empate"), "ok" if delta_L > 0 else ("bad" if delta_L < 0 else "")),
    ])

    if delta_L > 0:
        st.markdown(
            f'<div class="veredicto e2"><div class="t">Conviene E2 (ΔL = {delta_L:+.1f} h)</div>'
            f'<div class="d">Con d = {d_pct}%, m = {m_min:.1f} min y h = {h_hora:.1f} h, la inspección con alerta compromete '
            f'{delta_L:.1f} h menos que el preventivo fijo. Su inspección (m = {m_min:.2f} min) está por debajo del '
            f'equilibrio m* = {res["m_star"]:.2f} min.</div></div>', unsafe_allow_html=True)
    elif delta_L < 0:
        st.markdown(
            f'<div class="veredicto e1"><div class="t">Conviene E1 (ΔL = {delta_L:+.1f} h)</div>'
            f'<div class="d">Con m = {m_min:.1f} min, por encima del equilibrio m* = {res["m_star"]:.2f} min, '
            f'el preventivo fijo consume {abs(delta_L):.1f} h menos en total que la inspección con alerta.</div></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="veredicto"><div class="t">Empate técnico (ΔL = 0.0 h)</div>'
            f'<div class="d">Ambos escenarios comprometen exactamente {res["E1"]["L"]:.1f} h.</div></div>',
            unsafe_allow_html=True)

    col_tabla, col_chart = st.columns([1.0, 1.25], gap="large")
    with col_tabla:
        st.markdown("#### Comparativa de políticas (Tabla 2 v9)")
        df_comp = pd.DataFrame([
            {"Escenario": res[k]["nombre"], "Pᵢ (h)": res[k]["P"], "Hᵢ (h)": res[k]["H"],
             "D mecánica (%)": res[k]["Dmec"], "Lᵢ = Pᵢ + Hᵢ (h)": res[k]["L"]}
            for k in ["E0", "E1", "E2"]
        ])
        st.dataframe(
            df_comp, use_container_width=True, hide_index=True,
            column_config={
                "Pᵢ (h)": st.column_config.NumberColumn(format="%.1f"),
                "Hᵢ (h)": st.column_config.NumberColumn(format="%.1f"),
                "D mecánica (%)": st.column_config.NumberColumn(format="%.2f"),
                "Lᵢ = Pᵢ + Hᵢ (h)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.caption("Lᵢ es el total de horas comprometidas: paradas no programadas más carga planificada.")

    with col_chart:
        st.markdown("#### Composición del balance de horas")
        nombres = ["E0 Referencia", "E1 Preventivo fijo", "E2 Inspección con alerta"]
        p_vals = [res[k]["P"] for k in ["E0", "E1", "E2"]]
        h_vals = [res[k]["H"] for k in ["E0", "E1", "E2"]]
        l_vals = [res[k]["L"] for k in ["E0", "E1", "E2"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Paradas no programadas (Pᵢ)", x=nombres, y=p_vals, marker_color=CORAL, width=0.5,
                             text=[f"{v:.1f} h" for v in p_vals], textposition="inside",
                             textfont=dict(color="#FFFFFF", size=12)))
        fig.add_trace(go.Bar(name="Carga planificada (Hᵢ)", x=nombres, y=h_vals, marker_color=TEAL, width=0.5,
                             text=[f"{v:.1f} h" if v > 0 else "" for v in h_vals], textposition="inside",
                             textfont=dict(color="#FFFFFF", size=12)))
        fig.add_trace(go.Scatter(x=nombres, y=l_vals, mode="text", showlegend=False,
                                 text=[f"<b>L = {v:.1f} h</b>" for v in l_vals], textposition="top center",
                                 textfont=dict(size=13, color=INK)))
        fig.add_hline(y=res["E0"]["L"], line_dash="dot", line_color=STEEL,
                      annotation_text="Referencia E0", annotation_position="bottom right",
                      annotation_font=dict(size=11, color=MUTED))
        fig.update_layout(**base_layout(380, barmode="stack",
                                        yaxis=dict(title="Horas-máquina", gridcolor="#E6EBED", zeroline=False,
                                                   range=[0, max(l_vals) * 1.2])))
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# VISTA 2: CAUSAS DE PARADA
# =========================================================
elif menu_seleccion == "Causas de Parada (Tabla 1)":
    st.subheader("Distribución referencial de paradas (Tabla 1 v9)")
    st.caption(f"Total estimado por jefatura de planta: {PAR['EV_TOTAL']} eventos y {PAR['P0']:.0f} h en T = 4,608 h-máquina.")

    c1, c2 = st.columns([1.0, 1.4], gap="large")
    with c1:
        st.dataframe(
            DF_T1, use_container_width=True, hide_index=True,
            column_config={
                "Horas": st.column_config.NumberColumn(format="%.0f"),
                "Porcentaje (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )
        st.markdown(
            f'<div class="bloque"><b>Agrupación por política</b>'
            f'<div class="g"><span class="sw" style="background:{AMBER}"></span><span><b>E1, preventivo fijo:</b> sin preventivo, {PAR["EV_E1"]} eventos y {PAR["H_E1"]:.0f} h.</span></div>'
            f'<div class="g"><span class="sw" style="background:{TEAL}"></span><span><b>E2, inspección con alerta:</b> desgaste (28 ev, 79 h) más lubricación (6 ev, 21 h), {PAR["EV_E2"]} eventos y {PAR["H_E2"]:.0f} h.</span></div>'
            f'<div class="g"><span class="sw" style="background:{STEEL}"></span><span><b>Sin intervención directa:</b> otras causas, 23 eventos y 74 h.</span></div>'
            f'</div>', unsafe_allow_html=True)

    with c2:
        df_p = DF_T1.sort_values("Horas", ascending=False).reset_index(drop=True)
        df_p["Acumulado (%)"] = df_p["Porcentaje (%)"].cumsum()
        color_pol = {"E1": AMBER, "E2": TEAL, "No": STEEL}
        colores = [color_pol[p[:2]] if p[:2] in color_pol else STEEL for p in df_p["Política Objetivo"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_p["Causa"], y=df_p["Horas"], marker_color=colores, name="Horas de parada", width=0.55,
                             text=df_p["Horas"].map(lambda x: f"{x:.0f} h"), textposition="outside", cliponaxis=False))
        fig.add_trace(go.Scatter(x=df_p["Causa"], y=df_p["Acumulado (%)"], name="% acumulado", yaxis="y2",
                                 mode="lines+markers", line=dict(color=INK, width=2),
                                 marker=dict(size=8, color=YELLOW, line=dict(width=1.5, color=INK))))
        fig.update_layout(**base_layout(400,
                                        yaxis=dict(title="Horas de parada", gridcolor="#E6EBED", zeroline=False, range=[0, 100]),
                                        yaxis2=dict(title="% acumulado", overlaying="y", side="right", range=[0, 110], showgrid=False)))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Color de las barras: ámbar para E1, verde azulado para E2, gris para causas no intervenidas.")

# =========================================================
# VISTA 3: SENSIBILIDAD Y EQUILIBRIO
# =========================================================
elif menu_seleccion == "Sensibilidad y Equilibrio (m*)":
    st.subheader("Sensibilidad (Tabla 3 v9) y punto de equilibrio m*")

    kpi_strip([
        ("Inspección de equilibrio m*(d, h)", f"{res['m_star']:.2f} min", f"Exacto: {res['m_star']:.4f} min por turno-máquina", ""),
        ("Detección mínima para Dmec ≥ 95%", f"{res['d_meta_95']*100:.1f}%", f"Con T = {res['T']:,.1f} h", ""),
        ("Detección para igualar la Dmec de E1", f"{res['d_igual_E1']*100:.1f}%", f"P₂(d) = P₁ = {res['E1']['P']:.1f} h", ""),
    ])

    col_s1, col_s2 = st.columns([1.0, 1.15], gap="large")
    with col_s1:
        st.markdown("#### Sensibilidad de ΔL = L₁ − L₂ (horas)")
        st.caption("Verde: favorece E2. Rojo: favorece E1.")
        df_t3 = generar_tabla3_sensibilidad()
        cols_dl = [c for c in df_t3.columns if c.startswith("ΔL")]

        def _color_dl(v):
            if v > 0:
                return "background-color:#DDF0EC;color:#14574D;font-weight:600"
            if v < 0:
                return "background-color:#F8E1DD;color:#8A2C20;font-weight:600"
            return ""

        sty = df_t3.style.format({c: "{:+.1f}" for c in cols_dl})
        sty = (sty.map if hasattr(sty, "map") else sty.applymap)(_color_dl, subset=cols_dl)
        st.dataframe(sty, use_container_width=True, hide_index=True)

        st.markdown("#### Sensibilidad del denominador T (E0)")
        P0 = PAR["P0"]
        df_t = pd.DataFrame([
            {"Variación de T": lab, "T supuesto (h-máquina)": f"{tv:,.1f}", "D mecánica de E0 (%)": (tv - P0) / tv * 100.0}
            for lab, tv in [("−10%", T_REF * 0.9), ("Referencia", T_REF), ("+10%", T_REF * 1.1)]
        ])
        st.dataframe(df_t, use_container_width=True, hide_index=True,
                     column_config={"D mecánica de E0 (%)": st.column_config.NumberColumn(format="%.2f")})

    with col_s2:
        st.markdown(f"#### Curva de equilibrio L₂(m) frente a L₁ (d = {d_pct}%, h = {h_hora:.1f} h)")
        m_grid = np.linspace(0, 12, 100)
        L2_grid = [calcular_modelo_v9(d=d_pct / 100.0, m=v, h=h_hora, T=T_val)["E2"]["L"] for v in m_grid]
        L1_const = res["E1"]["L"]
        m_star = res["m_star"]

        fig = go.Figure()
        if m_star > 0:
            fig.add_vrect(x0=0, x1=min(m_star, 12), fillcolor=TEAL_MID, opacity=0.10, line_width=0,
                          annotation_text="E2 conviene", annotation_position="top left",
                          annotation_font=dict(size=11, color=TEAL))
        fig.add_trace(go.Scatter(x=m_grid, y=L2_grid, mode="lines", name="L₂(m), inspección con alerta",
                                 line=dict(color=TEAL, width=3)))
        fig.add_trace(go.Scatter(x=[0, 12], y=[L1_const, L1_const], mode="lines", name=f"L₁, preventivo fijo ({L1_const:.1f} h)",
                                 line=dict(color=AMBER, width=2.5, dash="dash")))
        if 0 <= m_star <= 12:
            fig.add_trace(go.Scatter(x=[m_star], y=[L1_const], mode="markers+text", name=f"Equilibrio m* = {m_star:.2f} min",
                                     marker=dict(size=13, color=YELLOW, symbol="diamond", line=dict(width=2, color=INK)),
                                     text=[f"m* = {m_star:.2f} min"], textposition="top right"))
        if 0 <= m_min <= 12:
            L2_actual = res["E2"]["L"]
            fig.add_trace(go.Scatter(x=[m_min], y=[L2_actual], mode="markers", name=f"Valor actual m = {m_min:.1f} min",
                                     marker=dict(size=11, color="#FFFFFF", line=dict(width=2.5, color=CORAL))))
        if m_star <= 0:
            fig.add_annotation(text="Con estos d y h, E1 conviene para cualquier m ≥ 0", xref="paper", yref="paper",
                               x=0.01, y=0.98, showarrow=False, font=dict(size=11, color=CORAL), xanchor="left")
        fig.update_layout(**base_layout(430,
                                        xaxis=dict(title="Duración de inspección m (min por turno-máquina)", showgrid=False, linecolor=LINE),
                                        yaxis=dict(title="Balance total de horas Lᵢ (h)", gridcolor="#E6EBED", zeroline=False)))
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# VISTA 4: DATOS DE CAMPO
# =========================================================
elif menu_seleccion == "Datos Campo (Google Sheets)":
    st.subheader("Registro operativo de checklists LUP-01")
    c_info, c_btn = st.columns([3, 1])
    with c_info:
        st.write(
            "Los registros enviados por los operarios mediante el código QR se muestran aquí. "
            "De acuerdo con la Guía v9, los parámetros del modelo (T, N, d, m, h) se mantienen aislados como supuestos de evaluación."
        )
    with c_btn:
        st.link_button("Abrir formulario QR", URL_FORMS_DEFAULT, use_container_width=True)

    st.divider()
    if gs_conectado and not df_gs.empty:
        st.success(f"Conexión activa con Google Sheets: {len(df_gs)} registros recibidos.")
        st.dataframe(df_gs, use_container_width=True)
    elif gs_conectado:
        st.info("La hoja está conectada y aún no tiene registros desde planta.")
    else:
        st.warning("No se pudo leer la hoja. Revisa que esté publicada como CSV y que la URL de la barra lateral sea correcta.")

# =========================================================
# VISTA 5: ECUACIONES Y REPORTE PDF
# =========================================================
elif menu_seleccion == "Ecuaciones & Reporte PDF":
    st.subheader("Formulación matemática (artículo v9)")

    st.markdown(r"""
    **1. Calendario supuesto y disponibilidad mecánica:**
    $$T = 192 \times 8 \times 3 = 4,608\text{ h-máquina} \qquad N = 192 \times 3 = 576\text{ turnos-máquina}$$
    $$D_{\text{mec}, i} = \left(\frac{T - P_i}{T}\right) \times 100$$

    **2. Balance de horas por política ($L_i$):**
    $$L_i = P_i + H_i \qquad \Delta L = L_1 - L_2$$
    * **Escenario $E_0$ (Referencia):** $P_0 = 250\text{ h}$, $H_0 = 0\text{ h}$, $L_0 = 250\text{ h}$.
    * **Escenario $E_1$ (Preventivo fijo):** $3 \times \lfloor 1,536 / 120 \rfloor = 36\text{ intervenciones}$; $P_1 = 250 - 76 = 174\text{ h}$; $H_1 = 36h$; $L_1 = 174 + 36h$.
    * **Escenario $E_2$ (Inspección con alerta):** $P_2(d) = 250 - 100d$; $H_2(d,m,h) = \frac{576m}{60} + 34dh = 9.6m + 34dh$; $L_2 = 250 - 100d + 9.6m + 34dh$.

    **3. Ecuación de sensibilidad y punto de equilibrio ($m^*$):**
    $$\Delta L = 100d - 76 + (36 - 34d)h - \frac{576m}{60}$$
    $$m^*(d,h) = \frac{100d - 76 + (36 - 34d)h}{9.6}$$
    """)

    st.divider()
    st.subheader("Informe ejecutivo en PDF")
    pdf_bytes = generar_reporte_pdf(res, escenario_sel, total_lup)
    st.download_button(
        label="Descargar reporte analítico v9 (PDF)",
        data=pdf_bytes,
        file_name=f"Reporte_Mantenimiento_MIG_v9_{clave_esc}.pdf",
        mime="application/pdf",
    )
