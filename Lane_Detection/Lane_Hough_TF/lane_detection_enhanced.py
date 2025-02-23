import cv2
import numpy as np

# --- Helper Functions ---
def region_of_interest(img, vertices):
    """Apply an image mask defined by vertices."""
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, vertices, 255)
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

def draw_lines(img, lines, color=(0, 255, 0), thickness=5):
    """Draw lines on the image (for debugging/visualization)."""
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)

def resize_image(image, width, height):
    """Resize an image to a fixed size."""
    return cv2.resize(image, (width, height))

def average_line(lines):
    """Average a group of lines to produce one representative line.
       Returns a tuple (slope, intercept)."""
    if len(lines) == 0:
        return None
    slope_sum = 0
    intercept_sum = 0
    count = 0
    for x1, y1, x2, y2 in lines:
        if (x2 - x1) == 0:  # avoid division by zero
            continue
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        slope_sum += slope
        intercept_sum += intercept
        count += 1
    if count == 0:
        return None
    avg_slope = slope_sum / count
    avg_intercept = intercept_sum / count
    return avg_slope, avg_intercept

# --- Kalman Filter Setup for 1D deviation ---
# We use OpenCV's KalmanFilter with 1 dynamic parameter (state) and 1 measurement.
kalman = cv2.KalmanFilter(1, 1)
kalman.measurementMatrix = np.array([[1]], np.float32)   # Direct measurement
kalman.transitionMatrix = np.array([[1]], np.float32)      # State doesn't change unless updated
kalman.processNoiseCov = np.array([[1e-5]], np.float32)     # Process (model) noise covariance
kalman.measurementNoiseCov = np.array([[1e-1]], np.float32) # Measurement noise covariance
kalman.errorCovPost = np.array([[1]], np.float32)           # Initial estimation error

# --- Setup Video Capture and Create Trackbar for Threshold ---
cap = cv2.VideoCapture('Car1.mp4')

