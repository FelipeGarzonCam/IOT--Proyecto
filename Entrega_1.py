import os
import streamlit as st
import pandas as pd
import polars as pl
import matplotlib.pyplot as plt

# Obtener el directorio del archivo .py actual y construir la ruta completa al CSV
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "SensoresIOT.csv")

# Leer los datos desde el CSV
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

# Agrupar por Timestamp y calcular la media de cada sensor escalado

# Sensor Infrarrojo escalado
valor_SI_scaled = datos.group_by("Timestamp (seg)").agg(
    pl.col("Sensor Infrarrojo (ADC)_scaled").mean().alias("sensor_infrarrojo_escalado")
).sort("sensor_infrarrojo_escalado", descending=True)

fig1, ax1 = plt.subplots()
ax1.scatter(valor_SI_scaled["Timestamp (seg)"].to_list(), valor_SI_scaled["sensor_infrarrojo_escalado"].to_list())
ax1.set_xlabel("Tiempo")
ax1.set_ylabel("Valor sensor escalado (Min-Max)")
ax1.set_title("Sensor Infrarrojo Escalado (Min-Max)")
plt.xticks(rotation=20)
st.pyplot(fig1)

# Sensor Ultrasonico escalado
valor_SU_scaled = datos.group_by("Timestamp (seg)").agg(
    pl.col("Sensor Ultrasonico (cm)_scaled").mean().alias("sensor_ultrasonico_escalado")
).sort("sensor_ultrasonico_escalado", descending=True)

fig2, ax2 = plt.subplots()
ax2.scatter(valor_SU_scaled["Timestamp (seg)"].to_list(), valor_SU_scaled["sensor_ultrasonico_escalado"].to_list())
ax2.set_xlabel("Tiempo")
ax2.set_ylabel("Valor sensor escalado (Min-Max)")
ax2.set_title("Sensor Ultrasonico Escalado (Min-Max)")
plt.xticks(rotation=20)
st.pyplot(fig2)

# Sensor de Presion escalado (Galga)
valor_galga_scaled = datos.group_by("Sensor de Presion (valor calibrado)_scaled").agg(
    pl.col("Timestamp (seg)").mean().alias("sensor_galga_escalado")
).sort("sensor_galga_escalado", descending=True)

fig3, ax3 = plt.subplots()
ax3.scatter(valor_galga_scaled["Sensor de Presion (valor calibrado)_scaled"].to_list(), valor_galga_scaled["sensor_galga_escalado"].to_list())
ax3.set_xlabel("Tiempo")
ax3.set_ylabel("Valor sensor escalado (Min-Max)")
ax3.set_title("Sensor Galga Escalado (Min-Max)")
plt.xticks(rotation=20)
st.pyplot(fig3)
