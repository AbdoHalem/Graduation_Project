import os
import numpy as np
import cv2
from tensorflow.keras.models import load_model
import paho.mqtt.publish as publish
from ultralytics import YOLO
import numpy
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # To disaple displaying the tensorflow logs
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # Disable GPU
# Ensure the expected module is available in sys.modules:
sys.modules['numpy._core.multiarray'] = numpy.core.multiarray

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "ADAS_GP/sign"

'''################# Detection Functions #################'''
def initialize_model_and_source(model_path, input_type, input_source=None):
    """
    Initialize the YOLO model and input source.
    Args:
        model_path (str): Relative path to the YOLO model file (.pt).
        input_type (str): Type of input source ('video', 'image', 'camera').
        input_source (str or None): Relative path to the input file or folder (for 'video' or 'image').
    Returns:
        model: Loaded YOLO model.
        cap: VideoCapture object for video or camera inputs, or None for image input.
        input_images (list): List of image paths if input_type is 'image', otherwise None.
    """
    root = os.getcwd()
    model_path = os.path.join(root, model_path)
    input_source = os.path.join(root, input_source) if input_source else None
    model = YOLO(model_path)
    cap = None
    input_images = None

    if input_type == 'video':
        cap = cv2.VideoCapture(input_source)
    elif input_type == 'camera':
        cap = cv2.VideoCapture(0)  # Default to the first connected camera
    elif input_type == 'image':
        if os.path.isdir(input_source):
            input_images = [os.path.join(input_source, f) for f in os.listdir(input_source)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        else:
            raise ValueError("Input source must be a valid directory for images.")
    else:
        raise ValueError("Invalid input type. Choose 'video', 'image', or 'camera'.")

    return model, cap, input_images

def process_frame(model, confidence, frame):
    """
    Process a single frame using the YOLO model.
    Args:
        model: YOLO model instance.
        confidence (float): Confidence threshold for object detection.
        frame: A single video frame or image.
    Returns:
        annotated_frame: Frame with annotations.
        list: List of cropped images (regions of detected objects).
    """
    cropped_images = []

    # Perform inference on the current frame
    results = model(frame, conf=confidence)

    # Visualize the results on the frame
    annotated_frame = results[0].plot()

    # Extract bounding boxes and crop regions
    boxes = results[0].boxes.xyxy  # Bounding boxes (x1, y1, x2, y2)
    for box in boxes:
        x1, y1, x2, y2 = map(int, box[:4])
        cropped_region = frame[y1:y2, x1:x2]
        cropped_images.append(cropped_region)

    return annotated_frame, cropped_images
'''#########################################################'''

'''################# Recognition Functions #################'''
# Image Preprocessing Functions
def grayscale(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img

def equalize(img):
    img = cv2.equalizeHist(img)
    return img

def preprocessing(img):
    img = grayscale(img)
    img = equalize(img)
    img = img / 255  # Normalize the image
    return img

'''Function to get the label of ths input sign'''
def getClassName(classNo):
    class_names = [
    "Speed limit (20km/h)",
    "Speed limit (30km/h)",
    "Speed limit (50km/h)",
    "Speed limit (60km/h)",
    "Speed limit (70km/h)",
    "Speed limit (80km/h)",
    "End of speed limit (80km/h)",
    "Speed limit (100km/h)",
    "Speed limit (120km/h)",
    "No passing",
    "No passing for vehicles over 3.5 metric tons",
    "Right-of-way at the next intersection",
    "Priority road",
    "Yield",
    "Stop",
    "No vehicles",
    "Vehicles over 3.5 metric tons prohibited",
    "No entry",
    "General caution",
    "Dangerous curve to the left",
    "Dangerous curve to the right",
    "Double curve",
    "Bumpy road",
    "Slippery road",
    "Road narrows on the right",
    "Road work",
    "Traffic signals",
    "Pedestrians",
    "Children crossing",
    "Bicycles crossing",
    "Beware of ice/snow",
    "Wild animals crossing",
    "End of all speed and passing limits",
    "Turn right ahead",
    "Turn left ahead",
    "Ahead only",
    "Go straight or right",
    "Go straight or left",
    "Keep right",
    "Keep left",
    "Roundabout mandatory",
    "End of no passing",
    "End of no passing by vehicles over 3.5 metric tons",
    "Speed limit (40km/h)",
    "Speed limit (90km/h)",
    "No stopping",
    "No horn",
    "No passing"
    ]
    return class_names[classNo] if classNo < len(class_names) else "Unknown"

'''Function to predict the sign type'''
def predict_sign(cropped_image):
    if cropped_image is None or cropped_image.size == 0:
        print("Error: Cropped image is empty.")
        return "Unknown Sign"

    # Preprocess the image
    img = cv2.resize(cropped_image, (32, 32))  # Resize to the input size of the recog_model
    img = preprocessing(img)
    img = img.reshape(1, 32, 32, 1)

    # Predict the class
    predictions = recog_model.predict(img)
    classIndex = np.argmax(predictions, axis=-1)[0]
    probabilityValue = np.max(predictions)

    # Print the result
    if probabilityValue > 0.9:  # You can adjust this threshold
        className = getClassName(classIndex)
        print(f"Sign Type is: {className}")
        return className
    else:
        print("No sign detected")
        return "Unknown Sign"
'''#########################################################'''

''' Main Code '''
if __name__ == "__main__" :
    # Load the trained recog_model
    # recog_model_path = r'recognition_model\\model.h5'       # for windows
    recog_model_path = r'recognition_model/model_v3.h5'       # for linux
    # print(os.path.abspath(recog_model_path))                # for testing only
    recog_model = load_model(recog_model_path)

    # Get the detection model and video paths
    root = os.getcwd()
    # detection_model_path = r'detection_model\\best.pt'    # for windows
    detection_model_path = r'detection_model/best.pt'       # for linux
    input_type = 'video'                                    # Change to 'image' or 'camera' as needed
    # input_source = r'test_videos\\video2.mp4'             # Required for 'video' or 'image'
    input_source = r'test_videos/video2.mp4'                # Required for 'video' or 'image' (for linux)

    # Initialize model and input source
    detection_model, cap, input_images = initialize_model_and_source(detection_model_path, input_type, input_source)
    confidence_threshold = 0.34

    # New variables for frame skipping and duplicate detection
    frame_interval = 5          # Process every 5th frame
    last_sign = None            # Track last sent sign
    frame_counter = 0           # Count processed frames

    try:
        if input_type in ['video', 'camera']:
            if not cap.isOpened():
                print("Error: Unable to open the input source.")
            else:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frame_counter += 1
                    # Only process every 10th frame
                    if frame_counter % frame_interval != 0:
                        continue

                    # Process the frame and get the cropped signs
                    _, cropped_signs = process_frame(detection_model, confidence_threshold, frame)
                    # Predict the sign type of each crop
                    for cropped_image in cropped_signs:
                        if cropped_image.size == 0:
                            continue  # Skip empty crops

                        # Get current sign prediction
                        current_sign = predict_sign(cropped_image)
                        # Only send if sign is different from previous
                        if current_sign != last_sign:                            
                            message = f"Sign Type is: {current_sign}"
                            try:
                                # send_mqtt(mqtt_client, message)
                                publish.single(MQTT_TOPIC, message, hostname=MQTT_BROKER)
                                last_sign = current_sign       # Update last sent sign
                            except KeyboardInterrupt:
                                print("\nShutting down the publisher.")
                cap.release()
        
        elif input_type == 'image':
            if not input_images:
                print("Error: No images found in the specified directory.")
            else:
                for image_path in input_images:
                    frame = cv2.imread(image_path)
                    # Process the image
                    _, cropped_signs = process_frame(detection_model, confidence_threshold, frame)
                    # Predict the sign type of each image
                    for cropped_image in cropped_signs:
                        if cropped_image.size == 0:
                            continue

                        # Get current sign prediction
                        current_sign = predict_sign(cropped_image)
                        # Only send if sign is different from previous
                        if current_sign != last_sign:
                            message = f"Sign Type is: {current_sign}"
                            try:
                                # send_mqtt(mqtt_client, message)
                                publish.single(MQTT_TOPIC, message, hostname=MQTT_BROKER)
                                last_sign = current_sign        # Update last sent sign
                            except KeyboardInterrupt:
                                print("\nShutting down the client.")

    except KeyboardInterrupt:
        print("\nShutting down the client.")
    finally:
        print("Publisher closed.")
