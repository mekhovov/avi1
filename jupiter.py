import threading
import time
import io
import base64
from flask import Flask, Response
from jetcam.csi_camera import CSICamera
from jetcam.utils import bgr8_to_jpeg
import ipywidgets as widgets
from IPython.display import display

# Create the Flask app
app = Flask(__name__)

# Initialize the JetCam Camera
camera = CSICamera(width=500, height=500, capture_device=0)
camera.running = True

# Image widget for Jupyter display
image_widget = widgets.Image(format='jpeg')

# Variable to store the current image
current_image = None

# Define a function to stream images to the web page
def generate_frames():
    global current_image
    while True:
        if current_image is not None:
            frame = bgr8_to_jpeg(current_image)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.1)  # Add a delay to control the frame rate

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return """
        <html>
            <head><title>JetCam Camera Stream</title></head>
            <body>
                <h1>Live Camera Feed</h1>
                <img src="/video_feed" width="480" height="480" />
            </body>
        </html>
    """

# Flask server thread function
def start_flask_app():
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

# Start the Flask app in a separate thread
flask_thread = threading.Thread(target=start_flask_app)
flask_thread.start()

# Display the image in Jupyter (this can be removed if not needed)
display(image_widget)

# Function to update the image and store it globally
def update_image(change):
    global current_image
    current_image = change['new']  # Store the new image from the camera
    image_widget.value = bgr8_to_jpeg(current_image)  # Update the widget

# Observe the camera value and update the widget
camera.observe(update_image, names='value')


# cell 2
# Attention!  Execute this cell before moving to another notebook
# The USB camera application only requires that the notebook be reset
# The CSI camera application requires that the 'camera' object be specifically released

camera.running = False
camera.cap.release()