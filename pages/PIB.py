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

    # Filtrado de datos por país
    countries = df['Country Name'].unique()
    selected_countries = st.multiselect('Seleccione los países para visualizar', countries)

    if selected_countries:
        filtered_df = df[df['Country Name'].isin(selected_countries)]
        st.write(filtered_df)
    else:
        filtered_df = df
        st.write(filtered_df)

    range = list(range(1960, 2024))

    st.bar_chart(df, x="Country Name", y='1960', horizontal=True)