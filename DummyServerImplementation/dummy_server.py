import asyncio
import threading
import json
from datetime import datetime
from flask import Flask, jsonify, render_template, send_from_directory
from bleak import BleakClient, BleakScanner

CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Global database to store real-time data for all connected machines
REAL_TIME_DB = {}
# Dictionary to track active clients and prevent duplicate connections
active_clients = {}

app = Flask(__name__, static_folder='.', template_folder='.')

def make_notification_handler(machine_id):
    """Creates a specific BLE notification handler for a given machine."""
    def handler(sender, data):
        try:
            # Decode the incoming JSON payload from the ESP32
            payload = json.loads(data.decode('utf-8'))
            
            if machine_id in REAL_TIME_DB:
                REAL_TIME_DB[machine_id].update({
                    "core_temperature": str(payload.get("temp", 0)),
                    "last_connection": datetime.now().strftime("%H:%M:%S")
                })
                
            print(f"[BLE] {machine_id} -> Temp: {payload.get('temp')} °C")
        except Exception as e:
            print(f"[BLE] Error decoding data from {machine_id}: {e}")
            
    return handler

async def manage_device(device, rssi):
    """Manages the persistent BLE connection to a single machine."""
    machine_id = device.name.lower()
    
    if machine_id in active_clients:
        return # Device is already being managed

    print(f"[BLE] Connecting to {machine_id}...")
    active_clients[machine_id] = True
    
    # Initialize database entry if this is a new machine
    if machine_id not in REAL_TIME_DB:
        REAL_TIME_DB[machine_id] = {
            "core_temperature": "0", 
            "signal_level": "0", 
            "last_connection": "Never"
        }

    # Store the RSSI value measured during the initial scan
    REAL_TIME_DB[machine_id]["signal_level"] = f"{rssi} dBm"

    try:
        async with BleakClient(device) as client:
            # Subscribe to the Bluetooth characteristic
            await client.start_notify(CHARACTERISTIC_UUID, make_notification_handler(machine_id))
            
            # Keep the async task alive as long as the device remains connected
            while client.is_connected:
                await asyncio.sleep(5)
                
    except Exception as e:
        print(f"[BLE] Lost connection to {machine_id}: {e}")
        
    finally:
        # Cleanup when the device disconnects
        if machine_id in active_clients:
            del active_clients[machine_id]
        REAL_TIME_DB[machine_id]["signal_level"] = "No signal"

async def scan_loop():
    """Continuously scans the air and launches management tasks for each new machine found."""
    while True:
        print("[BLE] Scanning for machines...")
        # Use return_adv=True to capture the RSSI signal strength
        devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
        
        for address, (d, adv) in devices.items():
            # Check if the device matches our naming convention
            if d.name and d.name.startswith("MACHINE_"):
                # Launch a new independent background task for this specific machine
                asyncio.create_task(manage_device(d, adv.rssi))
        
        # Pause before the next scan to avoid saturating the Bluetooth adapter
        await asyncio.sleep(10) 

def run_ble_background():
    """Sets up the asynchronous event loop for the BLE background thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scan_loop())


# ==========================================
# FLASK WEB ROUTES
# ==========================================

@app.route('/')
def index():
    """Serves the main Augmented Reality page."""
    return render_template('diagnostic.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """
    Serves static files like the 3D model (.glb) to the AR frontend.
    Without this, A-Frame will freeze on a white screen waiting for assets.
    """
    return send_from_directory('.', filename)

@app.route('/print/<int:marker_id>')
def print_marker(marker_id):
    """Generates a clean HTML page to display or print a specific barcode marker."""
    img_url = f"https://raw.githubusercontent.com/nicolocarpignoli/artoolkit-barcode-markers-collection/master/4x4_bch_13_9_3/{marker_id}.png"
    return f'<html><body style="display:flex;justify-content:center;align-items:center;height:100vh;margin:0;"><img src="{img_url}" style="width:15cm;"></body></html>'

@app.route('/api/diagnostics/<device_id>')
def get_diagnostics(device_id):
    """API endpoint called by the AR frontend to fetch real-time data."""
    data = REAL_TIME_DB.get(device_id)
    if data:
        return jsonify(data), 200
    else:
        return jsonify({"error": "Device Offline"}), 404

if __name__ == '__main__':
    # 1. Start the Bluetooth scanner in a separate background thread
    threading.Thread(target=run_ble_background, daemon=True).start()
    
    print("\n" + "="*60)
    print("🚀 MULTI-DEVICE IOT GATEWAY ACTIVE")
    print("="*60 + "\n")
    
    # 2. Start the Flask web server (Standard HTTP)
    # NOTE: Run Ngrok in a separate terminal to expose this port to HTTPS!
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)