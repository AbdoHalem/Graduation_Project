import cv2
import face_recognition
import time
import ssl
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_SERVER = "46ecfaf93a7b4d4b87b953f6cdc35b6d.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_PATH = "ADAS_GP/facerecog"
USERNAME = "ADAS_GP_25"
PASSWORD = "ADAS_Gp_25"

# Create MQTT client and connect
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)
client.connect(MQTT_SERVER, MQTT_PORT, 60)
client.loop_start()

# Face recognition setup
known_face_encodings = []
known_face_names = []

# Load and encode known faces
known_person1_img = face_recognition.load_image_file("images//nancy.png")
known_person2_img = face_recognition.load_image_file("images//logy.jpg")
known_person3_img = face_recognition.load_image_file("images//abdo.jpg")

known_person1_encoding = face_recognition.face_encodings(known_person1_img)[0]
known_person2_encoding = face_recognition.face_encodings(known_person2_img)[0]
known_person3_encoding = face_recognition.face_encodings(known_person3_img)[0]

known_face_encodings.extend([known_person1_encoding, known_person2_encoding, known_person3_encoding])
known_face_names.extend(["Nancy Ahmed", "logy", "abdo"])

PASSWORD_INPUT = "123"
password_authenticated = False
unknown_face_start_time = None
UNKNOWN_FACE_THRESHOLD = 5

last_sent_name = None

# Start camera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    unknown_face_detected = False

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            unknown_face_start_time = None

            if name != last_sent_name:
                print("It's", name)
                client.publish(MQTT_PATH, f"It's {name}")
                print(f"[MQTT] Published: It's {name}")
                last_sent_name = name
                break 

        else:
            name = "Unknown"
            unknown_face_detected = True

            if unknown_face_start_time is None:
                unknown_face_start_time = time.time()

            elapsed_time = time.time() - unknown_face_start_time
            if elapsed_time >= UNKNOWN_FACE_THRESHOLD and not password_authenticated:
                print("Unknown face detected for 5 seconds! Please enter the password:")
                client.publish(MQTT_PATH, "Unknown face detected for 5 seconds! Please enter the password:")
                entered_password = input("Password: ").strip()

                if entered_password == PASSWORD_INPUT:
                    print("Access granted!")
                    client.publish(MQTT_PATH, "Access granted!")
                    password_authenticated = True
                else:
                    print("Incorrect password. Exiting...")
                    client.publish(MQTT_PATH, "Incorrect password. Exiting...")
                
                break  

            last_sent_name = None

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 0, 255), 2)

    if not unknown_face_detected:
        unknown_face_start_time = None

    cv2.imshow("Video", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if last_sent_name is not None or password_authenticated:
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
