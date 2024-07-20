from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

# Ruta del archivo CSV
file_path = "datos/66375.csv"


def load_data():
    df = pd.read_csv(file_path, encoding='utf-8', sep=';')
    return df


def save_data(df):
    df.to_csv(file_path, index=False, encoding='utf-8', sep=';')


def add_new_poblacion(data):
    df = load_data()
    nacionalidad = data['Nacionalidad']
    periodo = data['Periodo']
    sexo = data['Sexo']
    total = data['Total']

    if nacionalidad not in df['Nacionalidad'].values:
        # Añadir nuevo país si no existe
        new_row = pd.DataFrame({
            'Nacionalidad': [nacionalidad],
            'Periodo': [periodo],
            'Sexo': [sexo],
            'Total': [total]
        })
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        # Actualizar el registro existente
        df.loc[(df['Nacionalidad'] == nacionalidad) & (df['Periodo'] == periodo) & (df['Sexo'] == sexo), 'Total'] = total

    save_data(df)
    return {"message": "Registro añadido correctamente"}