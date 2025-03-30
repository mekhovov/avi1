import time

import cv2
from ultralytics import YOLO

# Load YOLO model (replace with your model file path)
model = YOLO('./model/best-yolo8.pt')  # Use your trained model path (e.g., best.pt)

# IP Camera HTTP stream URL
# ip_camera_url = "http://127.0.0.1:8000/"  # Your HTTP stream URL
ip_camera_url = "http://192.168.0.116:8000/"  # Your HTTP stream URL

# Open video capture using OpenCV
cap = cv2.VideoCapture(ip_camera_url)

import gimbalcmd

gc = gimbalcmd.GimbalControl()

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

gc.reset()

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
        gc.move(dy, 0, dx, 1, acc=0)
        time.sleep(1)

    # Display the frame with detection results
    cv2.imshow("YOLO Inference", rendered_frame)
    
    # Exit loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
