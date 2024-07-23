from flask import Flask, jsonify, request
import pandas as pd
import redis
import json
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, text, update
from sqlalchemy.exc import OperationalError, SQLAlchemyError, IntegrityError
import psycopg2
from psycopg2 import OperationalError
from sqlalchemy.orm import sessionmaker
import time
app = Flask(__name__)

# Ruta del archivo CSV
file_path = "datos/data.csv"
data_key = 'geospatial_data1'

# Configuración de Redis
redis_host = "redis"
redis_port = 6379
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Configuración de PostgreSQL
POSTGRES_HOST = "postgres"
POSTGRES_PORT = "5432"
POSTGRES_DB = "data_mex"
POSTGRES_USER = "user_mex"
POSTGRES_PASSWORD = "mex_231**#"
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Definición de la tabla
metadata = MetaData()

estados_mexico = Table(
    'estados_mexico', metadata,
    Column('id', Integer, primary_key=True),
    Column('estado', String(255), unique=True, nullable=False),
    Column('lat', Float),
    Column('lon', Float),
    Column('poblacion', Integer),
    Column('region', String(255))
)


def create_record(estado, lat, lon, poblacion, region):
    session = Session()
    try:
        new_record = {
            'estado': estado,
            'lat': lat,
            'lon': lon,
            'poblacion': poblacion,
            'region': region
        }
        session.execute(estados_mexico.insert().values(new_record))
        session.commit()
        return {"message": "Registro creado exitosamente."}, 201
    except IntegrityError as e:
        session.rollback()
        if "duplicate key value violates unique constraint" in str(e.orig):
            return {"error": f"El estado '{estado}' ya existe."}, 409
        return {"error": f"Error de integridad: {e}"}, 400
    except SQLAlchemyError as e:
        session.rollback()
        return {"error": f"Error al crear el registro: {e}"}, 400
    finally:
        session.close()


def update_record(id, **kwargs):
    session = Session()
    try:
        # Verificar si el registro existe
        existing_record = session.query(estados_mexico).filter_by(id=id).first()
        if not existing_record:
            print(f"Registro con ID {id} no encontrado.")
            return {"error": "El registro con el ID proporcionado no existe."}, 404

        # Actualizar el registro con los datos restantes en kwargs
        print(f"Actualizando el registro con ID {id} con datos {kwargs}")
        stmt = (
            update(estados_mexico)
            .where(estados_mexico.c.id == id)
            .values(**kwargs)
        )
        session.execute(stmt)
        session.commit()
        print(f"Registro con ID {id} actualizado exitosamente.")
        return {"message": "Registro actualizado exitosamente."}, 200
    except IntegrityError as e:
        session.rollback()
        if "duplicate key value violates unique constraint" in str(e.orig):
            print(f"Error de integridad: {e}")
            return {"error": "El estado ya existe."}, 409
        print(f"Error de integridad: {e}")
        return {"error": f"Error de integridad: {e}"}, 400
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error al actualizar el registro: {e}")
        return {"error": f"Error al actualizar el registro: {e}"}, 400
    except Exception as e:
        session.rollback()
        print(f"Error inesperado: {e}")
        return {"error": f"Error inesperado: {e}"}, 500
    finally:
        session.close()


def delete_record(id):
    print("funcion delete record")
    session = Session()
    try:
        stmt = estados_mexico.delete().where(estados_mexico.c.id == id)
        session.execute(stmt)
        session.commit()
        return {"Registro eliminado exitosamente."}, 201
    except SQLAlchemyError as e:
        session.rollback()
        return {f"Error al eliminar el registro: {e}"}, 400
    finally:
        session.close()


def get_data_from_db():
    metadata = MetaData()
    data = []

    try:
        # Conectar y obtener datos
        with engine.connect() as connection:
            # Consulta SQL en orden ascendente por la columna 'id'
            result = connection.execute(text("SELECT * FROM estados_mexico ORDER BY id ASC"))

            # Convertir los resultados a una lista de diccionarios
            for row in result:
                data.append(dict(row._mapping))
    except SQLAlchemyError as e:
        # Verificar el código de error de PostgreSQL
        if hasattr(e.orig, 'pgcode') and e.orig.pgcode == '42P01':  # Código de error para "tabla no existe"
            return jsonify({"status": "error", "message": "La tabla 'estados_mexico' no existe."})
        else:
            return jsonify({"status": "error", "message": f"Error al recuperar datos: {e}"})

    return jsonify(data)


def load_data():
    try:
        # Carga el archivo CSV con datos
        df = pd.read_csv(file_path, encoding='utf-8')
        # Guarda los datos en Redis
        redis_client.set(data_key, json.dumps(df.to_dict(orient='records')))
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo {file_path} no se encontró.")
    except pd.errors.ParserError:
        raise ValueError(f"Error al parsear el archivo {file_path}.")
    except Exception as e:
        raise Exception(f"Ocurrió un error: {e}")


def check_db_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM estados_mexico"))
            if result.fetchone():
                return {"status": "success", "message": "Database connection successful"}
            else:
                return {"status": "error", "message": "Database connection failed"}
    except OperationalError as e:
        return {"status": "error", "message": str(e)}


def wait_for_postgres():
    while True:
        try:
            conn = psycopg2.connect(dbname='postgres', user=POSTGRES_USER,
                                    password=POSTGRES_PASSWORD,
                                    host=POSTGRES_HOST, port=POSTGRES_PORT)
            conn.close()
            print("PostgreSQL está disponible.")
            return
        except OperationalError:
            print("Esperando a que PostgreSQL esté disponible...")
            time.sleep(10)


