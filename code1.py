import base64
import os
import queue
import time
import cv2
import pickle
import mediapipe as mp
import numpy as np
import logging


# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

model_file_path = os.path.join('model', 'model.p')
model_dict = pickle.load(open(model_file_path, 'rb'))
model = model_dict['model']

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

# Extract the labels from the loaded model
# Update the labels_dict to map 's' to 'space'
labels_dict = {label: label if label != 's' else 'Space' for label in model.classes_}

# Flag to control the frame processing loop
recognized_signs_tracker = []  # Store recognized signs
recognized_signs_queue = queue.Queue()  # Create a thread-safe queue
sentence_signs = []  # Store recognized signs to build the sentence
last_recognized_label = ''  # Initialize with an empty string

def process_frames_with_sign(frame, socketio):
    global recognized_signs_tracker, sentence_signs, last_recognized_label
    logger.info("Frame Processing Started")

    try:
        H, W, _ = frame.shape

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        predicted_character = None
        label = None

        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())
                try:
                    data_aux = []
                    x_ = []
                    y_ = []

                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y

                        x_.append(x)
                        y_.append(y)

                    for i in range(len(hand_landmarks.landmark)):
                        x = hand_landmarks.landmark[i].x
                        y = hand_landmarks.landmark[i].y
                        data_aux.append(x - min(x_))
                        data_aux.append(y - min(y_))

                    x1 = int(min(x_) * W) - 10
                    y1 = int(min(y_) * H) - 10

                    x2 = int(max(x_) * W) - 10
                    y2 = int(max(y_) * H) - 10

                    num_hands = len(results.multi_hand_landmarks)
                    num_features = 42 * num_hands
                    data_aux = data_aux[:num_features]

                    prediction = model.predict([np.asarray(data_aux)])
                    predicted_character = labels_dict[prediction[0]]

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                    cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3)
                    
                    label = predicted_character
                    recognized_signs_tracker.append((label, time.time()))

                    logger.info(f"Detected Sign: {predicted_character}")

                    if label == 'Space':
                        sentence_signs.append(' ')
                    elif label != last_recognized_label:
                        sentence_signs.append(label)
                    last_recognized_label = label
                    logger.info(f"sentence_signs list: {sentence_signs}")
                    emit_processed_data(frame, label, socketio)

                except Exception as e:
                    logger.error(f"An error occurred during hand landmarks processing: {str(e)}")
        else:
            label = None  # Set label to None if no hand signs are detected

        emit_processed_data(frame, label, socketio)

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")


def emit_processed_data(frame, label, socketio):
    global recognized_signs_queue
    _, buffer = cv2.imencode('.jpg', frame)
    processed_frame_data = 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')
    logger.info("Sending processed frames to client")
    socketio.emit('processed_frame_data', processed_frame_data)

    if label:
        recognized_signs_queue.put((label, time.time()))
        logger.info(f"recognized_signs_tracker: {list(recognized_signs_queue.queue)}")  # Log the updated queue

def get_ordered_recognized_sign(min_continuous_duration=3.0):
    global recognized_signs_queue
    current_time = time.time()

    logger.info("Getting ordered recognized sign...")

    continuous_sign_duration = 0
    continuous_sign = None

    for sign, timestamp in reversed(list(recognized_signs_queue.queue)):
        duration = current_time - timestamp

        if duration >= min_continuous_duration:
            if continuous_sign:
                logger.info(f"Continuous sign '{continuous_sign}' recognized for {continuous_sign_duration:.2f} seconds.")
                return continuous_sign
            break
        elif sign != continuous_sign:
            continuous_sign = sign
            continuous_sign_duration = duration

    if continuous_sign_duration >= min_continuous_duration:
        logger.info(f"Continuous sign '{continuous_sign}' recognized for {continuous_sign_duration:.2f} seconds.")
        recognized_signs_tracker.clear()
        logger.info("Ordered recognized sign retrieved.")
        return continuous_sign

    logger.info("Ordered recognized sign retrieved.")
    return None


def reset_data():
    global recognized_signs_tracker, sentence_signs, last_recognized_label
    recognized_signs_tracker.clear()
    sentence_signs.clear()
    last_recognized_label = ''
