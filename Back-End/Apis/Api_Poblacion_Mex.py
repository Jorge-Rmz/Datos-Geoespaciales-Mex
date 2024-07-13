from flask import Flask, jsonify, request
import pandas as pd
from Redis_api import connect_redis, get_data_from_redis, load_data_from_csv

app = Flask(__name__)

# Conectar a Redis
r = connect_redis()

# Ruta del archivo CSV
file_path = "Back-End/datos/data.csv"
data_key = 'geospatial_data'


@app.route('/load_data', methods=['GET'])
def load_data():
    try:
        df = load_data_from_csv(file_path)
        return jsonify({"message": "Datos cargados desde el archivo CSV y guardados en Redis."})
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500


@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        df = get_data_from_redis(r, data_key)
        if df is not None:
            return jsonify(df.to_dict(orient='records'))
        else:
            return jsonify({"error": "Datos no encontrados en Redis."}), 404
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500



if __name__ == '__main__':
    app.run(debug=True)
