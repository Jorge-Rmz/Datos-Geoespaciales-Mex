from flask import Flask, jsonify, request
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


def save_data(df):
    # Renombrar las columnas a su forma original antes de guardar
    column_rename = {
        'Nombre del País': 'Country Name',
        'Código del País': 'Country Code'
    }
    column_rename.update({f'Año {year}': str(year) for year in range(1960, 2015)})
    df = df.rename(columns=column_rename)
    df.to_csv(file_path, index=False)


def add_new_record(data):
    df = load_data()
    country = data['Nombre del País']
    year = data['Año']
    consumo = data['Consumo']

    if country not in df['Nombre del País'].values:
        # Añadir nuevo país si no existe
        new_row = {col: None for col in df.columns}
        new_row['Nombre del País'] = country
        new_row['Código del País'] = 'N/A'  # Puedes ajustar esto según sea necesario
        new_row[year] = consumo
        df = df.append(new_row, ignore_index=True)
    else:
        # Actualizar el registro existente
        df.loc[df['Nombre del País'] == country, year] = consumo

    save_data(df)
    return {"message": "Registro añadido correctamente"}
