from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import random
import os

app = Flask(__name__)
CORS(app)

# 1. The API that generates random data based on the requested ID
@app.route('/api/diagnostics/<device_id>')
def get_diagnostics(device_id):
    data = {
        "id": device_id,
        "battery": random.randint(20, 100),
        "state": "Operative" if random.choice([True, False]) else "OutOfOrder",
        "temperature": round(random.uniform(30.0, 60.0), 1)
    }
    return jsonify(data)

# 2. SHORTCUT: Automatically serves the HTML file when visiting the root URL
@app.route('/')
def index():
    return send_from_directory(os.getcwd(), 'diagnostic.html')

# 3. Serves any other files requested by the browser
@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.run(port=8080)