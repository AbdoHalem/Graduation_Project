import cv2
import os
import mmap
import time

# --- CONFIG ---
SHM_PATH = "/dev/shm/frame_buf"  # shared memory file


FRAME_W = 640
FRAME_H = 480
FRAME_C = 3  # BGR
BUF_SIZE = FRAME_W * FRAME_H * FRAME_C


if not os.path.exists(SHM_PATH):
    with open(SHM_PATH, "wb") as f:
        f.truncate(BUF_SIZE)


fd = os.open(SHM_PATH, os.O_RDWR)
shm = mmap.mmap(fd, BUF_SIZE, flags=mmap.MAP_SHARED, prot=mmap.PROT_WRITE | mmap.PROT_READ)


gst_pipeline = (
    "v4l2src device=/dev/video0 ! "
    "videoconvert ! "
    "videoflip method=rotate-180 ! "
    "video/x-raw,format=BGR ! "
    "appsink"
)

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
if not cap.isOpened():
    raise RuntimeError("Failed to open GStreamer pipeline")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break


        FRAME_H, FRAME_W, FRAME_C = frame.shape
        new_buf_size = FRAME_W * FRAME_H * FRAME_C

        
        if new_buf_size > BUF_SIZE:
            shm.close()
            os.close(fd)
            with open(SHM_PATH, "wb") as f:
                f.truncate(new_buf_size)
            fd = os.open(SHM_PATH, os.O_RDWR)
            shm = mmap.mmap(fd, new_buf_size, flags=mmap.MAP_SHARED, prot=mmap.PROT_WRITE | mmap.PROT_READ)
            BUF_SIZE = new_buf_size

        shm.seek(0)
        shm.write(frame.tobytes())

        status = cv2.imwrite("frame.jpg", frame)
        print("Image saved:", status)

        time.sleep(0.04)

finally:
    cap.release()
    shm.close()
    os.close(fd)
