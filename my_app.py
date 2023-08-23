import base64
import os
import queue
import subprocess
import threading
from queue import Queue
import time
import cv2
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
import numpy as np
import create_dataset
import code1, code2
import logging


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")


app.config['SECRET_KEY'] = 'secret_key'

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


capture_status = 'idle'  # Variable to keep track of capture status
dataset_status = 'idle'  # Variable to keep track of dataset creation status
dataset_thread = None

process = None
recognized_signs = []  # Define recognized_signs globally
recognized_signs_tracker = []

@app.route('/index.html')
@app.route('/')
def index():
    return render_template('index.html')



# Define the data directory
data_dir = './data'

# Endpoint to receive and save the captured images
@app.route('/save_capture', methods=['POST'])
def save_capture():
    try:
        # Get the image data from the POST request
        image_data = request.form.get('image_data')

        # Get the hand and gesture name from the POST request
        hand = request.form.get('hand')
        gesture_name = request.form.get('gesture_name')

        # Prepare the directory path to save the captured image
        hand_folder = f"{hand}_hand"  # Add _hand to the hand folder name
        gesture_dir = os.path.join(data_dir, hand_folder, gesture_name)
        if not os.path.exists(gesture_dir):
            os.makedirs(gesture_dir)

        # Decode the base64 image data
        image_bytes = base64.b64decode(image_data.split(',')[1])
        
        # Save the image to the specified directory
        image_path = os.path.join(gesture_dir, f'{gesture_name}_{len(os.listdir(gesture_dir)) + 1}.jpg')
        with open(image_path, 'wb') as f:
            f.write(image_bytes)

        return jsonify({'status': 'success', 'message': 'Image saved successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

    
@app.route('/create_dataset', methods=['POST'])
def create_dataset_route():
    global dataset_status, dataset_thread, stop_event

    # Check if dataset creation is already in progress
    if dataset_thread and dataset_thread.is_alive():
        return jsonify({'status': 'failure', 'message': 'Dataset creation is already in progress.'})

    # Clear the stop_creation event to allow new dataset creation
    stop_event.clear()

    # Set dataset status to in_progress
    dataset_status = 'in_progress'

    # Run the create_dataset function in a separate thread
    dataset_thread = threading.Thread(target=run_create_dataset, args=(stop_event,))
    dataset_thread.start()

    return jsonify({'status': 'success'})


def run_create_dataset(stop_event):
    global dataset_status

    # Set dataset status to in_progress
    dataset_status = 'in_progress'

    # Run the create_dataset function
    success = create_dataset.create_dataset(stop_event=stop_event)

    if stop_event.is_set():
        dataset_status = 'stopped'
        return

    # Set dataset status based on the success of dataset creation
    if success:
        dataset_status = 'completed'
    else:
        dataset_status = 'failed'

    # Sleep for a while to allow the status message to be displayed
    time.sleep(5)

    # Reset dataset status to idle
    dataset_status = 'idle'




# Create a threading event
stop_event = threading.Event()

@app.route('/stop_dataset_creation', methods=['GET'])
def stop_dataset_creation_route():
    global stop_event
    stop_event.set()  # Set the event to signal the thread to stop
    return jsonify({'status': 'success'})



@app.route('/dataset_status', methods=['GET'])
def get_dataset_status():
    # Check the status of the dataset creation process
    return jsonify({'status': dataset_status})





@app.route('/model-selection', methods=['POST'])
def model_selection():
    selected_model = request.form['model']
    if selected_model == 'model1':
        try:
            process = subprocess.run(["python", "train_RandomForestModel.py"], capture_output=True, text=True)
            if process.returncode == 0:
                output = process.stdout.strip()
                formatted_output = output.replace('\n', '<br>')
                return jsonify({'status': 'success', 'message': formatted_output})
            else:
                error_output = process.stderr.strip()
                formatted_error_output = error_output.replace('\n', '<br>')
                return jsonify({'status': 'error', 'message': formatted_error_output})
        except FileNotFoundError:
            return jsonify({'status': 'error', 'message': 'Error: data.pickle file not found. Training failed.'})
    elif selected_model == 'model2':
        try:
            process = subprocess.run(["python", "train_CNNModel.py"], capture_output=True, text=True)
            if process.returncode == 0:
                output = process.stdout.strip()
                formatted_output = output.replace('\n', '<br>')
                return jsonify({'status': 'success', 'message': formatted_output})
            else:
                error_output = process.stderr.strip()
                formatted_error_output = error_output.replace('\n', '<br>')
                return jsonify({'status': 'error', 'message': formatted_error_output})
        except FileNotFoundError:
            return jsonify({'status': 'error', 'message': 'Error: data.pickle file not found. Training failed.'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid model selection'})



processing_queue = queue.Queue()
keep_processing = False
processing_lock = threading.Lock()


@socketio.on('send_frame')
def send_frame(data):
    global keep_processing

    # Set keep_processing to True to start processing frames again
    keep_processing = True

    logger.info('Received data from client')

    # Extract frame_data and selectedModel from the received data
    frame_data = data.get('frameData')
    selected_model = data.get('selectedModel')

    nparr = np.frombuffer(base64.b64decode(frame_data.split(',')[1]), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if selected_model == 'RandomForest':
        threading.Thread(target=code1.process_frames_with_sign, args=(frame, socketio,), daemon=True).start()
    elif selected_model == 'CNN':
        num_landmarks = 21
        threading.Thread(target=code2.process_frames_with_sign_cnn, args=(frame, num_landmarks, socketio,), daemon=True).start()


@socketio.on('recognition_status_request')
def get_recognition_status(data):
    global recognized_signs_tracker
    logger.info('Received Recognition status request from client')
    selected_model = data.get('selectedModel', '')

    # Define a function to get ordered recognized signs and emit recognition status
    def get_ordered_sign_and_emit():
        ordered_sign = []

        if selected_model == 'RandomForest':
            ordered_sign = code1.get_ordered_recognized_sign()
        elif selected_model == 'CNN':
            ordered_sign = code2.get_ordered_recognized_signs_cnn() 

        if keep_processing:
            if ordered_sign is not None:
                emit_data = {"status": "Recognition in progress...", "ordered_sign": ordered_sign}
            else:
                emit_data = {"status": "No continuous sign detected.", "ordered_sign": None}
        else:
            emit_data = {"status": "Recognition stopped", "ordered_sign": None}

        # Start a new thread for emitting recognition status to the client
        threading.Thread(target=emit_recognition_status, args=(emit_data,), daemon=True).start()

    # Start a new thread for getting ordered signs and emitting recognition status
    threading.Thread(target=get_ordered_sign_and_emit, daemon=True).start()

def emit_recognition_status(emit_data):
    # Emit recognition status to the client
    socketio.emit('recognition_status', emit_data)
    logger.info('Sending Recognition status to client')


@socketio.on('stop_processing')
def stop_processing():
    global keep_processing, processing_lock, recognized_signs_tracker
    logger.info('Received Stop request from client')

    # Acquire the processing lock to prevent concurrent access to keep_processing flag
    with processing_lock:
        # Set keep_processing to False to stop further processing
        keep_processing = False

    # Clear the recognized signs tracker and reset other relevant data
    recognized_signs_tracker.clear()
    code1.reset_data()  # Reset data for code1
    code2.reset_data()  # Reset data for code2

    # Emit a message to indicate that processing has been stopped
    socketio.emit('recognition_status', {"status": "Recognition stopped", "ordered_sign": None})

# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Use the environment variable for the port, or default to 5000 if not available
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
