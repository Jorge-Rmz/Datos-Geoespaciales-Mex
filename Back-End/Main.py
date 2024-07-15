from flask import Flask, jsonify
import Apis.BackendTrabajoDomestico as TrabajoDomestico
import Apis.ApiConsumoElectrico as ConsumoElectrico
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return 'API Funcionando'

@app.route('/get_consumo_electrico', methods=['GET'])
def get_consumo_electrico():
    try:
        df = ConsumoElectrico.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        df = TrabajoDomestico.load_data()
        return jsonify(df.to_dict(orient='records'))
    except FileNotFoundError:
        return jsonify({"error": "El archivo de datos no se encuentra."}), 500
    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
