import streamlit as st
import pandas as pd

# Título de la aplicación
st.title('Visualizador de datos del PIB en el mundo')

# Cargar el archivo CSV con datos del PIB
file_path = "datos/pibdata.csv"

if file_path is not None:
    df = pd.read_csv(file_path)

    # Filtrado de datos por país
    countries = df['Country'].unique()
    selected_countries = st.multiselect('Seleccione los países para visualizar', countries)

    if selected_countries:
        filtered_df = df[df['Country'].isin(selected_countries)]
        st.write(filtered_df)
    else:
        filtered_df = df
        st.write(filtered_df)

    # Lista de años
    range = list(range(1961, 2024))

    # Selección del año
    selected = st.selectbox("Año", range, index=0)

    # Gráfica de PIB en el mundo por Año
    st.bar_chart(df, x="Country", y=str(selected), horizontal=True)