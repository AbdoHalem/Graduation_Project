import cv2
import os, mmap, time, threading, ssl, subprocess
import paho.mqtt.client as mqtt

# --- SHARED‐MEMORY CONFIG ---
SHM_PATH    = "/dev/shm/frame_buf"
FRAME_W     = 640
FRAME_H     = 480
FRAME_C     = 3
BUF_SIZE    = FRAME_W * FRAME_H * FRAME_C

# MQTT Configuration
MQTT_BROKER = "46ecfaf93a7b4d4b87b953f6cdc35b6d.s1.eu.hivemq.cloud"
BROKER_USERNAME = "ADAS_GP_25"
BROKER_PASSWORD = "ADAS_Gp_25"
MQTT_PORT = 8883
MQTT_TOPICS = ["ADAS_GP/sign", "ADAS_GP/lane"]

# container/image mapping
CONTAINERS = {
    "ADAS_GP/sign": {
        "name": "sign_cont",
        "image": "halem10/sign_publisher:1.3"
    },
    "ADAS_GP/lane": {
        "name": "lane_cont",
        "image": "halem10/lane_publisher:1.2"
    }
}

# Variables for checking the feature is ON or OFF
sign_status = None
lane_status = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"📡 Subscribed to topic: {topic}")
    else:
        print(f"❌ MQTT connection failed, rc={rc}")


def on_message(client, userdata, msg):
    global sign_status, lane_status

    message = msg.message.decode(errors="ignore")
    topic   = msg.topic

    if topic == "ADAS_GP/sign":
        sign_status = message
        print(f"📥 [sign] status updated: {sign_status}")
    elif topic == "ADAS_GP/lane":
        lane_status = message
        print(f"📥 [lane] status updated: {lane_status}")
    else:
        print(f"📥 [unknown topic {topic}]: {message}")


def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(BROKER_USERNAME, BROKER_PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_forever()  # blocking, so we run it in its own thread

def manage_container(topic, status):
    cfg = CONTAINERS[topic]
    cont_name = cfg["name"]
    image = cfg["image"]

    # check if container exists at all
    exists = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name=^{cont_name}$"],
        stdout=subprocess.PIPE, text=True
    ).stdout.strip()

    running = subprocess.run(
        ["docker", "ps", "-q", "-f", f"name=^{cont_name}$"],
        stdout=subprocess.PIPE, text=True
    ).stdout.strip()

    if status == "1":
        if not exists:
            # run new container
            print(f"▶️ Starting new container '{cont_name}' from {image}")
            subprocess.run(["docker", "run", "-d", "--name", cont_name, image])
        elif not running:
            # start existing
            print(f"🔄 Restarting container '{cont_name}'")
            subprocess.run(["docker", "start", cont_name])
    else:  # status == "0"
        if running:
            print(f"⏹ Stopping container '{cont_name}'")
            subprocess.run(["docker", "stop", cont_name])

# --- prepare shared memory file ---
if not os.path.exists(SHM_PATH):
    with open(SHM_PATH, "wb") as f:
        f.truncate(BUF_SIZE)

fd  = os.open(SHM_PATH, os.O_RDWR)
shm = mmap.mmap(fd, BUF_SIZE,
                flags=mmap.MAP_SHARED,
                prot=(mmap.PROT_WRITE | mmap.PROT_READ))

# --- GStreamer pipeline (V4L2) ---
gst_pipeline = (
    "v4l2src device=/dev/video0 ! "
    "videoconvert ! "
    "videoflip method=rotate-180 ! "
    "video/x-raw,format=BGR ! "
    "appsink"
)

# --- start MQTT thread ---
mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()
print("🚀 Started MQTT client in background. Capturing frames now...")

# cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Failed to open GStreamer pipeline")

try:
    # frame_id = 0
    current_buf_size = BUF_SIZE

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Frame grab failed; exiting loop.")
            break

        h, w, c = frame.shape
        new_size = w * h * c

        # re-map if size changed
        if new_size != current_buf_size:
            shm.close()
            os.close(fd)
            with open(SHM_PATH, "wb") as f:
                f.truncate(new_size)
            fd = os.open(SHM_PATH, os.O_RDWR)
            shm = mmap.mmap(fd, new_size,
                            flags=mmap.MAP_SHARED,
                            prot=(mmap.PROT_WRITE | mmap.PROT_READ))
            current_buf_size = new_size

        shm.seek(0)
        shm.write(frame.tobytes())

        # frame_id += 1
        time.sleep(0.04)

finally:
    cap.release()
    shm.close()
    os.close(fd)
    print("🛑 Clean shutdown complete.")
