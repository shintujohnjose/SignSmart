var videoElement;
var startCaptureButton;
var stopCaptureButton;


function initializeCaptureUI() {
    // videoElement = document.getElementById("video-feed");
    startCaptureButton = document.getElementById("start-capture");
    stopCaptureButton = document.getElementById("stop-capture");

    // Display the placeholder by default
    displayPlaceholder();

    var gestureNameInput = document.getElementById('gesture_name');

    gestureNameInput.addEventListener('input', function () {
        var gestureName = gestureNameInput.value.trim();
        startCaptureButton.disabled = gestureName === '';
    });

    // Clear the active container
    activeContainer = "";

    // Check local storage for reference image display state
    var referenceImageDisplay = localStorage.getItem('referenceImageDisplay');
    if (referenceImageDisplay !== null) {
        displayReferenceImage(referenceImageDisplay === 'true');
    }

    // capture status on page load
    setStatusMessage('Capture is idle.');
}

function displayPlaceholder() {
    var placeholder = document.getElementById('video-placeholder');
    var customContainer = document.getElementById('video-custom-container');

    // Show the placeholder and hide the custom container when capture is not in progress
    placeholder.style.display = 'block';
    customContainer.style.display = 'none';

    startCaptureButton.style.display = 'block'; // Enable the Start Capture button
    stopCaptureButton.style.display = 'none'; // Hide the Stop Capture button

}

function displayCustomContainer() {
    var customContainer = document.getElementById('video-custom-container');
    var placeholder = document.getElementById('video-placeholder');

    // Show the custom container and hide the placeholder
    customContainer.style.display = 'block';
    placeholder.style.display = 'none';
}


let isCaptureInProgress = false;
let captureInterval;
let captureStatusIntervalId;
let completionTimeout;
let activeContainer = "";

function startCapture() {
    var hand = document.getElementById('hand').value;
    var gestureName = document.getElementById('gesture_name').value;


    if (gestureName.trim() === '') {
        setStatusMessage('Please enter a gesture name.');

        // Set a timeout to display "Capture is idle." after 2 seconds
        clearTimeout(completionTimeout); // Clear the previous timeout
        completionTimeout = setTimeout(function () {
            setStatusMessage('Capture is idle.');
        }, 2000);

        return;
    }

    // Set the active container to "video-custom-container" during capture
    activeContainer = "video-custom-container";
    displayCustomContainer();


    // Request user permission to access the camera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            var clientVideoElement = document.getElementById("client-video");
            clientVideoElement.srcObject = stream;

            // Wait for the 'loadedmetadata' event before playing the video and starting frame capture
            clientVideoElement.onloadedmetadata = function () {
                clientVideoElement.play();

                // Start capturing frames
                startFrameCapture(clientVideoElement, hand, gestureName);
            };
        })
        .catch(error => {
            console.error('Error accessing client camera:', error);
        });
}

function startFrameCapture(videoElement, hand, gestureName) {
    var capturedFrames = 0;
    captureInterval = setInterval(() => {
        if (capturedFrames >= 300) {
            clearInterval(captureInterval);
            stopCapture();
            return;
        }

        var clientCanvasElement = document.createElement('canvas');
        clientCanvasElement.width = videoElement.videoWidth;
        clientCanvasElement.height = videoElement.videoHeight;
        var context = clientCanvasElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, clientCanvasElement.width, clientCanvasElement.height);

        var frameData = clientCanvasElement.toDataURL('image/jpeg', 0.5);

        // Send the frame data to the server
        sendFrameToServer(frameData, hand, gestureName); // Pass hand and gestureName

        capturedFrames++;
    }, 300);

    // Update UI and capture status
    isCaptureInProgress = true;
    setStatusMessage('Capture Started...');
    startCaptureButton.style.display = 'none'; // Hide the Start Capture button
    stopCaptureButton.style.display = 'block'; // Enable the Stop Capture button
    displayReferenceImage(true);
    // captureStatusIntervalId = setInterval(checkCaptureStatus, 1000);
}

