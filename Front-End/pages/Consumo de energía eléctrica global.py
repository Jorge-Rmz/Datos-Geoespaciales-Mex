import streamlit as st
import pandas as pd
import plotly.express as px
import redis
import pickle

redis_host = "localhost"
redis_port = 6379
redis_password = ""

r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=False)

def load_data(file_path):
    df = pd.read_csv(file_path)
    years = [str(year) for year in range(1960, 2015)]
    columns = ['Country Name', 'Country Code'] + years
    df = df[columns]
    column_rename = {
        'Country Name': 'Nombre del País',
        'Country Code': 'Código del País'
    }
    column_rename.update({year: f'Año {year}' for year in years})
    df = df.rename(columns=column_rename)
    return df

def get_data_from_redis(key):
    cached_data = r.get(key)
    if cached_data:
        return pickle.loads(cached_data)
    return None

def set_data_to_redis(key, data):
    r.set(key, pickle.dumps(data))

st.title('Visualizador de Consumo de energía eléctrica global')
st.markdown('En esta sección, se mostrará un análisis del consumo de energía eléctrica global en kilowatts/hora.')

file_path = 'Back-End/datos/API_EG.USE.ELEC.KH.PC_DS2_es_csv_v2_834019.csv'
data_key = "energy_consumption_data"

df = get_data_from_redis(data_key)
if df is None:
    df = load_data(file_path)
    set_data_to_redis(data_key, df)

years = [str(year) for year in range(1960, 2015)]
renamed_years = [f'Año {year}' for year in years]

df = df.dropna(subset=renamed_years, how='all')
df = df.reset_index(drop=True)
st.write(df)

st.subheader('Promedio de Consumo de Energía Eléctrica por País')
df['Consumo Promedio'] = df[renamed_years].mean(axis=1)
avg_fig = px.bar(df, x='Nombre del País', y='Consumo Promedio', title='Consumo Anual Promedio de Energía Eléctrica por País')
st.plotly_chart(avg_fig)

st.subheader('Tendencia del Consumo de Energía Eléctrica')
country = st.selectbox('Selecciona un país para ver la tendencia del consumo de energía eléctrica:', df['Nombre del País'].unique())
country_data = df[df['Nombre del País'] == country].melt(id_vars=['Nombre del País', 'Código del País'], value_vars=renamed_years, var_name='Año', value_name='Consumo')
trend_fig = px.line(country_data, x='Año', y='Consumo', title=f'Tendencia del Consumo de Energía Eléctrica en {country}')
st.plotly_chart(trend_fig)

year = st.selectbox('Selecciona un año para comparar el consumo de energía eléctrica entre países:', renamed_years)
compare_fig = px.bar(df, x='Nombre del País', y=year, title=f'Comparación del Consumo de Energía Eléctrica en {year}')
st.plotly_chart(compare_fig)

st.subheader('Cambio Porcentual en el Consumo de Energía Eléctrica')
year1 = st.selectbox('Selecciona el primer año:', renamed_years, index=0)
year2 = st.selectbox('Selecciona el segundo año:', renamed_years, index=len(renamed_years)-1)
df['Cambio Porcentual'] = ((df[year2] - df[year1]) / df[year1]) * 100
change_fig = px.bar(df, x='Nombre del País', y='Cambio Porcentual', title=f'Cambio Porcentual en el Consumo de Energía de {year1} a {year2}')
st.plotly_chart(change_fig)

st.subheader('Top N Países con Mayor Consumo de Energía Eléctrica')
top_n = st.slider('Selecciona el número de países a mostrar:', 1, 10, 5)
top_countries = df.nlargest(top_n, year)
top_fig = px.bar(top_countries, x='Nombre del País', y=year, title=f'Top {top_n} Países con Mayor Consumo de Energía en {year}')
st.plotly_chart(top_fig)
