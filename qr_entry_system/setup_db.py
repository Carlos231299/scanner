print("Starting setup_db.py...")
try:
    import pymysql
    import pymysql.cursors
    import os
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    exit(1)


print("Defining constants...")
DB_NAME = os.environ.get('DB_NAME', 'qr_entry_db')

def force_reset_tables(cursor):
    print("!!! FORCING FULL TABLE RESET !!!")
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS logs")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("Tables dropped successfully.")
    except Exception as e:
        print(f"Error dropping tables: {e}")

TABLES = {}
TABLES['users'] = (
    "CREATE TABLE `users` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `username` varchar(50) NOT NULL,"
    "  `password_hash` varchar(255) DEFAULT NULL,"
    "  `role` enum('admin','employee','supervisor') NOT NULL DEFAULT 'employee',"
    "  `cedula` varchar(20) DEFAULT NULL,"
    "  `area` varchar(100) DEFAULT NULL,"
    "  `qr_code_data` varchar(255) NOT NULL,"
    "  `face_descriptor` JSON DEFAULT NULL,"
    "  PRIMARY KEY (`id`),"
    "  UNIQUE KEY `username` (`username`)"
    ") ENGINE=InnoDB")

TABLES['logs'] = (
    "CREATE TABLE `logs` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `user_id` int(11) NOT NULL,"
    "  `type` enum('entry','exit','start_lunch','end_lunch') NOT NULL,"
    "  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`),"
    "  KEY `user_id` (`user_id`),"
    "  CONSTRAINT `logs_ibfk_1` FOREIGN KEY (`user_id`) "
    "     REFERENCES `users` (`id`) ON DELETE CASCADE"
    ") ENGINE=InnoDB")

def create_database(cursor):
    try:
        print(f"Attempting to create database {DB_NAME}...")
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
        print("Database created.")
    except pymysql.MySQLError as err:
        print("Failed creating database: {}".format(err))
        exit(1)

print("Starting main execution...")
try:
    print("Connecting to MySQL...")
    # Connect to server (no DB selected yet)
    cnx = pymysql.connect(
        user=os.environ.get('DB_USER', 'root'), 
        password=os.environ.get('DB_PASSWORD', ''), 
        host=os.environ.get('DB_HOST', '127.0.0.1'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Connected to MySQL.")
    cursor = cnx.cursor()
    print("Cursor created.")

    try:
        print(f"Switching to database {DB_NAME}...")
        cursor.execute("USE {}".format(DB_NAME))
        print("Database selected.")
    except pymysql.MySQLError as err:
        print(f"Error switching to DB: {err}")
        # Check for "Unknown database" error (code 1049)
        if err.args[0] == 1049:
            print("Database {} does not exist.".format(DB_NAME))
            create_database(cursor)
            print("Database {} created successfully.".format(DB_NAME))
            cnx.select_db(DB_NAME)
        else:
            print(err)
            exit(1)

    # Reset tables to ensure new schema is applied
    print("Resetting tables (DROP IF EXISTS)...")
    try:
        cursor.execute("DROP TABLE IF EXISTS logs")
        cursor.execute("DROP TABLE IF EXISTS users")
        print("Tables dropped.")
    except pymysql.MySQLError as err:
        print(f"Warning dropping tables: {err}")

    # Reset tables to ensure new schema is applied
    print("Resetting tables (DROP IF EXISTS)...")
    try:
        cursor.execute("DROP TABLE IF EXISTS logs")
        cursor.execute("DROP TABLE IF EXISTS users")
        print("Tables dropped.")
    except pymysql.MySQLError as err:
        print(f"Warning dropping tables: {err}")

    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except pymysql.MySQLError as err:
            # Check for "Table already exists" error (code 1050)
            if err.args[0] == 1050:
                print("already exists.")
            else:
                print(err)
        else:
            print("OK")

    cursor.close()
    cnx.close()
    print("Done.")
except pymysql.MySQLError as err:
    print("Error connecting to MySQL: {}".format(err))
    print("Make sure XAMPP MySQL is running!")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
