import numpy as np
import cv2
import time
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

    # Detect at every 10 frame and store the lane status (1: on lane, 0: off lane)
    frame_count = 0
    status = None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open /dev/video0; check V4L2 driver")

    print("Starting lane detection on camera stream (press Ctrl+C to stop)")
    print("Lane status for each frame (1: On Lane, 0: Off Lane):")

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        # Detect the lane every 10 frames not at each frame
        if frame_count % 10 == 0:
            status = road_lines_status(frame, update_model=True)
            # Send the status of the car according to the lane
            mqtt_client.publish(MQTT_TOPIC, str(status))
            print(status)
        else:
            status = road_lines_status(frame, update_model=False)
        
        frame_count += 1

    cap.release()

   
