from Redis_api import connect_redis, fetch_data_from_redis, load_data_from_csv, save_data_to_redis
from flask import Flask, jsonify

app = Flask(__name__)

r = connect_redis()

file_path = "Back-End/datos/data.csv"
data_key = 'geospatial_data1'

@app.route('/api/load_data', methods=['GET'])
def load_data_to_redis():
    try:
        df = load_data_from_csv(file_path)
        save_data_to_redis(r, data_key, df)
        return jsonify({"message": "Datos cargados desde el archivo CSV y guardados en Redis."})
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/api/get_data', methods=['GET'])
def fetch_data_from_redis_route():
    try:
        df = fetch_data_from_redis(r, data_key)
        if df is not None:
            return jsonify(df.to_dict(orient='records'))
        else:
            return jsonify({"error": "Datos no encontrados en Redis."}), 404
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500
