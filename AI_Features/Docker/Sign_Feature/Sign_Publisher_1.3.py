import os
import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
import paho.mqtt.client as mqtt
import onnxruntime
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'    # Suppress TensorFlow logs
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'   # Disable GPU
sys.modules['np._core.multiarray'] = np.core.multiarray  # Fix numpy import

# MQTT Configuration
MQTT_BROKER = 'test.mosquitto.org'
MQTT_PORT   = 1883
MQTT_TOPIC  = 'ADAS_GP/sign'

mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# Detection setup

def initialize_model_and_source(model_path, input_type, input_source=None):
    root = os.getcwd()
    model_path = os.path.join(root, model_path)
    input_source = os.path.join(root, input_source) if input_source else None
    session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    cap = None
    input_images = None

    if input_type == 'video':
        cap = cv2.VideoCapture(input_source, cv2.CAP_FFMPEG)
    elif input_type == 'camera':
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)  # force V4L2 backend
        # set desired resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    elif input_type == 'image':
        if os.path.isdir(input_source):
            input_images = [os.path.join(input_source, f)
                            for f in os.listdir(input_source)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        else:
            raise ValueError('Input source must be a valid directory for images.')
    else:
        raise ValueError("Invalid input type. Choose 'video', 'image', or 'camera'.")

    return session, cap, input_images

# Preprocessor

def preprocessor(frame, w, h):
    x = cv2.resize(frame, (w, h))
    image_data = x.astype(np.float32) / 255.0
    image_data = np.transpose(image_data, (2, 0, 1))
    return np.expand_dims(image_data, axis=0)

# Frame processing

def process_frame(session, conf, frame, iou_thresh=0.45):
    inp = session.get_inputs()[0]
    _, _, H, W = inp.shape

    # ensure 3-channel
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

    tensor = preprocessor(frame, W, H)
    ort_val = onnxruntime.OrtValue.ortvalue_from_numpy(tensor)
    raw = session.run(['output0'], {inp.name: ort_val})[0]

    outputs = np.squeeze(raw)
    outputs = np.transpose(outputs)

    img_h, img_w = frame.shape[:2]
    x_factor = img_w / W
    y_factor = img_h / H

    boxes, scores, class_ids = [], [], []
    for row in outputs:
        coords, class_scores = row[:4], row[4:]
        score = float(np.max(class_scores))
        if score < conf:
            continue
        cid = int(np.argmax(class_scores))
        x_c, y_c, w, h = coords
        left   = int((x_c - w/2) * x_factor)
        top    = int((y_c - h/2) * y_factor)
        width  = int(w * x_factor)
        height = int(h * y_factor)
        boxes.append([left, top, width, height])
        scores.append(score)
        class_ids.append(cid)

    idxs = cv2.dnn.NMSBoxes(boxes, scores, conf, iou_thresh)
    annotated = frame.copy()
    crops = []
    if len(idxs) > 0:
        for i in idxs.flatten():
            x, y, w, h = boxes[i]
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
            c = frame[y:y+h, x:x+w]
            if c.size:
                crops.append(c)
    return annotated, crops

# Recognition helpers

def grayscale(img): return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def equalize(img): return cv2.equalizeHist(img)

def preprocessing(img):
    img = grayscale(img)
    img = equalize(img)
    return img / 255


def getClassName(i):
    names = [
        "Speed limit (20km/h)", "Speed limit (30km/h)", "Speed limit (50km/h)",
        # ... (rest as before)
    ]
    return names[i] if i < len(names) else 'Unknown'


# Main
if __name__ == '__main__':
    # TFLite init
    interp = tflite.Interpreter(model_path='recognition_model/sign_model.tflite')
    interp.allocate_tensors()
    in_det = interp.get_input_details()
    out_det = interp.get_output_details()

    # Detection model
    det_model = 'detection_model/best_quant_v2.onnx'
    session, cap, imgs = initialize_model_and_source(det_model, 'camera')
    conf_thresh = 0.34

    frame_interval = 5
    last_sign = None
    count = 0

    try:
        if cap is None or not cap.isOpened():
            print('Error: Unable to open camera.')
        else:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                count += 1
                if count % frame_interval != 0:
                    continue

                annotated, crops = process_frame(session, conf_thresh, frame)

                # Display detection output
                cv2.imshow('Detection Output', annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                for c in crops:
                    if c.size == 0: continue
                    # recognize
                    img = cv2.resize(c, (32, 32))
                    img = preprocessing(img).reshape(1, 32, 32, 1).astype(np.float32)
                    interp.set_tensor(in_det[0]['index'], img)
                    interp.invoke()
                    preds = interp.get_tensor(out_det[0]['index'])
                    idx = np.argmax(preds)
                    prob = float(np.max(preds))
                    if prob > 0.9:
                        name = getClassName(idx)
                        if name != last_sign:
                            mqtt_client.publish(MQTT_TOPIC, f'Sign Type is: {name}')
                            last_sign = name
    except KeyboardInterrupt:
        pass
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        if cap: cap.release()
