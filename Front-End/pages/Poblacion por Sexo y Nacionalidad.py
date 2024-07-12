import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Título de la aplicación
st.title('Visualizador de población por sexo y nacionalidad')

file_path = "datos/66375.csv"

# Verificar si el archivo existe
if not os.path.exists(file_path):
    st.error(f"El archivo no existe: {file_path}")
else:
    # Intentar cargar el archivo CSV
    try:
        df = pd.read_csv(file_path, encoding='utf-8', delimiter=';', thousands=',')
        st.write(df)

        # Filtrado de datos por periodo
        df['Periodo'] = df['Periodo'].astype(str).str.replace(',', '')  # Remover comas
        periodos = df['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['Periodo'] == selected_period]

        # Selección de múltiples nacionalidades para comparación
        selected_nacionalidades = st.multiselect('Seleccione las nacionalidades para comparar', filtered_df['Nacionalidad'].unique())

        if selected_nacionalidades:
            comparison_df = filtered_df[filtered_df['Nacionalidad'].isin(selected_nacionalidades)]
        else:
            comparison_df = pd.DataFrame(columns=df.columns)

        # Generar gráfico de pastel si hay datos seleccionados
        if not comparison_df.empty:
            st.subheader('Total de población por nacionalidad')

            fig = px.pie(comparison_df, values='Total', names='Nacionalidad', title='Distribución de la población total por nacionalidad')
            st.plotly_chart(fig)

            st.subheader('Total de población por nacionalidad')
            fig2 = px.bar(comparison_df, x='Nacionalidad', y='Total', title='Total de población por nacionalidad')
            st.plotly_chart(fig2)

            st.subheader('Evolución de la Población en el Tiempo')
            fig3 = px.pie(comparison_df, values='Total', names='Nacionalidad', title=f'Evolución de la población en el período {selected_period}')
            st.plotly_chart(fig3)

            # Mostrar tabla comparativa sin comas en la columna 'Periodo'
            st.write('Tabla Comparativa de Nacionalidades Seleccionadas')
            comparison_df_display = comparison_df.copy()
            comparison_df_display['Periodo'] = comparison_df_display['Periodo'].astype(str).str.replace(',', '')
            st.write(comparison_df_display)

    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}")
