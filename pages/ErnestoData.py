import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px

# Título de la aplicación
st.title('Visualizador de datos del PIB en el mundo')

# Cargar el archivo CSV con datos del PIB
file_path = "datos/pibdata.csv"

if file_path is not None:
    df = pd.read_csv(file_path)
    st.write(df)

    # Filtrado de datos por región
    regiones = df['region'].unique()
    selected_regions = st.multiselect('Seleccione las regiones para visualizar', regiones)

    if selected_regions:
        filtered_df = df[df['region'].isin(selected_regions)]
    else:
        filtered_df = df

    # Filtrado de datos por país
    min_population, max_population = st.slider('Rango de población', min_value=int(df['poblacion'].min()), max_value=int(df['poblacion'].max()), value=(int(df['poblacion'].min()), int(df['poblacion'].max())))
    filtered_df = filtered_df[(filtered_df['poblacion'] >= min_population) & (filtered_df['poblacion'] <= max_population)]

    # Selección de múltiples países para comparación
    selected_states = st.multiselect('Seleccione los estados para comparar', filtered_df['estado'].unique())

    if selected_states:
        comparison_df = filtered_df[filtered_df['estado'].isin(selected_states)]
    else:
        comparison_df = pd.DataFrame(columns=df.columns)
