import cv2
import dlib
import playsound
from scipy.spatial import distance
from imutils import face_utils

# Constants for thresholds and frame limits
EYE_ASPECT_RATIO_THRESHOLD = 0.2  # The EAR value below which the driver is considered drowsy
YAWN_RATIO_THRESHOLD = 0.5  # The Yawn ratio above which the driver is considered yawning
DROWSINESS_FRAME_THRESHOLD = 15  # Number of frames to trigger drowsiness warning
NO_FACE_FRAME_THRESHOLD = 25  # Number of frames to trigger no-face warning

# Paths to resources
SHAPE_PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
LOOK_AHEAD_SOUND = "look_in_front_of_you.mp3"
OPEN_EYES_SOUND = "open_your_eyes.mp3"
YAWN_WARNING_SOUND = "you_are_yawning.mp3"

# counters
drowsiness_frame_counter = 0 # counter for drowsy frames
no_face_detected_counter = 0  # counter for frames with no face detected

# Calculate the Eye Aspect Ratio (EAR) for a given eye for param eye which is an Array of eye landmarks
def calculate_ear(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2 * C)

# Calculate the yawn ratio for a given mouth with param mouth which is an Array of mouth landmarks
def calculate_yawn_ratio(mouth):
    D = distance.euclidean(mouth[1], mouth[7])
    E = distance.euclidean(mouth[3], mouth[5])
    F = distance.euclidean(mouth[0], mouth[4])
    return (D + E) / (2 * F)

def play_alarm(sound_file):
    playsound.playsound(sound_file, True)

# Check if the driver is drowsy or yawning and trigger warnings if necessary.
def detect_drowsiness(frame, average_ear, yawn_ratio):

    global drowsiness_frame_counter
    
    if average_ear < EYE_ASPECT_RATIO_THRESHOLD or yawn_ratio > YAWN_RATIO_THRESHOLD: # Check if the driver is drowsy based on EAR or yawn ratio
        drowsiness_frame_counter += 1 # Increment the counter for consecutive drowsy frames
        if drowsiness_frame_counter > DROWSINESS_FRAME_THRESHOLD: 
            cv2.putText(frame, "You are drowsy!!", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            if average_ear < EYE_ASPECT_RATIO_THRESHOLD:
                play_alarm(OPEN_EYES_SOUND)
            if yawn_ratio > YAWN_RATIO_THRESHOLD:
                play_alarm(YAWN_WARNING_SOUND)
    else:
        drowsiness_frame_counter = 0  # Reset counter if no drowsiness detected

# Handle the case where no face is detected
def no_face_detection(frame, face_detected):
   
    global no_face_detected_counter

    if not face_detected: # Check if no face is detected
        no_face_detected_counter += 1
        if no_face_detected_counter > NO_FACE_FRAME_THRESHOLD:
            cv2.putText(frame, "Look in front of you!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            play_alarm(LOOK_AHEAD_SOUND)
    else:
        no_face_detected_counter = 0  # Reset counter if a face is detected

def main():
    cap = cv2.VideoCapture(0)
    detector = dlib.get_frontal_face_detector()  # Initialize the face detector from dlib to detect frontal faces
    predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH) # Load the facial landmark predictor to estimate key facial landmarks on detected faces
    (left_eye_start, left_eye_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]  # Get indices for the left eye landmarks
    (right_eye_start, right_eye_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]  # Get indices for the right eye landmarks
    (inner_mouth_start, inner_mouth_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["inner_mouth"]  # Get indices for the inner mouth landmarks


    while True:
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert frame to grayscale for improved processing efficiency in face detection
            faces_detected = detector(gray) # Detect faces in the grayscale image

            # Handle no-face detection
            no_face_detection(frame, face_detected=(len(faces_detected) > 0))

            for face in faces_detected:
                # Draw a rectangle around the detected face on the frame
                x1 = face.left()
                y1 = face.top()
                x2 = face.right()
                y2 = face.bottom()
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

                landmarks = predictor(gray, face)  # Predict facial landmarks for the detected face in the grayscale image
                landmarks = face_utils.shape_to_np(landmarks)  # Convert landmarks to a NumPy array for easier manipulation

                # Extract eyes and mouth landmarks
                left_eye = landmarks[left_eye_start:left_eye_end]
                right_eye = landmarks[right_eye_start:right_eye_end]
                inner_mouth = landmarks[inner_mouth_start:inner_mouth_end]

                # Calculate EAR and Yawn ratios
                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)
                average_ear = (left_ear + right_ear) / 2
                yawn_ratio = calculate_yawn_ratio(inner_mouth)

                # Draw contours for eyes and mouth
                cv2.drawContours(frame, [cv2.convexHull(left_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(right_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(inner_mouth)], -1, (0, 255, 0), 1)

                # Detect drowsiness
                detect_drowsiness(frame, average_ear, yawn_ratio)

            cv2.imshow("Drowsiness Detection", frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()
    cap.release()


if __name__ == "__main__":
    main()