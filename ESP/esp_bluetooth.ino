#include "BluetoothSerial.h"
#include <CRC.h>  
#include <SPI.h>

#define LED_BUILTIN 2  // Adjust if needed

BluetoothSerial SerialBT;
String inputString = "";

/**********************************************************************/
#define SS_PIN  5   // SPI Chip Select (Adjust according to your ESP32 wiring)
uint8_t crc = 0;
char data[] = {'f', 'b', 'l', 'r' ,'s'};


void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT_CAR");  // Bluetooth device name
  Serial.println("Bluetooth device ready. Connect and send commands.");

  SPI.begin();  // Initialize SPI
  pinMode(SS_PIN, OUTPUT);
  digitalWrite(SS_PIN, HIGH);  // Ensure CS is HIGH initially
}

void sendSPI(char data) {
    digitalWrite(SS_PIN, LOW);   // Enable SPI communication
    SPI.transfer(data);          // Send the character
    digitalWrite(SS_PIN, HIGH);  // Disable SPI communication
}


void loop() {
   
  if (SerialBT.available()) {
    char inChar = (char)SerialBT.read();
    if (inChar == '\n') {  // End of message
      inputString.trim();

      if (inputString == "right") {
        //digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));  // Toggle LED
        SerialBT.println("command: " + inputString);
         Serial.print("inputString=");
        Serial.println(inputString);
        crc = crc8((uint8_t*)&data[3], 1, 0x07, 0x00, 0x00, false, false);
        
        sendSPI(data[3]);
        sendSPI(crc);
      }
      else if ( inputString == "left") {
        SerialBT.println("command: " + inputString);
         Serial.print("inputString=");
        Serial.println(inputString);
        crc = crc8((uint8_t*)&data[2], 1, 0x07, 0x00, 0x00, false, false);
        sendSPI(data[2]);
        sendSPI(crc);
      }
      else if ( inputString == "up") {
        SerialBT.println("command: " + inputString);
         Serial.print("inputString=");
          Serial.println(inputString);
        crc = crc8((uint8_t*)&data[0], 1, 0x07, 0x00, 0x00, false, false);
        sendSPI(data[0]);
        sendSPI(crc);
      }
      else if ( inputString == "down") {
        SerialBT.println("command: " + inputString);
         Serial.print("inputString=");
          Serial.println(inputString);
        crc = crc8((uint8_t*)&data[1], 1, 0x07, 0x00, 0x00, false, false);
        sendSPI(data[1]);
        sendSPI(crc);
      }
      else if (inputString == "stop"){
         SerialBT.println("command: " + inputString);
         Serial.print("inputString=");
        Serial.println(inputString);
        crc = crc8((uint8_t*)&data[4], 1, 0x07, 0x00, 0x00, false, false);
        sendSPI(data[4]);
        sendSPI(crc);
      }
      else {
        SerialBT.println("Unknown command: " + inputString);
      }
      inputString = "";
    } 
    else {
      inputString += inChar;
    }
  }
   
}