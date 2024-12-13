import paho.mqtt.client as mqtt

# MQTT settings
broker = "test.mosquitto.org"
port = 1883
topic = "test/topic"

# Define the callback functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(topic)

def on_message(client, userdata, msg):
    print(msg.payload.decode())
    if msg.payload.decode() == "close":
        client.loop_stop()
        client.disconnect()


# Create an MQTT client
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker and start the loop
client.connect(broker, port, 60)
client.loop_forever()
