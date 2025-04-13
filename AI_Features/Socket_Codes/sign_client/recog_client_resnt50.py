import os
import numpy as np
import cv2
from pathlib import Path
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # To disaple displaying the tensorflow logs
from tensorflow.keras.models import load_model
import socket 
# from threading import Thread

# Load the trained recog_model
# recog_model_path = 'sign_client\\recognition_model\\recog_model.h5'
recog_model_path = r"recognition_model\\final_resnet_model_RRDB.h5"
recog_model = load_model(recog_model_path)


# Image Preprocessing Function
def preprocessing(image):
    """Preprocess image to match model input."""
    img = cv2.resize(image, (128, 128))  # Resize to model input size
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
    img = img / 255.0  # Normalize to [0,1], just like ImageDataGenerator
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img


# Function to get the label of ths input sign
def getClassName(classNo):
    class_names = [
        'Speed limit (20km/h)','Speed limit (30km/h)','No passing for vechiles over 3.5 metric tons',
        'Right-of-way at the next intersection','Priority road','Yield','Stop','No vechiles','Vechiles over 3.5 metric tons prohibited',
        'No entry','General caution','Dangerous curve to the left','Speed limit (50km/h)','Dangerous curve to the right','Double curve',
        'Bumpy road','Slippery road','Road narrows on the right','Road work','Traffic signals','Pedestrians','Children crossing',
        'Bicycles crossing','Speed limit (60km/h)','Beware of ice/snow','Wild animals crossing','End of all speed and passing limits',
        'Turn right ahead','Turn left ahead','Ahead only','Go straight or right','Go straight or left','Keep right','Keep left',
        'Speed limit (70km/h)','Roundabout mandatory','End of no passing','End of no passing by vechiles over 3.5 metric tons',
        'Speed limit (40km/h)','Speed limit (90km/h)','No stopping','No horn','No waiting','Speed limit (80km/h)',
        'End of speed limit (80km/h)','Speed limit (100km/h)','Speed limit (120km/h)','No passing'
    ]
    return class_names[classNo] if classNo < len(class_names) else "Unknown"

def predict_sign(image_path):
    # Read and preprocess the image
    imgOriginal = cv2.imread(image_path)
    if imgOriginal is None:
        print(f"Error: Unable to read image from path: {image_path}")
        return

    # Preprocess the image
    img = preprocessing(imgOriginal)
    

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


# Function to establish a socket connection between client and server
def client_connect(SOCKET):
    server_IP = socket.gethostbyname("Halem-Lab")
    port = 1234
    SOCKET.connect((server_IP, port))
    print("Connected to server.")

# Function to send data from client to server
def Sending(s, message):
    try:
        if message.lower() == 'exit':  # Exit condition
            s.send(bytes("exit", "utf-8"))
        else:
            s.send(bytes(message, "utf-8"))
    except Exception as e:
        print("Error sending message:", e)

# Main code
if __name__ == "__main__" :
    # image_path = "D:/Engineering/College/4th_Year/GP/Sign_Recognition/Code/My_Code/Dataset/10/10_17134_1577672005.5387852.png"
    image_folder = Path("output_images")
    # Establish a socket object
    SOCKET = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client_connect(SOCKET)
    try:
        for image_path in image_folder.glob("*"):
            message = "Sign Type is: " + predict_sign(str(image_path))
            try:
                Sending(SOCKET, message)
            except KeyboardInterrupt:
                print("\nShutting down the client.")
                break
    finally:
        SOCKET.close()
