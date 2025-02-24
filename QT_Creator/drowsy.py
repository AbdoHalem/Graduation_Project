import sys
import cv2
import dlib
import playsound
from scipy.spatial import distance
from imutils import face_utils
import time
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, pyqtSignal

# Constants for thresholds and frame limits
EYE_ASPECT_RATIO_THRESHOLD = 0.2
YAWN_RATIO_THRESHOLD = 0.5
DROWSINESS_FRAME_THRESHOLD = 15
NO_FACE_FRAME_THRESHOLD = 25
DANGER_THRESHOLD = 3
TIME_THRESHOLD = 60

# Paths to resources
SHAPE_PREDICTOR_PATH = "shape_predictor_68_face_landmarks.dat"
LOOK_AHEAD_SOUND = "look_in_front_of_you.mp3"
OPEN_EYES_SOUND = "open_your_eyes.mp3"
YAWN_WARNING_SOUND = "you_are_yawning.mp3"
DANGER_SOUND = "danger_sound.mp3"

# Counters and storage for warning times
drowsiness_frame_counter = 0
no_face_detected_counter = 0
warning_times = []

# Calculate the Eye Aspect Ratio (EAR)
def calculate_ear(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    return (A + B) / (2 * C)

# Calculate the yawn ratio for a given mouth
def calculate_yawn_ratio(mouth):
    D = distance.euclidean(mouth[1], mouth[7])
    E = distance.euclidean(mouth[3], mouth[5])
    F = distance.euclidean(mouth[0], mouth[4])
    return (D + E) / (2 * F)

# Worker thread for detection logic
class DetectionThread(QThread):
    update_text_signal = pyqtSignal(str)

    def run(self):
        global drowsiness_frame_counter, no_face_detected_counter, warning_times
        cap = cv2.VideoCapture(0)
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
        (left_eye_start, left_eye_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
        (right_eye_start, right_eye_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
        (inner_mouth_start, inner_mouth_end) = face_utils.FACIAL_LANDMARKS_68_IDXS["inner_mouth"]

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces_detected = detector(gray)
            face_detected = len(faces_detected) > 0

            for face in faces_detected:
                x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 3)

                landmarks = predictor(gray, face)
                landmarks = face_utils.shape_to_np(landmarks)

                left_eye = landmarks[left_eye_start:left_eye_end]
                right_eye = landmarks[right_eye_start:right_eye_end]
                inner_mouth = landmarks[inner_mouth_start:inner_mouth_end]

                left_ear = calculate_ear(left_eye)
                right_ear = calculate_ear(right_eye)
                average_ear = (left_ear + right_ear) / 2
                yawn_ratio = calculate_yawn_ratio(inner_mouth)

                cv2.drawContours(frame, [cv2.convexHull(left_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(right_eye)], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [cv2.convexHull(inner_mouth)], -1, (0, 255, 0), 1)

                if average_ear < EYE_ASPECT_RATIO_THRESHOLD or yawn_ratio > YAWN_RATIO_THRESHOLD:
                    drowsiness_frame_counter += 1
                    if drowsiness_frame_counter > DROWSINESS_FRAME_THRESHOLD:
                        self.update_text_signal.emit("Drowsy!")
                        if average_ear < EYE_ASPECT_RATIO_THRESHOLD:
                            play_alarm(OPEN_EYES_SOUND)
                        if yawn_ratio > YAWN_RATIO_THRESHOLD:
                            play_alarm(YAWN_WARNING_SOUND)
                        warning_times.append(time.time())
                else:
                    drowsiness_frame_counter = 0

            if not face_detected:
                no_face_detected_counter += 1
                if no_face_detected_counter > NO_FACE_FRAME_THRESHOLD:
                    self.update_text_signal.emit("No face detected! Look in front of you!")
                    play_alarm(LOOK_AHEAD_SOUND)
            else:
                no_face_detected_counter = 0

            # Continuous danger alert
            if len(warning_times) > DANGER_THRESHOLD:
                warning_times.pop(0)  # Keep only the latest warnings
            if len(warning_times) == DANGER_THRESHOLD and (warning_times[-1] - warning_times[0] <= TIME_THRESHOLD):
                self.update_text_signal.emit("DANGER ALERT! Take immediate action!")
                play_alarm(DANGER_SOUND)
                warning_times.pop(0)  # Remove the oldest warning after triggering danger

            cv2.imshow("Drowsiness Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

def play_alarm(sound_file):
    playsound.playsound(sound_file, True)

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("adas.ui", self)  
        # Start the detection thread
        self.detection_thread = DetectionThread()
        self.detection_thread.update_text_signal.connect(self.display_output)
        self.detection_thread.start()

    def display_output(self, message):
        self.textBrowser.append(message) 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
