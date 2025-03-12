import cv2
import os
from ultralytics import YOLO
import numpy
import sys
# Ensure the expected module is available in sys.modules:
sys.modules['numpy._core.multiarray'] = numpy.core.multiarray

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

if __name__ == "__main__":
    root = os.getcwd()
    detection_model_path = r'detection_model\best.pt'
    input_type = 'video'                         # Change to 'image' or 'camera' as needed
    input_source = r'test_videos\\video2.mp4'    # Required for 'video' or 'image'
    counter = 0

    # Initialize model and input source
    detection_model, cap, input_images = initialize_model_and_source(detection_model_path, input_type, input_source)

    confidence_threshold = 0.34

    # Create output folder for cropped images
    output_image_folder = os.path.join(root, r'sign_client\\output_images')
    os.makedirs(output_image_folder, exist_ok=True)

    if input_type in ['video', 'camera']:
        if not cap.isOpened():
            print("Error: Unable to open the input source.")
        else:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                # Call process_frame for each frame
                _, cropped_regions = process_frame(detection_model, confidence_threshold, frame)
                # Save only cropped regions
                for cropped_image in cropped_regions:
                    cropped_path = os.path.join(output_image_folder, f'cropped_{counter}.jpg')
                    cv2.imwrite(cropped_path, cropped_image)
                    counter += 1

            cap.release()

    elif input_type == 'image':
        if not input_images:
            print("Error: No images found in the specified directory.")
        else:
            for image_path in input_images:
                frame = cv2.imread(image_path)

                # Call process_frame for each image
                _, cropped_regions = process_frame(detection_model, confidence_threshold, frame)

                # Save only cropped regions
                for cropped_image in cropped_regions:
                    cropped_path = os.path.join(output_image_folder, f'cropped_{counter}.jpg')
                    cv2.imwrite(cropped_path, cropped_image)
                    counter += 1

    print(f"Processing completed. Cropped images saved in '{output_image_folder}'.")
