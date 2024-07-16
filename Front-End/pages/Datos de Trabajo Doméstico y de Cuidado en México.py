import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis
from io import StringIO

# Configuración de Redis
redis_host = "redis"
redis_port = 6379
data_key = "data"
# Conectar a Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Título de la aplicación
st.title('Datos de Trabajo Doméstico y de Cuidado en México')

# URL del backend
backend_url = "http://Backend:5000/get_data_trabajo_domestico"

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
        data = redis_client.get(data_key)
        if data:
            st.info("Mostrando datos de Redis")
            redis_df = pd.read_json(StringIO(data), orient='split', encoding='utf-8')
        else:
            redis_df = pd.DataFrame()
            st.info("No hay datos en Redis")
    else:
        st.warning("Redis no está disponible. Intentando cargar datos desde el backend")
        redis_df = pd.DataFrame()

    try:
        response = requests.get(backend_url)
        response.raise_for_status()
        data = response.json()
        backend_df = pd.DataFrame(data)

        if not redis_df.empty:
            # Asegurarse de que ambos DataFrames tengan las mismas columnas
            common_columns = redis_df.columns.intersection(backend_df.columns)
            redis_df = redis_df[common_columns]
            backend_df = backend_df[common_columns]

            # Se identifica filas editadas
            updated_df = pd.merge(backend_df, redis_df, on=common_columns.tolist(), how='outer', indicator=True)
            updated_df = updated_df[updated_df['_merge'] == 'left_only'].drop(columns=['_merge'])

            if not updated_df.empty:
                # Reemplazar filas editadas en Redis
                redis_df.update(updated_df)
                # Guardar datos actualizados en Redis
                redis_client.set(data_key, redis_df.to_json(orient='split'))
                st.info("Datos actualizados en Redis")
                return redis_df
            else:
                st.info("No hay datos nuevos ni editados para actualizar en Redis")
                return redis_df
        else:
            if redis_available:
                redis_client.set(data_key, backend_df.to_json(orient='split'))
                st.info("Datos guardados en Redis por primera vez")
            return backend_df

    except requests.RequestException:
        st.error("No se pudo obtener datos del backend ni de Redis")
        if not redis_df.empty:
            st.info("Mostrando datos de Redis almacenados previamente")
            return redis_df
        else:
            return None

# Botón para refrescar los datos
if st.button('Refrescar Datos'):
    st.experimental_rerun()

# Obtiene los datos del backend o desde Redis
df = load_data()

# Mostrar la tabla
if df is not None:
    st.write("Datos Completos:")
    st.dataframe(df)

# Filtrado de datos por periodo
if df is not None:
    if 'Periodo' in df.columns:
        df['Periodo'] = df['Periodo'].astype(str).str.replace(',', '').astype(int)

        periodos = df['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['Periodo'] == selected_period]

        if 'Entidad federativa' in df.columns:
            selected_states = st.multiselect('Seleccione las entidades federativas para comparar',
                                             filtered_df['Entidad federativa'].unique())

            if selected_states:
                comparison_df = filtered_df[filtered_df['Entidad federativa'].isin(selected_states)]
            else:
                comparison_df = pd.DataFrame(columns=df.columns)

            # Genera los gráficos comparativos si hay entidades seleccionadas
            if not comparison_df.empty:
                st.subheader('Comparación de Entidades Seleccionadas')

                # Verificar si las columnas necesarias existen y no están vacías
                if 'Horas Domesticas y Cuidado' in comparison_df.columns and not comparison_df['Horas Domesticas y Cuidado'].isnull().all():
                    fig = px.pie(comparison_df, names='Entidad federativa', values='Horas Domesticas y Cuidado',
                                 title='Horas a actividades domésticas y de cuidado')
                    st.plotly_chart(fig)
                else:
                    st.warning("No hay datos suficientes para 'Horas Domésticas y Cuidado'.")

                if 'Tasa Trabajo Domestico' in comparison_df.columns and not comparison_df['Tasa Trabajo Domestico'].isnull().all():
                    fig2 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Domestico',
                                  title='Participación en trabajo doméstico no remunerado')
                    st.plotly_chart(fig2)
                else:
                    st.warning("No hay datos suficientes para 'Tasa Trabajo Doméstico'.")

                if 'Tasa Trabajo Cuidado' in comparison_df.columns and not comparison_df['Tasa Trabajo Cuidado'].isnull().all():
                    fig3 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Cuidado',
                                  title='Participación en trabajo no remunerado de cuidado')
                    st.plotly_chart(fig3)
                else:
                    st.warning("No hay datos suficientes para 'Tasa Trabajo Cuidado'.")

                # Tabla comparativa de las entidades seleccionadas
                st.write('Tabla Comparativa de Entidades Seleccionadas')
                st.dataframe(comparison_df)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Entidad federativa' no se encuentra en el archivo CSV.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el archivo CSV.")
