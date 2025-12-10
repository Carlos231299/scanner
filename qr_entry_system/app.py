from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from db import get_db, close_db
import qrcode
import os
import io
import csv
import base64
import pymysql
from xhtml2pdf import pisa

from datetime import timedelta

app = Flask(__name__)
# Use a static secret key from environment or fallback to random (random breaks sessions in multi-worker Gunicorn)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
        if user is None:
            error = 'Usuario incorrecto.'
        elif not check_password_hash(user['password_hash'], password):
            error = 'Contraseña incorrecta.'
        else:
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            # Direct redirect based on role
            if user['role'] == 'supervisor':
                return redirect(url_for('scanner'))
            return redirect(url_for('dashboard'))
        
        flash(error)
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Allow both admin and supervisor to view dashboard
    # Specific elements will be hidden in the template based on role
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        current_user = cursor.fetchone()
        
    # Both ADMIN and SUPERVISOR use the admin dashboard template now (with restricted view for supervisor)
    if session['role'] in ['admin', 'supervisor']:
        with db.cursor() as cursor:
            # Supervisors see same logs as admin
            cursor.execute("""
                SELECT logs.type, logs.timestamp, users.username 
                FROM logs 
                JOIN users ON logs.user_id = users.id 
                ORDER BY logs.timestamp DESC 
                LIMIT 20
            """)
            recent_logs = cursor.fetchall()
        return render_template('dashboard_admin.html', user=current_user, recent_logs=recent_logs, role=session['role'])
    else:
        return render_template('dashboard_employee.html', user=current_user)

