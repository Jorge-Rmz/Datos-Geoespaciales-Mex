import streamlit as st
import pandas as pd
import plotly.express as px

# Título de la aplicación
st.title('Visualizador de Datos de Trabajo Doméstico y de Cuidado en México')

# Ruta del archivo CSV con datos geoespaciales
file_path = "datos/ssdp02a_por_trab_dom_cui.csv"

# Cargar el archivo CSV con datos
if file_path is not None:
    df = pd.read_csv(file_path, encoding='latin1')
    st.write(df)

    # Filtrado de datos por periodo
    periodos = df['Periodo'].unique()
    selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

    filtered_df = df[df['Periodo'] == selected_period]

    # Selección de múltiples entidades federativas para comparación
    selected_states = st.multiselect('Seleccione las entidades federativas para comparar', filtered_df['Entidad federativa'].unique())

    if selected_states:
        comparison_df = filtered_df[filtered_df['Entidad federativa'].isin(selected_states)]
    else:
        comparison_df = pd.DataFrame(columns=df.columns)

    # Generar gráficos comparativos si hay entidades seleccionadas
    if not comparison_df.empty:
        st.subheader('Comparación de Entidades Seleccionadas')

        # Gráfico circular del porcentaje de horas dedicadas a actividades domésticas y de cuidado
        fig = px.pie(comparison_df, names='Entidad federativa', values='Suma de porcentajes del total de horas por semana dedicados a actividades domésticas y de cuidado que realizan los integrantes del hogar de 12 y más años', title='Horas a actividades domésticas y de cuidado')
        st.plotly_chart(fig)

        # Gráfico circular de la tasa de participación en trabajo doméstico no remunerado
        fig2 = px.pie(comparison_df, names='Entidad federativa', values='Tasa de participación de la población de 12 años y más en trabajo doméstico no remunerado para el propio hogar', title='Participación en trabajo doméstico no remunerado')
        st.plotly_chart(fig2)

        # Gráfico circular de la tasa de participación en trabajo no remunerado de cuidado
        fig3 = px.pie(comparison_df, names='Entidad federativa', values='Tasa de participación de la población de 12 años y más en trabajo no remunerado de cuidado a integrantes del hogar', title='Participación en trabajo no remunerado de cuidado')
        st.plotly_chart(fig3)

        # Tabla comparativa de las entidades seleccionadas
        st.write('Tabla Comparativa de Entidades Seleccionadas')
        st.write(comparison_df)
