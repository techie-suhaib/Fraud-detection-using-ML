import os
import mysql.connector
from mysql.connector import errorcode

def load_env():
    env = {}
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
    return env

ENV = load_env()

def get_db_connection(include_db=True):
    config = {
        'host': ENV.get('DB_HOST', 'localhost'),
        'port': int(ENV.get('DB_PORT', '3306')),
        'user': ENV.get('DB_USER', 'root'),
        'password': ENV.get('DB_PASSWORD', ''),
        'use_pure': True
    }
    if include_db:
        config['database'] = ENV.get('DB_NAME', 'fraud_detection_db')
        
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise err

def execute_query(query, params=(), commit=False, fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    result = None
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
            result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
        elif fetch:
            result = cursor.fetchall()
    except Exception as e:
        conn.rollback()
        print(f"Error executing query: {query}\nError: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
    return result
