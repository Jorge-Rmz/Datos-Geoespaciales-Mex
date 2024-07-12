import streamlit as st
import pandas as pd
import redis
from io import StringIO

# Conecta a Redis
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()  # Verifica la conexión
    st.success("Conectado a Redis")
except redis.ConnectionError as e:
    st.error(f"No se pudo conectar a Redis: {e}")

# Título de la aplicación
st.title('Visualizador de datos del PIB en el mundo')

# Cargar el archivo CSV con datos del PIB
file_path = "Back-End/datos/pibdata.csv"

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path)

        # Almacena en Redis
        redis_client.set('data', df.to_json(orient='split'))

        st.write(df)

        return df

    except FileNotFoundError:
        st.error(f"El archivo {file_path} no se encontró. Asegúrate de que el archivo está en el directorio correcto.")
    except pd.errors.ParserError:
        st.error(f"Hubo un error al intentar parsear el archivo {file_path}. Verifica el formato del archivo CSV.")
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        return None

def get_data():
    try:
        data = redis_client.get('data')
        if data:
            df = pd.read_json(StringIO(data), orient='split')
            return df
        else:
            return load_data()
    except redis.ConnectionError as e:
        st.error(f"No se pudo conectar a Redis para obtener los datos: {e}")
        return load_data()

# Obtiene los datos de Redis o los carga si no existen
df = get_data()

if df is not None:
    df = pd.read_csv(file_path)

    # Filtrado de datos por país
    countries = df['Country'].unique()
    selected_countries = st.multiselect('Seleccione los países para visualizar', countries)

    if selected_countries:
        filtered_df = df[df['Country'].isin(selected_countries)]
        st.write(filtered_df)
    else:
        filtered_df = df
        st.write(filtered_df)

    # Lista de años
    range = list(range(1961, 2024))

    # Selección del año
    selected = st.selectbox("Año", range, index=0)

    # Gráfica de PIB en el mundo por Año
    st.bar_chart(df, x="Country", y=str(selected), horizontal=True)