import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import requests

# URL de la API Flask
api_url = "http://127.0.0.1:5000"

# Título de la aplicación
st.title('Visualizador de Datos Geoespaciales - Estados de México')

# Verificar si los datos están en la API

try:
    # Verificar si los datos están en la API
    response = requests.get(f"{api_url}/get_data")

    if response.status_code == 200:
        df = pd.DataFrame(response.json())
        st.success("Datos cargados desde Redis")
    else:
        # Cargar el archivo CSV con datos geoespaciales
        file_path = "Back-End/datos/data.csv"
        if file_path is not None:
            df = pd.read_csv(file_path)
            # Guardar los datos en la API
            requests.post(f"{api_url}/update_data", json=df.to_dict(orient='records'))
            st.write("Datos cargados desde el archivo CSV y guardados en la API Flask")

        st.write(df)

except requests.exceptions.ConnectionError:
    st.error("No se pudo conectar a la API. Por favor, asegúrate de que la API Flask esté en funcionamiento.")
except FileNotFoundError:
    st.error("El archivo CSV no se encontró. Por favor, verifica la ruta del archivo.")
except requests.exceptions.HTTPError as http_err:
    st.error(f"Error HTTP: {http_err}")
except Exception as e:
    st.error(f"Se produjo un error inesperado: {e}")

try:
    # Filtrado de datos por región
    regiones = df['region'].unique()
    selected_regions = st.multiselect('Seleccione las regiones para visualizar', regiones)

    if selected_regions:
        filtered_df = df[df['region'].isin(selected_regions)]
    else:
        filtered_df = df

    # Filtrado de datos por población
    min_population, max_population = st.slider('Rango de población', min_value=int(df['poblacion'].min()), max_value=int(df['poblacion'].max()), value=(int(df['poblacion'].min()), int(df['poblacion'].max())))
    filtered_df = filtered_df[(filtered_df['poblacion'] >= min_population) & (filtered_df['poblacion'] <= max_population)]

    # Selección de múltiples estados para comparación
    selected_states = st.multiselect('Seleccione los estados para comparar', filtered_df['estado'].unique())

    if selected_states:
        comparison_df = filtered_df[filtered_df['estado'].isin(selected_states)]
    else:
        comparison_df = pd.DataFrame(columns=df.columns)

    # Crear el mapa base
    m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lon'].mean()], zoom_start=6)

    # Agregar puntos al mapa
    for _, row in filtered_df.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=f"Estado: {row['estado']}<br>Población: {row['poblacion']}"
        ).add_to(m)

    # Mostrar el mapa
    folium_static(m)

    # Generar gráficos comparativos si hay estados seleccionados
    if not comparison_df.empty:
        st.subheader('Comparación de Estados Seleccionados')

        # Gráfico de barras de la población
        fig = px.bar(comparison_df, x='estado', y='poblacion', title='Población de los Estados Seleccionados')
        st.plotly_chart(fig)

        # Gráfico de pie de la población por región
        fig_pie = px.pie(comparison_df, names='region', values='poblacion', title='Distribución de la Población por Región')
        st.plotly_chart(fig_pie)

        # Tabla comparativa de los estados seleccionados
        st.write('Tabla Comparativa de Estados Seleccionados')
        st.write(comparison_df)

except NameError:
    st.error("Error variables vacías")
