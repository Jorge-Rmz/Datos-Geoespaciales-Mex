import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import redis
from io import StringIO

# Configuración de Redis
redis_host = "redis"
redis_port = 6379
data_key = "data_Trabajo_domestico"
# Conectar a Redis
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Título de la aplicación
st.title('Datos de Trabajo Doméstico y de Cuidado en México')

# URL del backend
backend_url = "http://backend:5000/"

# Función para verificar si Redis está disponible
def is_redis_available():
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False

# Función para cargar los datos desde el backend o Redis
def load_data():
    redis_available = is_redis_available()

    if redis_available:
        st.success("Conectado a Redis")
        data = redis_client.get(data_key)
        if data:
            st.info("Mostrando datos de Redis")
            redis_df = pd.read_json(StringIO(data), orient='split')
        else:
            st.info("No hay datos en Redis")
            redis_df = pd.DataFrame()
    else:
        st.warning("Redis no está disponible. Intentando cargar datos desde el backend")
        redis_df = pd.DataFrame()

    try:
        response = requests.get(backend_url + 'get_all_datos_trabajo_domestico')
        response.raise_for_status()
        data = response.json()
        backend_df = pd.DataFrame(data)

        if redis_available:
            redis_client.set(data_key, backend_df.to_json(orient='split'))
            st.info("Datos guardados en Redis")

        return backend_df

    except requests.RequestException as e:
        st.error(f"No se pudo obtener datos del backend: {e}")
        if not redis_df.empty:
            st.info("Mostrando datos de Redis almacenados previamente")
            return redis_df
        else:
            return None

# Botón para refrescar los datos
if st.button('Refrescar Datos'):
    st.experimental_rerun()

# Cargar datos
df = load_data()

# Opciones de acción
action = st.radio("Seleccione una acción", ('Agregar', 'Editar', 'Eliminar'))

# Mostrar formulario según la acción seleccionada
if action == 'Agregar':
    st.write("Agregar Registro")
    with st.form(key='add_form'):
        entidad_federativa = st.text_input('Entidad Federativa')
        periodo = st.number_input('Periodo', min_value=2000, max_value=2100, step=1)
        horas_domesticas_y_cuidado = st.number_input('Horas Domésticas y Cuidado')
        tasa_trabajo_domestico = st.number_input('Tasa Trabajo Doméstico')
        tasa_trabajo_cuidado = st.number_input('Tasa Trabajo Cuidado')
        submit_button = st.form_submit_button(label='Confirmar')

        if submit_button:
            new_data = {
                'entidad_federativa': entidad_federativa,
                'periodo': periodo,
                'horas_domesticas_y_cuidado': horas_domesticas_y_cuidado,
                'tasa_trabajo_domestico': tasa_trabajo_domestico,
                'tasa_trabajo_cuidado': tasa_trabajo_cuidado
            }
            try:
                response = requests.post(
                    backend_url + 'post_datos_trabajo_domestico',
                    json=new_data
                )
                response.raise_for_status()
                st.success("Registro agregado exitosamente")

                # Actualizar datos en Redis
                df_updated = load_data()
                if df_updated is not None:
                    redis_client.set(data_key, df_updated.to_json(orient='split'))
                    st.info("Datos actualizados en Redis")
            except requests.RequestException as e:
                st.error(f"Error al agregar el registro: {e}")

            st.experimental_rerun()

elif action == 'Editar':
    st.write("Editar Registro")
    if df is not None:
        ids = df['id'].tolist()
        selected_id = st.selectbox("Seleccione el ID del registro a editar", ids)
        if selected_id:
            selected_row = df[df['id'] == selected_id].iloc[0]
            with st.form(key='edit_form'):
                entidad_federativa = st.text_input('Entidad Federativa', selected_row['entidad_federativa'])
                periodo = st.number_input('Periodo', value=selected_row['periodo'])
                horas_domesticas_y_cuidado = st.number_input('Horas Domésticas y Cuidado', value=selected_row['horas_domesticas_y_cuidado'])
                tasa_trabajo_domestico = st.number_input('Tasa Trabajo Doméstico', value=selected_row['tasa_trabajo_domestico'])
                tasa_trabajo_cuidado = st.number_input('Tasa Trabajo Cuidado', value=selected_row['tasa_trabajo_cuidado'])
                submit_button = st.form_submit_button(label='Confirmar')

                if submit_button:
                    update_data = {
                        'entidad_federativa': entidad_federativa,
                        'periodo': periodo,
                        'horas_domesticas_y_cuidado': horas_domesticas_y_cuidado,
                        'tasa_trabajo_domestico': tasa_trabajo_domestico,
                        'tasa_trabajo_cuidado': tasa_trabajo_cuidado
                    }
                    try:
                        response = requests.put(
                            backend_url + f"update_datos_trabajo_domestico?id={selected_id}",
                            json=update_data
                        )
                        response.raise_for_status()
                        st.success("Registro actualizado exitosamente")

                        # Actualizar datos en Redis
                        df_updated = load_data()
                        if df_updated is not None:
                            redis_client.set(data_key, df_updated.to_json(orient='split'))
                            st.info("Datos actualizados en Redis")
                    except requests.RequestException as e:
                        st.error(f"Error al actualizar el registro: {e}")

                    st.experimental_rerun()

