from flask import Flask, request, jsonify, render_template
import json
import datetime

app = Flask(__name__)

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

# Главная страница — график
@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data)

# Получение данных от ESP32
@app.route('/data', methods=['POST'])
def receive_data():
    content = request.json
    liters = content.get('liters')
    timestamp = content.get('timestamp', datetime.datetime.now().isoformat())
    
    if liters is not None:
        data = load_data()
        data.append({'liters': liters, 'timestamp': timestamp})
        save_data(data)
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'No liters value'}), 400

# Запуск сервера
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)