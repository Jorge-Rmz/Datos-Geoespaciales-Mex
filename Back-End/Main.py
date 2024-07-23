from flask import Flask, jsonify, request
import mariadb
import Apis.BackendTrabajoDomestico as TrabajoDomestico
import Apis.ApiConsumoElectrico as ConsumoElectrico
import Apis.Api_Poblacion_Mex as pm
import Apis.ApiPoblacionPorSexo as Poblacion
import Apis.ApiPIB as PIB
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return 'API Funcionando'

@app.route('/api/get_poblacion_mex', methods=['GET'])
def get_poblacion():
    try:
        df = pm.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/get_consumo_electrico', methods=['GET'])
def get_consumo_electrico():
    try:
        df = ConsumoElectrico.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/post_consumo_electrico', methods=['POST'])
def post_consumo_electrico():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        result = ConsumoElectrico.add_new_record(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

# Endpoints

@app.route('/get_load_data_trabajo_domestico', methods=['GET'])
def get_data():
    try:
        df = TrabajoDomestico.load_data()
        return "Datos cargados y almacenados en la base de datos exitosamente."
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/post_datos_trabajo_domestico', methods=['POST'])
def create_dato_route():
    try:
        data = request.json
        conn = mariadb.connect(**TrabajoDomestico.db_config)
        cursor = conn.cursor()
        TrabajoDomestico.create_dato(cursor, data)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(message="Registro creado exitosamente"), 201
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/get_all_datos_trabajo_domestico', methods=['GET'])
def getall_datos_route():
    try:
        conn = mariadb.connect(**TrabajoDomestico.db_config)
        cursor = conn.cursor()
        datos = TrabajoDomestico.get_all_datos(cursor)
        conn.close()
        return jsonify(datos)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/get_datos_trabajo_domestico', methods=['GET'])
def get_dato_route():
    try:
        id = int(request.args.get('id'))

        conn = mariadb.connect(**TrabajoDomestico.db_config)
        cursor = conn.cursor()
        dato = TrabajoDomestico.get_dato_by_id(cursor, id)
        conn.close()
        if dato:
            return jsonify(dato)
        else:
            return jsonify(error="Registro no encontrado"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/update_datos_trabajo_domestico', methods=['PUT'])
def update_dato_route():
    try:
        id = int(request.args.get('id'))
        data = request.json

        conn = mariadb.connect(**TrabajoDomestico.db_config)
        cursor = conn.cursor()
        TrabajoDomestico.update_dato_by_id(cursor, id, data)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(message="Registro actualizado exitosamente")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/delete_datos_trabajo_domestico', methods=['DELETE'])
def delete_dato_route():
    try:
        id = int(request.args.get('id'))

        conn = mariadb.connect(**TrabajoDomestico.db_config)
        cursor = conn.cursor()
        TrabajoDomestico.delete_dato_by_id(cursor, id)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify(message="Registro eliminado exitosamente")
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/get_poblacion_data', methods=['GET'])
def get_poblacion_data():
    try:
        df = Poblacion.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/post_poblacion', methods=['POST'])
def post_poblacion():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        result = Poblacion.add_new_record(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500


@app.route('/get_pib_data', methods=['GET'])
def get_pib_data():
    try:
        df = PIB.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/post_pib_data', methods=['POST'])
def post_pib_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        result = PIB.add_new_pib(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
