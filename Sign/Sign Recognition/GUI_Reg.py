import os
import numpy as np
import cv2
import tensorflow as tf
from tensorflow.keras.models import load_model
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# Load the trained model
MODEL_PATH = 'model.h5'

model = load_model(MODEL_PATH)

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

def load_image():
    file_path = filedialog.askopenfilename(title="Select Image", 
                                           filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if file_path:
        imgOriginal = cv2.imread(file_path)

        # Preprocess the image
        img = cv2.resize(imgOriginal, (32, 32))  # Resize to the input size of the model
        img = preprocessing(img)
        img = img.reshape(1, 32, 32, 1)

        # Predict the class
        predictions = model.predict(img)
        classIndex = np.argmax(predictions, axis=-1)[0]
        probabilityValue = np.max(predictions)

        # Prepare the result text
        if probabilityValue > 0.75:  # You can adjust this threshold
            className = getClassName(classIndex)
            result_text = f"Class: {className}\nProbability: {probabilityValue*100:.2f}%"
        else:
            result_text = "No sign detected"

        # Display the result
        result_label.config(text=result_text)

        # Show the image
        show_image(imgOriginal)

def show_image(imgOriginal):
    # Convert to RGB format
    imgOriginal = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(imgOriginal)
    
    # Resize the image for display
    img_pil = img_pil.resize((300, 300))  # Change size here
    img_tk = ImageTk.PhotoImage(img_pil)

    # Update image label
    image_label.config(image=img_tk)
    image_label.image = img_tk  # Keep a reference to avoid garbage collection

# Create the main window
root = tk.Tk()
root.title("Traffic Sign Recognition")
root.geometry("500x600")  # Set a larger window size
root.configure(bg='black')  # Set background color to black

# Create a canvas for the background
canvas = tk.Canvas(root, width=500, height=600, bg='black')
canvas.pack(fill="both", expand=True)

# Create UI elements
load_button = tk.Button(canvas, text="Load Image", command=load_image, bg='red', fg='white', font=('Arial', 12, 'bold'))
load_button.pack(pady=10)

image_label = tk.Label(canvas, bg='black')  # Set the image label background color
image_label.pack()

result_label = tk.Label(canvas, text="", wraplength=300, justify="center", font=('Arial', 20), fg='white', bg='black')  
result_label.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()
