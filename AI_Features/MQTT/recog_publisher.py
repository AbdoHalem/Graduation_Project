import os
import numpy as np
import cv2
from pathlib import Path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'        # To disaple displaying the tensorflow logs
from tensorflow.keras.models import load_model
import paho.mqtt.publish as publish

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

# Function to get the label of ths input sign
def getClassName(classNo):
    class_names = [
        'Speed Limit 20 km/h', 'Speed Limit 30 km/h', 'Speed Limit 50 km/h',
        'Speed Limit 60 km/h', 'Speed Limit 70 km/h', 'Speed Limit 80 km/h',
        'End of Speed Limit 80 km/h', 'Speed Limit 100 km/h', 
        'Speed Limit 120 km/h', 'No passing', 
        'No passing for vehicles over 3.5 metric tons', 
        'Right-of-way at the next intersection', 'Priority road', 
        'Yield', 'Stop', 'No vehicles', 
        'Vehicles over 3.5 metric tons prohibited', 'No entry', 
        'General caution', 'Dangerous curve to the left', 
        'Dangerous curve to the right', 'Double curve', 
        'Bumpy road', 'Slippery road', 
        'Road narrows on the right', 'Road work', 
        'Traffic signals', 'Pedestrians', 
        'Children crossing', 'Bicycles crossing', 
        'Beware of ice/snow', 'Wild animals crossing', 
        'End of all speed and passing limits', 
        'Turn right ahead', 'Turn left ahead', 
        'Ahead only', 'Go straight or right', 
        'Go straight or left', 'Keep right', 
        'Keep left', 'Roundabout mandatory', 
        'End of no passing', 
        'End of no passing by vehicles over 3.5 metric tons'
    ]
    return class_names[classNo] if classNo < len(class_names) else "Unknown"

def predict_sign(image_path):
    # Read and preprocess the image
    imgOriginal = cv2.imread(image_path)
    if imgOriginal is None:
        print(f"Error: Unable to read image from path: {image_path}")
        return

    # Preprocess the image
    img = cv2.resize(imgOriginal, (32, 32))  # Resize to the input size of the recog_model
    img = preprocessing(img)
    img = img.reshape(1, 32, 32, 1)

    # Predict the class
    predictions = recog_model.predict(img)
    classIndex = np.argmax(predictions, axis=-1)[0]
    probabilityValue = np.max(predictions)

    # Print the result
    if probabilityValue > 0.75:  # You can adjust this threshold
        className = getClassName(classIndex)
        print(f"Sign Type is: {className}")
        return className
    else:
        print("No sign detected")
        return "Unknown Sign"


# Load the trained recog_model
recog_model_path = r"recognition_model\\model.h5"
print(os.path.exists(recog_model_path))
recog_model = load_model(recog_model_path)

# Main code
if __name__ == "__main__" :
    image_folder = Path("D:\Engineering\My-Github\Graduation_Project\Socket_Codes\sign_client\output_images")
    # Select the mqtt server and its topic
    MQTT_SERVER = "test.mosquitto.org"
    MQTT_PATH = "ADAS_GP/sign"
    # Save the last message to prevent resending of the same message
    last_message = None
    try:
        for image_path in image_folder.glob("*"):
            message = "Sign Type is: " + predict_sign(str(image_path))
            try:
                if(message != last_message):
                    publish.single(MQTT_PATH, message, hostname=MQTT_SERVER)
                else:
                    continue
                last_message = message
            except KeyboardInterrupt:
                print("\nShutting down the client.")
                break
    finally:
        print("Publisher Close")
        

