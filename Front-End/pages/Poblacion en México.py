import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
import requests
import time
import redis
import json
import io


# URL de la API Flask
api_url = "http://Backend:5000"
data_key = 'geospatial_data1'
file_path = "datos/data.csv"

# Conectar a Redis
redis_host = "redis"
redis_port = 6379

redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)


def download_csv_from_redis():
    if is_redis_available():
        data = get_data_from_redis(redis_client, data_key)
        if data is not None:
            csv_buffer = io.StringIO()
            data.to_csv(csv_buffer, index=False, sep=',')
            csv_buffer.seek(0)
            return csv_buffer.getvalue().encode('utf-8')
        else:
            st.warning("No hay datos disponibles para descargar")
            return None
    else:
        st.error("No se pudo conectar a Redis. No se pueden descargar los datos.")
        return None


def is_redis_available():
    try:
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False

def save_data_to_redis(redis_conn, key, df):
    redis_conn.set(key, json.dumps(df.to_dict(orient='records')))

def get_data_from_redis(redis_conn, key):
    if redis_conn.exists(key):
        return pd.DataFrame(json.loads(redis_conn.get(key)))
    return None

def load_data_from_csv(file_path):
    return pd.read_csv(file_path)

def validar_coordenadas(latitud, longitud):
    """Valida longitud y latitud para poder marcarlos en el mapa folium"""
    if latitud < -90 or latitud > 90:
        return False
    if longitud < -180 or longitud > 180:
        return False
    return True

# Título de la aplicación
st.title('Visualizador de Datos Geoespaciales - Estados de México')

# Botón para descargar datos desde Redis
csv_data = download_csv_from_redis()
if csv_data:
    st.download_button(
        label="Descargar CSV desde Redis",
        data=csv_data,
        file_name='datos_geoespaciales.csv',
        mime='text/csv'
    )

def add_data_to_redis(new_data):
    try:
        if is_redis_available():
            current_data = get_data_from_redis(redis_client, data_key)
            if current_data is not None:
                # Append new_data to current_data
                updated_data = pd.concat([current_data, new_data]).reset_index(drop=True)
                st.success("Datos agregados exitosamente a Redis")
                time.sleep(3)  # Pausar por 3 segundos
            else:
                updated_data = new_data

            save_data_to_redis(redis_client, data_key, updated_data)
            st.experimental_rerun()  # Recargar la página
        else:
            st.error("No se pudo conectar a Redis. No se han agregado los datos.")
    except Exception as e:
        st.error(f"Error al agregar datos a Redis: {e}")


def edit_data_in_redis(updated_data):
    try:
        if is_redis_available():
            save_data_to_redis(redis_client, data_key, updated_data)
            st.success("Datos actualizados exitosamente en Redis")
            time.sleep(3)
            st.experimental_rerun()  # Recargar la página
        else:
            st.error("No se pudo conectar a Redis. No se han actualizado los datos.")
    except Exception as e:
        st.error(f"Error al actualizar datos en Redis: {e}")

def load_data_from_csv(file_path):
    df = pd.read_csv(file_path)
    # redis_client.set(data_key, json.dumps(df.to_dict(orient='records')))
    st.write("Datos cargados desde el archivo CSV")
    return df

def load_data_from_redis():
    try:
        if is_redis_available():
            if redis_client.exists(data_key):
                df = pd.DataFrame(json.loads(redis_client.get(data_key)))
                st.success("Datos cargados desde Redis")
                return df
            else:
                save_data_to_redis(redis_client, data_key, pd.read_csv(file_path))
                df = get_data_from_redis(redis_client, data_key)
                st.success("Datos cargados desde Redis")
                return df
        else:
            st.error("No se pudo conectar a Redis. Cargando desde el archivo CSV...")
            return load_data_from_csv(file_path)
    except redis.exceptions.ConnectionError:
        st.error("Error al conectar con Redis. Verifica que Redis esté disponible.")
        return None

def load_data():
    try:
        # Verificar si los datos están en la API
        response = requests.get(f"{api_url}/api/get_poblacion_mex")

        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.success("Datos cargados desde la API Flask")
            return df
        else:
            return load_data_from_redis()

    except requests.exceptions.ConnectionError:
        st.error("No se pudo conectar a la API Flask. Intentando cargar desde Redis...")
        return load_data_from_redis()
    except FileNotFoundError:
        st.error("El archivo CSV no se encontró. Por favor, verifica la ruta del archivo.")
        return None
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Error HTTP: {http_err}")
        return None
    except Exception as e:
        st.error(f"Se produjo un error inesperado: {e}")
        return None



df = load_data()

