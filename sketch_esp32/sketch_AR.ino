#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// --- BOARD CONFIGURATION ---
// Change this ID when programming a new board!
const int MACHINE_ID = 78; 

// Standard BLE UUIDs
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;

// Connection callback handler
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) { 
      deviceConnected = true; 
    }
    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      // Restart advertising so the PC can find it again if disconnected
      pServer->getAdvertising()->start();
    }
};

void setup() {
  Serial.begin(115200);

  // Generate dynamic device name (e.g., "MACHINE_78")
  String deviceName = "MACHINE_" + String(MACHINE_ID);
  
  BLEDevice::init(deviceName.c_str());
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID,
                      BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
                    );
  pCharacteristic->addDescriptor(new BLE2902());
  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  BLEDevice::startAdvertising();
  
  Serial.println("BLE Server started as: " + deviceName);
}

void loop() {
  if (deviceConnected) {
    // 1. Read the internal CPU core temperature (Celsius)
    float coreTemp = temperatureRead();
    
    // 2. Create the JSON string payload
    String jsonPayload = "{\"temp\":" + String(coreTemp, 1) + "}";
    
    // 3. Send the data via Bluetooth
    pCharacteristic->setValue(jsonPayload.c_str());
    pCharacteristic->notify();

    Serial.println("Sent: " + jsonPayload);
  }
  
  // Wait 3 seconds before the next reading
  delay(3000);
}