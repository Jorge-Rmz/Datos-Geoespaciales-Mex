import redis
import json
import pandas as pd


def connect_redis(host='localhost', port=6379, db=0):
    return redis.Redis(host=host, port=port, db=db)


def fetch_data_from_redis(redis_conn, key):
    if redis_conn.exists(key):
        return pd.DataFrame(json.loads(redis_conn.get(key)))
    return None


def save_data_to_redis(redis_conn, key, df):
    redis_conn.set(key, json.dumps(df.to_dict(orient='records')))


def get_data_from_redis(redis_conn, key):
    if redis_conn.exists(key):
        return pd.DataFrame(json.loads(redis_conn.get(key)))
    return None


def load_data_from_csv(file_path):
    return pd.read_csv(file_path)
