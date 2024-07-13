import redis
import json
import pandas as pd


def connect_redis(host='localhost', port=6379, db=0):
    return redis.Redis(host=host, port=port, db=db)


def get_data_from_redis(redis_conn, key):
    if redis_conn.exists(key):
        return pd.DataFrame(json.loads(redis_conn.get(key)))
    return None


def load_data_from_csv(file_path):
    return pd.read_csv(file_path)
