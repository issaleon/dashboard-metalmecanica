Tablero de mantenimiento de soldadoras MIG (Modelo v9)

Tablero interactivo que compara dos políticas de mantenimiento en una celda de soldadura MIG de una pyme metalmecánica peruana (equipos EQ-01, EQ-02 y EQ-03): el preventivo fijo (E1) y la inspección con alerta (E2), frente a la situación de referencia (E0). La comparación se hace con un balance de horas: Lᵢ = Pᵢ + Hᵢ.

Acompaña al artículo del Proyecto de Investigación Aplicada 1 (UPC) y reproduce sus Tablas 1, 2 y 3.

Qué calcula
Tabla 1: distribución referencial de paradas (85 eventos y 250 h). De ella se derivan las constantes del modelo.
Tabla 2: Pᵢ, Hᵢ, disponibilidad mecánica y Lᵢ para E0, E1 y E2.
Tabla 3: sensibilidad de ΔL = L₁ − L₂ frente a la detección d, la inspección m y la intervención h.
Punto de equilibrio m*: duración de inspección a partir de la cual conviene E1 en lugar de E2.
Módulos
Comparativa (E0, E1, E2): indicadores, veredicto y composición del balance de horas.
Causas de parada (Tabla 1): Pareto de horas por causa y agrupación por política.
Sensibilidad y equilibrio (m*): Tabla 3, sensibilidad de T y curva de equilibrio.
Datos campo (Google Sheets): registros de los checklists LUP-01 enviados desde planta por código QR.
Ecuaciones y reporte PDF: formulación del modelo y exportación de un informe ejecutivo.
Tecnologías
Python 3.10 o superior
Streamlit, con streamlit-option-menu para la navegación
Pandas y NumPy
Plotly (Graph Objects)
Google Forms y Google Sheets (CSV publicado)
FPDF2 para el reporte en PDF
Estructura del repositorio
codigo.py: código fuente del tablero.
requirements.txt: dependencias para el despliegue.
README.md: esta documentación.
Ejecución local
bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd <carpeta-del-repositorio>

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Lanzar la aplicación
streamlit run codigo.py
Despliegue en Streamlit Community Cloud

Streamlit busca un archivo llamado exactamente requirements.txt en la raíz del repositorio y codigo.py como archivo principal.
