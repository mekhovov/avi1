import time

import cv2
from ultralytics import YOLO

# Load YOLO model (replace with your model file path)
model = YOLO('./model/best-yolo8.pt')  # Use your trained model path (e.g., best.pt)

# IP Camera HTTP stream URL
# ip_camera_url = "http://127.0.0.1:5000/video_feed"  # Your HTTP stream URL
ip_camera_url = "http://192.168.0.116:5000/video_feed"  # Your HTTP stream URL

# Open video capture using OpenCV
cap = cv2.VideoCapture(ip_camera_url)

import gimbalcmd

gc = gimbalcmd.GimbalControl()
gc.reset()

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# gc.reset()

while True:
    ret, frame = cap.read()  # Capture a frame from the IP camera stream

    if not ret:
        print("Error: Failed to capture image.")
        break

    # print(time.time())
    # continue

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
        print(x, y, x_center, y_center)
        try:
            dx = x_center - x
            if abs(dx) < 10:
                dx = 0
            else:
                dx = int(dx // abs(dx))
        except (ValueError, ZeroDivisionError):
            dx = 0
        try:
            dy = y_center - y
            if abs(dy) < 10:
                dy = 0
            else:
                dy = -int(dy // abs(dy))
        except (ValueError, ZeroDivisionError):
            dy = 0
        gc.move(dy, 0, dx, 0.5, acc=0)
        # time.sleep(1)

    # print(time.time())


    # Display the frame with detection results
    # cv2.imshow("YOLO Inference", rendered_frame)

    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
