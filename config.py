# config.py
import pymysql.cursors

TELEGRAM_BOT_TOKEN = "8295989926:AAHS9tmVGflD6DLYhBzEVHMmZ-orj-lDskc"

DB_CONFIG = {
    "host": "10.10.10.9",
    "user": "admin",
    "password": "S!Mgos2@rswh",
    "database": "inventory",
    "cursorclass": pymysql.cursors.DictCursor,
}

ALLOWED_CHAT_IDS = [
    # contoh: 123456789,
]
