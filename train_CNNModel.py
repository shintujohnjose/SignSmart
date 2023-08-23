import json
import os
import pickle
import logging
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import Dense, Flatten, Conv1D, MaxPooling1D
from keras.utils import to_categorical
import numpy as np
import sys

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and set the log file path
log_file_path = 'CNN_training_log.log'
file_handler = logging.FileHandler(log_file_path)

# Create a formatter and attach it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

def train_cnn_model(input_shape, num_classes):
    try:
        pickle_file_path = os.path.join('dataset', 'data.pickle')
        data_dict = pickle.load(open(pickle_file_path, 'rb'))
    except FileNotFoundError:
        logger.error("Error: CNNdata.pickle file not found. Training failed.")
        sys.exit(1)

    # Check if the 'data' and 'labels' are in the expected format
    if not all(isinstance(sample, np.ndarray) for sample in data_dict['data']):
        logger.error("Error: 'data' should contain only arrays. Training failed.")
        sys.exit(1)

    if not isinstance(data_dict['labels'], np.ndarray):
        logger.error("Error: 'labels' should be a numpy array. Training failed.")
        sys.exit(1)

    data = np.vstack(data_dict['data']) 
    labels = np.asarray(data_dict['labels'])

    if len(data) == 0 or len(labels) == 0:
        logger.error("Error: Empty data or labels. Training failed.")
        sys.exit(1)

    # Convert labels to categorical format
    unique_labels = np.unique(labels)
    label_to_int = {label: i for i, label in enumerate(unique_labels)}
    labels = np.array([label_to_int[label] for label in labels])
    labels = to_categorical(labels, num_classes=num_classes)

    # Reshape data to the format expected by the CNN model
    data = data.reshape(-1, num_landmarks * 2, 1)  # Reshape data to (None, 42, 1)

    # Split data into training and validation sets
    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, shuffle=True, stratify=labels)

    if len(np.unique(y_train)) <= 1:
        logger.error("Error: Insufficient number of classes. Training failed.")
        sys.exit(1)

    model = Sequential()
    model.add(Conv1D(32, kernel_size=3, activation='relu', input_shape=input_shape))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(128, activation='relu'))
    model.add(Dense(num_classes, activation='softmax'))

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.summary()

    # Train the model and capture the training history
    history = model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=10, batch_size=32)

    # Save the trained model inside the 'model' folder
    model_folder = 'model'
    os.makedirs(model_folder, exist_ok=True)
    model_file_path = os.path.join(model_folder, 'hand_gesture_cnn_model.h5')
    model.save(model_file_path)

    logger.info('Training completed. CNN model saved.')

    # Log the history as a JSON string
    history_str = json.dumps(history.history)
    logger.info('Training history: %s', history_str)
    
    return history

if __name__ == '__main__':
    try:
        num_classes = 27  # Assuming there are 26 classes (A-Z) + space 
        num_landmarks = 21  # Assuming 21 (x, y) hand landmarks for each hand

        input_shape = (num_landmarks * 2, 1)  # The CNN model expects a 3D input shape (None, 42, 1)

        training_history = train_cnn_model(input_shape, num_classes)

        # Access the accuracy and loss history from the training_history object
        train_accuracy = training_history.history['accuracy']
        val_accuracy = training_history.history['val_accuracy']
        train_loss = training_history.history['loss']
        val_loss = training_history.history['val_loss']

        logger.info("Train Accuracy: %s", train_accuracy)
        logger.info("Validation Accuracy: %s", val_accuracy)
        logger.info("Train Loss: %s", train_loss)
        logger.info("Validation Loss: %s", val_loss)

    except Exception as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)
