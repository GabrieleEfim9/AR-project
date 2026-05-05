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
# ENDPOINT TO PRINT THE BARCODES
# ==========================================
@app.route('/print_marker/<int:marker_id>')
def stampa_etichetta(marker_id):
    # Building direct link to the image of the barcode needed
    github_url = f"https://raw.githubusercontent.com/nicolocarpignoli/artoolkit-barcode-markers-collection/master/4x4_bch_13_9_3/{marker_id}.png"
    
    # Showing the image through html script
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Marker {marker_id}</title>
        <style>
            /* Stili per la visualizzazione su SCHERMO */
            body {{ text-align: center; font-family: Arial, sans-serif; margin-top: 50px; background-color: #f4f4f9; }}
            .card {{ background: white; display: inline-block; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            img {{ width: 300px; height: 300px; }} /* ASSOLUTAMENTE NESSUN BORDO CSS QUI */
            button {{ margin-top: 20px; padding: 10px 20px; font-size: 16px; cursor: pointer; background-color: #2980b9; color: white; border: none; border-radius: 5px; }}
            
            /* Stili ESCLUSIVI per la STAMPANTE */
            @media print {{
                @page {{ margin: 0; }} /* Rimuove url, data e numero pagina dai bordi del foglio */
                body {{ 
                    margin: 0; 
                    background-color: white; 
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; /* Centra l'immagine a metà del foglio A4 */
                }}
                .no-print {{ display: none !important; }} /* Nasconde testi e bottoni sul foglio di carta */
                .card {{ box-shadow: none; padding: 0; }}
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <!-- Questa sezione sparirà quando si stampa -->
            <div class="no-print">
                <h2>AR label for Machine ID: {marker_id}</h2>
                <p>Print this marker. Ensure there are no reflections on the paper.</p>
            </div>
            
            <!-- Solo questa immagine finirà sul foglio di carta -->
            <img src="{github_url}" alt="Barcode {marker_id}">
            
            <!-- Anche il bottone sparirà -->
            <div class="no-print">
                <br>
                <button onclick="window.print()">Print label</button>
            </div>
        </div>
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
    app.run(host='0.0.0.0', port=8080)