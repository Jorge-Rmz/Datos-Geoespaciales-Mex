import pandas as pd
import mariadb
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Ruta del archivo CSV
file_path = "datos/trabajo_domestico.csv"

# Configuración de la conexión a la base de datos MariaDB
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'rootpassword'),
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'datos_geo')
}

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS datos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        entidad_federativa VARCHAR(255),
        periodo INT,
        horas_domesticas_y_cuidado FLOAT,
        tasa_trabajo_domestico FLOAT,
        tasa_trabajo_cuidado FLOAT
    )
    """
    cursor.execute(create_table_query)

def table_is_empty(cursor):
    check_table_query = "SELECT COUNT(*) FROM datos"
    cursor.execute(check_table_query)
    result = cursor.fetchone()
    return result[0] == 0

def insert_data(cursor, df):
    for index, row in df.iterrows():
        insert_query = """
        INSERT INTO datos (
            entidad_federativa, 
            periodo, 
            horas_domesticas_y_cuidado, 
            tasa_trabajo_domestico, 
            tasa_trabajo_cuidado
        ) VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(insert_query, (
            row['Entidad federativa'],
            row['Periodo'],
            row['Horas Domesticas y Cuidado'],
            row['Tasa Trabajo Domestico'],
            row['Tasa Trabajo Cuidado']
        ))

def load_data():
    try:
        print(f"Verificando existencia del archivo en: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo {file_path} no se encontró.")

        print("Archivo encontrado, cargando datos...")
        df = pd.read_csv(file_path, encoding='utf-8')
        print("Datos cargados, primeras filas del DataFrame:")
        print(df.head())

        print("Conectando a la base de datos...")
        conn = mariadb.connect(**db_config)
        cursor = conn.cursor()
        print("Conexión establecida.")

        print("Creando tabla si no existe...")
        create_table(cursor)
        print("Tabla creada/existente.")

        print("Verificando si la tabla está vacía...")
        if table_is_empty(cursor):
            print("La tabla está vacía, insertando datos...")
            insert_data(cursor, df)
            print("Datos insertados.")
        else:
            print("La tabla ya contiene datos, no se insertaron nuevos datos.")

        conn.commit()
        cursor.close()
        conn.close()
        print("Conexión cerrada.")

        return df

    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise e
    except pd.errors.ParserError as e:
        print(f"Error al parsear el archivo {file_path}: {e}")
        raise e
    except mariadb.Error as e:
        print(f"Error conectando a la base de datos: {e}")
        raise e
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        raise e

def create_dato(cursor, data):
    insert_query = """
    INSERT INTO datos (
        entidad_federativa, 
        periodo, 
        horas_domesticas_y_cuidado, 
        tasa_trabajo_domestico, 
        tasa_trabajo_cuidado
    ) VALUES (?, ?, ?, ?, ?)
    """
    cursor.execute(insert_query, (
        data['entidad_federativa'],
        data['periodo'],
        data['horas_domesticas_y_cuidado'],
        data['tasa_trabajo_domestico'],
        data['tasa_trabajo_cuidado']
    ))

def get_all_datos(cursor):
    select_query = "SELECT * FROM datos"
    cursor.execute(select_query)
    rows = cursor.fetchall()
    datos = []
    for row in rows:
        datos.append({
            'id': row[0],
            'entidad_federativa': row[1],
            'periodo': row[2],
            'horas_domesticas_y_cuidado': row[3],
            'tasa_trabajo_domestico': row[4],
            'tasa_trabajo_cuidado': row[5]
        })
    return datos

def get_dato_by_id(cursor, id):
    select_query = "SELECT * FROM datos WHERE id = ?"
    cursor.execute(select_query, (id,))
    row = cursor.fetchone()
    if row:
        return {
            'id': row[0],
            'entidad_federativa': row[1],
            'periodo': row[2],
            'horas_domesticas_y_cuidado': row[3],
            'tasa_trabajo_domestico': row[4],
            'tasa_trabajo_cuidado': row[5]
        }
    else:
        return None

def update_dato_by_id(cursor, id, data):
    update_query = """
    UPDATE datos SET 
        entidad_federativa = ?, 
        periodo = ?, 
        horas_domesticas_y_cuidado = ?, 
        tasa_trabajo_domestico = ?, 
        tasa_trabajo_cuidado = ?
    WHERE id = ?
    """
    cursor.execute(update_query, (
        data['entidad_federativa'],
        data['periodo'],
        data['horas_domesticas_y_cuidado'],
        data['tasa_trabajo_domestico'],
        data['tasa_trabajo_cuidado'],
        id
    ))

def delete_dato_by_id(cursor, id):
    delete_query = "DELETE FROM datos WHERE id = ?"
    cursor.execute(delete_query, (id,))