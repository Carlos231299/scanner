import pymysql
import os

try:
    cnx = pymysql.connect(
        user=os.environ.get('DB_USER', 'root'), 
        password=os.environ.get('DB_PASSWORD', ''), 
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        database=os.environ.get('DB_NAME', 'qr_entry_db')
    )
    with cnx.cursor() as cursor:
        print("Attempting to add face_descriptor column...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN face_descriptor JSON DEFAULT NULL")
            cnx.commit()
            print("Column added successfully.")
        except pymysql.MySQLError as e:
            if e.args[0] == 1060: # Duplicate column name
                print("Column already exists.")
            else:
                print(f"Error: {e}")
                
except Exception as e:
    print(f"Connection failed: {e}")
