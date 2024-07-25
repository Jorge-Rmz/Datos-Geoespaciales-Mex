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
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('estado', String(255), unique=True, nullable=False),
    Column('lat', Float),
    Column('lon', Float),
    Column('poblacion', Integer),
    Column('region', String(255))
)

# Tabla de control para verificar si los datos iniciales ya fueron cargados
init_control = Table(
    'init_control', metadata,
    Column('id', Integer, primary_key=True),
    Column('table_name', String(255), unique=True, nullable=False),
    Column('initialized', Integer, default=0)
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
        # Insertar en la base de datos
        session.execute(estados_mexico.insert().values(new_record))
        session.commit()

        # Agregar el nuevo registro a Redis
        redis_data = redis_client.get(data_key)
        if redis_data:
            redis_data = json.loads(redis_data)
        else:
            redis_data = []

        new_record_with_id = {'id': session.execute(text("SELECT LASTVAL()")).scalar(), **new_record}
        redis_data.append(new_record_with_id)
        redis_client.set(data_key, json.dumps(redis_data))

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
            return {"error": "El registro con el ID proporcionado no existe."}, 404

        # Actualizar el registro en la base de datos
        stmt = update(estados_mexico).where(estados_mexico.c.id == id).values(**kwargs)
        session.execute(stmt)
        session.commit()

        # Actualizar el registro en Redis
        redis_data = redis_client.get(data_key)
        if redis_data:
            redis_data = json.loads(redis_data)
            for record in redis_data:
                if record['id'] == id:
                    record.update(kwargs)
                    break
            redis_client.set(data_key, json.dumps(redis_data))

        return {"message": "Registro actualizado exitosamente."}, 200
    except IntegrityError as e:
        session.rollback()
        if "duplicate key value violates unique constraint" in str(e.orig):
            return {"error": "El estado ya existe."}, 409
        return {"error": f"Error de integridad: {e}"}, 400
    except SQLAlchemyError as e:
        session.rollback()
        return {"error": f"Error al actualizar el registro: {e}"}, 400
    finally:
        session.close()


def delete_record(id):
    session = Session()
    try:
        # Eliminar el registro de la base de datos
        stmt = estados_mexico.delete().where(estados_mexico.c.id == id)
        session.execute(stmt)
        session.commit()

        # Eliminar el registro de Redis
        redis_data = redis_client.get(data_key)
        if redis_data:
            redis_data = json.loads(redis_data)
            redis_data = [record for record in redis_data if record['id'] != id]
            redis_client.set(data_key, json.dumps(redis_data))

        return {"message": "Registro eliminado exitosamente."}, 201
    except SQLAlchemyError as e:
        session.rollback()
        return {"error": f"Error al eliminar el registro: {e}"}, 400
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
        conn = psycopg2.connect(dbname='data_mex', user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST, port=POSTGRES_PORT)
        conn.autocommit = True  # Necesario para ejecutar CREATE DATABASE
        with conn.cursor() as cursor:
            # Verificar si la base de datos ya existe
            cursor.execute(f"SELECT * FROM pg_database WHERE datname = '{POSTGRES_DB}'")
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
        with engine.connect() as connection:
            # Verificar si la tabla ya existe
            table_exists = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'estados_mexico'
                );
            """)).scalar()

            if not table_exists:
                # Crear la tabla si no existe
                metadata.create_all(engine)
                print("Tabla 'estados_mexico' creada correctamente.")

            # Verificar si los datos iniciales ya fueron cargados
            init_control_exists = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'init_control'
                );
            """)).scalar()

            if not init_control_exists:
                # Crear la tabla de control si no existe
                metadata.create_all(engine)
                print("Tabla 'init_control' creada correctamente.")

            # Verificar si los datos ya fueron inicializados
            init_record = connection.execute(text("""
                SELECT initialized FROM init_control WHERE table_name = 'estados_mexico';
            """)).fetchone()

            if init_record and init_record[0] == 1:
                print("Los datos iniciales ya fueron cargados.")
                return

            # Leer datos desde el archivo CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            df['id'] = range(1, len(df) + 1)  # Asignar IDs únicos
            data = df.to_dict(orient='records')

            # Insertar datos en PostgreSQL
            for record in data:
                estado = record['estado']
                lat = record['lat']
                lon = record['lon']
                poblacion = record['poblacion']
                region = record['region']
                id = record['id']

                try:
                    print(f"Insertando: {id}, {estado}, {lat}, {lon}, {poblacion}, {region}")
                    query = text("""
                        INSERT INTO estados_mexico (id, estado, lat, lon, poblacion, region)
                        VALUES (:id, :estado, :lat, :lon, :poblacion, :region)
                        ON CONFLICT (estado) DO NOTHING;
                    """)
                    connection.execute(query, {'id': id, 'estado': estado,
                                               'lat': lat, 'lon': lon,
                                               'poblacion': poblacion,
                                               'region': region})
                except SQLAlchemyError as e:
                    print(f"Error al insertar {estado}: {e}")

            connection.commit()
            print("Datos iniciales insertados correctamente en la tabla 'estados_mexico'.")

            # Cargar los datos en Redis
            redis_client.set(data_key, json.dumps(data))
            print("Datos cargados en Redis correctamente.")

            # Marcar los datos como inicializados en la tabla de control
            connection.execute(text("""
                INSERT INTO init_control (table_name, initialized)
                VALUES ('estados_mexico', 1)
                ON CONFLICT (table_name) DO UPDATE
                SET initialized = 1;
            """))
            connection.commit()

    except SQLAlchemyError as e:
        print(f"Error al inicializar la base de datos: {e}")

    except Exception as e:
        print(f"Error general: {e}")



