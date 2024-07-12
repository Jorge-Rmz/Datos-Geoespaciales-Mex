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
st.title('Visualizador de población por sexo y nacionalidad')

# Ruta del archivo CSV
file_path = "Back-End/datos/66375.csv"

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path, encoding='utf-8', delimiter=';', thousands=',')

        # Almacena en Redis
        redis_client.set('data', df.to_json(orient='split'))

        st.write(df.head())
        st.write("Columnas del DataFrame después de cargar el CSV:", df.columns)

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