if df is not None:
    def actualizar_visualizacion(df):

        # Mostrar los datos
        st.write("Datos completos:")
        st.write(df)

        # Filtrado de datos por región
        regiones = df['region'].unique()
        selected_regions = st.multiselect('Seleccione las regiones para visualizar', regiones)

        if selected_regions:
            filtered_df = df[df['region'].isin(selected_regions)]
        else:
            filtered_df = df

        # Filtrado de datos por población
        min_population, max_population = st.slider('Rango de población',
                                                   min_value=int(df['poblacion'].min()),
                                                   max_value=int(df['poblacion'].max()),
                                                   value=(int(df['poblacion'].min()), int(df['poblacion'].max())))
        filtered_df = filtered_df[(filtered_df['poblacion'] >= min_population) & (filtered_df['poblacion'] <= max_population)]

        # Crear el mapa base
        m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lon'].mean()], zoom_start=6)

        # Agregar puntos al mapa
        for _, row in filtered_df.iterrows():
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=f"Estado: {row['estado']}<br>Población: {row['poblacion']}"
            ).add_to(m)

        # Mostrar el mapa
        folium_static(m)

        # Generar gráficos comparativos si hay estados seleccionados
        selected_states = st.multiselect('Seleccione los estados para comparar', filtered_df['estado'].unique())

        if selected_states:
            comparison_df = filtered_df[filtered_df['estado'].isin(selected_states)]
            st.subheader('Comparación de Estados Seleccionados')

            # Gráfico de barras de la población
            fig = px.bar(comparison_df, x='estado', y='poblacion', title='Población de los Estados Seleccionados')
            st.plotly_chart(fig)

            # Gráfico de pie de la población por región
            fig_pie = px.pie(comparison_df, names='region', values='poblacion', title='Distribución de la Población por Región')
            st.plotly_chart(fig_pie)

            # Tabla comparativa de los estados seleccionados
            st.write('Tabla Comparativa de Estados Seleccionados')
            st.write(comparison_df)

    # Inicializar visualización de datos
    actualizar_visualizacion(df)

    # Sección para agregar nuevos datos
    st.subheader('Agregar Nuevo Registro')

    nuevo_estado = st.text_input('Estado:')
    nueva_poblacion = st.number_input('Población:')
    nueva_region = st.selectbox('Región:', df['region'].unique())
    nueva_latitud = st.number_input('Latitud:', min_value=-90.0, max_value=90.0)
    nueva_longitud = st.number_input('Longitud:', min_value=-180.0, max_value=180.0)

    if st.button('Agregar'):
        if nuevo_estado and nueva_poblacion and nueva_region and validar_coordenadas(nueva_latitud, nueva_longitud):
            new_data = pd.DataFrame({
                'estado': [nuevo_estado],
                'poblacion': [nueva_poblacion],
                'region': [nueva_region],
                'lat': [nueva_latitud],
                'lon': [nueva_longitud]
            })
            add_data_to_redis(new_data)  # No se necesita updated_df, la página se recargará


        else:
            st.warning(
                'Por favor complete todos los campos o ingrese coordenadas válidas. '
                'Latitud debe estar entre -90 y 90. Longitud debe estar entre -180 y 180.'
            )

    # Opción para editar registros existentes
    st.subheader('Editar Registro Existente')

    registros = get_data_from_redis(redis_client, data_key)

    if registros is not None:
        registros_list = registros.to_dict(orient='records')
        registro_editar = st.selectbox(
            'Seleccione el registro a editar:', registros_list,
            format_func=lambda
                x: f"{x['estado']} (Población: {x['poblacion']})")

        if registro_editar:
            nuevo_estado_editar = st.text_input(
                'Nuevo Estado:', value=registro_editar['estado'])
            nueva_poblacion_editar = st.number_input(
                'Nueva Población:', value=registro_editar['poblacion'])


            region_unique = df['region'].unique()
            data_select = registro_editar['region']
            index_data_select = region_unique.tolist().index(data_select)

            nueva_region_editar = st.selectbox('Nueva Región:',
                                               df['region'].unique(),
                                               index=index_data_select)

            nueva_latitud_editar = st.number_input(
                'Nueva Latitud:', value=registro_editar['lat'])
            nueva_longitud_editar = st.number_input(
                'Nueva Longitud:', value=registro_editar['lon'])

            if st.button('Guardar Cambios'):
                if validar_coordenadas(nueva_latitud_editar, nueva_longitud_editar):
                    # Actualizar el registro seleccionado con los nuevos valores
                    for registro in registros_list:
                        if registro == registro_editar:
                            registro['estado'] = nuevo_estado_editar
                            registro['poblacion'] = nueva_poblacion_editar
                            registro['region'] = nueva_region_editar
                            registro['lat'] = nueva_latitud_editar
                            registro['lon'] = nueva_longitud_editar

                    # Guardar los datos actualizados en Redis
                    updated_data = pd.DataFrame(registros_list)
                    edit_data_in_redis(updated_data)
                else:
                    st.warning(
                        'Por favor complete todos los campos o ingrese coordenadas válidas. '
                        'Latitud debe estar entre -90 y 90. Longitud debe estar entre -180 y 180.'
                    )
    else:
        st.warning('No hay registros en Redis.')

else:
    # Si no hay datos, intenta cargar desde el CSV
    st.error("Cargando datos desde el archivo CSV")
    df = load_data_from_csv(file_path)

    if df is not None:
        st.write(df)
