import base64
import os
import queue
import time
import cv2
import pickle
import mediapipe as mp
import numpy as np
import logging
from keras.models import load_model


# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

model_path = os.path.join('model', 'hand_gesture_cnn_model.h5')
model = load_model(model_path)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

# Map model's class indices to gesture labels
labels_dict = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 
               9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R',
               18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z', 26: 'space'}



# Flag to control the frame processing loop
recognized_signs_tracker = []  # Store recognized signs
recognized_signs_queue = queue.Queue()  # Create a thread-safe queue
sentence_signs = []  # Store recognized signs to build the sentence
last_recognized_label = ''  # Initialize with an empty string


def process_frames_with_sign_cnn(frame, num_landmarks, socketio):
    global recognized_signs_tracker, sentence_signs, last_recognized_label
    logger.info("Frame Processing Started")
    try:
        H, W, _ = frame.shape

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        predicted_character = None  # Initialize with None
        label = None  # Initialize the label variable

        results = hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style())

            for hand_landmarks in results.multi_hand_landmarks:
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

                    data_aux = np.array(data_aux).reshape(-1, num_landmarks * 2, 1)

                    prediction = model.predict(data_aux)
                    predicted_label_index = np.argmax(prediction[0])
                    predicted_character = labels_dict[predicted_label_index]

                    logger.info(f"Detected Sign: {predicted_character}")

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
                    cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                                cv2.LINE_AA)

                    
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



def get_ordered_recognized_signs_cnn(min_continuous_duration=3.0):
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