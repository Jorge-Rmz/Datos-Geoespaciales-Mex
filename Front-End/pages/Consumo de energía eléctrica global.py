import pickle
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis

redis_host = "localhost"
redis_port = 6379
redis_password = ""

data_key = "data_consumo_electrico"
url = "http://localhost:5000/get_consumo_electrico"
post_url = "http://localhost:5000/post_consumo_electrico"

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=False)

def new_register(pais, year, consumo):
    new_data = {
        "Nombre del País": pais,
        "Año": year,
        "Consumo": consumo
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

st.title('Visualizador de Consumo de energía eléctrica global')
st.markdown('En esta sección, se mostrará un análisis del consumo de energía eléctrica global en kilowatts/hora.')

years = [str(year) for year in range(1960, 2015)]
renamed_years = [f'Año {year}' for year in years]

df = df.dropna(subset=renamed_years, how='all')
df = df.reset_index(drop=True)
st.write(df)

st.subheader('Promedio de Consumo de Energía Eléctrica por País')
df['Consumo Promedio'] = df[renamed_years].mean(axis=1)
avg_fig = px.bar(df, x='Nombre del País', y='Consumo Promedio',
                 title='Consumo Anual Promedio de Energía Eléctrica por País')
st.plotly_chart(avg_fig)

st.subheader('Tendencia del Consumo de Energía Eléctrica')
country = st.selectbox('Selecciona un país para ver la tendencia del consumo de energía eléctrica:',
                       df['Nombre del País'].unique())
country_data = df[df['Nombre del País'] == country].melt(id_vars=['Nombre del País', 'Código del País'],
                                                         value_vars=renamed_years, var_name='Año', value_name='Consumo')
trend_fig = px.line(country_data, x='Año', y='Consumo',
                    title=f'Tendencia del Consumo de Energía Eléctrica en {country}')
st.plotly_chart(trend_fig)

year = st.selectbox('Selecciona un año para comparar el consumo de energía eléctrica entre países:', renamed_years)
compare_fig = px.bar(df, x='Nombre del País', y=year, title=f'Comparación del Consumo de Energía Eléctrica en {year}')
st.plotly_chart(compare_fig)

st.subheader('Cambio Porcentual en el Consumo de Energía Eléctrica')
year1 = st.selectbox('Selecciona el primer año:', renamed_years, index=0)
year2 = st.selectbox('Selecciona el segundo año:', renamed_years, index=len(renamed_years) - 1)
df['Cambio Porcentual'] = ((df[year2] - df[year1]) / df[year1]) * 100
change_fig = px.bar(df, x='Nombre del País', y='Cambio Porcentual',
                    title=f'Cambio Porcentual en el Consumo de Energía de {year1} a {year2}')
st.plotly_chart(change_fig)

st.subheader('Top N Países con Mayor Consumo de Energía Eléctrica')
top_n = st.slider('Selecciona el número de países a mostrar:', 1, 10, 5)
top_countries = df.nlargest(top_n, year)
top_fig = px.bar(top_countries, x='Nombre del País', y=year,
                 title=f'Top {top_n} Países con Mayor Consumo de Energía en {year}')
st.plotly_chart(top_fig)

st.subheader('Nuevo Registro')
with st.form(key='new_register_form'):
    selected_country = st.selectbox('Selecciona un país:', df['Nombre del País'].unique())
    selected_year = st.selectbox('Selecciona un año:', renamed_years)
    consumo = st.number_input('Ingresa el consumo (kWh):', min_value=0.0, format="%.4f")
    submit_button = st.form_submit_button(label='Guardar Registro')

if submit_button:
    new_register(selected_country, selected_year, consumo)
