import pickle
import cv2
import numpy as np

# Replace 'full_CNN_train.p' with the actual filename of your training data
with open('full_CNN_train.p', 'rb') as f:
    train_data = pickle.load(f)

# Loop over the dataset and display each image as a video frame.
for i, img in enumerate(train_data):
    # Convert image from RGB to BGR if needed
    if img.ndim == 3 and img.shape[2] == 3:
        img_display = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        img_display = img

    # Optionally, resize for display
    img_display = cv2.resize(img_display, (640, 480))
    
    cv2.imshow("Training Data Video", img_display)
    # Wait for 30ms between frames (adjust to control playback speed)
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break
    
    # Stop after 90 frames if desired:
    # if i == 90:
    #     break

cv2.destroyAllWindows()
