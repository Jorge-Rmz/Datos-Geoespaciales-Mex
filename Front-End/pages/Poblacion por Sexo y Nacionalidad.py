import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis
from io import StringIO

redis_host = "redis"
redis_port = 6379

# Conectar a Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Título de la aplicación
st.title('Población por Sexo y Nacionalidad')

# URL del backend
backend_url = "http://Backend:5000/get_poblacion_data"

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

        # Elimina o comenta la siguiente línea para no mostrar las columnas del DataFrame filtrado
        # st.write("Columnas en filtered_df:", filtered_df.columns)

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

# Formulario para agregar nuevo registro
st.subheader("Agregar Nuevo Registro")

with st.form(key='add_record_form'):
    sexo = st.selectbox('Sexo', options=['Masculino', 'Femenino'])
    nacionalidad = st.text_input('Nacionalidad')
    periodo = st.text_input('Periodo')
    total = st.number_input('Total', min_value=0)

    submit_button = st.form_submit_button(label='Agregar Registro')

    if submit_button:
        new_data = {
            "Sexo": sexo,
            "Nacionalidad": nacionalidad,
            "Periodo": periodo,
            "Total": total
        }

        # Llamada a la API para agregar el nuevo registro
        response = requests.post("http://Backend:5000/post_poblacion", json=new_data)

        if response.status_code == 200:
            st.success("Registro agregado correctamente")
            # Actualiza los datos en Redis
            redis_client.set('poblacion_data', df_poblacion.to_json(orient='split'))
        else:
            st.error(f"Error al agregar registro: {response.json().get('error')}")

# Mostrar la tabla actualizada
if df_poblacion is not None:
    st.write("Datos Actualizados:")
    st.dataframe(df_poblacion)


# Opción para editar un registro existente
st.subheader("Editar Registro Existente")

# Seleccionar el registro a editar
nacionalidad_edit = st.selectbox('Selecciona la Nacionalidad a Editar:', df_poblacion['Nacionalidad'].unique())
periodo_edit = st.selectbox('Selecciona el Periodo a Editar:', df_poblacion['Periodo'].unique())

# Filtrar el DataFrame para obtener el registro específico
registro_edit = df_poblacion[
    (df_poblacion['Nacionalidad'] == nacionalidad_edit) & (df_poblacion['Periodo'] == periodo_edit)]

if not registro_edit.empty:
    row = registro_edit.iloc[0]

    sexo_edit = st.selectbox('Sexo', options=['Masculino', 'Femenino'], index=0 if row['Sexo'] == 'Masculino' else 1)
    total_edit = st.number_input('Total', min_value=0, value=int(row['Total']))

    if st.button('Actualizar Registro'):
        updated_data = {
            "Sexo": sexo_edit,
            "Nacionalidad": nacionalidad_edit,
            "Periodo": periodo_edit,
            "Total": total_edit
        }

        # Llamada a la API para editar el registro
        response = requests.post("http://Backend:5000/post_poblacion", json=updated_data)

        if response.status_code == 200:
            st.success("Registro actualizado correctamente")
            # Actualiza los datos en Redis
            redis_client.set('poblacion_data', df_poblacion.to_json(orient='split'))
        else:
            st.error(f"Error al actualizar registro: {response.json().get('error')}")
else:
    st.warning("No se encontró el registro seleccionado.")