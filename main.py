from flask import Flask, request, jsonify, render_template, send_file
import json
import datetime
import os

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
@app.route("/post", methods=["POST"])
def post_data():
    content = request.get_json()

    # Проверка ключа
    if content.get("key") != SECRET_KEY:
        return jsonify({"status": "unauthorized"}), 403

    # Извлечение данных
    time = content.get("time")
    liters = content.get("liters")

    if time and liters:
        with open("data.json", "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append({"time": time, "liters": liters})
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "invalid data"}), 400

@app.route('/data.json')
def serve_data():
    return send_file(DATA_FILE, mimetype='application/json')

# Запуск сервера
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)