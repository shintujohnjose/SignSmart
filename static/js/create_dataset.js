window.addEventListener('load', function () {
    initializeCreateDataset();
});

function initializeCreateDataset() {
    // Check dataset status if inside the create dataset container
    var createDatasetContainer = document.getElementById('create-dataset-container');
    if (createDatasetContainer) {
        fetch('/dataset_status')
            .then(response => response.json())
            .then(data => {
                var status = data.status;
                if (status === 'in_progress') {
                    setDatasetStatusMessage('Dataset creation in progress...');
                    setTimeout(checkDatasetStatus, 1000); // Check dataset status again after 1 second
                    hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
                } else if (status === 'completed') {
                    setDatasetStatusMessage('Dataset creation completed!');
                    hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
                    resetDatasetStatus();
                } else if (status === 'failed') {
                    setDatasetStatusMessage('Dataset creation failed.');
                    setNoDatasetMessage('No gestures found inside Data folder.');
                    showNoDatasetMessage(); // Show the "no-dataset-message"
                    resetDatasetStatus();
                } else {
                    setDatasetStatusMessage('Dataset creation status idle.');
                    hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
                    resetDatasetStatus();
                }
            })
            .catch(error => {
                console.log('Error checking dataset status:', error);
                setDatasetStatusMessage('Failed to retrieve dataset status.');
            });
    }
}

function startDatasetCreation() {
    fetch('/create_dataset', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            var status = data.status;
            if (status === 'success') {
                setDatasetStatusMessage('Dataset creation initiated!');
                setTimeout(checkDatasetStatus, 1000); // Check dataset status after 1 second
            } else if (status === 'failed') {
                setDatasetStatusMessage('Failed to initiate dataset creation.');
                setNoDatasetMessage('No gestures found inside Data folder.');
                showNoDatasetMessage(); // Show the "no-dataset-message"
                resetDatasetStatus();
            }
        })
        .catch(error => {
            console.log('Error initiating dataset creation:', error);
            setDatasetStatusMessage('Failed to initiate dataset creation.');
            setNoDatasetMessage('No gestures found inside Data folder.');
            showNoDatasetMessage(); // Show the "no-dataset-message"
            resetDatasetStatus();
        });
}

function stopDatasetCreation() {
    fetch('/stop_dataset_creation', {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            var status = data.status;
            if (status === 'success') {
                setDatasetStatusMessage('Dataset creation stopped.');
            } else {
                setDatasetStatusMessage('Failed to stop dataset creation.');
            }
        })
        .catch(error => {
            console.log('Error stopping dataset creation:', error);
            setDatasetStatusMessage('Failed to stop dataset creation.');
        });
}

function updateProgressBar(percentage, elapsedTime, remainingTime) {
    var progressBar = document.getElementById("progress-bar");
    var progressText = document.getElementById("progress-text");

    progressBar.value = percentage;
    progressText.textContent = `Processing... ${percentage.toFixed(2)}%`;
}


function setDatasetStatusMessage(message) {
    var datasetStatusMessageElement = document.getElementById("dataset-status-message");
    datasetStatusMessageElement.textContent = message;
}

function setNoDatasetMessage(message) {
    var noDatasetMessageElement = document.getElementById("no-dataset-message");
    noDatasetMessageElement.textContent = message;
}

function showNoDatasetMessage() {
    var noDatasetMessageElement = document.getElementById("no-dataset-message");
    noDatasetMessageElement.style.display = "block";
}

function hideNoDatasetMessage() {
    var noDatasetMessageElement = document.getElementById("no-dataset-message");
    noDatasetMessageElement.style.display = "none";
}

function resetDatasetStatus() {
    setTimeout(function () {
        setDatasetStatusMessage('Dataset creation status idle.');
        hideNoDatasetMessage(); // Hide the "no-dataset-message"
    }, 3000); // Reset status to idle after 3 seconds
}

function checkDatasetStatus() {
    fetch('/dataset_status')
        .then(response => response.json())
        .then(data => {
            var status = data.status;
            if (status === 'in_progress') {
                setDatasetStatusMessage('Dataset creation in progress...');
                setTimeout(checkDatasetStatus, 1000); // Check dataset status again after 1 second
                hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
            } else if (status === 'completed') {
                setDatasetStatusMessage('Dataset creation completed!');
                hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
                resetDatasetStatus();
            } else if (status === 'failed') {
                setDatasetStatusMessage('Dataset creation failed.');
                setNoDatasetMessage('No gestures found inside Data folder.');
                showNoDatasetMessage(); // Show the "no-dataset-message"
                resetDatasetStatus();
            } else {
                setDatasetStatusMessage('Dataset creation status idle.');
                hideNoDatasetMessage(); // Hide the "no-dataset-message" if it was previously displayed
                resetDatasetStatus();
            }
        })
        .catch(error => {
            console.log('Error checking dataset status:', error);
            setDatasetStatusMessage('Failed to retrieve dataset status.');
        });
}
