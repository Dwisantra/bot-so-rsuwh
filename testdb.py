# testdb.py
from config import DB_CONFIG
import pymysql

conn = pymysql.connect(**DB_CONFIG)
print("✅ Koneksi berhasil ke:", DB_CONFIG["host"])
conn.close()