@app.route('/register_user', methods=['POST'])
def register_user():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    username = request.form['username']
    password = request.form.get('password')
    role = request.form['role'] # 'employee', 'admin', 'supervisor'
    cedula = request.form.get('cedula')
    area = request.form.get('area')
    face_descriptor = request.form.get('face_descriptor') 
    qr_data = f"user:{username}:{secrets.token_hex(4)}"
    
    db = get_db()
    
    # ... duplicate checks ...

    # Password Logic: Only hash if provided
    pwd_hash = None
    if password and password.strip():
        pwd_hash = generate_password_hash(password)
    
    # ... insert ...

    try:
        with db.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, cedula, area, qr_code_data, face_descriptor) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (username, pwd_hash, role, cedula, area, qr_data, face_descriptor)
            )
        db.commit()
        flash('Usuario registrado exitosamente.')
    except pymysql.MySQLError as e:
        flash(f'Error al registrar usuario: {e}')
        
    return redirect(url_for('dashboard'))

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return {'status': 'error', 'message': 'Unauthorized'}, 403
        
    user_id = session['user_id']
    username = request.form.get('username')
    password = request.form.get('password')
    
    db = get_db()
    try:
        with db.cursor() as cursor:
            if password and password.strip():
                cursor.execute("UPDATE users SET username = %s, password_hash = %s WHERE id = %s", 
                              (username, generate_password_hash(password), user_id))
            else:
                cursor.execute("UPDATE users SET username = %s WHERE id = %s", (username, user_id))
        db.commit()
        return {'status': 'success', 'message': 'Perfil actualizado correctmente'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/generate_qr_image')
def generate_qr_image():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT qr_code_data FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
    if not user or not user['qr_code_data']:
        return "No QR code data found", 404
        
    img = qrcode.make(user['qr_code_data'])
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return Flask.response_class(buf.getvalue(), mimetype='image/png')

@app.route('/scanner')
def scanner():
    # Allow admin AND supervisor
    if 'user_id' not in session or session['role'] not in ['admin', 'supervisor']:
        return redirect(url_for('login'))
    return render_template('scanner.html', role=session['role'])

@app.route('/api/log_scan', methods=['POST'])
def log_scan():
    if 'user_id' not in session or session['role'] not in ['admin', 'supervisor']:
        return {'status': 'error', 'message': 'Unauthorized'}, 403
    
    data = request.get_json()
    qr_data = data.get('qr_data')
    username = data.get('username')
    action_type = data.get('action_type')
    
    if not action_type or (not qr_data and not username):
        return {'status': 'error', 'message': 'Missing data'}, 400
        
    db = get_db()
    with db.cursor() as cursor:
        user = None
        if qr_data:
            cursor.execute("SELECT id, username FROM users WHERE qr_code_data = %s", (qr_data,))
            user = cursor.fetchone()
        elif username:
            cursor.execute("SELECT id, username FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
        
        if not user:
             return {'status': 'error', 'message': 'Usuario no encontrado'}, 404

        # Log action
        valid_actions = ['entry', 'exit', 'start_lunch', 'end_lunch']
        if action_type not in valid_actions:
             return {'status': 'error', 'message': 'Acción inválida'}, 400

        cursor.execute(
            "INSERT INTO logs (user_id, type) VALUES (%s, %s)",
            (user['id'], action_type)
        )
        db.commit()
    
    return {'status': 'success', 'message': f'Registro exitoso: {user["username"]} - {action_type}'}

@app.route('/api/users/faces')
def get_user_faces():
    if 'user_id' not in session:
         return {'status': 'error', 'message': 'Unauthorized'}, 403

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT username, face_descriptor FROM users WHERE face_descriptor IS NOT NULL")
        users = cursor.fetchall()
    
    import json
    result = []
    for u in users:
        try:
             desc = u['face_descriptor']
             if isinstance(desc, str):
                 desc = json.loads(desc)
             result.append({'username': u['username'], 'descriptor': desc})
        except:
            continue
            
    return {'status': 'success', 'users': result}


# --- User Management APIs ---

@app.route('/api/users')
def list_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return {'status': 'error', 'message': 'Unauthorized'}, 403
        
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT id, username, role, cedula, area FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        
    result = []
    for u in users:
        result.append({
            'id': u['id'],
            'username': u['username'],
            'role': u['role'],
            'cedula': u['cedula'] or '',
            'area': u['area'] or ''
        })
        
    return {'status': 'success', 'users': result}

@app.route('/api/users/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return {'status': 'error', 'message': 'Unauthorized'}, 403
        
    username = request.form.get('username')
    role = request.form.get('role')
    cedula = request.form.get('cedula')
    area = request.form.get('area')
    password = request.form.get('password')
    face_descriptor = request.form.get('face_descriptor') 
    
    db = get_db()

    # Face Uniqueness Check (if updating face)
    if face_descriptor and face_descriptor.strip():
        import json
        import math
        try:
            new_desc = json.loads(face_descriptor)
            with db.cursor() as cursor:
                # Get all OTHER users' faces
                cursor.execute("SELECT username, face_descriptor FROM users WHERE face_descriptor IS NOT NULL AND id != %s", (user_id,))
                other_users = cursor.fetchall()
            
            for other in other_users:
                try:
                    stored_desc = json.loads(other['face_descriptor'])
                    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(new_desc, stored_desc)))
                    if distance < 0.5:
                         return {'status': 'error', 'message': f'Rostro ya registrado por "{other["username"]}".'}
                except:
                    continue
        except Exception as e:
            return {'status': 'error', 'message': f'Error procesando biometría: {str(e)}'}
    
    try:
        with db.cursor() as cursor:
            # Prepare update query
            query = "UPDATE users SET username = %s, role = %s, cedula = %s, area = %s"
            params = [username, role, cedula, area]
            
            if password:
                query += ", password_hash = %s"
                params.append(generate_password_hash(password))
            
            if face_descriptor:
                if not face_descriptor.strip():
                     face_descriptor = None
                query += ", face_descriptor = %s"
                params.append(face_descriptor)
                
            query += " WHERE id = %s"
            params.append(user_id)
            
            cursor.execute(query, tuple(params))
        db.commit()
        return {'status': 'success', 'message': 'Usuario actualizado'}
    except pymysql.MySQLError as e:
        if e.args[0] == 1062:
             return {'status': 'error', 'message': 'El usuario o la cédula ya existen.'}
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return {'status': 'error', 'message': 'Unauthorized'}, 403
        
    # Prevent self-deletion
    if user_id == session['user_id']:
        return {'status': 'error', 'message': 'No puedes eliminar tu propia cuenta'}, 400
        
    db = get_db()
    try:
        with db.cursor() as cursor:
            # Cascading delete usually handled by DB, but let's be safe
            cursor.execute("DELETE FROM logs WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.commit()
        return {'status': 'success', 'message': 'Usuario eliminado'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

# --- Admin Logs Management APIs ---

@app.route('/api/logs/search')
def search_logs():
    if 'user_id' not in session or session['role'] not in ['admin', 'supervisor']:
        return {'status': 'error', 'message': 'Unauthorized'}, 403

    username = request.args.get('username', '')
    action_type = request.args.get('action_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = """
        SELECT logs.id, logs.type, logs.timestamp, users.username 
        FROM logs 
        JOIN users ON logs.user_id = users.id 
        WHERE 1=1
    """
    params = []
    
    if username:
        query += " AND users.username LIKE %s"
        params.append(f"%{username}%")
        
    if action_type:
        query += " AND logs.type = %s"
        params.append(action_type)
        
    if date_from:
        query += " AND DATE(logs.timestamp) >= %s"
        params.append(date_from)
        
    if date_to:
        query += " AND DATE(logs.timestamp) <= %s"
        params.append(date_to)
        
    query += " ORDER BY logs.timestamp DESC LIMIT 100"
    
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(query, tuple(params))
        logs = cursor.fetchall()
        
    # Convert datetime to string for JSON
    results = []
    for log in logs:
        results.append({
            'id': log['id'],
            'username': log['username'],
            'type': log['type'],
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        })
        
    return {'status': 'success', 'logs': results}

@app.route('/api/logs/delete/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return {'status': 'error', 'message': 'Unauthorized'}, 403
        
    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute("DELETE FROM logs WHERE id = %s", (log_id,))
        db.commit()
        return {'status': 'success', 'message': 'Registro eliminado'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

@app.route('/api/logs/export_pdf')
def export_logs_pdf():
    if 'user_id' not in session or session['role'] not in ['admin', 'supervisor']:
        return redirect(url_for('login'))
        
    # Reuse Search Logic
    username = request.args.get('username', '')
    action_type = request.args.get('action_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = """
        SELECT logs.id, users.username, logs.type, logs.timestamp
        FROM logs 
        JOIN users ON logs.user_id = users.id 
        WHERE 1=1
    """
    params = []
    
    if username:
        query += " AND users.username LIKE %s"
        params.append(f"%{username}%")
    if action_type:
        query += " AND logs.type = %s"
        params.append(action_type)
    if date_from:
        query += " AND DATE(logs.timestamp) >= %s"
        params.append(date_from)
    if date_to:
        query += " AND DATE(logs.timestamp) <= %s"
        params.append(date_to)
        
    query += " ORDER BY logs.timestamp DESC"
    
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(query, tuple(params))
        logs = cursor.fetchall()

    
    # --- COLOMBIAN PAYROLL LOGIC ---
    from datetime import datetime, timedelta

    # Hardcoded Holidays 2024-2025 (Simplified List)
    HOLIDAYS = [
        '2024-01-01', '2024-03-25', '2024-03-28', '2024-03-29', '2024-05-01', 
        '2024-05-13', '2024-06-03', '2024-06-10', '2024-07-01', '2024-07-20', 
        '2024-08-07', '2024-08-19', '2024-10-14', '2024-11-04', '2024-11-11', 
        '2024-12-08', '2024-12-25',
        '2025-01-01' 
    ]

    def is_sunday_or_holiday(date_obj):
        if date_obj.weekday() == 6: return True # Sunday
        if date_obj.strftime('%Y-%m-%d') in HOLIDAYS: return True
        return False

    # Group logs by User
    user_logs = {}
    for log in logs:
        uid = log['username'] # Group by username for report
        if uid not in user_logs: user_logs[uid] = []
        user_logs[uid].append(log)

    payroll_summary = {}

    for username, u_logs in user_logs.items():
        # Sort by time ASC for processing
        sorted_logs = sorted(u_logs, key=lambda x: x['timestamp'])
        
        total_hours = 0
        sunday_holiday_hours = 0
        overtime_hours = 0
        
        # Session Logic: Pair Entry -> Exit
        i = 0
        while i < len(sorted_logs):
            current = sorted_logs[i]
            
            if current['type'] == 'entry':
                # Look for next exit
                next_log = None
                for j in range(i+1, len(sorted_logs)):
                    if sorted_logs[j]['type'] == 'exit':
                        next_log = sorted_logs[j]
                        i = j # Advance main loop
                        break
                
                if next_log:
                    # Calculate Duration
                    start = current['timestamp']
                    end = next_log['timestamp']
                    duration = (end - start).total_seconds() / 3600 # Hours
                    
                    # 1. Total
                    total_hours += duration
                    
                    # 2. Sunday/Holiday Check (Check Start Date)
                    if is_sunday_or_holiday(start):
                        sunday_holiday_hours += duration
                        
                    # 3. Daily Overtime ( Simplified: >8h in a single session, or check daily total? 
                    # Real law is daily total, but for this summary session-based > 8 is a good approximation or we track by day)
                    # Let's simple check: if session > 8h
                    if duration > 8:
                        overtime_hours += (duration - 8)
            
            i += 1
            
        payroll_summary[username] = {
            'total_hours': round(total_hours, 2),
            'sunday_holiday_hours': round(sunday_holiday_hours, 2),
            'overtime_hours': round(overtime_hours, 2)
        }

    # Render HTML for PDF
    html_content = render_template('pdf_report.html', logs=logs, summary=payroll_summary)
    
    pdf_output = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,    # the HTML to convert
        dest=pdf_output      # file handle to recieve result
    )

    if pisa_status.err:
        return f"Error generating PDF", 500
        
    pdf_output.seek(0)
    return Flask.response_class(pdf_output.getvalue(), mimetype='application/pdf')

@app.route('/api/logs/export')
def export_logs():
    if 'user_id' not in session or session['role'] not in ['admin', 'supervisor']:
        return redirect(url_for('login'))
        
    # Reuse Search Logic (Clean Code Refactoring would be better, but duplication is acceptable for now)
    username = request.args.get('username', '')
    action_type = request.args.get('action_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = """
        SELECT logs.id, users.username, logs.type, logs.timestamp
        FROM logs 
        JOIN users ON logs.user_id = users.id 
        WHERE 1=1
    """
    params = []
    
    if username:
        query += " AND users.username LIKE %s"
        params.append(f"%{username}%")
    if action_type:
        query += " AND logs.type = %s"
        params.append(action_type)
    if date_from:
        query += " AND DATE(logs.timestamp) >= %s"
        params.append(date_from)
    if date_to:
        query += " AND DATE(logs.timestamp) <= %s"
        params.append(date_to)
        
    query += " ORDER BY logs.timestamp DESC"
    
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(query, tuple(params))
        logs = cursor.fetchall()
        
    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Usuario', 'Tipo Accion', 'Fecha y Hora'])
    
    for log in logs:
        cw.writerow([log['id'], log['username'], log['type'], log['timestamp']])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=registros_acceso.csv"
    output.headers["Content-type"] = "text/csv"
    return output

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, ssl_context='adhoc')
