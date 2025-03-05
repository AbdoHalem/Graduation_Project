//-----------------------------------------------------------
//ESP-NOW: Receiver
//-----------------------------------------------------------
#include <esp_now.h>
#include <WiFi.h>
#include <Wire.h>
#include <CRC.h>  
#include <SPI.h>

//#define UART_BAUD_RATE 9600
//#define UART_TX_PIN 17
//#define UART_RX_PIN 16
#define SS_PIN  5   // SPI Chip Select

#define ENA 5
#define ENB 6
#define IN1 7
#define IN2 8
#define IN3 9
#define IN4 10
uint8_t crc = 0;
char data[] = {'f', 'b', 'l', 'r'};
//uint8_t dataSize = sizeof(data);
//-------------------------------------------------------------------------------------
typedef struct CONTROLER{
  int x_axis;
  int y_axis;
}CONTROLER;
CONTROLER my_controler;

//-------------------------------------------------------------------------------------
void OnDataRecv(const esp_now_recv_info *info, const uint8_t *incomingData, int len){
  memcpy(&my_controler, incomingData, sizeof(my_controler));
}
//======================================================================================
void setup(){
  Serial.begin(9600);
  //Serial2.begin(UART_BAUD_RATE, SERIAL_8N1, UART_RX_PIN, UART_TX_PIN);
  SPI.begin();  // Initialize SPI
  pinMode(SS_PIN, OUTPUT);
  digitalWrite(SS_PIN, HIGH);  // Ensure CS is HIGH initially

  pinMode(ENA,OUTPUT);
  pinMode(ENB,OUTPUT);
  pinMode(IN1,OUTPUT);
  pinMode(IN2,OUTPUT);
  pinMode(IN3,OUTPUT);
  pinMode(IN4,OUTPUT);
  
  //-------------------------------------------------------------------------------------
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK)
  {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  esp_now_register_recv_cb(OnDataRecv);
}
//======================================================================================
void sendSPI(char data) {
    digitalWrite(SS_PIN, LOW);   // Enable SPI communication
    SPI.transfer(data);          // Send the character
    digitalWrite(SS_PIN, HIGH);  // Disable SPI communication
}

void loop(){
  
  
  //int x_read = my_controler.x_axis;
  //int y_read = my_controler.y_axis;

  int x_read = 3500;
  int y_read = 2500;

  if (x_read > 3000 && y_read < 3000 && y_read > 2000){
     
    //Forward(200,200);
    crc = crc8((uint8_t*)&data[0], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[0]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[0]);
    Serial.println(crc);
    //"Sending char: 
    //Serial.print(data[0]);
    // with CRC8:
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[0]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (x_read > 3000 && y_read > 2000){
    //Forward(200,100);
    crc = crc8((uint8_t*)&data[0], 1, 0x07, 0x00, 0x00, false, false);

    sendSPI(data[0]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[0]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[0]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[0]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (y_read > 3000 && x_read < 3000 && x_read > 2000){
    //Right(150);
    crc = crc8((uint8_t*)&data[3], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[3]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[3]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[3]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[3]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (x_read < 2000 && y_read < 3000){
    //Backward(100,200);
    crc = crc8((uint8_t*)&data[1], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[1]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[1]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[1]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[1]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (x_read < 2000 && y_read < 3000 && y_read > 2000){
    //Backward(100,100);
    crc = crc8((uint8_t*)&data[1], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[1]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[1]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[1]);
    //Serial.print(" with CRC8: 0x");
    //.print(crc);
    // sending the character using usart
    //Serial2.write(data[1]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (x_read < 2000 && y_read > 2000){
    //Backward(200,100);
    crc = crc8((uint8_t*)&data[1], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[1]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[1]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[1]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[1]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (y_read < 3000 && x_read < 3000 && x_read > 2000){
    //Left(150);
    crc = crc8((uint8_t*)&data[2], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[2]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[2]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[2]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[2]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
  if (x_read > 3000 && y_read < 3000){
    //Forward(100,200);
    crc = crc8((uint8_t*)&data[0], 1, 0x07, 0x00, 0x00, false, false);
    sendSPI(data[0]);
    sendSPI(crc);
//Serial.print("Sent: ");
    Serial.println(data[0]);
    Serial.println(crc);
    //Serial.print("Sending char: ");
    //Serial.print(data[0]);
    //Serial.print(" with CRC8: 0x");
    //Serial.print(crc);
    // sending the character using usart
    //Serial2.write(data[0]);
    // sending crc8 ( one byte)
    //Serial2.write(crc);
    delay(500); 
  }
}
//-----------------------------------------------------------------------
void Forward(int speed,int speed2){
  analogWrite(ENA,speed);
  analogWrite(ENB,speed2);
  digitalWrite(IN1,1);
  digitalWrite(IN2,0);
  digitalWrite(IN3,1);
  digitalWrite(IN4,0);
}
void Backward(int speed,int speed2){
  analogWrite(ENA,speed);
  analogWrite(ENB,speed2);
  digitalWrite(IN1,0);
  digitalWrite(IN2,1);
  digitalWrite(IN3,0);
  digitalWrite(IN4,1);
}
void Right(int speed){
  analogWrite(ENA,speed);
  analogWrite(ENB,speed);
  digitalWrite(IN1,1);
  digitalWrite(IN2,0);
  digitalWrite(IN3,0);
  digitalWrite(IN4,1);
}
void Left(int speed){
  analogWrite(ENA,speed);
  analogWrite(ENB,speed);
  digitalWrite(IN1,0);
  digitalWrite(IN2,1);
  digitalWrite(IN3,1);
  digitalWrite(IN4,0);
}
void End(){
  digitalWrite(IN1,0);
  digitalWrite(IN2,0);
  digitalWrite(IN3,0);
  digitalWrite(IN4,0);
}