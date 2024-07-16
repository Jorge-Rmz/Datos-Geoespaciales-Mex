from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# Ruta del archivo CSV
file_path = "datos/66375.csv"

def load_data():
    try:
        df = pd.read_csv(file_path, encoding='utf-8', delimiter=';')
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")

def save_data(df):
    df.to_csv(file_path, index=False, encoding='utf-8', sep=';')

def add_new_record(data):
    df = load_data()
    sexo = data['Sexo']
    nacionalidad = data['Nacionalidad']
    periodo = data['Periodo']
    total = data['Total']

    if not ((df['Sexo'] == sexo) & (df['Nacionalidad'] == nacionalidad) & (df['Periodo'] == periodo)).any():
        new_row = pd.DataFrame([{
            'Sexo': sexo,
            'Nacionalidad': nacionalidad,
            'Periodo': periodo,
            'Total': total
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        return {"message": "Registro añadido correctamente"}
    else:
        return {"error": "El registro ya existe."}
