import streamlit as st
import pandas as pd
import plotly.express as px
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
st.title('Datos de Trabajo Doméstico y de Cuidado en México')

# Ruta del archivo CSV
file_path = "Back-End/datos/ssdp02a_por_trab_dom_cui.csv"

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path, encoding='latin1')

        # Renombra las columnas
        df.rename(columns={
            'Suma de porcentajes del total de horas por semana dedicados a actividades domésticas y de cuidado que realizan los integrantes del hogar de 12 y más años': 'Horas Domésticas y Cuidado',
            'Tasa de participación de la población de 12 años y más en trabajo doméstico no remunerado para el propio hogar': 'Tasa Trabajo Doméstico',
            'Tasa de participación de la población de 12 años y más en trabajo no remunerado de cuidado a integrantes del hogar': 'Tasa Trabajo Cuidado'
        }, inplace=True)

        # Almacena en Redis
        redis_client.set('data', df.to_json(orient='split'))

        st.write(df.head())

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

                # Gráfico circular del porcentaje de horas dedicadas a actividades domésticas y de cuidado
                if 'Horas Domésticas y Cuidado' in df.columns:
                    fig = px.pie(comparison_df, names='Entidad federativa', values='Horas Domésticas y Cuidado',
                                 title='Horas a actividades domésticas y de cuidado')
                    st.plotly_chart(fig)

                # Gráfico circular de la tasa de participación en trabajo doméstico no remunerado
                if 'Tasa Trabajo Doméstico' in df.columns:
                    fig2 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Doméstico',
                                  title='Participación en trabajo doméstico no remunerado')
                    st.plotly_chart(fig2)

                # Gráfico circular de la tasa de participación en trabajo no remunerado de cuidado
                if 'Tasa Trabajo Cuidado' in df.columns:
                    fig3 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Cuidado',
                                  title='Participación en trabajo no remunerado de cuidado')
                    st.plotly_chart(fig3)

                # Tabla comparativa de las entidades seleccionadas
                st.write('Tabla Comparativa de Entidades Seleccionadas')
                st.write(comparison_df)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Entidad federativa' no se encuentra en el archivo CSV.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el archivo CSV.")
