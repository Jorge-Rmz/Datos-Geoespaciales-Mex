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
redis_host = "localhost"
redis_port = 6379

redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


def is_redis_available():
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False


def save_data_to_redis(redis_conn, key, df):
    redis_conn.set(key, json.dumps(df.to_dict(orient='records')))


def get_data_from_redis(redis_conn, key):
    if redis_conn.exists(key):
        return pd.DataFrame(json.loads(redis_conn.get(key)))
    return None


def load_data_from_csv(file_path):
    return pd.read_csv(file_path)



# Título de la aplicación
st.title('Visualizador de Datos Geoespaciales - Estados de México')

def load_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    # redis_client.set(data_key, json.dumps(df.to_dict(orient='records')))
    st.write("Datos cargados desde el archivo CSV")
    return df


def load_data_from_redis():
    try:
        if is_redis_available():
            if redis_client.exists(data_key):
                df = pd.DataFrame(json.loads(redis_client.get(data_key)))
                st.success("Datos cargados desde Redis")
                return df
            else:
                save_data_to_redis(redis_client, data_key, pd.read_csv(file_path))
                df = get_data_from_redis(redis_client, data_key)
                st.success("Datos cargados desde Redis")
                return df
        else:
            st.error("No se pudo conectar a Redis. Cargando desde el archivo CSV...")
            return load_data_from_csv(file_path)
    except redis.exceptions.ConnectionError:
        st.error("Error al conectar con Redis. Verifica que Redis esté disponible.")
        return None


def load_data():
    try:
        # Verificar si los datos están en la API
        response = requests.get(f"{api_url}/api/get_poblacion_mex")

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
