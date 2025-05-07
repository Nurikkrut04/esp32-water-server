from flask import Flask, request, jsonify, render_template, send_file, Response
import json, datetime, os, csv, requests

app = Flask(__name__)

DATA_FILE = 'data.json'
ESP32_URL = 'http://192.168.39.52/command'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

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
        data = load_data()
        entry = {
            'liters': liters,
            'pulses': pulses if pulses is not None else '-',
            'timestamp': timestamp
        }
        data.append(entry)
        save_data(data)
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'error': 'No liters value'}), 400

@app.route('/data.json')
def serve_data():
    return send_file(DATA_FILE, mimetype='application/json')

@app.route('/reset', methods=['GET'])
def reset_data():
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)
    return "<h3>Данные успешно очищены!</h3>"

@app.route('/export', methods=['GET'])
def export_csv():
    data = load_data()
    output = [['Время', 'Литры', 'Импульсы']]
    for entry in data:
        output.append([
            entry.get('timestamp') or entry.get('time'),
            entry['liters'],
            entry.get('pulses', '-')
        ])
    csv_data = '\ufeff' + '\n'.join([','.join(map(str, row)) for row in output])
    return Response(
        csv_data,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=water_data.csv'}
    )

@app.route('/send-command', methods=['POST'])
def send_command():
    liters = request.form.get('liters')
    if not liters:
        return jsonify({'error': 'No liters provided'}), 400
    try:
        response = requests.post(ESP32_URL, data={'liters': liters}, timeout=5)
        return jsonify({'status': 'sent', 'esp_response': response.text})
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'failed', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)