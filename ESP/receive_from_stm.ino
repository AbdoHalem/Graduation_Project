// تعريف المتغيرات
byte receivedFrame[4];    // مصفوفة لتخزين الـ 4 bytes
int byteCount = 0;        // عداد لتتبع عدد الـ bytes
bool frameStarted = false; // مؤشر لبداية الـ frame

void setup() {
  // بدء الاتصال التسلسلي مع الـ Serial Monitor و UART0 بسرعة 115200 baud
  Serial.begin(9600);
  
  Serial.println("ESP32 جاهز لاستقبال الـ Frame");
}

void loop() {
  if (Serial.available() > 0) {
    byte incomingByte = Serial.read();

    // التحقق من الـ Start Byte
    if (incomingByte == 0xAA && !frameStarted) {
      frameStarted = true;         // بدء استقبال الـ frame
      byteCount = 0;               // إعادة تهيئة العداد
      receivedFrame[byteCount] = incomingByte; // تخزين الـ Start Byte
      byteCount++;
    }
    // إذا تم العثور على الـ Start Byte، اجمع الـ bytes التالية
    else if (frameStarted) {
      receivedFrame[byteCount] = incomingByte;
      byteCount++;

      // عند اكتمال الـ frame (4 bytes)
      if (byteCount == 4) {
        // طباعة الـ Frame على الـ Serial Monitor
        Serial.print("Received Frame: ");
        for (int i = 0; i < 4; i++) {
          if (receivedFrame[i] < 0x10) {
            Serial.print("0"); // إضافة صفر إذا كان الرقم أقل من 16
          }
          Serial.print(receivedFrame[i], HEX);
          Serial.print(" ");
        }
        Serial.println();

        // إعادة تهيئة الحالة لاستقبال frame جديد
        frameStarted = false;
        byteCount = 0;
      }
    }
  }
}
