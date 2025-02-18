#include <Arduino.h>

const uint16_t crc_polynomial = 0x8008;

uint16_t calculateCRC(const uint8_t* data, size_t length) {
    uint16_t crc = 0;

    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;

        for (int j = 0; j < 8; ++j) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ crc_polynomial;
            } else {
                crc = crc << 1;
            }
        }
    }

    return crc;
}

void setup() {
    Serial.begin(9600);
   
    

    // Simulated received data
    uint8_t data[] = {0x12, 0x34, 0x56, 0x78};
    uint16_t crcChecksum = calculateCRC(data, sizeof(data));

    // Print Data
    Serial.print("Data: ");
    for (size_t i = 0; i < sizeof(data); ++i) {
        Serial.print(data[i], HEX);
        Serial.print(" ");
    }
    // Print CRC
    Serial.print("\nCRC Checksum: 0x");
    Serial.println(crcChecksum, HEX);

    Serial.write(data, sizeof(data));
    Serial.write((uint8_t*)&crcChecksum, sizeof(crcChecksum)); 
}

void loop() {
  
}
