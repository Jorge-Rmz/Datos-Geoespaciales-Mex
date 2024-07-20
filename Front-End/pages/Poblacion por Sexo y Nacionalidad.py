import pickle
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis

redis_host = "redis"
redis_port = 6379
redis_password = ""

data_key = "data_poblacion"
url = "http://Backend:5000/get_poblacion_data"
post_url = "http://Backend:5000/post_poblacion_data"

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=False)

def new_register(nacionalidad, periodo, sexo, total):
    new_data = {
        "Nacionalidad": nacionalidad,
        "Periodo": int(periodo),
        "Sexo": sexo,
        "Total": int(total)
    }
    try:
        response = requests.post(post_url, json=new_data)
        if response.status_code == 200:
            st.success(f'Registro guardado correctamente: {new_data}')
            df = load_data_from_api()
            if df is not None:
                set_data_to_redis(data_key, df)
                st.experimental_rerun()
        else:
            st.error('No se pudo guardar el registro en el backend.')
    except Exception as e:
        st.error(f'Error al enviar el registro al backend: {e}')

def load_data_from_api():
    try:
        data = get_data_from_api()
        if data is not None:
            df = pd.DataFrame(data)
            return df
    except Exception as e:
        st.error(f'Error al cargar los datos de la API: {e}')
        return None

def get_data_from_api():
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error('No se pudo obtener los datos de la API.')
            return None
    except Exception as e:
        st.error(f'Error al realizar la solicitud a la API: {e}')
        return None

def get_data_from_redis(key):
    try:
        cached_data = r.get(key)
        if cached_data:
            return pickle.loads(cached_data)
        else:
            st.warning("Sin información en redis")
            return None
    except Exception as e:
        st.error(f'Error al obtener datos de Redis: {e}')
        return None

def set_data_to_redis(key, data):
    try:
        r.set(key, pickle.dumps(data))
    except Exception as e:
        st.error(f'Error al guardar datos en Redis: {e}')

df = get_data_from_redis(data_key)
if df is None:
    df = load_data_from_api()
    if df is not None:
        set_data_to_redis(data_key, df)
        st.success("Datos cargados correctamente desde la API.")
    else:
        st.write('No se pudo obtener los datos de la API.')
        st.stop()
else:
    st.success("Usando información en redis")

# Ocultar columnas no deseadas
if df is not None:
    df = df.drop(columns=['Provincias', 'Secciones', 'Municipios'], errors='ignore')

# Mostrar la tabla completa
if df is not None:
    st.write("Datos Completos:")
    st.dataframe(df)  # Muestra todos los datos

# Filtrado de datos por periodo
if df is not None:
    if 'Periodo' in df.columns:
        df['Periodo'] = df['Periodo'].astype(str).str.replace(',', '')
        periodos = df['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['Periodo'] == selected_period]

        if 'Nacionalidad' in filtered_df.columns:
            selected_nacionalidades = st.multiselect('Seleccione las nacionalidades para comparar', filtered_df['Nacionalidad'].unique())

            if selected_nacionalidades:
                comparison_df = filtered_df[filtered_df['Nacionalidad'].isin(selected_nacionalidades)]
            else:
                comparison_df = pd.DataFrame(columns=df.columns)

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

columns_order = ['Nacionalidad', 'Periodo', 'Sexo', 'Total'] + [col for col in df.columns if col not in ['Nacionalidad', 'Periodo', 'Sexo', 'Total']]
df = df[columns_order]

st.write(df)

st.subheader('Nuevo Registro')
with st.form(key='new_register_form'):
    input_nacionalidad = st.text_input('Nacionalidad')
    input_periodo = st.number_input('Periodo', min_value=2000)
    input_sexo = st.text_input('Sexo')
    input_total = st.number_input('Total', min_value=1)
    submit_button_register = st.form_submit_button(label='Guardar Registro')

if submit_button_register:
    new_register(input_nacionalidad, input_periodo, input_sexo, input_total)

st.subheader('Editar Registro')
with st.form(key='new_edit_form'):
    select_nacionalidad = st.selectbox('Selecciona una nacionalidad: ', df['Nacionalidad'].unique(), index=0)
    select_periodo = st.selectbox('Selecciona un periodo: ', df['Periodo'].unique(), index=0)
    select_sexo = st.selectbox('Selecciona un sexo: ', df['Sexo'].unique(), index=0)
    input_total = st.number_input('Ingresa el total:', min_value=0)
    submit_button_edit = st.form_submit_button(label='Editar Registro')

if submit_button_edit:
    new_register(select_nacionalidad, select_periodo, select_sexo, input_total)