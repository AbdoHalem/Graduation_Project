import cv2
import face_recognition
import time  

known_face_encodings = []
known_face_names = []

known_person1_img = face_recognition.load_image_file(r"C:\Users\DELL\OneDrive\Desktop\graduation project\face recognition\nancy.png")
known_person2_img = face_recognition.load_image_file(r"C:\Users\DELL\OneDrive\Desktop\graduation project\face recognition\logy.jpg")
known_person3_img = face_recognition.load_image_file(r"C:\Users\DELL\OneDrive\Desktop\graduation project\face recognition\abdo.jpg")

known_person1_encoding = face_recognition.face_encodings(known_person1_img)[0]
known_person2_encoding = face_recognition.face_encodings(known_person2_img)[0]
known_person3_encoding = face_recognition.face_encodings(known_person3_img)[0]

known_face_encodings.append(known_person1_encoding)
known_face_encodings.append(known_person2_encoding)
known_face_encodings.append(known_person3_encoding)

known_face_names.append("Nancy Ahmed")
known_face_names.append("logy")
known_face_names.append("abdo")

PASSWORD = "123"

password_authenticated = False
unknown_face_start_time = None  # To track when the unknown face first appears
UNKNOWN_FACE_THRESHOLD = 15  # Time in seconds to trigger password prompt

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()

    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    unknown_face_detected = False  # Flag to check if an unknown face exists in the current frame

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            unknown_face_start_time = None  # Reset timer when a known face is detected
        else:
            unknown_face_detected = True
            if unknown_face_start_time is None:  # Start the timer for the unknown face
                unknown_face_start_time = time.time()

            # Check if 15 seconds have passed with an unknown face
            elapsed_time = time.time() - unknown_face_start_time
            if elapsed_time >= UNKNOWN_FACE_THRESHOLD and not password_authenticated:
                print("Unknown face detected for 15 seconds! Please enter the password:")
                entered_password = input("Password: ").strip()

                # Check password
                if entered_password == PASSWORD:
                    print("Access granted!")
                    password_authenticated = True
                else:
                    print("Incorrect password. Exiting...")
                    cap.release()
                    cv2.destroyAllWindows()
                    exit()

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
        cv2.putText(frame, name, (left, top-10), cv2.FONT_HERSHEY_COMPLEX, 0.9, (0, 0, 255), 2)

    # If no unknown face is detected, reset the timer
    if not unknown_face_detected:
        unknown_face_start_time = None

    cv2.imshow("Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        break

cap.release()
cv2.destroyAllWindows()
