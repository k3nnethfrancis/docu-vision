/**
 * Screen Recording Documentation Generator
 * 
 * This script handles the client-side functionality for recording the screen,
 * processing the video, and generating documentation.
 */

let mediaRecorder;
let recordedChunks = [];

console.log("app.js loaded and initialized");

// Event listeners for UI buttons
document.getElementById('startRecording').addEventListener('click', startRecording);
document.getElementById('stopRecording').addEventListener('click', stopRecording);
document.getElementById('generateDocumentation').addEventListener('click', generateDocumentation);

/**
 * Starts the screen recording process.
 * 
 * This function requests screen capture permission from the user,
 * sets up the MediaRecorder, and begins recording.
 */
async function startRecording() {
    console.log("Starting recording...");
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
        };

        mediaRecorder.onstop = () => {
            console.log("MediaRecorder stopped at", new Date().toISOString());
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
    console.log("Stopping recording...");
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        document.getElementById('startRecording').disabled = false;
        document.getElementById('stopRecording').disabled = true;
        document.getElementById('generateDocumentation').disabled = false;
        console.log("Recording stopped successfully");
    } else {
        console.log("No active recording to stop");
    }
}

/**
 * Generates documentation based on the recorded video.
 * 
 * This function sends the recorded video to the server for processing,
 * then requests documentation generation for each processed frame grid.
 */
async function generateDocumentation() {
    console.log("Starting documentation generation process...");
    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<h2>Processing Video and Generating Documentation...</h2>';

    try {
        // Create video blob from recorded chunks
        console.log("Creating video blob...");
        const blob = new Blob(recordedChunks, { type: 'video/webm' });
        console.log(`Video blob created. Size: ${blob.size} bytes`);

        // Send video to server for processing
        console.log("Sending video to server for processing...");
        const formData = new FormData();
        formData.append('video', blob, 'screen_recording.webm');

        const processResponse = await fetch('/process_video', {
            method: 'POST',
            body: formData
        });

        if (!processResponse.ok) {
            throw new Error(`HTTP error! status: ${processResponse.status}`);
        }

        const processResult = await processResponse.json();
        console.log("Video processing result:", processResult);

        // Fetch processed frames
        console.log("Fetching processed frames...");
        const gridImagesResponse = await fetch('/processed_frames');
        const gridImages = await gridImagesResponse.json();
        console.log(`Received ${gridImages.length} processed frames`);

        // Generate documentation for each frame grid
        for (let i = 0; i < gridImages.length; i++) {
            console.log(`Generating documentation for grid ${i + 1}...`);
            const docResponse = await fetch('/generate_docs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_path: gridImages[i],
                    grid_index: i + 1
                }),
            });

            if (!docResponse.ok) {
                throw new Error(`HTTP error! status: ${docResponse.status}`);
            }

            const docResult = await docResponse.json();
            console.log(`Received documentation for grid ${i + 1}`);
            resultDiv.innerHTML += `<h3>Grid ${i + 1} Documentation:</h3><p>${docResult.documentation}</p>`;
        }
        console.log("Documentation generation process completed");
    } catch (error) {
        console.error("Error processing video and generating documentation:", error);
        resultDiv.innerHTML += '<p>An error occurred while processing the video and generating documentation.</p>';
    }
}

console.log("app.js loaded and initialized");