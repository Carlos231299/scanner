import pymysql
import os

# Manual config since we can't easily import from db.py if it depends on Flask context
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'db': os.environ.get('DB_NAME', 'qr_entry_db'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def fix_enum():
    print("Connecting to DB...")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        try:
            with connection.cursor() as cursor:
                # 1. Check current structure
                print("Checking current columns...")
                cursor.execute("DESCRIBE users")
                columns = cursor.fetchall()
                for col in columns:
                    if col['Field'] == 'role':
                        print(f"Current Role Type: {col['Type']}")

                # 2. Modify ENUM
                print("Modifying 'role' column...")
                alter_query = "ALTER TABLE users MODIFY COLUMN role ENUM('admin', 'employee', 'supervisor') NOT NULL DEFAULT 'employee'"
                cursor.execute(alter_query)
                connection.commit()
                print("Successfully altered table.")
                
                # 3. Verify
                cursor.execute("DESCRIBE users")
                columns = cursor.fetchall()
                for col in columns:
                    if col['Field'] == 'role':
                        print(f"New Role Type: {col['Type']}")
                        
        finally:
            connection.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_enum()