function stopCapture() {
    if (!isCaptureInProgress) {
        setStatusMessage('No capture is currently in progress.');
        return;
    }

    // Stop capturing frames and sending them to the server
    clearInterval(captureInterval);

    // Stop the video stream and clear the stream from the client video element
    var clientVideoElement = document.getElementById("client-video");
    var stream = clientVideoElement.srcObject;
    if (stream) {
        var tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        clientVideoElement.srcObject = null;
    }

    displayPlaceholder();
    // Updating UI and status messages
    setStatusMessage('Capture Stopped!'); // Update status message

    displayReferenceImage(false); // Stop displaying the reference image

    // Set the active container back to an empty string after stopping the capture
    activeContainer = "";

    completionTimeout = setTimeout(function () {
        resetCapture(); // Reset the form and re-initialize the UI after stopping the capture
    }, 1000); // Hide the completion message after 1 second

    startCaptureButton.style.display = 'block'; // Enable the Start Capture button
    stopCaptureButton.style.display = 'none'; // Disable the Stop Capture button
}

function sendFrameToServer(frameData, hand, gestureName) {
    // Create a FormData object to send the data
    var formData = new FormData();
    formData.append('image_data', frameData);
    formData.append('hand', hand);
    formData.append('gesture_name', gestureName);

    // Make a POST request to the server's /save_capture endpoint
    fetch('/save_capture', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            console.log('Server response:', data);
            // Handle the server response as needed
        })
        .catch(error => {
            console.error('Error sending frame to server:', error);
        });
}


function showCaptureInProgress() {
    startCaptureButton.disabled = true;
    stopCaptureButton.style.display = 'inline-block';
    setStatusMessage('Capture is in progress...'); // Update status message
}

function showCaptureCompletionMessage() {
    if (isCaptureInProgress) {
        isCaptureInProgress = false;
        clearTimeout(completionTimeout); // Clear the completion message timeout if it exists

        setStatusMessage('Capture Completed!'); // Update status message

        displayReferenceImage(false); // Stop displaying the reference image

        // Set the active container back to an empty string after stopping the capture
        activeContainer = "";

        completionTimeout = setTimeout(function () {
            resetCapture(); // Reset the form and re-initialize the UI after stopping the capture
        }, 1000); // Hide the completion message after 1 second

        enableStartCaptureButton(true); // Enable the Start Capture button
        enableStopCaptureButton(false); // Disable the Stop Capture button

        clearInterval(captureStatusIntervalId); // Stop capture status polling
        // checkCaptureStatus(); // Update the capture status immediately
    }
}

function displayReferenceImage(display) {
    var referenceImage = document.getElementById('reference-image');
    var placeholder = document.getElementById('video-placeholder');
    var customContainer = document.getElementById('video-custom-container');

    // Display the reference image if 'display' is true, otherwise, display the placeholder
    referenceImage.style.display = display ? 'block' : 'none';
    placeholder.style.display = display ? 'none' : 'block';
    customContainer.style.display = display ? 'flex' : 'none';

    // Update local storage with the reference image display state
    localStorage.setItem('referenceImageDisplay', display ? 'true' : 'false');
}


function resetCapture() {
    var gestureNameInput = document.getElementById('gesture_name');
    gestureNameInput.value = '';
    startCaptureButton.disabled = false; // Enable the Start Capture button
    stopCaptureButton.style.display = 'none'; // Hide the Stop Capture button

    displayReferenceImage(false); // Stop displaying the reference image
    // Set the active container back to an empty string after resetting the capture
    activeContainer = "";

    setStatusMessage('Capture is idle.'); // Clear the status message
    isCaptureInProgress = false; // Reset the flag when capture is completed or stopped

    // Re-initialize the capture UI
    initializeCaptureUI();
}



function setStatusMessage(message) {
    var statusMessageElement = document.getElementById("gesture-status-message");
    statusMessageElement.textContent = message;
}

window.addEventListener('load', function () {
    initializeCaptureUI();
});
