#include "HardwareSerial.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include <freertos/queue.h>

#define RX_PIN 16  // RX pin (GPIO16)
#define TX_PIN 17  // TX pin (GPIO17)

// WiFi credentials
const char* ssid = "WE_F87610";
const char* password = "12028502";

// MQTT Broker details
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_topic = "ADAS_GP/Baremetal";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

HardwareSerial MySerial(1);  // Use UART1

// FreeRTOS queue for UART data
QueueHandle_t uartQueue;

// MQTT reconnect function
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 2 seconds");
      delay(2000);
    }
  }
}

// ISR for receiving UART data
void IRAM_ATTR onUartReceive() {
  while (MySerial.available()) {
    char receivedChar = MySerial.read();
    // Send to queue (non-blocking)
    xQueueSendFromISR(uartQueue, &receivedChar, NULL);
  }
}

void setup() {
  Serial.begin(9600);
  MySerial.begin(9600, SERIAL_8N1, RX_PIN, TX_PIN);

  // Create FreeRTOS queue (size: 100 chars)
  uartQueue = xQueueCreate(100, sizeof(char));
  if (uartQueue == NULL) {
    Serial.println("Failed to create queue");
    while (1);
  }

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting...");
  }
  Serial.println("Connected to WiFi");

  // Configure MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);

  // Connect to MQTT
  reconnectMQTT();

  // Enable UART RX interrupt
  MySerial.onReceive(onUartReceive);
  Serial.println("ESP32 UART Interrupt Initialized!");
}

void loop() {
  // Keep MQTT connection alive
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // Process data from UART queue
  char receivedChar;
  if (xQueueReceive(uartQueue, &receivedChar, 0) == pdTRUE) {
    char msg[2] = {receivedChar, '\0'}; // Convert to C-string for MQTT
    mqttClient.publish(mqtt_topic, msg);
    // Serial.println(msg);
  }
}