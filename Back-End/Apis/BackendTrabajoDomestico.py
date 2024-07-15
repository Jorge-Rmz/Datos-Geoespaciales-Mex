from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

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

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")


