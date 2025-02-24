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

# Class to average lanes with
class Lanes():
    def __init__(self):
        self.recent_fit = []
        self.avg_fit = []

def road_lines(image):
    """
    Processes a road image:
    - Resizes for model input and gets lane prediction.
    - Averages predictions over the last 5 frames.
    - Generates a lane overlay (green if on lane, red if off lane) and merges with the original image.
    - Computes lane center, calculates deviation from the vehicle's center,
      applies a Kalman filter for smoothing, and overlays lane status.
    - Draws the car center and lane center as points, and a line connecting them.
    """
    # Resize for model input (target size: 80x160; cv2.resize expects (width, height))
    small_img = cv2.resize(image, (160, 80))
    small_img = small_img[None, :, :, :]  # add batch dimension

    # Predict lane using the model (un-normalize by multiplying by 255)
    prediction = model.predict(small_img)[0] * 255

    # Add prediction to recent fits and compute average over last 5 frames
    lanes.recent_fit.append(prediction)
    if len(lanes.recent_fit) > 5:
        lanes.recent_fit = lanes.recent_fit[1:]
    lanes.avg_fit = np.mean(np.array(lanes.recent_fit), axis=0)

    # Convert averaged prediction to uint8
    lane_channel = np.clip(lanes.avg_fit, 0, 255).astype(np.uint8)

    # Create a blank image with the same dimensions as lane_channel
    blanks = np.zeros_like(lane_channel, dtype=np.uint8)

    # Stack to create a 3-channel image; initially set to green channel
    lane_drawn = np.dstack((blanks, lane_channel, blanks))

    # Resize lane overlay to match original image size
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
    threshold = 50  # threshold in pixels

    if lane_center is not None:
        deviation = lane_center - car_center
        # Apply Kalman filter to smooth deviation measurements
        measurement = np.array([[np.float32(deviation)]])
        kalman_dev.predict()
        estimated = kalman_dev.correct(measurement)
        filtered_deviation = estimated[0, 0]

        # Determine lane status
        on_lane = abs(filtered_deviation) < threshold
        status = "On Lane" if on_lane else "Off Lane"

        # Change lane overlay color based on status
        if on_lane:
            # Green overlay
            lane_drawn = np.dstack((blanks, lane_channel, blanks))
        else:
            # Red overlay
            lane_drawn = np.dstack((lane_channel, blanks, blanks))

        # Resize and merge lane overlay with original image
        lane_image = cv2.resize(lane_drawn, (image.shape[1], image.shape[0]))
        lane_image = lane_image.astype(np.uint8)
        result = cv2.addWeighted(image, 1, lane_image, 1, 0)

        # Overlay status text
        cv2.putText(result, f"{status} (Deviation: {filtered_deviation:.1f}px)",
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        result = image.copy()
        cv2.putText(result, "Lane Not Detected",
                    (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # --- Draw center points and connecting line ---
    # Define a fixed y-coordinate near the bottom for visualization (e.g., 90% of the height)
    y_visual = int(image.shape[0] * 0.9)
    # Car center point (red)
    car_center_pt = (int(car_center), y_visual)
    cv2.circle(result, car_center_pt, radius=5, color=(0, 0, 255), thickness=-1)
    
    # Lane center point (green or red) if detected; otherwise, default to car center
    if lane_center is not None:
        lane_center_pt = (int(lane_center), y_visual)
        lane_color = (0, 255, 0) if on_lane else (0, 0, 255)
    else:
        lane_center_pt = car_center_pt
        lane_color = (0, 255, 0)  # Default to green if not detected
    cv2.circle(result, lane_center_pt, radius=5, color=lane_color, thickness=-1)
    
    # Draw a thin blue line connecting the two points
    cv2.line(result, car_center_pt, lane_center_pt, color=(255, 0, 0), thickness=2)

    return result

if __name__ == '__main__':
    # Load the pre-trained Keras model for lane detection
    model = load_model('full_CNN_model.h5')
    lanes = Lanes()

    # Specify input and output video paths
    vid_output = f'Output_Videos/OutVid.mp4'
    clip1 = VideoFileClip(f"Test_Videos/Car.mp4")
    # Apply road_lines function to each video frame
    vid_clip = clip1.fl_image(road_lines)
    vid_clip.write_videofile(vid_output, audio=False)
