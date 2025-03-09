
byte receivedFrame[4];    
int byteCount = 0;        
bool frameStarted = false; 

void setup() {
  
  Serial.begin(9600);
  
  Serial.println("ESP32 جاهز لاستقبال الـ Frame");
}

void loop() {
  if (Serial.available() > 0) {
    byte incomingByte = Serial.read();

    
    if (incomingByte == 0xAA && !frameStarted) {
      frameStarted = true;         
      byteCount = 0;               
      receivedFrame[byteCount] = incomingByte; 
      byteCount++;
    }
    
    else if (frameStarted) {
      receivedFrame[byteCount] = incomingByte;
      byteCount++;

      
      if (byteCount == 4) {
       
        Serial.print("Received Frame: ");
        for (int i = 0; i < 4; i++) {
          if (receivedFrame[i] < 0x10) {
            Serial.print("0"); 
          }
          Serial.print(receivedFrame[i], HEX);
          Serial.print(" ");
        }
        Serial.println();

       
        frameStarted = false;
        byteCount = 0;
      }
    }
  }
}
