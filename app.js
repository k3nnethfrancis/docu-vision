/**
 * Screen Recording Documentation Generator
 * 
 * This script handles the client-side functionality for recording the screen,
 * processing the video, and generating documentation.
 */

let mediaRecorder;
let recordedChunks = [];
let videoBlob = null;
let isUploadedVideo = false;

document.getElementById('startRecording').addEventListener('click', startRecording);
document.getElementById('stopRecording').addEventListener('click', stopRecording);
document.getElementById('videoUpload').addEventListener('change', handleVideoUpload);
document.getElementById('processVideo').addEventListener('click', processVideo);
document.getElementById('generateDocumentation').addEventListener('click', generateDocumentation);

/**
 * Starts the screen recording process.
 * 
 * This function requests screen capture permission from the user,
 * sets up the MediaRecorder, and begins recording.
 */
async function startRecording() {
    console.log("startRecording function called");
    try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
        console.log("Display media stream obtained");
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
                console.log(`Chunk added. Total chunks: ${recordedChunks.length}, Chunk size: ${event.data.size} bytes`);
            }
        };

        mediaRecorder.onstart = () => {
            console.log("MediaRecorder started at", new Date().toISOString());
            recordedChunks = []; // Clear any previous recording
            isUploadedVideo = false;
        };

        mediaRecorder.onstop = () => {
            console.log("MediaRecorder stopped at", new Date().toISOString());
            videoBlob = new Blob(recordedChunks, { type: 'video/webm' });
            console.log(`Recording completed. Total size: ${videoBlob.size} bytes`);
            displayVideo(videoBlob, 'videoPreview');
            document.getElementById('processVideo').disabled = false;
        };

        mediaRecorder.start(1000); // Collect data every second
        document.getElementById('startRecording').disabled = true;
        document.getElementById('stopRecording').disabled = false;
        console.log("Recording started successfully");
    } catch (error) {
        console.error("Error starting recording:", error);
        alert("Error starting recording. Please make sure you've granted screen capture permissions.");
    }
}

/**
 * Stops the ongoing screen recording.
 * 
 * This function stops the MediaRecorder and enables the generate documentation button.
 */
function stopRecording() {
    console.log("stopRecording function called");
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        document.getElementById('startRecording').disabled = false;
        document.getElementById('stopRecording').disabled = true;
        console.log("Recording stopped. Total recorded chunks:", recordedChunks.length);
    } else {
        console.log("No active recording to stop");
    }
}

/**
 * Handles the video upload event.
 * 
 * @param {Event} event - The change event triggered by the file input.
 */
function handleVideoUpload(event) {
    const file = event.target.files[0];
    if (file) {
        console.log(`Video file uploaded: ${file.name}, Size: ${file.size} bytes`);
        videoBlob = file;
        isUploadedVideo = true;
        displayVideo(file, 'uploadedVideo');
        document.getElementById('processVideo').disabled = false;
    }
}

/**
 * Displays the video in the specified video element.
 * 
 * @param {Blob} videoFile - The video file to display.
 * @param {string} videoElementId - The ID of the video element.
 */
function displayVideo(videoFile, videoElementId) {
    const videoURL = URL.createObjectURL(videoFile);
    const videoElement = document.getElementById(videoElementId);
    videoElement.src = videoURL;
    videoElement.style.display = 'block';
    console.log(`Video displayed in ${videoElementId}`);
}

/**
 * Processes the video for documentation generation.
 * 
 * This function sends the video to the server for processing,
 * then displays the processed frames.
 */
async function processVideo() {
    console.log("processVideo function called");
    if (!videoBlob) {
        console.error("No video to process");
        alert("Please record or upload a video before processing.");
        return;
    }

    const formData = new FormData();
    formData.append('video', videoBlob, 'video.webm');
    const framesPerSecond = document.getElementById('framesPerSecond').value || 4;
    formData.append('frames_per_second', framesPerSecond);
    formData.append('is_uploaded_video', isUploadedVideo);

    console.log(`Processing video. Size: ${videoBlob.size} bytes, Frames per second: ${framesPerSecond}, Is uploaded: ${isUploadedVideo}`);

    try {
        console.log("Sending video to server for processing...");
        const response = await fetch('/process_video', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log("Received processed frames from server:", results);
        if (results.error) {
            throw new Error(results.error);
        }
        displayGrids(results);
        document.getElementById('generateDocumentation').disabled = false;
    } catch (error) {
        console.error('Error processing video:', error);
        alert('Error processing video. Please check the console for details.');
    }
}

/**
 * Displays the processed grids.
 * 
 * @param {Array} grids - An array of objects containing grid images.
 */
function displayGrids(grids) {
    const gridContainer = document.getElementById('gridContainer');
    gridContainer.innerHTML = '';
    grids.forEach((grid, index) => {
        const img = document.createElement('img');
        img.src = `data:image/jpeg;base64,${grid.image}`;
        img.alt = `Grid ${index + 1}`;
        img.className = 'grid-image';
        gridContainer.appendChild(img);
    });
    console.log(`Displayed ${grids.length} grid images`);
}

/**
 * Generates documentation based on the processed video.
 * 
 * This function sends a request to the server for documentation generation,
 * then displays the results.
 */
async function generateDocumentation() {
    console.log("generateDocumentation function called");
    try {
        const response = await fetch('/generate_documentation', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        console.log("Received documentation from server:", results);
        displayResults(results.grid_results);
        displayFinalSummary(results.final_summary);
    } catch (error) {
        console.error('Error generating documentation:', error);
        alert('Error generating documentation. Please check the console for details.');
    }
}

/**
 * Displays the results of the documentation generation.
 * 
 * @param {Array} results - An array of objects containing grid images and their documentation.
 */
function displayResults(results) {
    console.log("Displaying results:", results);
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = '';

    if (!Array.isArray(results) || results.length === 0) {
        resultsContainer.innerHTML = '<p>No results to display. Please try again.</p>';
        return;
    }

    results.forEach(result => {
        const gridContainer = document.createElement('div');
        gridContainer.className = 'grid-container';

        const image = document.createElement('img');
        image.src = `data:image/jpeg;base64,${result.image}`;
        image.alt = `Grid ${result.grid_number}`;
        image.className = 'grid-image';

        const documentation = document.createElement('p');
        documentation.textContent = result.documentation;

        gridContainer.appendChild(image);
        gridContainer.appendChild(documentation);
        resultsContainer.appendChild(gridContainer);
    });
}

function displayFinalSummary(summary) {
    console.log("Displaying final summary");
    const summaryContainer = document.getElementById('finalSummary');
    summaryContainer.innerHTML = '<h2>Final Process Summary</h2>';
    const summaryText = document.createElement('p');
    summaryText.textContent = summary;
    summaryContainer.appendChild(summaryText);
}

console.log("app.js loaded and initialized");