from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
import json
from datetime import datetime

app = Flask(__name__)
auth = HTTPBasicAuth()

UPLOAD_FOLDER = './uploads'
LOG_FILE = 'passenger_log.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

users = {
    "student1": generate_password_hash("mitwpu")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

def save_log(entry):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    logs.append(entry)
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

@app.route('/upload', methods=['POST'])
@auth.login_required
def upload():
    count = request.form.get('count')
    image = request.files.get('image')

    if count is None or image is None:
        return jsonify({'error': 'Missing count or image'}), 400

    filename = f"passenger_{count}_{int(time.time())}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    try:
        image.save(filepath)
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({'error': 'Failed to save image'}), 500

    log_entry = {'timestamp': int(time.time()), 'count': int(count), 'image': filename}
    save_log(log_entry)

    print(f"Received passenger count: {count}, saved image: {filename}")
    return jsonify({'status': 'success', 'filename': filename, 'count': count})

@app.route('/')
@auth.login_required
def index():
    return render_template('dashboard.html')

@app.route('/logs')
@auth.login_required
def logs():
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    return jsonify(logs)

@app.route('/uploads/<filename>')
@auth.login_required
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

