from ultralytics import YOLO
import os
import torch

model = YOLO("runs/detect/train6/weights/last.pt")

# # Load a model
# model = YOLO("yolov8n.yaml")  # build a new model from scratch
# model = YOLO("yolov8n.pt")  # build a new model from scratch
# model = YOLO("runs/detect/train4/weights/last.pt")  # load a pretrained model (recommended for training)

# Use the model
results = model.train(data="/run/media/omar/Windows-SSD/DATA_SET/data.yaml",epochs=200,batch=32,plots=True,resume = True , amp=True,val=True,save_period=10)  # train the model
# Evaluate the model's performance on the validation set
results = model.val(data="/run/media/omar/Windows-SSD/DATA_SET/data.yaml") 


