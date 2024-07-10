#consulta de api de datos monetarios del mundo

import  streamlit as st
import  pandas as pd
import  requests
import  json
import  plotly.express as px

# Título de la aplicación
st.title('Visualizador de Consumo de energía eléctrica global')
st.markdown('En esta sección, se mostrará un gráfico de barras que muestra el consumo de energía eléctrica global en kilowatts/hora.')

file_path  = 'datos/API_EG.USE.ELEC.KH.PC_DS2_es_csv_v2_834019.csv'

if file_path is not None:
    df = pd.read_csv(file_path )
    st.write(df)
