import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Visualizador de Consumo de energía eléctrica global')
st.markdown('En esta sección, se mostrará un análisis del consumo de energía eléctrica global en kilowatts/hora.')

file_path = 'datos/API_EG.USE.ELEC.KH.PC_DS2_es_csv_v2_834019.csv'

if file_path is not None:
    df = pd.read_csv(file_path)

    years = [str(year) for year in range(1960, 2015)]

    columns = ['Country Name', 'Country Code'] + years
    df = df[columns]

    df = df.dropna(subset=years, how='all')
    df = df.reset_index(drop=True)
    st.write(df)

    st.subheader('Promedio de Consumo de Energía Eléctrica por País')
    df['Average Consumption'] = df[years].mean(axis=1)
    avg_fig = px.bar(df, x='Country Name', y='Average Consumption', title='Consumo Anual Promedio de Energía Eléctrica por País')
    st.plotly_chart(avg_fig)

    st.subheader('Tendencia del Consumo de Energía Eléctrica')
    country = st.selectbox('Selecciona un país para ver la tendencia del consumo de energía eléctrica:', df['Country Name'].unique())
    country_data = df[df['Country Name'] == country].melt(id_vars=['Country Name', 'Country Code'], value_vars=years, var_name='Year', value_name='Consumption')
    trend_fig = px.line(country_data, x='Year', y='Consumption', title=f'Tendencia del Consumo de Energía Eléctrica en {country}')
    st.plotly_chart(trend_fig)

    st.subheader('Comparación del Consumo de Energía Eléctrica Entre Países')
    year = st.selectbox('Selecciona un año para comparar el consumo de energía eléctrica entre países:', years)
    compare_fig = px.bar(df, x='Country Name', y=year, title=f'Comparación del Consumo de Energía Eléctrica en {year}')
    st.plotly_chart(compare_fig)

    st.subheader('Cambio Porcentual en el Consumo de Energía Eléctrica')
    year1 = st.selectbox('Selecciona el primer año:', years, index=0)
    year2 = st.selectbox('Selecciona el segundo año:', years, index=len(years)-1)
    df['Percentage Change'] = ((df[year2] - df[year1]) / df[year1]) * 100
    change_fig = px.bar(df, x='Country Name', y='Percentage Change', title=f'Cambio Porcentual en el Consumo de Energía de {year1} a {year2}')
    st.plotly_chart(change_fig)

    st.subheader('Top N Países con Mayor Consumo de Energía Eléctrica')
    top_n = st.slider('Selecciona el número de países a mostrar:', 1, 30, 5)
    top_countries = df.nlargest(top_n, year)
    top_fig = px.bar(top_countries, x='Country Name', y=year, title=f'Top {top_n} Países con Mayor Consumo de Energía en {year}')
    st.plotly_chart(top_fig)
