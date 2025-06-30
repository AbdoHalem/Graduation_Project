import cv2
import dlib
import time
import ssl
import paho.mqtt.client as mqtt
from scipy.spatial import distance
from imutils import face_utils
import playsound

# Constants
EYE_ASPECT_RATIO_THRESHOLD = 0.2
YAWN_RATIO_THRESHOLD = 0.5
DROWSINESS_FRAME_THRESHOLD = 15
NO_FACE_FRAME_THRESHOLD = 25
TIME_THRESHOLD = 60  # seconds between warnings

# Paths to resources
SHAPE_PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
LOOK_AHEAD_SOUND = "look_in_front_of_you.mp3"
OPEN_EYES_SOUND = "open_your_eyes.mp3"
YAWN_WARNING_SOUND = "you_are_yawning.mp3"
DANGER_SOUND = "danger_sound.mp3"

# MQTT (Private HiveMQ Cloud)
broker = "46ecfaf93a7b4d4b87b953f6cdc35b6d.s1.eu.hivemq.cloud"
port = 8883
USERNAME = "ADAS_GP_25"
PASSWORD = "ADAS_Gp_25"
MQTT_PATH = "ADAS_GP/drowsiness"
ENABLE_TOPIC = "ADAS_GP/drowsy_enable"

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# State variables
drowsy_enabled = True  # ← متغير التفعيل
drowsiness_frame_counter = 0
no_face_detected_counter = 0
warning_times = []

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_PATH)
    client.subscribe(ENABLE_TOPIC)
    print(f"📥 Subscribed to: {MQTT_PATH} and {ENABLE_TOPIC}")

def on_message(client, userdata, msg):
    global drowsy_enabled
    topic = msg.topic
    payload = msg.payload.decode()

    print(f"📨 Received from {topic}: {payload}")

    if topic == ENABLE_TOPIC:
        if payload == "1":
            drowsy_enabled = True
            print("✅ Drowsiness detection ENABLED")
        elif payload == "0":
            drowsy_enabled = False
            print("⛔ Drowsiness detection DISABLED")

client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port, 60)
client.loop_start()

# Utilities
def calculate_ear(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def calculate_yawn_ratio(mouth):
    D = distance.euclidean(mouth[1], mouth[7])
    E = distance.euclidean(mouth[3], mouth[5])
    F = distance.euclidean(mouth[0], mouth[4])
    return (D + E) / (2.0 * F)

def play_alarm(sound_file):
    playsound.playsound(sound_file, True)

def check_driver_alertness(frame, face_detected, average_ear=None, yawn_ratio=None):
    global drowsiness_frame_counter, no_face_detected_counter, warning_times

    current_time = time.time()

    if not face_detected:
        no_face_detected_counter += 1
        if no_face_detected_counter > NO_FACE_FRAME_THRESHOLD:
            cv2.putText(frame, "Look in front of you!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            play_alarm(LOOK_AHEAD_SOUND)
            message = "Warning: Look in front of you!"
            client.publish(MQTT_PATH, message)
            print(f"[MQTT] Published: {message}")
            warning_times.append(current_time)
    else:
        no_face_detected_counter = 0

        if average_ear is not None and yawn_ratio is not None:
            if average_ear < EYE_ASPECT_RATIO_THRESHOLD or yawn_ratio > YAWN_RATIO_THRESHOLD:
                drowsiness_frame_counter += 1
                if drowsiness_frame_counter > DROWSINESS_FRAME_THRESHOLD:
                    cv2.putText(frame, "You are drowsy!!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    if average_ear < EYE_ASPECT_RATIO_THRESHOLD:
                        play_alarm(OPEN_EYES_SOUND)
                        message = "Warning: You are drowsy! Open your eyes!"
                        client.publish(MQTT_PATH, message)
                        print(f"[MQTT] Published: {message}")
                    if yawn_ratio > YAWN_RATIO_THRESHOLD:
                        play_alarm(YAWN_WARNING_SOUND)
                        message = "Warning: You are yawning!"
                        client.publish(MQTT_PATH, message)
                        print(f"[MQTT] Published: {message}")
                    warning_times.append(current_time)
            else:
                drowsiness_frame_counter = 0

    # Danger detection logic
    if len(warning_times) > 3:
        warning_times.pop(0)

    if len(warning_times) == 3 and (warning_times[2] - warning_times[0] <= TIME_THRESHOLD):
        play_alarm(DANGER_SOUND)
        message = "Danger: Multiple warnings in a short period!"
        message2 = "d"
        client.publish(MQTT_PATH, message)
        client.publish(MQTT_PATH, message2)
        print(f"[MQTT] Published: {message}")
        print(f"[MQTT] Published: {message2}")
        warning_times.pop(0)

def main():
    cap = cv2.VideoCapture(0)
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)

    (l_start, l_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
    (r_start, r_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
    (m_start, m_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["inner_mouth"]

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        face_detected = len(faces) > 0

        if drowsy_enabled:
            for face in faces:
                landmarks = predictor(gray, face)
                landmarks = face_utils.shape_to_np(landmarks)

                left_eye = landmarks[l_start:l_end]
                right_eye = landmarks[r_start:r_end]
                mouth = landmarks[m_start:m_end]

                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)
                average_ear = (left_ear + right_ear) / 2.0
                yawn_ratio = calculate_yawn_ratio(mouth)

                cv2.drawContours(frame, [cv2.convexHull(left_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(right_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(mouth)], -1, (0, 255, 0), 1)

                check_driver_alertness(frame, True, average_ear, yawn_ratio)

            if not face_detected:
                check_driver_alertness(frame, False)
        else:
            cv2.putText(frame, "Drowsy Detection OFF", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow("Drowsiness Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
