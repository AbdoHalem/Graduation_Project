'''
This script reads frames from a GStreamer pipeline and writes them to shared memory.
It uses OpenCV to capture frames from a camera and stores them in a shared memory segment.
The shared memory segment is created using the `mmap` module, which allows for efficient inter-process communication.
The script is designed to work with a Raspberry Pi camera and uses the `libcamerasrc` GStreamer plugin to capture frames.
The script is intended to be run on a Raspberry Pi with a camera module connected.'''
# Import necessary libraries
import cv2
import os
import mmap
import struct
import time

# --- CONFIG ---
SHM_PATH    = "/dev/shm/frame_buf"       # shared memory file
FRAME_W     = 640
FRAME_H     = 480
FRAME_C     = 3                         # BGR
BUF_SIZE = FRAME_W * FRAME_H * FRAME_C

# Create/truncate backing file once
if not os.path.exists(SHM_PATH):
    with open(SHM_PATH, "wb") as f:
        f.truncate(BUF_SIZE)

# Memory-map the file, size 0 means whole file
fd = os.open(SHM_PATH, os.O_RDWR)
shm = mmap.mmap(fd, BUF_SIZE, flags=mmap.MAP_SHARED, prot=mmap.PROT_WRITE|mmap.PROT_READ)

# GStreamer pipeline
gst_pipeline = (
    "libcamerasrc ! "
    "video/x-raw,width=640,height=480,format=YUY2 ! "
    "videoconvert ! "
    "videoflip method=rotate-180 ! "
    "video/x-raw,format=BGR ! "
    "appsink"
)

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
# cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Failed to open GStreamer pipeline")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        #cv2.imshow("Pi camera", frame)
        shm.seek(0)
        shm.write(frame.tobytes())
        time.sleep(0.04)  # Adjust the sleep time as needed

finally:
    cap.release()
    shm.close()
    os.close(fd)
