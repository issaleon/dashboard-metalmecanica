# Dashboard de Control Operativo OEE - Celda de Soldadura MIG

Sistema de monitoreo de indicadores de mantenimiento (Disponibilidad, MTBF, MTTR) y captura de datos en tiempo real mediante integración Nube (Google Forms / Google Sheets).

## 🚀 Descripción del Proyecto
Este repositorio contiene el artefacto digital desarrollado para optimizar la disponibilidad mecánica y reducir tiempos de cambio (setup) en una celda de soldadura MIG (unidades `EQ-01`, `EQ-02`, `EQ-03`) perteneciente a una empresa del sector metalmecánico en Perú.

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3.10+
* **Framework Web:** Streamlit
* **Visualización Analítica:** Plotly Express & Graph Objects
* **Base de Datos Nube:** Google Sheets (CSV Endpoint) & Google Forms (QR Code)
* **Reportabilidad:** FPDF2

## 📂 Estructura del Repositorio
* `codigo.py`: Código fuente principal del tablero interactivo.
* `requirements (1).txt`: Lista de librerías y dependencias necesarias para el despliegue.
* `README.md`: Documentación técnica del proyecto.

## 📊 Módulos del Sistema
1. **Visión General OEE:** Métricas principales en vivo, tacómetro de disponibilidad y matriz de diagnóstico Andón.
2. **Análisis de Paradas:** Diagrama de Pareto 80/20 (causa-raíz) y análisis de horas improductivas por máquina.
3. **Datos Campo (Google Sheets):** Trazabilidad transaccional de inspecciones autónomas LUP-01 enviadas desde la planta vía QR.
4. **Plan & Reporte PDF:** Matriz estratégica TPM/SMED y generación de informes ejecutivos descargables.

## ⚙️ Instrucciones de Ejecución Local
```bash
# 1. Clonar repositorio
git clone [https://github.com/tu-usuario/dashboard-oee-metalmecanica.git](https://github.com/tu-usuario/dashboard-oee-metalmecanica.git)

# 2. Instalar librerías
pip install -r requirements (1).txt

# 3. Lanzar aplicación
streamlit run codigo.py
