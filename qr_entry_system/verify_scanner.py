import unittest
import json
from app import app
from db import get_db

class TestScannerAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        # Setup test data
        with app.app_context():
            db = get_db()
            with db.cursor() as cursor:
                # Create test admin user for session
                cursor.execute("DELETE FROM users WHERE username = 'test_admin'")
                cursor.execute("INSERT INTO users (username, password_hash, role, qr_code_data) VALUES ('test_admin', 'hash', 'admin', 'admin:qr')")
                db.commit()
                
                # Get admin id
                cursor.execute("SELECT id FROM users WHERE username = 'test_admin'")
                self.admin_id = cursor.fetchone()['id']
                
                # Create test regular user for scanning
                cursor.execute("DELETE FROM users WHERE username = 'test_scan_user'")
                cursor.execute("INSERT INTO users (username, password_hash, role, qr_code_data) VALUES ('test_scan_user', 'hash', 'employee', 'user:test_scan:1234')")
                db.commit()
    
    def tearDown(self):
        with app.app_context():
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username = 'test_admin'")
                cursor.execute("DELETE FROM users WHERE username = 'test_scan_user'")
                db.commit()

    def test_log_scan_success(self):
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['role'] = 'admin'
            
        response = self.app.post('/api/log_scan', 
            data=json.dumps({
                'qr_data': 'user:test_scan:1234', 
                'action_type': 'entry'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        
    def test_log_scan_invalid_qr(self):
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.admin_id
            sess['role'] = 'admin'
            
        response = self.app.post('/api/log_scan', 
            data=json.dumps({
                'qr_data': 'invalid:qr:code', 
                'action_type': 'entry'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