elif action == 'Eliminar':
    st.write("Eliminar Registro")
    if df is not None:
        ids = df['id'].tolist()
        selected_id = st.selectbox("Seleccione el ID del registro a eliminar", ids)
        if selected_id:
            selected_row = df[df['id'] == selected_id].iloc[0]
            st.write(f"¿Está seguro de que desea eliminar el registro de {selected_row['entidad_federativa']} para el periodo {selected_row['periodo']}?")
            if st.button('Confirmar'):
                try:
                    response = requests.delete(
                        backend_url + f"delete_datos_trabajo_domestico?id={selected_id}"
                    )
                    response.raise_for_status()
                    st.success("Registro eliminado exitosamente")

                    # Actualizar datos en Redis
                    df_updated = load_data()
                    if df_updated is not None:
                        redis_client.set(data_key, df_updated.to_json(orient='split'))
                        st.info("Datos actualizados en Redis")
                except requests.RequestException as e:
                    st.error(f"Error al eliminar el registro: {e}")

                st.experimental_rerun()

# Mostrar la tabla con todos los datos
if df is not None:
    st.write("Datos Completos:")
    st.dataframe(df)

# Filtrado de datos por periodo
if df is not None:
    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].astype(str).str.replace(',', '').astype(int)

        periodos = df['periodo'].unique()
        selected_period = st.selectbox('Seleccione el periodo para visualizar', periodos)

        filtered_df = df[df['periodo'] == selected_period]

        if 'entidad_federativa' in df.columns:
            selected_states = st.multiselect('Seleccione las entidades federativas para comparar',
                                             filtered_df['entidad_federativa'].unique())

            if selected_states:
                comparison_df = filtered_df[filtered_df['entidad_federativa'].isin(selected_states)]
            else:
                comparison_df = pd.DataFrame(columns=df.columns)

            # Genera los gráficos comparativos si hay entidades seleccionadas
            if not comparison_df.empty:
                st.subheader('Comparación de Entidades Seleccionadas')

                # Verificar si las columnas necesarias existen y no están vacías
                if 'horas_domesticas_y_cuidado' in comparison_df.columns and not comparison_df['horas_domesticas_y_cuidado'].isnull().all():
                    fig = px.pie(comparison_df, names='entidad_federativa', values='horas_domesticas_y_cuidado',
                                 title='Horas a actividades domésticas y de cuidado')
                    st.plotly_chart(fig)
                else:
                    st.warning("No hay datos suficientes para 'Horas Domésticas y Cuidado'.")

                if 'tasa_trabajo_domestico' in comparison_df.columns and not comparison_df['tasa_trabajo_domestico'].isnull().all():
                    fig2 = px.pie(comparison_df, names='entidad_federativa', values='tasa_trabajo_domestico',
                                  title='Participación en trabajo doméstico no remunerado')
                    st.plotly_chart(fig2)
                else:
                    st.warning("No hay datos suficientes para 'Tasa Trabajo Doméstico'.")

                if 'tasa_trabajo_cuidado' in comparison_df.columns and not comparison_df['tasa_trabajo_cuidado'].isnull().all():
                    fig3 = px.pie(comparison_df, names='entidad_federativa', values='tasa_trabajo_cuidado',
                                  title='Participación en trabajo no remunerado de cuidado')
                    st.plotly_chart(fig3)
                else:
                    st.warning("No hay datos suficientes para 'Tasa Trabajo Cuidado'.")

                # Tabla comparativa de las entidades seleccionadas
                st.write('Tabla Comparativa de Entidades Seleccionadas')
                st.dataframe(comparison_df)
            else:
                st.warning("No hay datos seleccionados.")
        else:
            st.error("La columna 'Entidad federativa' no se encuentra en el archivo CSV.")
    else:
        st.error("La columna 'Periodo' no se encuentra en el archivo CSV.")
