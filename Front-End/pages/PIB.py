import streamlit as st
import pandas as pd
import requests
import redis
from io import StringIO

redis_host = "redis"
redis_port = 6379

# Conectar a Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Título de la aplicación
st.title('PIB')

# URL del backend
backend_url = "http://Backend:5000/get_pib_data"


# Función para verificar si Redis está disponible
def is_redis_available():
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False


# Función para cargar los datos desde el backend o Redis
def load_data():
    redis_available = is_redis_available()

    if redis_available:
        st.success("Conectado a Redis")
        data = redis_client.get('data')
        if data:
            st.info("Mostrando datos de Redis")
            return pd.read_json(StringIO(data), orient='split')
        else:
            st.info("Intentando cargar datos desde el backend")
    else:
        st.warning("Redis no está disponible. Intentando cargar datos desde el backend")

    try:
        response = requests.get(backend_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        # Almacena datos en Redis si está disponible
        if redis_available:
            redis_client.set('data', df.to_json(orient='split'))
        st.info("Mostrando datos del backend")
        return df
    except requests.RequestException:
        st.error("No se pudo obtener datos del backend ni de Redis")
        return None


# Obtiene los datos del backend o desde Redis
df = load_data()

if df is not None:
    # Filtrado de datos por país
    countries = df['Country Name'].unique()
    selected_countries = st.multiselect('Seleccione los países para visualizar', countries)

    if selected_countries:
        filtered_df = df[df['Country Name'].isin(selected_countries)]
        st.write(filtered_df)
    else:
        filtered_df = df
        st.write(filtered_df)

    # Lista de años
    range = list(range(1961, 2024))

    # Selección del año
    selected = st.selectbox("Año", range, index=0)

    # Gráfica de PIB en el mundo por Año
    st.bar_chart(df, x="Country Name", y=str(selected), horizontal=True)