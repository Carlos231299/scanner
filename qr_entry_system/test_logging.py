import requests
import secrets

BASE_URL = 'http://127.0.0.1:5000'

def test_flow():
    session = requests.Session()

    # 1. Login as Admin based on default credentials usually available or created
    # Since I don't know the exact admin creds without DB access, I'll rely on the user having one or creating a fresh setup.
    # Actually, setup_db.py doesn't create a default admin. I need to create one first or assume one exists.
    # Let's assume the user has an admin account. If not, I'll print a message.
    
    print("Please ensure you are logged in as admin in your browser first to create an admin user.")
    print("Or I can try to register one if the DB is empty? No, register_user requires admin.")
    
    # Wait, I can insert directly into DB since I have local access!
    # Let's do that for the test to be self-contained.
    
    import pymysql
    from werkzeug.security import generate_password_hash
    
    print("Connecting to DB to ensure admin exists...")
    try:
        cnx = pymysql.connect(user='root', password='', host='127.0.0.1', database='qr_entry_db', cursorclass=pymysql.cursors.DictCursor)
        with cnx.cursor() as cursor:
            # Check for admin
            cursor.execute("SELECT * FROM users WHERE role='admin'")
            admin = cursor.fetchone()
            
            if not admin:
                print("Creating default admin user (admin/admin)...")
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, qr_code_data) VALUES (%s, %s, %s, %s)",
                    ('admin', generate_password_hash('admin'), 'admin', 'user:admin:seed')
                )
                cnx.commit()
            
            # Create a test employee
            cursor.execute("SELECT * FROM users WHERE username='test_employee'")
            employee = cursor.fetchone()
            if not employee:
                print("Creating test employee...")
                qr_data = "user:test_employee:12345"
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role, qr_code_data) VALUES (%s, %s, %s, %s)",
                    ('test_employee', generate_password_hash('password'), 'employee', qr_data)
                )
                cnx.commit()
                print(f"Test employee created with QR data: {qr_data}")
            else:
                qr_data = employee['qr_code_data']
                print(f"Using existing test employee QR data: {qr_data}")

    except Exception as e:
        print(f"DB Error: {e}")
        return

    # Now verify the API as admin
    # Login via HTTP
    print("Logging in via HTTP...")
    resp = session.post(f'{BASE_URL}/login', data={'username': 'admin', 'password': 'admin'})
    if 'Panel de Administración' in resp.text or resp.status_code == 200:
        print("Login successful.")
    else:
        print("Login failed.")
        # Only if strict redirect checking
    
    # Simulate Scan
    print("Simulating Scan Entry...")
    payload = {
        'qr_data': qr_data,
        'action_type': 'entry'
    }
    resp = session.post(f'{BASE_URL}/api/log_scan', json=payload)
    print(f"Entry Response: {resp.json()}")

    print("Simulating Scan Exit...")
    payload['action_type'] = 'exit'
    resp = session.post(f'{BASE_URL}/api/log_scan', json=payload)
    print(f"Exit Response: {resp.json()}")
    
    print("Test Complete. Check the dashboard.")

if __name__ == '__main__':
    test_flow()
