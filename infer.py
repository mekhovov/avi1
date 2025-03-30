import asyncio
import base64
import time

import cv2
from ultralytics import YOLO

# Load YOLO model (replace with your model file path)
model = YOLO('./model/best-yolo8.pt')  # Use your trained model path (e.g., best.pt)

# IP Camera HTTP stream URL
# ip_camera_url = "http://192.168.0.116:8000/"  # Your HTTP stream URL
ip_camera_url = "http://127.0.0.1:8000/"  # Your HTTP stream URL

# Open video capture using OpenCV
cap = cv2.VideoCapture(ip_camera_url)

import gimbalcmd

gc = gimbalcmd.GimbalControl()
gc.reset()

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

def automated(embedded=True, event=None, clients=None):
    while True:
        ret, frame = cap.read()  # Capture a frame from the IP camera stream

        if not ret:
            print("Error: Failed to capture image.")
            break

        # Perform inference on the captured frame
        results = model(frame, verbose=False)

        # Access the first result and render detections on the frame
        rendered_frame = results[0].plot()  # Use plot() to render the result

        h, w = results[0].orig_shape
        x_center, y_center = w / 2, h / 2

        if len(results[0].boxes) == 1:
            box = results[0].boxes
            x_min, y_min, x_max, y_max = box.xyxy[0]
            x = (x_min + x_max) // 2
            y = (y_min + y_max) // 2
            try:
                dx = int((x_center - x)//abs(x_center - x))
            except (ValueError, ZeroDivisionError):
                dx = 0
            try:
                dy = -int((y_center - y)//abs(y_center - y))
            except (ValueError, ZeroDivisionError):
                dy = 0
            if not event or event.is_set():
                gc.move(dy, 0, dx, 1, acc = 0)
                cv2.imshow("YOLO Inference", rendered_frame)
                time.sleep(1)
                # await asyncio.sleep(1)

        # if not embedded:

        # if ws:
        # if clients:
        #     encoded_frame = encode_frame(rendered_frame)
            # await ws.send(encoded_frame)
            # await asyncio.gather(*(client.send(encoded_frame) for client in clients))

        # Exit loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the capture object and close OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


def encode_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def process_frame():
    ret, frame = cap.read()  # Capture a frame from the IP camera stream

    # Perform inference on the captured frame
    results = model(frame, verbose=False)

    # Access the first result and render detections on the frame
    rendered_frame = results[0].plot()  # Use plot() to render the result

    h, w = results[0].orig_shape
    x_center, y_center = w / 2, h / 2

    if len(results[0].boxes) == 1:
        box = results[0].boxes
        x_min, y_min, x_max, y_max = box.xyxy[0]
        x = (x_min + x_max) // 2
        y = (y_min + y_max) // 2
        acc = 1
        try:
            dx = x_center - x
            if abs(dx) > 20:
                dx = int(dx // abs(dx))
            else:
                dx = 0
        except (ValueError, ZeroDivisionError):
            dx = 0
        try:
            dy = y_center - y
            if abs(dx) > 20:
                dy = -int(dy // abs(dy))
            else:
                dy = 0
        except (ValueError, ZeroDivisionError):
            dy = 0
        gc.move(dy, 0, dx, 1, acc = 0)
        time.sleep(1)

    encoded_frame = encode_frame(frame)
    return encoded_frame

async def main():
    await automated(embedded=False)

if __name__ == '__main__':
    # asyncio.run(main())
    automated(embedded=False)
