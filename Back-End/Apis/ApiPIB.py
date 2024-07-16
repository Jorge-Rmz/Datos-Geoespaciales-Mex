from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# Ruta del archivo CSV
file_path = "Back-End/datos/pib.csv"

def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path)
        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")


