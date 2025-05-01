import paho.mqtt.client as mqtt
import threading

# MQTT settings
broker = "test.mosquitto.org"
port = 1883
topics = ["ADAS_GP/sign", "ADAS_GP/drowsiness", "ADAS_GP/lane"]

# Define the callback functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    for topic in topics:
        client.subscribe(topic)
    print("Subscribed to topics:", topics)

def process_topic(client, userdata, topic):
    while not userdata["stop"]:
        if topic in userdata["messages"] and userdata["messages"][topic] is not None:
            message = userdata["messages"].pop(topic)
            if message == "close":
                userdata["stop"] = True
                client.loop_stop()
                client.disconnect()
                break

def on_message(client, userdata, msg):
    topic = msg.topic
    message = msg.payload.decode()
    print(f"{topic} => {message}")
    userdata["messages"][topic] = message

# Userdata to hold messages and stop signal
userdata = {
    "messages": {topic: None for topic in topics},
    "stop": False
}

# Create an MQTT client
# client = mqtt.Client(userdata=userdata, protocol=mqtt.MQTTv311)
client = mqtt.Client(userdata=userdata, protocol=mqtt.MQTTv311,
                     callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

# Assign callback functions
# client.on_connect = on_connect
@client.connect_callback()
def handle_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    for topic in topics:
        client.subscribe(topic)
    print("Subscribed to topics:", topics)

# client.on_message = on_message
@client.message_callback()
def handle_message(client, userdata, message):
    print(f"{message.topic} => {message.payload.decode()}")
    userdata["messages"][message.topic] = message.payload.decode()

# Connect to the broker
client.connect(broker, port, 60)

# Create threads for each topic
threads = []
for topic in topics:
    thread = threading.Thread(target=process_topic, args=(client, userdata, topic))
    threads.append(thread)
    thread.start()

# Start the loop
client.loop_start()

try:
    while not userdata["stop"]:
        pass  # Keep the main thread alive to detect KeyboardInterrupt
except KeyboardInterrupt:
    print("\nKeyboardInterrupt detected, stopping...")
    userdata["stop"] = True
    client.loop_stop()      # Stop the MQTT loop
    client.disconnect()     # Disconnect from broker
    for thread in threads:
        thread.join()  # Wait for all threads to finish

print("Program terminated.")
