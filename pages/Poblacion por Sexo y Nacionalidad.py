import streamlit as st
import pandas as pd
import plotly.express as px

# Título de la aplicación
st.title('Visualizador de población por sexo y nacionalidad')

# Ruta del archivo CSV con datos
file_path = "datos/66375.csv"  # Update the file path here

# Cargar el archivo CSV con datos
if file_path is not None:
    # Leer el archivo CSV y manejar caracteres especiales
    df = pd.read_csv(file_path, encoding='utf-8', delimiter=';', thousands=',')  # Codificación UTF-8 y manejo de comas en números
    st.write(df)

    # Filtrado de datos por periodo
    periodos = df['Periodo'].astype(str).str.replace(',', '').str.split().apply(lambda x: x[0])  # Remover comas y separar por espacio
    selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

    filtered_df = df[df['Periodo'].astype(str).str.replace(',', '').str.split().apply(lambda x: x[0]) == selected_period]

    # Selección de múltiples nacionalidades para comparación
    selected_nacionalidades = st.multiselect('Seleccione las nacionalidades para comparar', filtered_df['Nacionalidad'].unique())

    if selected_nacionalidades:
        comparison_df = filtered_df[filtered_df['Nacionalidad'].isin(selected_nacionalidades)]
    else:
        comparison_df = pd.DataFrame(columns=df.columns)

    # Generar gráfico de pastel si hay datos seleccionados
    if not comparison_df.empty:
        st.subheader('Gráfico de Pastel: Horas a actividades domésticas y de cuidado por nacionalidad')

        fig = px.pie(comparison_df, values='Total', names='Nacionalidad', title='Distribución de horas a actividades domésticas y de cuidado por nacionalidad')
        st.plotly_chart(fig)

        # Mostrar tabla comparativa sin comas en la columna 'Periodo'
        st.write('Tabla Comparativa de Nacionalidades Seleccionadas')
        comparison_df_display = comparison_df.copy()
        comparison_df_display['Periodo'] = comparison_df_display['Periodo'].astype(str).str.replace(',', '').str.split().apply(lambda x: x[0])  # Remover comas y tomar solo el primer elemento
        st.write(comparison_df_display)
