import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis
from io import StringIO

redis_host = "localhost"
redis_port = 6379

# Conectar a Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Título de la aplicación
st.title('Población por Sexo y Nacionalidad')

# URL del backend
backend_url = "http://localhost:5000/get_poblacion_data"

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
        data = redis_client.get('poblacion_data')
        if data:
            st.info("Mostrando datos de Redis")
            return pd.read_json(StringIO(data), orient='split')
        else:
            st.info("Intentando cargar datos desde el backend")

    try:
        response = requests.get(backend_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        # Almacena datos en Redis si está disponible
        if redis_available:
            redis_client.set('poblacion_data', df.to_json(orient='split'))
        st.info("Mostrando datos del backend")
        return df
    except requests.RequestException:
        st.error("No se pudo obtener datos del backend ni de Redis")
        return None

# Obtiene los datos del backend o desde Redis
df_poblacion = load_data()

# Mostrar la tabla completa
if df_poblacion is not None:
    st.write("Datos Completos:")
    st.dataframe(df_poblacion)  # Muestra todos los datos

# Filtrado de datos por periodo
if df_poblacion is not None:
    if 'Periodo' in df_poblacion.columns:
        df_poblacion['Periodo'] = df_poblacion['Periodo'].astype(str).str.replace(',', '')
        periodos = df_poblacion['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df_poblacion[df_poblacion['Periodo'] == selected_period]

        if 'Nacionalidad' in filtered_df.columns:
            selected_nacionalidades = st.multiselect('Seleccione las nacionalidades para comparar', filtered_df['Nacionalidad'].unique())

            if selected_nacionalidades:
                comparison_df = filtered_df[filtered_df['Nacionalidad'].isin(selected_nacionalidades)]
            else:
                comparison_df = pd.DataFrame(columns=df_poblacion.columns)

            if not comparison_df.empty:

                st.write('Tabla Comparativa de Nacionalidades Seleccionadas')
                comparison_df_display = comparison_df.copy()
                comparison_df_display['Periodo'] = comparison_df_display['Periodo'].astype(str).str.replace(',', '')
                st.write(comparison_df_display)

                st.subheader('Total de población por nacionalidad')
                fig = px.pie(comparison_df, values='Total', names='Nacionalidad', title='Distribución de la población total por nacionalidad')
                st.plotly_chart(fig)

                fig2 = px.bar(comparison_df, x='Nacionalidad', y='Total', title='Total de población por nacionalidad')
                st.plotly_chart(fig2)

                fig3 = px.pie(comparison_df, values='Total', names='Nacionalidad', title=f'Evolución de la población en el período {selected_period}')
                st.plotly_chart(fig3)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Nacionalidad' no se encuentra en el DataFrame filtrado.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el DataFrame.")
else:
    st.error("Error al obtener los datos.")
