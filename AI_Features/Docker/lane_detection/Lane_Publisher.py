import numpy as np
import cv2
import time, os, glob, socket, struct
import tflite_runtime.interpreter as tflite
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "ADAS_GP/lane"

# 1️⃣ Initialize a persistent MQTT client
mqtt_client = mqtt.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# Create a Kalman filter for the deviation variable
kalman_dev = cv2.KalmanFilter(1, 1)
kalman_dev.measurementMatrix = np.array([[1]], np.float32)
kalman_dev.transitionMatrix = np.array([[1]], np.float32)
kalman_dev.processNoiseCov = np.array([[1e-3]], np.float32)
kalman_dev.measurementNoiseCov = np.array([[1e-1]], np.float32)
kalman_dev.errorCovPost = np.array([[1]], np.float32)

# ─── CONFIGURE INPUT MODE HERE ────────────────────────────────────────────────
# Choose one of: 'camera', 'video', 'image'
input_type   = 'image'
#  For 'video', set this to your video file.
# For **socket**-based image mode, set input_source = None
# Ignored when input_type == 'camera'
input_source = None
# ────────────────────────────────────────────────────────────────────────────────

# Socket settings (for image-over-socket mode)
HOST = '0.0.0.0'
PORT = 9999

def recvall(sock, count):
    """Read exactly `count` bytes from `sock` or return None on failure."""
    buf = b''
    while len(buf) < count:
        chunk = sock.recv(count - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf

def initialize_source(input_type, input_source=None):
    """
    Initialize the image source for lane detection.
    Args:
      input_type (str): 'camera', 'video', or 'image'
      input_source (str or None):
        - For 'video', a path to the video file.
        - For 'image', a path to a directory containing .jpg/.png.
        - Ignored for 'camera'.
    Returns:
      cap (cv2.VideoCapture or None), images (list of paths or None)
    """
    cap = None
    images = None

    if input_type == 'camera':
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    elif input_type == 'video':
        if not input_source:
            raise ValueError("For 'video' mode, input_source must be a video file path")
        cap = cv2.VideoCapture(input_source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video {input_source}")

    elif input_type == 'image':
        # If input_source is provided, treat as file-based; otherwise assume socket mode
        if input_source:
            images = sorted(glob.glob(os.path.join(input_source, "*.[jJ][pP][gG]")) +
                            glob.glob(os.path.join(input_source, "*.[pP][nN][gG]")))
            if not images:
                raise RuntimeError(f"No images found in {input_source}")
    
    else:
        raise ValueError("input_type must be 'camera', 'video', or 'image'")

    return cap, images


# Class to hold recent lane predictions for temporal smoothing
class Lanes():
    def __init__(self):
        self.recent_fit = []
        self.avg_fit = None

# Create the TFLite interpreter and allocate tensors
interpreter = tflite.Interpreter(model_path="CNN_model.tflite")  # Update with your quantized model path
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def predict_lane_tflite(image):
    """
    Preprocesses the image and runs TFLite inference.
    Assumes the model expects images of size (80, 160) and type float32.
    """
    # Resize image for model input (target size: 80x160)
    small_img = cv2.resize(image, (160, 80))
    small_img = np.expand_dims(small_img, axis=0).astype(np.float32)
    
    # Set the tensor and run inference
    interpreter.set_tensor(input_details[0]['index'], small_img)
    interpreter.invoke()
    # Get prediction and rescale to 0-255
    prediction = interpreter.get_tensor(output_details[0]['index'])[0] * 255.0
    return prediction

# This function now accepts an 'update_model' flag.
def road_lines_status(image, update_model=True):
    """
    Processes a road image and computes lane status:
      - If update_model is True, runs the TFLite model to get a new lane prediction,
        updating the temporal average over the last 5 predictions.
      - If update_model is False, uses the previous lane prediction.
    
    Returns:
      - 1 if the filtered deviation (smoothed by the Kalman filter) is within the threshold (i.e. on lane)
      - 0 if the deviation exceeds the threshold or if no lane is detected.
    """
    if update_model:
        # Use TFLite model prediction
        prediction = predict_lane_tflite(image)
        
        # Append prediction for temporal smoothing over the last 5 frames
        lanes.recent_fit.append(prediction)
        if len(lanes.recent_fit) > 5:
            lanes.recent_fit = lanes.recent_fit[1:]
        lanes.avg_fit = np.mean(np.array(lanes.recent_fit), axis=0)
    
    # If no prediction has been made yet, force a prediction
    if lanes.avg_fit is None:
        prediction = predict_lane_tflite(image)
        lanes.recent_fit.append(prediction)
        lanes.avg_fit = prediction

    # Prepare the averaged lane prediction for further processing
    lane_channel = np.clip(lanes.avg_fit, 0, 255).astype(np.uint8)
    blanks = np.zeros_like(lane_channel, dtype=np.uint8)
    # Create a 3-channel image with the lane prediction in the green channel
    lane_drawn = np.dstack((blanks, lane_channel, blanks))

    # Resize lane overlay to match the original image size
    lane_image = cv2.resize(lane_drawn, (image.shape[1], image.shape[0]))
    lane_image = lane_image.astype(np.uint8)

    # Compute lane center as the average x-coordinate of nonzero pixels in the green channel
    green_channel = lane_image[:, :, 1]
    indices = np.where(green_channel > 0)
    if len(indices[1]) > 0:
        lane_center = np.mean(indices[1])
    else:
        lane_center = None

    # Assume the car's center is the horizontal center of the image
    car_center = image.shape[1] / 2
    threshold = 50  # pixel threshold for lane deviation

    if lane_center is not None:
        deviation = lane_center - car_center
        # Smooth the deviation using the Kalman filter
        measurement = np.array([[np.float32(deviation)]])
        kalman_dev.predict()
        estimated = kalman_dev.correct(measurement)
        filtered_deviation = estimated[0, 0]

        # Determine lane status: 1 if within threshold, else 0
        status = 1 if abs(filtered_deviation) < threshold else 0
    else:
        # If no lane is detected, consider the status as off lane (0)
        status = 2

    return status

if __name__ == '__main__':
    # Create a Lanes object for temporal smoothing
    lanes = Lanes()
    # Initialize the input source
    cap, images = initialize_source(input_type, input_source)

    # Detect at every 5 frame and store the lane status (1: on lane, 0: off lane)
    frame_counter = 0
    status = None
    last_status   = None
    img_idx       = 0
    sock = None

    if input_type == 'image':
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"[Socket] Listening on {HOST}:{PORT}")
        sock, addr = server.accept()
        print(f"[Socket] Connection from {addr}")

    print(f"Starting lane detection on {input_type} mode (press Ctrl+C to stop)")
    print("Lane status for each frame (1: On Lane, 0: Off Lane):")
    try:
        while True:
            # grab frame
            if input_type in ('camera','video'):
                ret, frame = cap.read()
                if not ret:
                    break
            else:  # 'image' over socket
                # Read length prefix
                header = recvall(sock, 4)
                if not header:
                    print("[Socket] Connection closed")
                    break
                length, = struct.unpack('!I', header)
                data = recvall(sock, length)
                if not data:
                    print("[Socket] Incomplete frame")
                    break
                buf   = np.frombuffer(data, np.uint8)
                frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if frame is None:
                    print("[Socket] Decode failure")
                    continue

            ''' Detect the lane every 5 frames not at each frame
            every 5th frame, update model; else reuse avg'''
            update = (frame_counter % 1 == 0)
            status = road_lines_status(frame, update_model=update)

            # publish only on change
            if status != last_status:
                mqtt_client.publish(MQTT_TOPIC, str(status))
                print("Lane status:", status)
                last_status = status

            frame_counter += 1
            time.sleep(0.01)

        # cap.release()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        if cap:
            cap.release()
            cv2.destroyAllWindows()
        elif sock:
            sock.close()
            server.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Shutting down.")
   
