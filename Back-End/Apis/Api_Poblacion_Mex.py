from flask import Flask, jsonify, request
import pandas as pd
import redis
import json

app = Flask(__name__)


# Ruta del archivo CSV
file_path = "datos/data.csv"
data_key = 'geospatial_data1'

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path, encoding='utf-8')

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")


if __name__ == '__main__':
    app.run(debug=True)
