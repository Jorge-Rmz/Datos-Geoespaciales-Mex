import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import requests
import redis
import json

# URL de la API Flask
api_url = "http://127.0.0.1:5000"
data_key = 'geospatial_data1'
file_path = "Back-End/datos/data.csv"

# Conectar a Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Título de la aplicación
st.title('Visualizador de Datos Geoespaciales - Estados de México')

def load_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    r.set(data_key, json.dumps(df.to_dict(orient='records')))
    st.write("Datos cargados desde el archivo CSV y guardados en Redis")
    return df

def load_data_from_redis():
    if r.exists(data_key):
        df = pd.DataFrame(json.loads(r.get(data_key)))
        st.success("Datos cargados desde Redis")
        return df
    else:
        st.error("Datos no encontrados en Redis")
        return None

def load_data():
    try:
        # Verificar si los datos están en la API
        response = requests.get(f"{api_url}/api/get_data")

        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.success("Datos cargados desde la API Flask")
            return df
        else:
            return load_data_from_redis()

    except requests.exceptions.ConnectionError:
        st.error("No se pudo conectar a la API Flask. Intentando cargar desde Redis...")
        return load_data_from_redis()
    except FileNotFoundError:
        st.error("El archivo CSV no se encontró. Por favor, verifica la ruta del archivo.")
        return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP: {http_err}")
        return None
    except Exception as e:
        st.error(f"Se produjo un error inesperado: {e}")
        return None

df = load_data()

if df is not None:
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
else:
    # Si no hay datos, intenta cargar desde el CSV
    st.error("Cargando datos desde el archivo CSV")
    df = load_data_from_csv(file_path)

    if df is not None:
        st.write(df)
