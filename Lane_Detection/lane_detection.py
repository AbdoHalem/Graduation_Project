"""import cv2
import numpy as np

# Define the region of interest (ROI) function to focus on the road lanes
def region_of_interest(img, vertices):
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, vertices, 255)
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

# Define the function to draw lines on the image
def draw_lines(img, lines):
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 5)

# Load the video
cap = cv2.VideoCapture('lanes_clip.mp4')

# Loop over the video frames
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise and improve edge detection
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny edge detection with adjusted thresholds
    edges = cv2.Canny(blur, 10, 60)  # Lowering the threshold to detect more edges

    # Define region of interest vertices (adjust based on video frame)
    height, width = frame.shape[:2]
    roi_vertices = [(0, height), (width // 2, height // 2), (width, height)]

    # Mask the edges image using the region of interest
    cropped_edges = region_of_interest(edges, np.array([roi_vertices], np.int32))

    # Apply Hough Line Transform with adjusted parameters
    lines = cv2.HoughLinesP(cropped_edges, rho=1, theta=np.pi/180, threshold=30, 
                            minLineLength=50, maxLineGap=150)  # Reduced minLineLength, increased maxLineGap

    # Draw lines on the original frame
    line_image = np.copy(frame)
    draw_lines(line_image, lines)

    # Combine the line image with the original frame
    combo_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)

    # Display the video with lanes detected
    cv2.imshow("Lane Detection", combo_image)
    cv2.imshow("Cropped Edges", cropped_edges)
    cv2.imshow("Edges", edges)
    cv2.imshow("Blur", blur)
    cv2.imshow("Gray", gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all windows
cap.release()
cv2.destroyAllWindows()"""




import cv2
import numpy as np

# Define the region of interest (ROI) function to focus on the road lanes
def region_of_interest(img, vertices):
    mask = np.zeros_like(img)
    cv2.fillPoly(mask, vertices, 255)
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

# Define the function to draw lines on the image
def draw_lines(img, lines):
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 5)

# Resize function to ensure all images are the same size for concatenation
def resize_image(image, width, height):
    return cv2.resize(image, (width, height))

# Load the video
cap = cv2.VideoCapture('car0.mp4')

# Loop over the video frames
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise and improve edge detection
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply Canny edge detection with adjusted thresholds
    edges = cv2.Canny(blur, 10, 60)  # Lowering the threshold to detect more edges

    # Define region of interest vertices (adjust based on video frame)
    height, width = frame.shape[:2]
    roi_vertices = [(0, height), (width // 2, height // 3), (width, height)]

    # Mask the edges image using the region of interest
    cropped_edges = region_of_interest(edges, np.array([roi_vertices], np.int32))

    # Apply Hough Line Transform with adjusted parameters
    lines = cv2.HoughLinesP(cropped_edges, rho=1, theta=np.pi/180, threshold=30, 
                            minLineLength=50, maxLineGap=150)  # Reduced minLineLength, increased maxLineGap

    # Draw lines on the original frame
    line_image = np.copy(frame)
    draw_lines(line_image, lines)

    # Combine the line image with the original frame
    combo_image = cv2.addWeighted(frame, 0.8, line_image, 1, 1)

    # Resize images to the same size for display
    resized_blur = resize_image(blur, 400, 300)
    resized_edges = resize_image(edges, 400, 300)
    resized_cropped_edges = resize_image(cropped_edges, 400, 300)
    resized_combo = resize_image(combo_image, 400, 300)

    # Convert grayscale images to BGR for concatenation
    resized_blur_bgr = cv2.cvtColor(resized_blur, cv2.COLOR_GRAY2BGR)
    resized_edges_bgr = cv2.cvtColor(resized_edges, cv2.COLOR_GRAY2BGR)
    resized_cropped_edges_bgr = cv2.cvtColor(resized_cropped_edges, cv2.COLOR_GRAY2BGR)

    # Concatenate images to create a 2x2 grid
    top_row = cv2.hconcat([resized_blur_bgr, resized_edges_bgr])
    bottom_row = cv2.hconcat([resized_cropped_edges_bgr, resized_combo])
    combined_image = cv2.vconcat([top_row, bottom_row])

    # Display the combined image
    cv2.imshow("Lane Detection - Combined View", combined_image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close all windows
cap.release()
cv2.destroyAllWindows()

