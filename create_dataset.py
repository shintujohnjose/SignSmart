import os
import pickle
import sys
import mediapipe as mp
import cv2
import numpy as np
import time

mp_hands = mp.solutions.hands

DATA_DIR = './data'
HAND_FOLDERS = ['left_hand', 'right_hand']

def set_dataset_status(status):
    global dataset_status
    dataset_status = status

def create_dataset(stop_event=None):
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

    hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

    data = []
    labels = []

    if not os.path.isdir(DATA_DIR):
        print("No directories found inside 'data' folder.")
        return False

    start_time = time.time()
    total_images = 0

    for hand_folder in HAND_FOLDERS:
        hand_folder_path = os.path.join(DATA_DIR, hand_folder)
        if os.path.isdir(hand_folder_path):
            for gesture_folder in os.listdir(hand_folder_path):
                gesture_folder_path = os.path.join(hand_folder_path, gesture_folder)
                if os.path.isdir(gesture_folder_path):
                    total_images += len(os.listdir(gesture_folder_path))

    image_count = 0

    for hand_folder in HAND_FOLDERS:
        hand_folder_path = os.path.join(DATA_DIR, hand_folder)
        if os.path.isdir(hand_folder_path):
            hand_side = 'left hand' if hand_folder == 'left_hand' else 'right hand'
            for gesture_folder in os.listdir(hand_folder_path):
                gesture_folder_path = os.path.join(hand_folder_path, gesture_folder)
                if os.path.isdir(gesture_folder_path):
                    for img_path in os.listdir(gesture_folder_path):
                        if stop_event and stop_event.is_set():
                            print("Dataset creation stopped by user.")
                            dataset_status = 'stopped'
                            return False
                        
                        img = cv2.imread(os.path.join(gesture_folder_path, img_path))
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                        results = hands.process(img_rgb)
                        if results.multi_hand_landmarks:
                            data_aux = []
                            x_ = []
                            y_ = []

                            for hand_landmarks in results.multi_hand_landmarks:
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

                            # Convert data_aux to a numpy array
                            data_aux = np.array(data_aux)

                            # Check if data_aux has the same shape as the first element in 'data'
                            if data and data_aux.shape[0] != data[0].shape[0]:
                                print("Warning: Skipping data_aux due to inconsistent shape.")
                                continue
                            
                            data.append(data_aux)
                            labels.append(gesture_folder)

                            image_count += 1
                            elapsed_time = time.time() - start_time
                            avg_time_per_image = elapsed_time / image_count
                            remaining_images = total_images - image_count
                            estimated_remaining_time = remaining_images * avg_time_per_image

                            print(f"Processing gesture {image_count}/{total_images}: {hand_side} {gesture_folder}, "
                                  f"Elapsed Time: {elapsed_time:.2f} seconds, "
                                  f"Estimated Remaining Time: {estimated_remaining_time:.2f} seconds")

    if len(data) == 0:
        print("No gestures found inside 'data' folder.")
        return False

    # Convert 'labels' to a numpy array
    labels = np.array(labels)

    # Check if the number of samples in 'data' matches the number of samples in 'labels'
    if len(data) != len(labels):
        print("Error: Inconsistent number of samples between data and labels. Training failed.", file=sys.stderr)
        print("Number of data samples:", len(data))
        print("Number of label samples:", len(labels))
        return False

    data = np.array(data)  # Convert 'data' to a numpy array

    dataset = {'data': data, 'labels': labels}
    pickle_file_path = os.path.join('dataset', 'data.pickle')
    os.makedirs(os.path.dirname(pickle_file_path), exist_ok=True)
    with open(pickle_file_path, 'wb') as f:
        pickle.dump(dataset, f)

    print("Data shape:", data.shape)
    print("Labels shape:", labels.shape)

    print("Dataset creation completed successfully.")
    return True

if __name__ == "__main__":
    create_dataset()