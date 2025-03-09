import cv2
import socket
import pickle
import struct

# Set up socket
HOST = "192.168.1.100"  # Change to your receiver's IP
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

cap = cv2.VideoCapture(0)  # Capture from webcam

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    data = pickle.dumps(frame)  # Serialize frame
    size = struct.pack("L", len(data))  # Send size of frame

    sock.sendall(size + data)  # Send frame

cap.release()
sock.close()
