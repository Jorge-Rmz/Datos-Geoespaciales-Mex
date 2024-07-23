import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
import requests
import time
import redis
import json
import io


# URL de la API Flask
api_url = "http://Backend:5000"
data_key = 'geospatial_data1'

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
    redis_conn.set(key, json.dmups(df.to_dict(orient='records')))

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



def add_record_to_db(df):
    url = 'http://Backend:5000/api/create_record'
    headers = {'Content-Type': 'application/json'}

    for index, row in df.iterrows():
        data = {
            'estado': row['estado'],
            'lat': row['lat'],
            'lon': row['lon'],
            'poblacion': row['poblacion'],
            'region': row['region']
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                result = response.json()
                st.success(f"{result}")
            else:
                st.error(f"Error al agregar el registro {row['estado']}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error al conectar con el servidor para el registro {row['estado']}: {e}")




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


def load_data_from_redis():
    try:
        if is_redis_available():
            df = pd.DataFrame(json.loads(redis_client.get(data_key)))
            st.success("Datos cargados desde Redis")
            return df
        else:
            st.error("No se pudo conectar a Redis. ")
    except redis.exceptions.ConnectionError:
        st.error("Error al conectar con Redis. Verifica que Redis esté disponible.")
        return None

def load_data():
    try:
        # Verificar si los datos están en la API
        response = requests.get(f"{api_url}/api/get_data/db/postgres")

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

def generate_table_html(df):
    table_html = """
    <style>
        body {
            background-color: #333;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid white;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #444;
        }
        tr:nth-child(even) {
            background-color: #555;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 2px 1px;
            cursor: pointer;
        }
        button.edit {
            background-color: #008CBA;
        }
        button.delete {
            background-color: #f44336;
        }
    </style>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Estado</th>
                <th>Latitud</th>
                <th>Longitud</th>
                <th>Población</th>
                <th>Región</th>
                <th>Acciones</th>
            </tr>
        </thead>
        <tbody>
    """

    for index, row in df.iterrows():
        table_html += f"""
        <tr>
            <td>{row['id']}</td>
            <td>{row['estado']}</td>
            <td>{row['lat']}</td>
            <td>{row['lon']}</td>
            <td>{row['poblacion']}</td>
            <td>{row['region']}</td>
            <td>
                <button class="edit" onclick="openEditModal({row['id']}, '{row['estado']}', {row['lat']}, {row['lon']}, {row['poblacion']}, '{row['region']}')">Editar</button>
                <button class="delete" onclick="deleteRecord({row['id']})">Eliminar</button>
            </td>
        </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    # Modal HTML
    modal_html = """
    <div id="editModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeEditModal()">&times;</span>
            <h2>Editar Registro</h2>
            <form id="editForm">
                <label for="estado">Estado:</label>
                <input type="text" id="estado" name="estado"><br><br>
                <label for="lat">Latitud:</label>
                <input type="number" id="lat" name="lat"><br><br>
                <label for="lon">Longitud:</label>
                <input type="number" id="lon" name="lon"><br><br>
                <label for="poblacion">Población:</label>
                <input type="number" id="poblacion" name="poblacion"><br><br>
                <label for="region">Región:</label>
                <input type="text" id="region" name="region"><br><br>
                <button type="button" onclick="submitEdit()">Guardar Cambios</button>
            </form>
        </div>
    </div>

    <style>
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.4);
        }
        .modal-content {
            background-color: #333;
            margin: 2% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            color: white;
        }
        .close {
            color: white;
            float: right;
            font-size: 28px;
            font-weight: bold;
        }
        .close:hover,
        .close:focus {
            color: #000;
            text-decoration: none;
            cursor: pointer;
        }
        label {
            display: inline-block;
            width: 140px;
        }
        input {
            width: calc(100% - 150px);
            padding: 5px;
            margin: 5px 0;
            box-sizing: border-box;
        }
    </style>
    """

    # JavaScript
    script_html = """
    <script>
    function openEditModal(id, estado, lat, lon, poblacion, region) {
        document.getElementById('editForm').dataset.id = id;
        document.getElementById('estado').value = estado;
        document.getElementById('lat').value = lat;
        document.getElementById('lon').value = lon;
        document.getElementById('poblacion').value = poblacion;
        document.getElementById('region').value = region;
        document.getElementById('editModal').style.display = "block";
    }

    function closeEditModal() {
        document.getElementById('editModal').style.display = "none";
    }

    async function submitEdit() {
        let form = document.getElementById('editForm');
        let recordId = form.dataset.id;
        let estado = document.getElementById('estado').value;
        let lat = document.getElementById('lat').value;
        let lon = document.getElementById('lon').value;
        let poblacion = document.getElementById('poblacion').value;
        let region = document.getElementById('region').value;

        console.log("Datos a enviar:", {
            "estado": estado,
            "lat": lat,
            "lon": lon,
            "poblacion": poblacion,
            "region": region
        });

        try {
            let response = await fetch(`http://localhost:5000/api/update_record/${recordId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    "estado": estado,
                    "lat": lat,
                    "lon": lon,
                    "poblacion": poblacion,
                    "region": region
                })
            });
            if (response.ok) {
                alert(`Registro ${recordId} editado exitosamente`);
                closeEditModal();
                window.parent.postMessage('reloadData', '*');  // Envía un mensaje al contenedor padre para recargar los datos
            } else {
                let error = await response.text();
                alert(`Error al editar el registro ${recordId}: ${error}`);
            }
        } catch (error) {
            alert(`Error al editar el registro ${recordId}: ${error.message}`);
        }
    }

    async function deleteRecord(recordId) {
        console.log("delete record " + recordId);
        try {
            let response = await fetch(`http://localhost:5000/api/delete_record/${recordId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'  // Opcional, pero puede ayudar a evitar problemas con CORS
                }
            });
            if (response.ok) {
                alert(`Registro ${recordId} eliminado exitosamente`);
                window.parent.postMessage('reloadData', '*');  // Envía un mensaje al contenedor padre para recargar los datos
            } else {
                let error = await response.text();
                alert(`Error al eliminar el registro ${recordId}: ${error}`);
            }
        } catch (error) {
            alert(`Error al eliminar el registro ${recordId}: ${error.message}`);
        }
    }

    </script>
    """

    return table_html + modal_html + script_html



def render_table(df):
    html_content = generate_table_html(df)
    st.components.v1.html(html_content, height=600, scrolling=True)



df = load_data()

if df is not None:
    def actualizar_visualizacion(df):

        st.title("Mostrar datos")
        # Reordenar columnas del DataFrame
        df = df[['id', 'estado', 'lat', 'lon', 'poblacion', 'region']]

        render_table(df)




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

    # Crear dos columnas en la misma fila
    col1, col2 = st.columns(
        [1, 3.9])  # Puedes ajustar el tamaño de las columnas si es necesario

    with col1:

        if st.button('Agregar a la DB'):
            if nuevo_estado and nueva_poblacion and nueva_region and validar_coordenadas(
                    nueva_latitud, nueva_longitud):
                new_data = pd.DataFrame({
                    'estado': [nuevo_estado],
                    'poblacion': [nueva_poblacion],
                    'region': [nueva_region],
                    'lat': [nueva_latitud],
                    'lon': [nueva_longitud]
                })
                add_record_to_db(
                    new_data)  # Llama a la función para agregar a la base de datos
            else:
                st.warning(
                    'Por favor complete todos los campos o ingrese coordenadas válidas. '
                    'Latitud debe estar entre -90 y 90. Longitud debe estar entre -180 y 180.'
                )

    # Columna 2 para el segundo botón
    with col2:

        if st.button('Agregar'):
            if nuevo_estado and nueva_poblacion and nueva_region and validar_coordenadas(
                    nueva_latitud, nueva_longitud):
                new_data = pd.DataFrame({
                    'estado': [nuevo_estado],
                    'poblacion': [nueva_poblacion],
                    'region': [nueva_region],
                    'lat': [nueva_latitud],
                    'lon': [nueva_longitud]
                })
                add_data_to_redis(
                    new_data)  # No se necesita updated_df, la página se recargará
            else:
                st.warning(
                    'Por favor complete todos los campos o ingrese coordenadas válidas. '
                    'Latitud debe estar entre -90 y 90. Longitud debe estar entre -180 y 180.'
                )



    # Opción para editar registros existentes
    st.subheader('Editar Registro Existente')

    registros = df

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
    st.error("Error al cargar los datos")

    if df is not None:
        st.write(df)
