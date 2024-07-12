import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Título de la aplicación
st.title('Datos de Trabajo Doméstico y de Cuidado en México')

# URL del backend
backend_url = "http://localhost:8503/get_data"

# Función para cargar los datos desde el backend
def load_data():
    try:
        response = requests.get(backend_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except requests.RequestException as e:
        st.error(f"No se pudo obtener datos del backend: {e}")
        return None

# Obtiene los datos del backend
df = load_data()

# Muestra la tabla completa inicialmente
if df is not None:
    st.write("Datos Completos:")
    st.dataframe(df)

# Filtrado de datos por periodo
if df is not None:
    if 'Periodo' in df.columns:
        df['Periodo'] = df['Periodo'].astype(str).str.replace(',', '').astype(int)

        periodos = df['Periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['Periodo'] == selected_period]

        if 'Entidad federativa' in df.columns:
            selected_states = st.multiselect('Seleccione las entidades federativas para comparar',
                                             filtered_df['Entidad federativa'].unique())

            if selected_states:
                comparison_df = filtered_df[filtered_df['Entidad federativa'].isin(selected_states)]
            else:
                comparison_df = pd.DataFrame(columns=df.columns)

            # Genera los gráficos comparativos si hay entidades seleccionadas
            if not comparison_df.empty:
                st.subheader('Comparación de Entidades Seleccionadas')

                # Gráfico circular del porcentaje de horas dedicadas a actividades domésticas y de cuidado
                if 'Horas Domésticas y Cuidado' in df.columns:
                    fig = px.pie(comparison_df, names='Entidad federativa', values='Horas Domésticas y Cuidado',
                                 title='Horas a actividades domésticas y de cuidado')
                    st.plotly_chart(fig)

                # Gráfico circular de la tasa de participación en trabajo doméstico no remunerado
                if 'Tasa Trabajo Doméstico' in df.columns:
                    fig2 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Doméstico',
                                  title='Participación en trabajo doméstico no remunerado')
                    st.plotly_chart(fig2)

                # Gráfico circular de la tasa de participación en trabajo no remunerado de cuidado
                if 'Tasa Trabajo Cuidado' in df.columns:
                    fig3 = px.pie(comparison_df, names='Entidad federativa', values='Tasa Trabajo Cuidado',
                                  title='Participación en trabajo no remunerado de cuidado')
                    st.plotly_chart(fig3)

                # Tabla comparativa de las entidades seleccionadas
                st.write('Tabla Comparativa de Entidades Seleccionadas')
                st.dataframe(comparison_df)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Entidad federativa' no se encuentra en el archivo CSV.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el archivo CSV.")