# Create (or re-use) the display window and attach a trackbar for threshold adjustment.
cv2.namedWindow('Lane Detection - Combined View')
initial_threshold = 70
max_threshold = 200
cv2.createTrackbar('Threshold', 'Lane Detection - Combined View', initial_threshold, max_threshold, lambda x: None)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    height, width = frame.shape[:2]
    
    # Preprocess the frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 10, 60)

    # Define ROI vertices (adjust as needed)
    roi_vertices = [(0, height), (width // 2, height // 3), (width, height)]
    cropped_edges = region_of_interest(edges, np.array([roi_vertices], np.int32))

    # Detect lines using Hough transform
    lines = cv2.HoughLinesP(cropped_edges, rho=1, theta=np.pi/180, threshold=30, 
                            minLineLength=50, maxLineGap=150)

    # Separate lines into left and right lane lines based on slope
    left_lines = []
    right_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if (x2 - x1) == 0:
                continue  # avoid division by zero
            slope = (y2 - y1) / (x2 - x1)
            if slope < -0.5:
                left_lines.append(line[0])
            elif slope > 0.5:
                right_lines.append(line[0])
    
    # Average the lines to get one representative line for each lane
    left_lane = average_line(left_lines)
    right_lane = average_line(right_lines)

    lane_center = None
    filtered_deviation = 0  # default value if no lane is detected
    if left_lane is not None and right_lane is not None:
        left_slope, left_intercept = left_lane
        right_slope, right_intercept = right_lane

        # Choose a fixed y (here, bottom of the frame) to compute x coordinates
        y_fixed = height  
        left_x = int((y_fixed - left_intercept) / left_slope)
        right_x = int((y_fixed - right_intercept) / right_slope)
        lane_center = (left_x + right_x) / 2

        # Draw lane boundaries for visualization
        cv2.line(frame, (left_x, y_fixed), (left_x, int(y_fixed/2)), (255, 0, 0), 5)
        cv2.line(frame, (right_x, y_fixed), (right_x, int(y_fixed/2)), (255, 0, 0), 5)
    
    # Assume the car's center is at the horizontal center of the frame.
    car_center = width // 2

    # --- Kalman Filter update for deviation ---
    if lane_center is not None:
        # Compute current deviation: positive if lane center is to the right of car center
        current_deviation = lane_center - car_center

        measurement = np.array([[np.float32(current_deviation)]])
        kalman.predict()
        estimated = kalman.correct(measurement)
        filtered_deviation = estimated[0, 0]
        
        # Draw lane center (blue circle) and car center (red circle)
        cv2.circle(frame, (int(lane_center), height), 8, (255, 0, 0), -1)
        cv2.circle(frame, (car_center, height), 8, (0, 0, 255), -1)
        cv2.line(frame, (car_center, height), (int(lane_center), height), (0, 255, 255), 2)
        cv2.putText(frame, f"Deviation: {int(filtered_deviation)} px", (50, height - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    else:
        cv2.putText(frame, "Lane Not Detected", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
    # --- Use Trackbar Value as Threshold ---
    threshold = cv2.getTrackbarPos('Threshold', 'Lane Detection - Combined View')
    if threshold == 0:
        threshold = 1  # avoid division by zero

    # Determine lane status based on filtered deviation
    status_filtered = "Unknown"
    if lane_center is not None:
        if abs(filtered_deviation) < threshold:
            status_filtered = "On Lane - filtered"
        else:
            status_filtered = "Off Lane - filtered"
        cv2.putText(frame, status_filtered, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Determine lane status based on unfiltered deviation
    status_unfiltered = "Unknown"
    if lane_center is not None:
        if abs(lane_center - car_center) < threshold:
            status_unfiltered = "On Lane - NOT filtered"
        else:
            status_unfiltered = "Off Lane - NOT filtered"
        cv2.putText(frame, status_unfiltered, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # --- Create Slider Overlay ---
    # Parameters for slider overlay
    slider_width, slider_height = 300, 50
    slider_img = np.zeros((slider_height, slider_width, 3), dtype=np.uint8)
    slider_img[:] = (50, 50, 50)  # background color

    # Draw horizontal line (slider axis)
    cv2.line(slider_img, (0, slider_height // 2), (slider_width, slider_height // 2), (255, 255, 255), 2)
    # Label the left, center, and right positions using the threshold as scale
    cv2.putText(slider_img, f"-{threshold}", (5, slider_height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    cv2.putText(slider_img, "0", (slider_width//2 - 10, slider_height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    cv2.putText(slider_img, f"{threshold}", (slider_width - 50, slider_height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)
    
    # Helper function to map a deviation value to a slider x-position
    def get_slider_pos(dev, thr, width_slider):
        pos = int(width_slider // 2 + (dev / thr) * (width_slider // 2))
        return max(0, min(width_slider - 1, pos))

    if lane_center is not None:
        unfiltered_dev = lane_center - car_center  # raw deviation
        filt_dev = filtered_deviation              # filtered deviation
        
        pos_unfiltered = get_slider_pos(unfiltered_dev, threshold, slider_width)
        pos_filtered = get_slider_pos(filt_dev, threshold, slider_width)
        
        # Draw markers for unfiltered (red) and filtered (yellow) deviations
        cv2.circle(slider_img, (pos_unfiltered, slider_height // 2), 5, (0, 0, 255), -1)
        cv2.circle(slider_img, (pos_filtered, slider_height // 2), 5, (0, 255, 255), -1)
        
        # Optionally, label the marker values above the slider
        cv2.putText(slider_img, f"{unfiltered_dev:.1f}", (pos_unfiltered - 20, slider_height // 2 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        cv2.putText(slider_img, f"{filt_dev:.1f}", (pos_filtered - 20, slider_height // 2 - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    
    # --- Create a Combined Debug View ---
    resized_blur = resize_image(blur, 400, 300)
    resized_edges = resize_image(edges, 400, 300)
    resized_cropped_edges = resize_image(cropped_edges, 400, 300)
    resized_frame = resize_image(frame, 400, 300)
    
    resized_blur_bgr = cv2.cvtColor(resized_blur, cv2.COLOR_GRAY2BGR)
    resized_edges_bgr = cv2.cvtColor(resized_edges, cv2.COLOR_GRAY2BGR)
    resized_cropped_edges_bgr = cv2.cvtColor(resized_cropped_edges, cv2.COLOR_GRAY2BGR)
    
    top_row = cv2.hconcat([resized_blur_bgr, resized_edges_bgr])
    bottom_row = cv2.hconcat([resized_cropped_edges_bgr, resized_frame])
    combined_image = cv2.vconcat([top_row, bottom_row])
    
    # Overlay the slider in the top right corner of the combined image
    comb_height, comb_width = combined_image.shape[:2]
    # Make sure the region is within the image boundaries
    if comb_width >= slider_width and comb_height >= slider_height:
        combined_image[0:slider_height, comb_width - slider_width:comb_width] = slider_img
    
    cv2.imshow("Lane Detection - Combined View", combined_image)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
