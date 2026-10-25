import os
import time
import io
import sqlite3
import pandas as pd
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from sms_templates import build_sms_message

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_college_key")
DB_NAME = "college.db"

# --- DATABASE SETUP ---
def init_db():
    """Initializes SQLite database tables for exam records and users."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Exam Records Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_type TEXT NOT NULL,
                student_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                failed_count INTEGER,
                failed_subjects TEXT,
                result_status TEXT,
                sms_status TEXT,
                sms_message TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Users Table for Permanent HOD Authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Insert default HOD account if table is empty
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (username, email, phone, password)
                VALUES (?, ?, ?, ?)
            ''', ('hod_cs', 'hod@college.edu', '9876543210', 'password123'))
            
        conn.commit()

init_db()

# --- FAST2SMS API CONFIGURATION ---
FAST2SMS_API_KEY = os.environ.get(
    "FAST2SMS_API_KEY", 
    "1RrzZhsem7PaQ4NiET0JL5gACS8qxpcFYBnIlWXOwHjoMDfdU6AcuBUeGsM0y3vLNt15PbKDhfOClFoz"
)

def send_real_sms(phone_number, message_text):
    """Function to trigger actual mobile text messages using Fast2SMS with debug logs."""
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    clean_phone = str(phone_number).replace(".0", "").strip()
    clean_phone = "".join(filter(str.isdigit, clean_phone))[-10:]
    
    if len(clean_phone) != 10:
        print(f"[-] Invalid phone number format: {phone_number} -> Cleaned: {clean_phone}")
        return False

    payload = {
        'authorization': FAST2SMS_API_KEY,
        'message': message_text,
        'language': 'english',
        'route': 'q',
        'numbers': clean_phone
    }
    
    headers = {
        'authorization': FAST2SMS_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        result = response.json()
        print(f"[SMS API Response] To: {clean_phone} | Response: {result}")
        return result.get('return') == True
    except Exception as e:
        print(f"[-] Network/API Exception for {clean_phone}: {e}")
        return False


# ==========================================
# AUTHENTICATION ROUTES (DB-Backed)
# ==========================================

@app.route('/', methods=['GET'])
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    identifier = request.form.get('identifier', '').strip()
    password = request.form.get('password', '').strip()
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT username FROM users 
            WHERE (username = ? OR email = ? OR phone = ?) AND password = ?
        ''', (identifier, identifier, identifier, password))
        row = cursor.fetchone()
        
    if row:
        session['user'] = row[0]
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', error="Invalid Username/Email/Phone or Password!")

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '').strip()
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, phone, password)
                VALUES (?, ?, ?, ?)
            ''', (username, email, phone, password))
            conn.commit()
        return render_template('login.html', success="Account created successfully! Please Sign In.")
    except sqlite3.IntegrityError:
        return render_template('login.html', error="Username, email, or phone number already registered!")

@app.route('/reset-password', methods=['POST'])
def reset_password():
    phone = request.form.get('phone', '').strip()
    new_password = request.form.get('new_password', '').strip()
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE phone = ?', (new_password, phone))
        conn.commit()
        rows_affected = cursor.rowcount
        
    if rows_affected > 0:
        return render_template('login.html', success="Password updated successfully! Please Sign In.")
    else:
        return render_template('login.html', error="Phone number not found in our records!")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# ==========================================
# DASHBOARD & EXAM SMS ROUTES
# ==========================================

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))

    selected_exam = request.args.get('exam_type', 'Unit 1 Test')
    
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT student_name, phone, failed_count, failed_subjects, result_status, sms_status, sms_message 
            FROM exam_records 
            WHERE exam_type = ?
        ''', (selected_exam,))
        rows = cursor.fetchall()

    total_students = len(rows)
    passed_students = sum(1 for r in rows if r[4] == 'Pass')
    failed_students = sum(1 for r in rows if r[4] == 'Fail')
    pass_percentage = round((passed_students / total_students * 100), 1) if total_students > 0 else 0

    return render_template(
        'dashboard.html',
        selected_exam=selected_exam,
        rows=rows,
        total_students=total_students,
        passed_students=passed_students,
        failed_students=failed_students,
        pass_percentage=pass_percentage,
        current_user=session['user']
    )

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:
        return redirect(url_for('index'))

    exam_type = request.form.get('exam_type')
    
    if 'file' not in request.files or not exam_type:
        flash("Please select an exam category and attach an Excel file.", "danger")
        return redirect(url_for('dashboard'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for('dashboard'))

    if file and file.filename.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file)
            df.columns = df.columns.astype(str).str.strip()
            
            column_mapping = {
                'Student Name': 'Name', 'Student': 'Name',
                'Parent Number': 'Phone', 'Contact': 'Phone', 'Mobile': 'Phone'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            if 'Name' not in df.columns or 'Phone' not in df.columns:
                flash(f"Missing required columns! Found: {list(df.columns)}", "danger")
                return redirect(url_for('dashboard'))

            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM exam_records WHERE exam_type = ?', (exam_type,))

                non_subject_cols = ['Roll No', 'Roll Number', 'Name', 'Phone', 'Parent Number', 'Marks', 'Total', 'Average', 'Result']
                subject_cols = [col for col in df.columns if col not in non_subject_cols]

                fail_count_total = 0
                pass_count_total = 0

                # Languages to dispatch simultaneously (English, Tamil, Kannada)
                target_languages = ['en', 'ta', 'kn']

                for index, row in df.iterrows():
                    student = str(row['Name']).strip()
                    phone = str(row['Phone']).strip()
                    failed_subjects = []

                    total_marks = 0
                    valid_subjects_count = 0

                    for subject in subject_cols:
                        try:
                            score = float(row[subject]) if pd.notna(row[subject]) else 0
                            total_marks += score
                            valid_subjects_count += 1
                            if score < 50:
                                failed_subjects.append(subject)
                        except (ValueError, TypeError):
                            continue

                    failed_count = len(failed_subjects)
                    subjects_str = ", ".join(failed_subjects) if failed_subjects else "None"
                    avg_score = round(total_marks / valid_subjects_count, 1) if valid_subjects_count > 0 else 0

                    context = {
                        'student_name': student,
                        'score': avg_score,
                        'failed_subjects': subjects_str
                    }

                    result_status = "Pass" if failed_count == 0 else "Fail"
                    status_key = 'pass' if failed_count == 0 else 'fail'

                    any_sent = False
                    all_messages = []

                    # Loop through all 3 languages and send messages
                    for lang in target_languages:
                        msg = build_sms_message(lang, status_key, context)
                        all_messages.append(f"[{lang.upper()}]: {msg}")
                        
                        is_sent = send_real_sms(phone, msg)
                        if is_sent:
                            any_sent = True
                        
                        time.sleep(0.1)

                    sms_status = "Sent" if any_sent else "Failed"
                    combined_msg_log = " | ".join(all_messages)

                    if result_status == "Pass":
                        pass_count_total += 1
                    else:
                        fail_count_total += 1

                    cursor.execute('''
                        INSERT INTO exam_records 
                        (exam_type, student_name, phone, failed_count, failed_subjects, result_status, sms_status, sms_message)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (exam_type, student, phone, failed_count, subjects_str, result_status, sms_status, combined_msg_log))

                conn.commit()

            flash(f"Successfully processed {exam_type}! Multi-language alerts dispatched for {fail_count_total} failed and {pass_count_total} passed student(s).", "success")

        except Exception as e:
            flash(f"Error processing Excel file: {str(e)}", "danger")

        return redirect(url_for('dashboard', exam_type=exam_type))

    flash("Invalid file format. Please upload an Excel (.xlsx or .xls) file.", "danger")
    return redirect(url_for('dashboard'))


@app.route('/export')
def export_excel():
    if 'user' not in session:
        return redirect(url_for('index'))

    selected_exam = request.args.get('exam_type', 'Unit 1 Test')

    with sqlite3.connect(DB_NAME) as conn:
        df = pd.read_sql_query('SELECT * FROM exam_records WHERE exam_type = ?', conn, params=(selected_exam,))

    if df.empty:
        flash(f"No records found to export for {selected_exam}.", "warning")
        return redirect(url_for('dashboard', exam_type=selected_exam))

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=selected_exam[:30], index=False)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'{selected_exam.replace(" ", "_")}_Audit_Log.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)