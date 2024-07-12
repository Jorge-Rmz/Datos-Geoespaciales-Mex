from flask import Flask, jsonify
import pandas as pd
import redis
from io import StringIO

app = Flask(__name__)

# Conecta a Redis
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Ruta del archivo CSV
file_path = "Back-End/datos/ssdp02a_por_trab_dom_cui.csv"

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path, encoding='latin1')

        # Renombra las columnas
        df.rename(columns={
            'Suma de porcentajes del total de horas por semana dedicados a actividades domésticas y de cuidado que realizan los integrantes del hogar de 12 y más años': 'Horas Domésticas y Cuidado',
            'Tasa de participación de la población de 12 años y más en trabajo doméstico no remunerado para el propio hogar': 'Tasa Trabajo Doméstico',
            'Tasa de participación de la población de 12 años y más en trabajo no remunerado de cuidado a integrantes del hogar': 'Tasa Trabajo Cuidado'
        }, inplace=True)

        # Almacena en Redis
        redis_client.set('data', df.to_json(orient='split'))

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        data = redis_client.get('data')
        if data:
            df = pd.read_json(StringIO(data), orient='split')
            return jsonify(df.to_dict(orient='records'))
        else:
            df = load_data()
            return jsonify(df.to_dict(orient='records'))
    except redis.ConnectionError as e:
        return jsonify({"error": f"No se pudo conectar a Redis: {e}"}), 500

if __name__ == '__main__':
    app.run(host='localhost', port=8503)
