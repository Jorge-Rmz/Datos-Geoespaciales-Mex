from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# Ruta del archivo CSV
file_path = "Back-End/datos/API_EG.USE.ELEC.KH.PC_DS2_es_csv_v2_834019.csv"

def load_data():
    df = pd.read_csv(file_path)
    years = [str(year) for year in range(1960, 2015)]
    columns = ['Country Name', 'Country Code'] + years
    df = df[columns]
    column_rename = {
        'Country Name': 'Nombre del País',
        'Country Code': 'Código del País'
    }
    column_rename.update({year: f'Año {year}' for year in years})
    df = df.rename(columns=column_rename)

    return df

