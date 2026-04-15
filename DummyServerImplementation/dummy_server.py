from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# ==========================================
# 1. STATIC DATABASE (Fallback)
# ==========================================
# This data is used if the Arduino has not sent anything yet.
STATIC_DB = {
    "machine_0": {
        "battery": 100,
        "last_connection": "2026-04-15 08:30:00",
        "signal_level": "-50 dBm (Excellent)"
    },
    "machine_1": {
        "battery": 15,
        "last_connection": "2026-04-14 18:45:00",
        "signal_level": "-85 dBm (Weak)"
    }
}

# ==========================================
# 2. REAL-TIME IN-MEMORY DATABASE
# ==========================================
# This will store actual data sent by the hardware.
REAL_TIME_DB = {}

# ==========================================
# AUGMENTED REALITY ENDPOINT (GET)
# ==========================================
@app.route('/api/diagnostics/<device_id>', methods=['GET'])
def get_diagnostics(device_id):
    # Check 1: Has the Arduino sent recent real data?
    if device_id in REAL_TIME_DB:
        data = REAL_TIME_DB[device_id].copy()
        data["data_source"] = "Real Sensor"
        return jsonify(data)
    
    # Check 2: No real data available. Is there a prepared static data entry?
    if device_id in STATIC_DB:
        data = STATIC_DB[device_id].copy()
        data["data_source"] = "Static Data"
        return jsonify(data)
    
    # Check 3: If the scanned ID does not exist anywhere,
    # return neutral data so the app never fails.
    return jsonify({
        "battery": 0,
        "last_connection": "Never connected",
        "signal_level": "No signal",
        "data_source": "Neutral Data"
    })

# ==========================================
# ARDUINO ENDPOINT (POST) - IoT READY
# ==========================================
@app.route('/api/sensors/<device_id>', methods=['POST'])
def update_sensor_data(device_id):
    # The Arduino will POST JSON data to this address.
    incoming_data = request.get_json()
    
    if not incoming_data:
        return jsonify({"error": "No data received"}), 400
    
    # Save the Arduino data into the real-time database.
    REAL_TIME_DB[device_id] = {
        "battery": incoming_data.get("battery", 0),
        "last_connection": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "signal_level": incoming_data.get("signal_level", "Unknown")
    }
    
    return jsonify({"status": "success", "message": f"Data updated for {device_id}"}), 200

# ==========================================
# ENDPOINT PER STAMPARE LE ETICHETTE
# ==========================================
@app.route('/stampa/<int:marker_id>')
def stampa_etichetta(marker_id):
    # Building direct link to the image of the barcode needed
    github_url = f"https://raw.githubusercontent.com/nicolocarpignoli/artoolkit-barcode-markers-collection/master/4x4_bch_13_9_3/{marker_id}.png"
    
    # Showing the image through html script
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stampa Marker {marker_id}</title>
        <style>
            body {{ text-align: center; font-family: Arial, sans-serif; margin-top: 50px; }}
            img {{ width: 300px; height: 300px; border: 2px solid black; }}
            button {{ margin-top: 20px; padding: 10px 20px; font-size: 16px; cursor: pointer; }}
            @media print {{ button {{ display: none; }} }} /* Nasconde il bottone quando si stampa */
        </style>
    </head>
    <body>
        <h2>Etichetta AR per Macchina ID: {marker_id}</h2>
        <p>Stampa questo foglio e incollalo sul macchinario.</p>
        
        <img src="{github_url}" alt="Barcode {marker_id}">
        <br>
        <button onclick="window.print()">Stampa Etichetta</button>
    </body>
    </html>
    """
    return html_page

# ==========================================
# ROUTES TO SERVE HTML FILES AND ASSETS
# ==========================================
@app.route('/')
def index():
    return send_from_directory(os.getcwd(), 'diagnostic.html')

@app.route('/<path:filename>')
def serve_files(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.run(port=8080)