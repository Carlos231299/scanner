from werkzeug.security import generate_password_hash
from db import get_db, close_db
from flask import Flask
import secrets

# Minimal app context to use get_db
app = Flask(__name__)
app.secret_key = 'dev'

def create_admin():
    with app.app_context():
        db = get_db()
        username = 'admin'
        password = 'admin123'  # Default password
        role = 'admin'
        qr_data = f"user:{username}:{secrets.token_hex(4)}"

        try:
            with db.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, qr_code_data) VALUES (%s, %s, %s, %s)",
                    (username, generate_password_hash(password), role, qr_data)
                )
            db.commit()
            print(f"Admin user created successfully.\nUsername: {username}\nPassword: {password}")
        except Exception as e:
            print(f"Error creating admin: {e}")

if __name__ == '__main__':
    create_admin()
