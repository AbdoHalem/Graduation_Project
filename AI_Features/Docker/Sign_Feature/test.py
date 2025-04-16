import os
import sys
import numpy as np
import cv2
import onnxruntime as ort  # Use ONNX Runtime for inference
import tflite_runtime.interpreter as tflite
import paho.mqtt.publish as publish
import numpy
# Ensure the expected module is available in sys.modules:
sys.modules['numpy._core.multiarray'] = numpy.core.multiarray

# Disable TensorFlow logs and force CPU usage
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "ADAS_GP/sign"

################### Detection Functions using ONNX Runtime ###################
def initialize_detection_onnx(model_path, input_type, input_source=None):
    """
    Initialize the detection model with ONNX Runtime and input source.
    Args:
        model_path (str): Relative path to the YOLO quantized model file (ONNX format).
        input_type (str): Type of input source ('video', 'image', 'camera').
        input_source (str or None): Relative path to the input file/folder.
    Returns:
        session: ONNX Runtime InferenceSession for the detection model.
        cap: cv2.VideoCapture object for video or camera inputs, or None for image input.
        input_images (list): List of image paths if input_type is 'image', otherwise None.
    """
    root = os.getcwd()
    model_path = os.path.join(root, model_path)
    input_source = os.path.join(root, input_source) if input_source else None

    # Create an ONNX Runtime session using the CPU provider
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    
    cap = None
    input_images = None
    if input_type == 'video':
        cap = cv2.VideoCapture(input_source)
    elif input_type == 'camera':
        cap = cv2.VideoCapture(0)
    elif input_type == 'image':
        if os.path.isdir(input_source):
            input_images = [os.path.join(input_source, f) for f in os.listdir(input_source)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        else:
            raise ValueError("Input source must be a valid directory for images.")
    else:
        raise ValueError("Invalid input type. Choose 'video', 'image', or 'camera'.")

    return session, cap, input_images

def preprocess_for_detection(frame, target_size=(640, 640)):
    """
    Preprocess a frame for YOLOv8 ONNX detection.
    Args:
        frame: Input image (BGR).
        target_size (tuple): Target size for the model (width, height).
    Returns:
        Preprocessed image as a numpy array with shape (1, 3, H, W).
    """
    # Resize image
    img_resized = cv2.resize(frame, target_size)
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # Normalize the image to [0,1]
    img_norm = img_rgb.astype(np.float32) / 255.0
    # Change data layout from HWC to CHW
    img_transposed = np.transpose(img_norm, (2, 0, 1))
    # Add a batch dimension: (1, 3, H, W)
    return np.expand_dims(img_transposed, 0)

def postprocess_detections(outputs, frame_shape, conf_threshold=0.34):
    """
    Process the raw ONNX model outputs to extract detections.
    This example assumes outputs[0] contains detections in format:
    [x1, y1, x2, y2, score, class] for each detection.
    Args:
        outputs: The raw outputs from the ONNX model.
        frame_shape: The shape of the original frame.
        conf_threshold: Confidence threshold.
    Returns:
        A list of detections, each as [x1, y1, x2, y2, score, class].
    """
    detections = []
    # Assuming outputs[0] is a NumPy array of shape (N, 6)
    for detection in outputs[0]:
        score = detection[4]
        if score < conf_threshold:
            continue
        # The coordinates might be normalized; here we assume they are already in pixels
        x1, y1, x2, y2 = map(int, detection[:4])
        cls = int(detection[5])
        detections.append([x1, y1, x2, y2, float(score), cls])
    return detections

def process_frame_onnx(session, confidence, frame):
    """
    Process a single frame using the ONNX detection model.
    Args:
        session: ONNX Runtime InferenceSession.
        confidence: Confidence threshold.
        frame: Input image/frame.
    Returns:
        annotated_frame: Frame with drawn bounding boxes.
        cropped_images: List of cropped regions corresponding to detections.
    """
    cropped_images = []
    input_tensor = preprocess_for_detection(frame, target_size=(640, 640))
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: input_tensor})
    detections = postprocess_detections(outputs, frame.shape, conf_threshold=confidence)

    annotated_frame = frame.copy()
    for det in detections:
        x1, y1, x2, y2, score, cls = det
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cropped_region = frame[y1:y2, x1:x2]
        cropped_images.append(cropped_region)
    
    return annotated_frame, cropped_images

