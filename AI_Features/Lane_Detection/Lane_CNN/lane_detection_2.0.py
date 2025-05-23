# import numpy as np
# import cv2
# from moviepy.editor import VideoFileClip
# from keras.models import load_model

# # Create a Kalman filter for the deviation variable
# kalman_dev = cv2.KalmanFilter(1, 1)
# kalman_dev.measurementMatrix = np.array([[1]], np.float32)
# kalman_dev.transitionMatrix = np.array([[1]], np.float32)
# kalman_dev.processNoiseCov = np.array([[1e-3]], np.float32)
# kalman_dev.measurementNoiseCov = np.array([[1e-1]], np.float32)
# kalman_dev.errorCovPost = np.array([[1]], np.float32)

# # Class to average lane predictions over recent frames
# class Lanes():
#     def __init__(self):
#         self.recent_fit = []
#         self.avg_fit = []

# def road_lines_status(image):
#     """
#     Processes a road image and computes lane status:
#       - Resizes image for the CNN model.
#       - Gets a lane prediction and averages over the last 5 frames.
#       - Computes the lane center and deviation from the car's center.
#       - Smooths the deviation using a Kalman filter.
    
#     Returns:
#       - 1 if the filtered deviation is within a threshold (i.e. on lane)
#       - 0 if the deviation is larger than the threshold or if no lane is detected.
#     """
#     # Resize image for model input (target size: 80x160)
#     small_img = cv2.resize(image, (160, 80))
#     small_img = small_img[None, :, :, :]  # add batch dimension

#     # Predict lane using the model (scale prediction back to 0-255)
#     prediction = model.predict(small_img)[0] * 255

#     # Append prediction for temporal smoothing over the last 5 frames
#     lanes.recent_fit.append(prediction)
#     if len(lanes.recent_fit) > 5:
#         lanes.recent_fit = lanes.recent_fit[1:]
#     lanes.avg_fit = np.mean(np.array(lanes.recent_fit), axis=0)

#     # Prepare the averaged lane prediction for further processing
#     lane_channel = np.clip(lanes.avg_fit, 0, 255).astype(np.uint8)
#     blanks = np.zeros_like(lane_channel, dtype=np.uint8)
#     # Create a 3-channel image using the lane_channel in the green channel
#     lane_drawn = np.dstack((blanks, lane_channel, blanks))

#     # Resize lane overlay to match the original image size
#     lane_image = cv2.resize(lane_drawn, (image.shape[1], image.shape[0]))
#     lane_image = lane_image.astype(np.uint8)

#     # Compute lane center as the average x-coordinate of nonzero pixels in the green channel
#     green_channel = lane_image[:, :, 1]
#     indices = np.where(green_channel > 0)
#     if len(indices[1]) > 0:
#         lane_center = np.mean(indices[1])
#     else:
#         lane_center = None

#     # Assume the car's center is the horizontal center of the image
#     car_center = image.shape[1] / 2
#     threshold = 50  # pixel threshold for lane deviation

#     if lane_center is not None:
#         deviation = lane_center - car_center
#         # Smooth the deviation using the Kalman filter
#         measurement = np.array([[np.float32(deviation)]])
#         kalman_dev.predict()
#         estimated = kalman_dev.correct(measurement)
#         filtered_deviation = estimated[0, 0]

#         # Determine lane status: 1 if within threshold, else 0
#         status = 1 if abs(filtered_deviation) < threshold else 0
#     else:
#         # If no lane is detected, consider the status as off lane (0)
#         status = 0

#     return status

# if __name__ == '__main__':
#     # Load the pre-trained Keras model for lane detection
#     model = load_model('full_CNN_model.h5')
#     lanes = Lanes()

#     # Input video path
#     input_video = "Test_Videos/Car.mp4"
#     clip = VideoFileClip(input_video)

#     # Process each frame and store the lane status (1: on lane, 0: off lane)
#     status_list = []
#     for frame in clip.iter_frames():
#         status = road_lines_status(frame)
#         status_list.append(status)

#     # Output the status for each frame
#     print("Lane status for each frame (1: On Lane, 0: Off Lane):")
#     print(status_list)

'''This code predicts the status of the car according to the lane
    one time at every 10 frames to reduce processing time'''
import numpy as np
import cv2
from moviepy.editor import VideoFileClip
from keras.models import load_model

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

# This function now accepts an 'update_model' flag.
def road_lines_status(image, update_model=True):
    """
    Processes a road image and computes lane status:
      - If update_model is True, runs the CNN model to get a new lane prediction,
        updating the temporal average over the last 5 predictions.
      - If update_model is False, uses the previous lane prediction.
    
    Returns:
      - 1 if the filtered deviation (smoothed by the Kalman filter) is within the threshold (i.e. on lane)
      - 0 if the deviation exceeds the threshold or if no lane is detected.
    """
    if update_model:
        # Resize image for model input (target size: 80x160)
        small_img = cv2.resize(image, (160, 80))
        small_img = small_img[None, :, :, :]  # add batch dimension

        # Predict lane using the CNN model (scale prediction back to 0-255)
        prediction = model.predict(small_img)[0] * 255

        # Append prediction for temporal smoothing over the last 5 frames
        lanes.recent_fit.append(prediction)
        if len(lanes.recent_fit) > 5:
            lanes.recent_fit = lanes.recent_fit[1:]
        lanes.avg_fit = np.mean(np.array(lanes.recent_fit), axis=0)

    # If no prediction has been made yet, force a prediction
    if lanes.avg_fit is None:
        small_img = cv2.resize(image, (160, 80))
        small_img = small_img[None, :, :, :]
        prediction = model.predict(small_img)[0] * 255
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
    # Load the pre-trained Keras model for lane detection
    model = load_model('full_CNN_model.h5')
    lanes = Lanes()

    # Input video path
    input_video = "Test_Videos/Car.mp4"
    clip = VideoFileClip(input_video)

    # Process each frame and store the lane status (1: on lane, 0: off lane)
    status_list = []
    frame_count = 0
    
    for frame in clip.iter_frames():
        # Only update the model prediction every 10 frames
        if frame_count % 10 == 0:
            status = road_lines_status(frame, update_model=True)
            status_list.append(status)
        else:
            status = road_lines_status(frame, update_model=False)
        # status_list.append(status)
        frame_count += 1

    # Output the status for each frame
    print("Lane status for each frame (1: On Lane, 0: Off Lane):")
    print(status_list)
