import paho.mqtt.publish as publish

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "test/topic"



while True:
    msg = input("Enter the message: ")
    publish.single(MQTT_PATH, msg, hostname=MQTT_SERVER)