def create_database():
    try:
        # Conectar al servidor de PostgreSQL sin especificar la base de datos
        conn = psycopg2.connect(dbname='postgres', user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
        conn.autocommit = True  # Necesario para ejecutar CREATE DATABASE
        with conn.cursor() as cursor:
            # Verificar si la base de datos ya existe
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{POSTGRES_DB}'")
            if cursor.fetchone():
                print(f"Base de datos '{POSTGRES_DB}' ya existe.")
            else:
                cursor.execute(f"CREATE DATABASE {POSTGRES_DB}")
                print(f"Base de datos '{POSTGRES_DB}' creada correctamente")

        # Conectar a la nueva base de datos (¡aquí está el cambio!)
        conn.close()  # Cerrar la conexión actual
        conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
        with conn.cursor() as cursor:
            # Otorgar privilegios al usuario en la nueva base de datos
            cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {POSTGRES_DB} TO {POSTGRES_USER};")
            cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {POSTGRES_USER};")
            print(f"Privilegios otorgados al usuario '{POSTGRES_USER}' en la base de datos '{POSTGRES_DB}'.")
    except OperationalError as e:
        print(f"Error al crear la base de datos o al otorgar privilegios: {e}")
    finally:
        conn.close()


def init_db():
    try:
        # Conectar al servidor de PostgreSQL
        with engine.connect() as connection:
            # Verificar si la tabla existe
            table_exists = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'estados_mexico'
                );
            """)).scalar()

            if not table_exists:
                # Crear la tabla si no existe
                connection.execute(text("""
                    CREATE TABLE estados_mexico (
                        id SERIAL PRIMARY KEY,
                        estado VARCHAR(255) UNIQUE NOT NULL,
                        lat FLOAT,
                        lon FLOAT,
                        poblacion INT,
                        region VARCHAR(255)
                    );
                """))
                print("Tabla 'estados_mexico' creada correctamente.")
            else:
                print("La tabla 'estados_mexico' ya existe.")

            # Insertar datos iniciales
            data = [
                (
                'Aguascalientes', 21.8853, -102.2916, 1434639, 'Centro-Norte'),
                ('Baja California', 32.6246, -115.4523, 3769020, 'Noroeste'),
                (
                'Baja California Sur', 24.1444, -110.3005, 798447, 'Noroeste'),
                ('Campeche', 19.8301, -90.5349, 928363, 'Sur-Sureste'),
                ('Chiapas', 16.7569, -93.1292, 5543828, 'Sur-Sureste'),
                ('Chihuahua', 28.6330, -106.0691, 3801487, 'Noroeste'),
                ('Ciudad de México', 19.4326, -99.1332, 9209944, 'Centro'),
                ('Coahuila', 25.4380, -100.9770, 3146771, 'Noroeste'),
                ('Colima', 19.2452, -103.7250, 731391, 'Centro'),
                ('Durango', 24.0277, -104.6532, 1832650, 'Noroeste'),
                ('Estado de México', 19.4969, -99.7233, 17427790, 'Centro'),
                ('Guanajuato', 21.0190, -101.2574, 6183976, 'Centro-Norte'),
                ('Guerrero', 17.4392, -99.5451, 3533251, 'Sur-Sureste'),
                ('Hidalgo', 20.1011, -98.7624, 3082841, 'Centro'),
                ('Jalisco', 20.6597, -103.3496, 8348193, 'Centro-Norte'),
                ('Michoacán', 19.7059, -101.1950, 4828681, 'Centro-Norte'),
                ('Morelos', 18.6813, -99.1013, 1971520, 'Centro'),
                ('Nayarit', 21.7514, -104.8455, 1282146, 'Centro-Norte'),
                ('Nuevo León', 25.6866, -100.3161, 5557720, 'Noreste'),
                ('Oaxaca', 17.0732, -96.7266, 4132148, 'Sur-Sureste'),
                ('Puebla', 19.0413, -98.2062, 6583278, 'Centro'),
                ('Querétaro', 20.5888, -100.3899, 2279632, 'Centro-Norte'),
                ('Quintana Roo', 19.1817, -88.4791, 1857985, 'Sur-Sureste'),
                ('San Luis Potosí', 22.1566, -100.9855, 2822235,
                 'Centro-Norte'),
                ('Sinaloa', 24.8041, -107.4937, 3078762, 'Noroeste'),
                ('Sonora', 29.0729, -110.9559, 2944842, 'Noroeste'),
                ('Tabasco', 17.8409, -92.6189, 2395272, 'Sur-Sureste'),
                ('Tamaulipas', 24.2669, -98.8363, 3650601, 'Noreste'),
                ('Tlaxcala', 19.3182, -98.2370, 1342977, 'Centro'),
                ('Veracruz', 19.1738, -96.1342, 8112505, 'Sur-Sureste'),
                ('Yucatán', 20.7099, -89.0943, 2320894, 'Sur-Sureste'),
                ('Zacatecas', 22.7709, -102.5832, 1622138, 'Centro-Norte')
            ]

            # Ejecutar la inserción de datos
            connection.execute(text("""
                INSERT INTO estados_mexico (estado, lat, lon, poblacion, 
                region) VALUES (:estado, :lat, :lon, :poblacion, :region)
                ON CONFLICT (estado) DO NOTHING;
            """), [{'estado': estado, 'lat': lat, 'lon': lon,
                    'poblacion': poblacion, 'region': region} for
                   estado, lat, lon, poblacion, region in data])
            print(
                "Datos iniciales insertados correctamente en la"
                " tabla 'estados_mexico'.")

    except SQLAlchemyError as e:
        print(f"Error al inicializar la base de datos: {e}")

