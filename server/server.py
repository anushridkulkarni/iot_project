from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
from mysql.connector import Error
import time
from datetime import datetime

app = Flask(__name__)
auth = HTTPBasicAuth()

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db_config = {
    'host': 'localhost',
    'user': 'flaskuser',          # Change to your MySQL user
    'password': 'mitwpu',          # Change to your MySQL password
    'database': 'passengerdb'
}

users = {
    "student1": generate_password_hash("mitwpu")
}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users[username], password):
        return username

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.template_filter('datetimeformat')
def datetimeformat(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value

@app.route('/upload', methods=['POST'])
@auth.login_required
def upload():
    count = request.form.get('count')
    image = request.files.get('image')

    if count is None or image is None:
        return jsonify({'error': 'Missing count or image'}), 400
    
    timestamp = int(time.time())
    filename = f"passenger_{timestamp}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image.save(filepath)

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO passengers (photo_file_name, served) VALUES (%s, %s)", (filename, 0))
        conn.commit()
        passenger_id = cursor.lastrowid
    except Error as e:
        print(f"Error inserting into database: {e}")
        return jsonify({'error': 'Database insert error'}), 500
    finally:
        cursor.close()
        conn.close()

    print(f"Uploaded passenger id {passenger_id} with image {filename}")
    return jsonify({'status': 'success', 'filename': filename, 'passenger_id': passenger_id})

@app.route('/served/<int:passenger_id>', methods=['POST'])
@auth.login_required
def mark_served(passenger_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT served FROM passengers WHERE id = %s", (passenger_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Passenger not found'}), 404
        
        served = result[0]
        if served == 0:
            cursor.execute("UPDATE passengers SET served=1 WHERE id=%s", (passenger_id,))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Passenger marked served'})
        else:
            return jsonify({'status': 'exists', 'message': 'Passenger already served'})
    except Error as e:
        print(f"Error updating served status: {e}")
        return jsonify({'error': 'Database update error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/active')
@auth.login_required
def active_count():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection error'}), 500
    
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM passengers WHERE served=0")
        count = cursor.fetchone()[0]
        return jsonify({'active_count': count})
    except Error as e:
        print(f"Error querying active count: {e}")
        return jsonify({'error': 'Database query error'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/')
@auth.login_required
def dashboard():
    conn = get_db_connection()
    if not conn:
        return "Database connection error", 500
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, photo_file_name, served, date_time FROM passengers ORDER BY date_time DESC")
        passengers = cursor.fetchall()
    except Error as e:
        print(f"Error fetching passengers: {e}")
        passengers = []
    finally:
        cursor.close()
        conn.close()
    return render_template('dashboard.html', passengers=passengers)

@app.route('/active_dashboard')
@auth.login_required
def active_dashboard():
    return render_template('active_dashboard.html')

@app.route('/uploads/<filename>')
@auth.login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

