document.addEventListener('DOMContentLoaded', () => {


  // const videoStream = document.getElementById('video-stream');
  const recognitionVideoPlaceholder = document.getElementById('recognition-video-placeholder');
  const recognitionVideoCustomContainer = document.getElementById('recognition-video-custom-container');
  const selectModel = document.getElementById('scan-model-select');
  const startButton = document.getElementById('scan-model-confirm-button');
  const stopButton = document.getElementById('scan-model-stop-button');
  const saveButton = document.getElementById('save-button');
  const readButton = document.getElementById('read-button');
  const statusText = document.getElementById('status-text');
  const canvas = document.getElementById('canvas');
  const context = canvas.getContext('2d');
  const processedFrameImg = document.getElementById('processed-frame-img');
  const recognizedSignsTextarea = document.getElementById('recognized-signs-textarea');
  const sentenceTextarea = document.getElementById('sentence-textarea');
  let isProcessing = false;
  let webcamStream = null;
  // Define a variable to hold the interval ID
  let recognitionInterval;

    // Set the initial status on page load
  statusText.textContent = "Recognition Status Idle";

  // Function to start webcam processing
  function startWebcamProcessing(selectedModel) {
    isProcessing = true;

    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        webcamStream = stream;
        const webcam = document.createElement('video');
        webcam.srcObject = webcamStream;
        webcam.play();

        const sendFrameInterval = setInterval(() => {
          if (!isProcessing) {
            clearInterval(sendFrameInterval);
            return;
          }

          context.drawImage(webcam, 0, 0, canvas.width, canvas.height);
          const frameData = canvas.toDataURL('image/jpeg', 0.5);

          // Emit the frame data to the server
          socket.emit('send_frame', { frameData, selectedModel });
        }, 100);
      })
      .catch(error => {
        console.error('Error accessing webcam:', error);
        stopWebcamProcessing(); // Call the function to stop webcam processing
      });
  }

  // Function to stop webcam processing
  function stopWebcamProcessing() {
    isProcessing = false;

    if (webcamStream) {
      webcamStream.getTracks().forEach(track => track.stop());
      webcamStream = null;
    }
    context.clearRect(0, 0, canvas.width, canvas.height);
  }


  // Listen for the "Start" button click
  startButton.addEventListener('click', () => {
    // Get the selected model from the dropdown
    const selectedModel = selectModel.value;
    if (!isProcessing) {
      // Enable the "Stop" button
      stopButton.disabled = false;

      // Clear the interval if it was previously set
      clearInterval(recognitionInterval);

      startWebcamProcessing(selectedModel); // Pass the selectedModel as a parameter
      // Hide the placeholder and show the custom container
      recognitionVideoPlaceholder.style.display = 'none';
      recognitionVideoCustomContainer.style.display = 'block';

      // Start sending recognition status requests every 5 seconds
      recognitionInterval = setInterval(function () {
        console.log("Sending recognition_status_request to Client");
        // Emit an event to request recognition status and ordered sign from the server
        socket.emit('recognition_status_request', { selectedModel: selectedModel });
      }, 5000); // Interval in milliseconds
    }
  });


  // Listen for the "Stop" button click
  stopButton.addEventListener('click', () => {
    if (isProcessing) {
      // Clear the interval and reset the variable
      clearInterval(recognitionInterval);
      recognitionInterval = null;
      console.log("Sending Stop Signal to Client");
      // Send the "stop_processing" event to the server
      socket.emit('stop_processing');
      stopWebcamProcessing(); // Call the function to stop webcam processing
      // Hide the custom container and show the placeholder
      recognitionVideoCustomContainer.style.display = 'none';
      recognitionVideoPlaceholder.style.display = 'block';

      // Clear the sentenceArray
      sentenceArray.length = 0;

      // Clear the textarea and disable buttons
      sentenceTextarea.value = "";
      recognizedSignsTextarea.value = "";
      saveButton.disabled = true;
      readButton.disabled = true;

      // Delay updating the status text to "Recognition Status Idle" after 3 seconds
      setTimeout(() => {
        statusText.textContent = "Recognition Status Idle";
      }, 3000);
    }
  });


  
  // Listen for the "processed_data" event from the server
  socket.on('processed_frame_data', processed_frame_data => {
    // console.log("Received Processed Data");
    console.log("Received Processed Data:", processed_frame_data);

    const frameData = processed_frame_data; // Updated property name

    // console.log("Frame Data:", frameData);

    processedFrameImg.onload = () => {
      // console.log("Processed frame image loaded");
      // Clear the canvas
      context.clearRect(0, 0, canvas.width, canvas.height);

      // Draw the loaded image on the canvas
      context.drawImage(processedFrameImg, 0, 0, canvas.width, canvas.height);
      // console.log("Loaded Image Dimensions:", processedFrameImg.width, processedFrameImg.height);
    };
    // console.log("Frame Data URL:", frameData);
    processedFrameImg.src = frameData;
  });

  const sentenceArray = []; // Array to store words for building the sentence

  // Listen for the "recognition_status" event from the server
  socket.on('recognition_status', data => {
    console.log("recognition_status:", data);

    const status = data.status; // Use the correct property name 'status'
    const ordered_sign = data.ordered_sign; // Use the correct property name 'ordered_sign'

    console.log("status:", status);
    console.log("ordered_sign:", ordered_sign);

    // Update status text
    statusText.textContent = status;
    recognizedSignsTextarea.value = ordered_sign;

    if (ordered_sign) {
      // Check if ordered_sign is 's' or 'space'
      if (ordered_sign === 's' || ordered_sign === 'space') {
        sentenceArray.push(' '); // Add space to the sentence
      } else {
        sentenceArray.push(ordered_sign); // Add ordered_sign to the sentence
      }

      // Build the sentence by joining the sentenceArray
      const sentence = sentenceArray.join('');

      // Display the sentence in recognizedSignsTextarea
      sentenceTextarea.value = sentence;

      // Enable the "Read" and "Save" buttons if the sentenceArray has at least one entry
      if (sentenceArray.length > 0) {
        readButton.disabled = false;
        saveButton.disabled = false;
      }

      // Delay updating the status text to "Recognition Status Idle" after 3 seconds
      setTimeout(() => {
        recognizedSignsTextarea.value = "";
      }, 500);
    }
  });



  // Function to read the sentence aloud using the Web Speech API
  function readSentenceAloud() {
    const sentence = document.getElementById('sentence-textarea').value.trim();
    if (sentence.length > 0) {
      // Specify the voice and other options (check the ResponsiveVoice documentation for more options)
      const voiceOptions = {
        pitch: 1,    // Pitch (0 to 2)
        rate: 1,     // Speed (0.1 to 10)
        volume: 1,   // Volume (0 to 1)
        lang: 'en-GB' // Language code for English (United Kingdom)
      };

      // Set the default voice to "UK English Male"
      responsiveVoice.setDefaultVoice('UK English Male');

      // Use ResponsiveVoice to read the sentence aloud
      responsiveVoice.speak(sentence, 'UK English Male', voiceOptions);
    }
  }



  // Event listener for the "Save" button
  saveButton.addEventListener('click', () => {
    const sentence = sentenceTextarea.value.trim();
    if (sentence.length > 0) {
      // Generate the filename with the timestamp
      const timestamp = new Date().toISOString().replace(/:/g, '-');
      const filename = `recognized_sentence_${timestamp}.txt`;
      const fileContent = sentence;

      // Create a Blob object from the content
      const blob = new Blob([fileContent], { type: 'text/plain' });

      // Create a URL for the Blob
      const url = URL.createObjectURL(blob);

      // Create a temporary link element and trigger the download
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();

      // Revoke the URL after the download is initiated
      URL.revokeObjectURL(url);

    }
  });

  // Event listener for the "Read" button
  readButton.addEventListener('click', () => {
    readSentenceAloud();
  });


});