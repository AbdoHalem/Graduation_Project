import cv2
import socket
import pickle
import struct

# Set up socket
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)

conn, addr = sock.accept()
print(f"Connected by {addr}")

data = b""
payload_size = struct.calcsize("L")

while True:
    while len(data) < payload_size:
        data += conn.recv(4096)

    packed_size = data[:payload_size]
    data = data[payload_size:]
    frame_size = struct.unpack("L", packed_size)[0]

    while len(data) < frame_size:
        data += conn.recv(4096)

    frame_data = data[:frame_size]
    data = data[frame_size:]

    frame = pickle.loads(frame_data)  # Deserialize frame

    cv2.imshow("Receiver", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

conn.close()
cv2.destroyAllWindows()
