import os
import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
import paho.mqtt.client as mqtt
import onnxruntime
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # To disaple displaying the tensorflow logs
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # Disable GPU
# Ensure the expected module is available in sys.modules:
sys.modules['np._core.multiarray'] = np.core.multiarray

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "ADAS_GP/sign"

# 1️⃣ Initialize a persistent MQTT client
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

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
    # Load ONNX model
    session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
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

    return session, cap, input_images

# ────────────────────────────────────────────────────────────────
# NEW: frame → ONNX‑ready input tensor
def preprocessor(frame, input_width, input_height):
    # 1) resize & pad to square
    x = cv2.resize(frame, (input_width, input_height))
    # 2) normalize to [0,1]
    image_data = x.astype(np.float32) / 255.0
    # 3) HWC → CHW
    image_data = np.transpose(image_data, (2, 0, 1))
    # 4) add batch dim
    return np.expand_dims(image_data, axis=0)
# ────────────────────────────────────────────────────────────────

def process_frame(session, confidence, frame, iou_thresh=0.45):
    """
    Runs quantized YOLO ONNX inference + NMS on a single frame.
    Args:
        session: ONNX Runtime inference session.
        confidence (float): Confidence threshold for object detection.
        frame: A single video frame or image.
    Returns:
        annotated_frame: Frame with annotations.
        list: List of cropped images (regions of detected objects).
    """
    # grab the model’s input shape
    inp = session.get_inputs()[0]
    _, _, input_height, input_width = inp.shape

    # 1) preprocess
    img_tensor = preprocessor(frame, input_width, input_height)
    # wrap for OrtValue if needed (same as inference.py)
    ort_val = onnxruntime.OrtValue.ortvalue_from_numpy(img_tensor)
    # 2) inference (output key is "output0" in that repo)
    raw_outputs = session.run(["output0"], {inp.name: ort_val})[0]

    # 3) postprocess
    # raw_outputs: shape (1, N, 5+num_classes)
    outputs = np.squeeze(raw_outputs)                # → (N, 5+C)
    outputs = np.transpose(outputs)                  # → (5+C, N)
    rows = outputs.shape[0]                          # N

    img_h, img_w = frame.shape[:2]
    x_factor = img_w / input_width
    y_factor = img_h / input_height

    boxes, scores, class_ids = [], [], []
    for i in range(rows):
        # 5 coords + C class scores
        coords = outputs[i, :4]
        class_scores = outputs[i, 4:]
        max_score = float(np.max(class_scores))
        if max_score < confidence:
            continue

        class_id = int(np.argmax(class_scores))
        x_c, y_c, w, h = coords

        # decode & scale back to original
        left   = int((x_c - w/2) * x_factor)
        top    = int((y_c - h/2) * y_factor)
        width  = int(w * x_factor)
        height = int(h * y_factor)

        boxes.append([left, top, width, height])
        scores.append(max_score)
        class_ids.append(class_id)

    # 4) NMS
    indices = cv2.dnn.NMSBoxes(boxes, scores, confidence, iou_thresh)

    annotated_frame = frame.copy()
    cropped_images = []
    if len(indices) > 0:
        for idx in indices.flatten():
            x, y, w, h = boxes[idx]
            # draw
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), (0,255,0), 2)
            # crop
            crop = frame[y:y+h, x:x+w]
            if crop.size:
                cropped_images.append(crop)

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

    # Predict the class — ensure dtype is FLOAT32, not FLOAT64
    img = img.astype(np.float32)
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])
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
    recog_model_path = r'recognition_model/sign_model.tflite'       # for linux
    # Create the TFLite interpreter and allocate tensors
    interpreter = tflite.Interpreter(model_path=recog_model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Get the detection model and video paths
    root = os.getcwd()
    detection_model_path = r'detection_model/best_quant_v2.onnx'     # for linux
    input_type = 'camera'                                        # Change to 'image' or 'camera' as needed
    input_source = r'test_videos/video2.mp4'                     # Required for 'video' or 'image' (for linux)

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
                    annotated_frame, cropped_signs = process_frame(detection_model, confidence_threshold, frame)
                    # # Add debug display
                    # cv2.imshow('Detection Output', annotated_frame)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                    
                    # Predict the sign type of each crop
                    for cropped_image in cropped_signs:
                        if cropped_image.size == 0:
                            continue  # Skip empty crops

                        # Get current sign prediction
                        current_sign = predict_sign(cropped_image)
                        # Only send if sign is different from previous
                        if (current_sign != last_sign) and (current_sign != "Unknown Sign"):                            
                            message = f"Sign Type is: {current_sign}"
                            try:
                                mqtt_client.publish(MQTT_TOPIC, message)
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
                        if (current_sign != last_sign) and (current_sign != "Unknown Sign"):
                            message = f"Sign Type is: {current_sign}"
                            try:
                                mqtt_client.publish(MQTT_TOPIC, message)
                                last_sign = current_sign        # Update last sent sign
                            except KeyboardInterrupt:
                                print("\nShutting down the client.")

    except KeyboardInterrupt:
        print("\nShutting down the client.")
    finally:
        # Close the mqtt connection
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        cap.release()
        print("Publisher closed.")
