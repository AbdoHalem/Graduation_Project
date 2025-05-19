import cv2
import socket
import struct, time

HOST = "127.0.0.1"  # or the container’s IP if bridged
PORT = 9999

# Build GStreamer pipeline just like before
gst_pipeline = (
    "libcamerasrc ! "
    "video/x-raw,width=640,height=480,format=YUY2 ! "
    "videoconvert ! "
    "videoflip method=rotate-180 ! "
    "video/x-raw,format=BGR ! appsink"
)

def main():
    # 1) Open the camera
    # cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    # 2) Connect to the container’s server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {HOST}:{PORT}…")
    sock.connect((HOST, PORT))

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 3) JPEG‑compress the frame (you can tune quality)
            ret2, jpg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ret2:
                print("Image is not compressed successfully!")
                continue

            data = jpg.tobytes()
            # 4) Send 4‑byte length prefix, then the JPEG bytes
            sock.sendall(struct.pack('!I', len(data)))
            sock.sendall(data)

            # throttle if you like
            time.sleep(0.02)
    finally:
        cap.release()
        sock.close()

if __name__ == "__main__":
    main()
