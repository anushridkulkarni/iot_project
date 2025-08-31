import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time
import requests
import os
import sys

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <server_ip>")
    sys.exit(1)

server_ip = sys.argv[1]
SERVER_URL = f"http://{server_ip}:5000/upload"

MODEL_PATH = "ssd_mobilenet_v2_coco.tflite"

# Create local folder for saving captured images
save_dir = 'captured_images'
os.makedirs(save_dir, exist_ok=True)

interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape'][1:3]

cap = cv2.VideoCapture(0)
frame_no = 0
last_count = 0

print("Started Passenger Counter......")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    img = cv2.resize(frame, tuple(input_shape))
    input_data = np.expand_dims(img, axis=0).astype(np.uint8)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[0]['index'])
    class_ids = interpreter.get_tensor(output_details[1]['index'])
    scores = interpreter.get_tensor(output_details[2]['index'])

    person_count = 0
    for i in range(len(scores[0])):
        if scores[0][i] > 0.5 and int(class_ids[0][i]) == 0:
            person_count += 1
            ymin, xmin, ymax, xmax = boxes[0][i]
            x1, y1 = int(xmin * frame.shape[1]), int(ymin * frame.shape[0])
            x2, y2 = int(xmax * frame.shape[1]), int(ymax * frame.shape[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    print(f"Frame {frame_no}: Passengers = {person_count}")

    if person_count > 0 and last_count == 0:
        # Save image locally with timestamp filename
        timestamp = int(time.time())
        filename = f"passenger_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        cv2.imwrite(filepath, frame)
        print(f"Saved local image: {filepath}")

        # Encode image for upload
        _, img_encoded = cv2.imencode('.jpg', frame)
        files = {'image': (filename, img_encoded.tobytes(), 'image/jpeg')}
        data = {'count': person_count}

        try:
            response = requests.post(
                SERVER_URL,
                data=data,
                files=files,
                auth=('student1', 'mitwpu'),  # Use your server basic auth
                timeout=5
            )
            print(f"Sent data to server: {response.status_code}")
        except Exception as e:
            print(f"Failed to send data: {e}")

    last_count = person_count
    frame_no += 1
    time.sleep(1.0)

cap.release()

