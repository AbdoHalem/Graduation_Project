#include <SPI.h>

#include <CRC.h>  

#define SS_PIN  5   // SPI Chip Select (Adjust according to your ESP32 wiring)

void setup() {
    Serial.begin(9600);
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
    char commands[] = {'f', 'b', 'l', 'r'};
    for (int i = 0; i < 4; i++) {
      uint8_t crc = crc8((uint8_t*)&commands[i], 1, 0x07, 0x00, 0x00, false, false);
        sendSPI(commands[i]);
        sendSPI(crc);
        //Serial.print("Sent: ");
        Serial.println(commands[i]);
        Serial.println(crc);
        delay(1000);
    }
}
