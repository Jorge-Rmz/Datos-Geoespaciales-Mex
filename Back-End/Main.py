from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

import Apis.BackendTrabajoDomestico as TrabajoDomestico
import Apis.ApiConsumoElectrico as ConsumoElectrico
import Apis.Api_Poblacion_Mex as pm
import Apis.ApiPoblacionPorSexo as Poblacion
import Apis.ApiPIB as PIB
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)

# Configura CORS para permitir solicitudes desde cualquier origen
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route('/')
def index():
    return 'API Funcionando'

@app.route('/api/check_db_connection', methods=['GET'])
def db_connection_status():
    return jsonify(pm.check_db_connection())


@app.route('/api/get_data/db/postgres', methods=['GET'])
def get_data_from_db():
    return pm.get_data_from_db()


@app.route('/api/create_record', methods=['POST'])
def create_record_endpoint():
    if request.is_json:
        data = request.get_json()
        print(data)
        estado = data.get('estado')
        lat = data.get('lat')
        lon = data.get('lon')
        poblacion = data.get('poblacion')
        region = data.get('region')
        result = pm.create_record(estado, lat, lon, poblacion, region)
        return jsonify(result)
    else:
        return jsonify({"error": "La solicitud debe ser en formato JSON"}), 415

@app.route('/api/update_record/<int:id>', methods=['PUT'])
def update_data(id):
    try:
        data = request.get_json()
        print("datos editar", data)
        pm.update_record(id, **data)
        return jsonify({'message': 'Registro actualizado exitosamente.'})
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_record/<int:id>', methods=['DELETE'])
def delete_data(id):
    try:
        pm.delete_record(id)
        return jsonify({'message': 'Registro eliminado exitosamente.'})
    except SQLAlchemyError as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/get_data_trabajo_domestico', methods=['GET'])
def get_data():
    try:
        df = TrabajoDomestico.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
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


@app.route('/get_poblacion_data', methods=['GET'])
def get_poblacion_data():
    try:
        df = Poblacion.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500


@app.route('/post_poblacion_data', methods=['POST'])
def post_poblacion_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se proporcionaron datos"}), 400
        result = Poblacion.add_new_poblacion(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
