# koneksi.py
import pymysql
from config import DB_CONFIG

def db_query(sql, params=None):
    """
    Jalankan SELECT dan return rows (list of dict).
    """
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()
