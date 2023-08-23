import os
import pickle
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import numpy as np
import sys

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and set the log file path
log_file_path = 'RF_training_log.log'
file_handler = logging.FileHandler(log_file_path)

# Create a formatter and attach it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

def train_random_forest_model():    
    try:
        pickle_file_path = os.path.join('dataset', 'data.pickle')
        data_dict = pickle.load(open(pickle_file_path, 'rb'))
    except FileNotFoundError:
        logger.error("Error: data.pickle file not found. Training failed.")
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

    # Check the shapes of 'data' and 'labels' before concatenation
    logger.info("Data shape before concatenation: %s", str(data_dict['data'][0].shape))
    logger.info("Labels shape before concatenation: %s", str(labels.shape))

    # Check if the number of samples in 'data' matches the number of samples in 'labels'
    if len(data) != len(labels):
        logger.error("Error: Inconsistent number of samples between data and labels. Training failed.")
        sys.exit(1)

    # Check the shapes of 'data' and 'labels' after concatenation
    logger.info("Data shape after concatenation: %s", str(data.shape))
    logger.info("Labels shape after concatenation: %s", str(labels.shape))

    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, shuffle=True, stratify=labels)

    if len(np.unique(y_train)) <= 1:
        logger.error("Error: Insufficient number of classes. Training failed.")
        sys.exit(1)

    model = RandomForestClassifier()
    model.fit(x_train, y_train)

    # Evaluate the model on the test dataset
    y_predict = model.predict(x_test)
    test_score = accuracy_score(y_predict, y_test)
    logger.info('Accuracy on Test Dataset: {:.2f}%'.format(test_score * 100))

    # Perform cross-validation and calculate the mean and standard deviation of scores
    cv_scores = cross_val_score(model, data, labels, cv=5)
    mean_cv_score = cv_scores.mean()
    std_cv_score = cv_scores.std()
    logger.info("Cross-Validation Scores: %s", str(cv_scores))
    logger.info("Mean Cross-Validation Score: %s", str(mean_cv_score))
    logger.info("Standard Deviation of Cross-Validation Score: %s", str(std_cv_score))

    model_folder = 'model'
    os.makedirs(model_folder, exist_ok=True)
    model_file_path = os.path.join(model_folder, 'model.p')
    with open(model_file_path, 'wb') as f:
        pickle.dump({'model': model}, f)

    logger.info('Training completed. Model saved.')

if __name__ == '__main__':
    try:
        train_random_forest_model()
    except Exception as e:
        logger.error("Error: %s", str(e))
        sys.exit(1)
