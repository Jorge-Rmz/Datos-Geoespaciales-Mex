import pickle
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis

redis_host = "redis"
redis_port = 6379
redis_password = ""

data_key = "data_pib"
url = "http://Backend:5000/get_pib_data"
post_url = "http://Backend:5000/post_pib_data"

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=False)

def new_register(pais, year, pib):
    new_data = {
        "Nombre del País": pais,
        "Año": year,
        "PIB": pib
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

columns_order = ['Código del País', 'Nombre del País'] + [col for col in df.columns if col not in ['Código del País', 'Nombre del País']]
df = df[columns_order]

st.title('PIB')

years = [str(year) for year in range(1960, 2024)]
renamed_years = [f'Año {year}' for year in years]

df = df.dropna(subset=renamed_years, how='all')
df = df.reset_index(drop=True)

if df is not None:
    # Filtrado de datos por país
    countries = df['Nombre del País'].unique()
    selected_countries = st.multiselect('Seleccione los países para visualizar', countries)

    if selected_countries:
        filtered_df = df[df['Nombre del País'].isin(selected_countries)]
        st.write(filtered_df)
    else:
        filtered_df = df
        st.write(filtered_df)

    # Selección del año
    selected_year = st.selectbox('Selecciona un año:', renamed_years, index=0)

    # Gráfica de PIB en el mundo por Año
    st.bar_chart(df, x='Nombre del País', y=str(selected_year), horizontal=True)

st.subheader('Nuevo Registro')
with st.form(key='new_register_form'):
    input_country = st.text_input('Nombre del País')
    selected_year = st.selectbox('Selecciona un año:', renamed_years)
    pib = st.number_input('Ingresa el PIB:', format="%.5f")
    submit_button_register = st.form_submit_button(label='Guardar Registro')

if submit_button_register:
    new_register(input_country, selected_year, pib)

st.subheader('Editar Registro')
with st.form(key='new_edit_form'):
    selected_country = st.selectbox('Selecciona un país:', df['Nombre del País'].unique())
    selected_year = st.selectbox('Selecciona un año:', renamed_years)
    pib = st.number_input('Ingresa el PIB:', format="%.5f")
    submit_button_edit = st.form_submit_button(label='Edit Registro')

if submit_button_edit:
    new_register(selected_country, selected_year, pib)

