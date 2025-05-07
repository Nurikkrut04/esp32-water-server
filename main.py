# app.py — сервер с SQLite
from flask import Flask, request, jsonify, render_template, send_file, Response
import sqlite3, datetime, csv, os

app = Flask(__name__)
DB_FILE = 'data.db'

# === Инициализация БД ===
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                liters REAL NOT NULL,
                pulses INTEGER,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# === Маршруты ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def receive_data():
    content = request.json
    liters = content.get('liters')
    pulses = content.get('pulses')
    timestamp = content.get('timestamp', datetime.datetime.now().isoformat())

    if liters is not None:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO measurements (liters, pulses, timestamp)
                VALUES (?, ?, ?)
            ''', (liters, pulses, timestamp))
            conn.commit()
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'No liters value'}), 400

@app.route('/data.json')
def serve_data():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, liters, pulses FROM measurements ORDER BY id ASC')
        rows = cursor.fetchall()
        data = [
            {'timestamp': row[0], 'liters': row[1], 'pulses': row[2]} for row in rows
        ]
    return jsonify(data)

@app.route('/reset')
def reset_data():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM measurements')
        conn.commit()
    return '<h3>Данные успешно очищены!</h3>'

@app.route('/export')
def export_csv():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, liters, pulses FROM measurements ORDER BY id ASC')
        rows = cursor.fetchall()

    output = [['Время', 'Литры', 'Импульсы']]
    for row in rows:
        output.append([row[0], row[1], row[2]])

    csv_data = '\ufeff' + '\n'.join([','.join(map(str, row)) for row in output])
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=water_data.csv'}
    )

@app.route('/send-command', methods=['POST'])
def send_command():
    import requests
    liters = request.form.get('liters')
    if not liters:
        return jsonify({'error': 'No liters provided'}), 400

    try:
        ESP32_URL = 'http://192.168.1.106/start'
        print(f"📡 Отправка команды на ESP32: {ESP32_URL}?liters={liters}")
        response = requests.get(ESP32_URL, params={'liters': liters}, timeout=5)
        return jsonify({'status': 'sent', 'esp_response': response.text})
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса к ESP32: {e}")
        return jsonify({'status': 'failed', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)