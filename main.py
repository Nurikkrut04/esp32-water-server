from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_socketio import SocketIO
import json
import datetime
import os
import csv

app = Flask(__name__)
socketio = SocketIO(app)  # ⬅ WebSocket поддержка

DATA_FILE = 'data.json'

# Загрузка данных из файла
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# Сохранение данных в файл
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Получение данных от ESP32
@app.route('/data', methods=['POST'])
def receive_data():
    content = request.json
    liters = content.get('liters')
    timestamp = content.get('timestamp', datetime.datetime.now().isoformat())

    if liters is not None:
        data = load_data()
        entry = {'liters': liters, 'timestamp': timestamp}
        data.append(entry)
        save_data(data)

        # Отправляем WebSocket-событие клиентам
        socketio.emit('new_data', entry)

        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'No liters value'}), 400

# Отдаём json для графика
@app.route('/data.json')
def serve_data():
    return send_file(DATA_FILE, mimetype='application/json')

# Очистка данных
@app.route('/reset', methods=['GET'])
def reset_data():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)
    return "<h3>Данные успешно очищены!</h3>"

# Экспорт в CSV
@app.route('/export', methods=['GET'])
def export_csv():
    data = load_data()
    output = [['Время', 'Литры']]
    for entry in data:
        output.append([entry.get('timestamp') or entry.get('time'), entry['liters']])
    csv_data = '\ufeff' + '\n'.join([','.join(map(str, row)) for row in output])
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=water_data.csv'}
    )

# Запуск сервера
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host='0.0.0.0', port=port)