################### Recognition Functions (unchanged) ###################
def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def equalize(img):
    return cv2.equalizeHist(img)

def preprocessing(img):
    img = grayscale(img)
    img = equalize(img)
    img = img / 255.0
    return img

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

def predict_sign(cropped_image):
    if cropped_image is None or cropped_image.size == 0:
        print("Error: Cropped image is empty.")
        return "Unknown Sign"
    
    # Preprocess the image
    img = cv2.resize(cropped_image, (32, 32))  # Resize to recognition model input size
    img = preprocessing(img)
    img = img.reshape(1, 32, 32, 1)
    
    # Run inference with TFLite interpreter
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])
    classIndex = np.argmax(predictions, axis=-1)[0]
    probabilityValue = np.max(predictions)
    
    if probabilityValue > 0.9:
        className = getClassName(classIndex)
        print(f"Sign Type is: {className}")
        return className
    else:
        print("No sign detected")
        return "Unknown Sign"

################### Main Code ###################
if __name__ == "__main__" :
    # Load the trained recognition model (TFLite)
    recog_model_path = r'sign_model.tflite'
    interpreter = tflite.Interpreter(model_path=recog_model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Detection model: Use the quantized ONNX model for detection
    detection_model_path = r'detection_model/best_quant.onnx'
    input_type = 'video'  # Options: 'video', 'image', 'camera'
    input_source = r'test_videos/video2.mp4'
    
    # Initialize the detection model and input source using ONNX Runtime
    detection_session, cap, input_images = initialize_detection_onnx(detection_model_path, input_type, input_source)
    confidence_threshold = 0.34

    frame_interval = 5  # Process every 5th frame
    last_sign = None
    frame_counter = 0

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
                    if frame_counter % frame_interval != 0:
                        continue

                    # Process frame using ONNX Runtime detection
                    annotated_frame, cropped_signs = process_frame_onnx(detection_session, confidence_threshold, frame)
                    
                    for cropped_image in cropped_signs:
                        if cropped_image.size == 0:
                            continue

                        current_sign = predict_sign(cropped_image)
                        if current_sign != last_sign:
                            message = f"Sign Type is: {current_sign}"
                            try:
                                publish.single(MQTT_TOPIC, message, hostname=MQTT_BROKER)
                                last_sign = current_sign
                            except KeyboardInterrupt:
                                print("\nShutting down the publisher.")
                                
                    cv2.imshow("Detection", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                cap.release()
        
        elif input_type == 'image':
            if not input_images:
                print("Error: No images found in the specified directory.")
            else:
                for image_path in input_images:
                    frame = cv2.imread(image_path)
                    annotated_frame, cropped_signs = process_frame_onnx(detection_session, confidence_threshold, frame)
                    
                    for cropped_image in cropped_signs:
                        if cropped_image.size == 0:
                            continue

                        current_sign = predict_sign(cropped_image)
                        if current_sign != last_sign:
                            message = f"Sign Type is: {current_sign}"
                            try:
                                publish.single(MQTT_TOPIC, message, hostname=MQTT_BROKER)
                                last_sign = current_sign
                            except KeyboardInterrupt:
                                print("\nShutting down the client.")
                    
                    # cv2.imshow("Detection", annotated_frame)
                    # cv2.waitKey(0)
                    # cv2.destroyAllWindows()

    except KeyboardInterrupt:
        print("\nShutting down the client.")
    finally:
        print("Publisher closed.")
