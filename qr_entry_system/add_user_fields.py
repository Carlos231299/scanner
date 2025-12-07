import pymysql
import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'db': os.environ.get('DB_NAME', 'qr_entry_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def migrate():
    print("Connecting to DB...")
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            print("Adding 'cedula' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN cedula VARCHAR(20) UNIQUE AFTER username")
                print("Added 'cedula'.")
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1060: print("'cedula' already exists.")
                else: raise e

            print("Adding 'area' column...")
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN area VARCHAR(50) AFTER cedula")
                print("Added 'area'.")
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1060: print("'area' already exists.")
                else: raise e
        conn.commit()
        print("Migration complete.")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
