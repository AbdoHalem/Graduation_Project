#include <CRC.h>  

#define UART_BAUD_RATE 115200
#define UART_TX_PIN 17
#define UART_RX_PIN 16

void setup() {
  Serial.begin(115200);  
  Serial2.begin(UART_BAUD_RATE, SERIAL_8N1, UART_TX_PIN, UART_RX_PIN);  
}

void loop() {

  char data[] = {'f', 'b', 'l', 'r'};  // data
  uint8_t dataSize = sizeof(data);     // size of data

  for (int i = 0; i < dataSize; i++) {
    // calculate crc8 for cuurent char.
    uint8_t crc = crc8((uint8_t*)&data[i], 1, 0x07, 0x00, 0x00, false, false);  // حساب CRC8 للحرف الواحد

    // printing the char and crc on monitor
    Serial.print("Sending char: ");
    Serial.print(data[i]);
    Serial.print(" with CRC8: 0x");
    Serial.println(crc, HEX);

    // sending the character using usart
    Serial2.write(data[i]);

    // sending crc8 ( one byte)
    Serial2.write(crc);

    delay(500);  // wait 500ms before sending the next char.
  }

  delay(1000);  // wait one second before sending again
}