import os
import numpy as np
import cv2
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # To disaple displaying the tensorflow logs
from tensorflow.keras.models import load_model
import socket 
from threading import Thread

# Load the trained model
MODEL_PATH = 'sign_client\model.h5'
model = load_model(MODEL_PATH)

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
    img = cv2.resize(imgOriginal, (32, 32))  # Resize to the input size of the model
    img = preprocessing(img)
    img = img.reshape(1, 32, 32, 1)

    # Predict the class
    predictions = model.predict(img)
    classIndex = np.argmax(predictions, axis=-1)[0]
    probabilityValue = np.max(predictions)

    # Print the result
    if probabilityValue > 0.75:  # You can adjust this threshold
        className = getClassName(classIndex)
        print(f"Class: {className}")
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
    # finally:
    #     s.close()

# Main code
if __name__ == "__main__" :
    image_path = "D:/Engineering/College/4th_Year/GP/Sign_Recognition/Code/My_Code/Dataset/10/10_17134_1577672005.5387852.png"
    # Establish a socket object
    SOCKET = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client_connect(SOCKET)
    try:
        for i in range(5):
            message = predict_sign(image_path)
            try:
                Sending(SOCKET, message)
            except KeyboardInterrupt:
                print("\nShutting down the client.")
                break
    finally:
        SOCKET.close()
