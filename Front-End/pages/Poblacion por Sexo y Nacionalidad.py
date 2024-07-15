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
st.title('Poblacion por Sexo y Nacionalidad')

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

# Filtrado de datos por periodo
if df is not None:
    if 'Periodo' in df.columns:
        df['Periodo'] = df['Periodo'].astype(str).str.replace(',', '')  # Remover comas
        periodos = df['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['Periodo'] == selected_period]

        # Mostrar las columnas del DataFrame filtrado
        st.write("Columnas en filtered_df:", filtered_df.columns)

        # Verifica si la columna 'Nacionalidad' está presente
        if 'Nacionalidad' in filtered_df.columns:
            # Selección de múltiples nacionalidades para comparación
            selected_nacionalidades = st.multiselect('Seleccione las nacionalidades para comparar', filtered_df['Nacionalidad'].unique())

            if selected_nacionalidades:
                comparison_df = filtered_df[filtered_df['Nacionalidad'].isin(selected_nacionalidades)]
            else:
                comparison_df = pd.DataFrame(columns=df.columns)

            # Generar gráfico de pastel si hay datos seleccionados
            if not comparison_df.empty:
                st.subheader('Total de población por nacionalidad')

                fig = px.pie(comparison_df, values='Total', names='Nacionalidad', title='Distribución de la población total por nacionalidad')
                st.plotly_chart(fig)

                st.subheader('Total de población por nacionalidad')
                fig2 = px.bar(comparison_df, x='Nacionalidad', y='Total', title='Total de población por nacionalidad')
                st.plotly_chart(fig2)

                st.subheader('Evolución de la Población en el Tiempo')
                fig3 = px.pie(comparison_df, values='Total', names='Nacionalidad', title=f'Evolución de la población en el período {selected_period}')
                st.plotly_chart(fig3)

                # Mostrar tabla comparativa sin comas en la columna 'Periodo'
                st.write('Tabla Comparativa de Nacionalidades Seleccionadas')
                comparison_df_display = comparison_df.copy()
                comparison_df_display['Periodo'] = comparison_df_display['Periodo'].astype(str).str.replace(',', '')
                st.write(comparison_df_display)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Nacionalidad' no se encuentra en el DataFrame filtrado.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el DataFrame.")
else:
    st.error("Error al obtener los datos.")
