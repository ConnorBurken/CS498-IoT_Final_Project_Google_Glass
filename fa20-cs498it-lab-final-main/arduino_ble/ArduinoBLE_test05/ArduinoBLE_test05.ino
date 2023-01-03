#include <ArduinoBLE.h>

BLEService UARTService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");
BLECharacteristic UARTCharRx("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLEWrite, 128);
BLECharacteristic UARTCharTx("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", BLERead | BLENotify, 128);
char bleStrBuffer[128];
int bufPos = 0;

bool firstTimeConnected = true;

void onMessage() {
  Serial.print("RX = ");
  Serial.println(bleStrBuffer);
}

void setup() {
  Serial.begin(9600);
  while (!Serial);

  pinMode(LED_BUILTIN, OUTPUT);
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  BLE.setLocalName("TheIoTeamGlass");
  BLE.setAdvertisedService(UARTService);
  UARTService.addCharacteristic(UARTCharRx);
  UARTService.addCharacteristic(UARTCharTx);
  BLE.addService(UARTService);

  BLE.advertise();
  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    if (firstTimeConnected) {
      firstTimeConnected = false;
      Serial.print("Connected to central: ");
      Serial.println(central.address());
    }
    
    digitalWrite(LED_BUILTIN, HIGH);

    while (central.connected()) {
//      Serial.println("Looping ...");
      bool hasWritten = UARTCharRx.written();

//      Serial.print("Written = ");
//      Serial.println(hasWritten);

      if (hasWritten) {
        if (((char*)UARTCharRx.value())[UARTCharRx.valueLength() - 1] == '\n') {
          Serial.print("bufPos = ");
          Serial.println(bufPos);
          
          strncpy(&(bleStrBuffer[bufPos]), (char*)UARTCharRx.value(), UARTCharRx.valueLength() - 1);
          
          onMessage();

          // reset buffer
          memset(bleStrBuffer, 0, sizeof(char) * 128);
          bufPos = 0;
        }
        else {
          Serial.print("bufPos = ");
          Serial.println(bufPos);
          
          strncpy(&(bleStrBuffer[bufPos]), (char*)UARTCharRx.value(), UARTCharRx.valueLength());
          bufPos += UARTCharRx.valueLength();
        }
      }
      delay(200);
    }
  }
  else {
    firstTimeConnected = true;
  }
  
  digitalWrite(LED_BUILTIN, LOW);
}
