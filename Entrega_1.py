import os
import streamlit as st
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

# Configuración inicial de la página para un mejor estilo
st.set_page_config(page_title="Dashboard de Sensores IoT", layout="wide")
st.markdown(
    """
    <style>
    .main {
        background-color: #2E86AB; /* Fondo azul */
    }
    .titulo {
        font-size: 40px;
        color: #FFFFFF; /* Texto blanco */
        text-align: center;
        font-weight: bold;
    }
    .subtitulo {
        font-size: 20px;
        color: #FFFFFF; /* Texto blanco */
        text-align: center;
    }
    .analisis {
        background-color: #E8F6F3;
        border-left: 5px solid #2E86AB;
        padding: 10px;
        margin-bottom: 20px;
        color: #333333; /* Texto oscuro para el análisis */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Título principal
st.markdown('<div class="titulo">Dashboard de Sensores IoT</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">Análisis de datos y comportamiento de cada sensor</div>', unsafe_allow_html=True)
st.markdown("---")

# Obtener el directorio del archivo .py actual y construir la ruta completa al CSV
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "SensoresIOT.csv")

# Leer los datos desde el CSV utilizando polars
datos = pl.read_csv(csv_path)

# Calcular min y max para cada columna a escalar
si_min = datos["Sensor Infrarrojo (ADC)"].min()
si_max = datos["Sensor Infrarrojo (ADC)"].max()

su_min = datos["Sensor Ultrasonico (cm)"].min()
su_max = datos["Sensor Ultrasonico (cm)"].max()

sp_min = datos["Sensor de Presion (valor calibrado)"].min()
sp_max = datos["Sensor de Presion (valor calibrado)"].max()

# Crear nuevas columnas escaladas (Min-Max Scaling)
datos = datos.with_columns([
    ((pl.col("Sensor Infrarrojo (ADC)") - si_min) / (si_max - si_min)).alias("Sensor Infrarrojo (ADC)_scaled"),
    ((pl.col("Sensor Ultrasonico (cm)") - su_min) / (su_max - su_min)).alias("Sensor Ultrasonico (cm)_scaled"),
    ((pl.col("Sensor de Presion (valor calibrado)") - sp_min) / (sp_max - sp_min)).alias("Sensor de Presion (valor calibrado)_scaled")
])

# Gráfico 1: Sensor Infrarrojo escalado
valor_SI_scaled = datos.group_by("Timestamp (seg)").agg(
    pl.col("Sensor Infrarrojo (ADC)_scaled").mean().alias("sensor_infrarrojo_escalado")
).sort("sensor_infrarrojo_escalado", descending=True)

fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.scatter(valor_SI_scaled["Timestamp (seg)"].to_list(), valor_SI_scaled["sensor_infrarrojo_escalado"].to_list(), color="#2E86AB", alpha=0.7)
ax1.set_xlabel("Tiempo (seg)", fontsize=12)
ax1.set_ylabel("Valor Sensor Escalado", fontsize=12)
ax1.set_title("Sensor Infrarrojo Escalado (Min-Max)", fontsize=14)
plt.xticks(rotation=20)
st.pyplot(fig1)

# Análisis para Sensor Infrarrojo
st.markdown(
    """
    <div class="analisis">
    <b>Análisis del Sensor Infrarrojo:</b><br>
    La gráfica muestra la variación del valor escalado del sensor infrarrojo a lo largo del tiempo. Se observan picos y posibles anomalías en la detección, lo que ayuda a identificar desviaciones y validar el correcto funcionamiento del sensor.
    </div>
    """, 
    unsafe_allow_html=True
)

# Gráfico 2: Sensor Ultrasonico escalado
valor_SU_scaled = datos.group_by("Timestamp (seg)").agg(
    pl.col("Sensor Ultrasonico (cm)_scaled").mean().alias("sensor_ultrasonico_escalado")
).sort("sensor_ultrasonico_escalado", descending=True)

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.scatter(valor_SU_scaled["Timestamp (seg)"].to_list(), valor_SU_scaled["sensor_ultrasonico_escalado"].to_list(), color="#E67E22", alpha=0.7)
ax2.set_xlabel("Tiempo (seg)", fontsize=12)
ax2.set_ylabel("Valor Sensor Escalado", fontsize=12)
ax2.set_title("Sensor Ultrasonico Escalado (Min-Max)", fontsize=14)
plt.xticks(rotation=20)
st.pyplot(fig2)

# Análisis para Sensor Ultrasonico
st.markdown(
    """
    <div class="analisis">
    <b>Análisis del Sensor Ultrasonico:</b><br>
    Esta gráfica representa la media de los valores escalados del sensor ultrasónico a lo largo del tiempo, permitiendo evaluar la consistencia en las mediciones y detectar fluctuaciones que podrían indicar interferencias o cambios en el entorno.
    </div>
    """, 
    unsafe_allow_html=True
)

# Gráfico 3: Sensor de Presión (Galga) escalado
valor_galga_scaled = datos.group_by("Sensor de Presion (valor calibrado)_scaled").agg(
    pl.col("Timestamp (seg)").mean().alias("sensor_galga_escalado")
).sort("sensor_galga_escalado", descending=True)

fig3, ax3 = plt.subplots(figsize=(10, 4))
ax3.scatter(valor_galga_scaled["Sensor de Presion (valor calibrado)_scaled"].to_list(), valor_galga_scaled["sensor_galga_escalado"].to_list(), color="#27AE60", alpha=0.7)
ax3.set_xlabel("Valor Sensor Escalado", fontsize=12)
ax3.set_ylabel("Tiempo (seg) Promedio", fontsize=12)
ax3.set_title("Sensor de Presión (Galga) Escalado (Min-Max)", fontsize=14)
plt.xticks(rotation=20)
st.pyplot(fig3)

# Análisis para Sensor de Presión (Galga)
st.markdown(
    """
    <div class="analisis">
    <b>Análisis del Sensor de Presión (Galga):</b><br>
    El gráfico permite observar la relación entre los valores escalados de la presión y el tiempo promedio de medición, ayudando a evaluar la estabilidad y precisión del sensor de presión, lo cual es crucial para detectar variaciones en la presión aplicada.
    </div>
    """, 
    unsafe_allow_html=True
)
