/**
 * Screen Recording Documentation Generator
 * 
 * This script handles the client-side functionality for recording the screen,
 * processing the video, and generating documentation.
 */

let mediaRecorder;
let recordedChunks = [];
let processedGrids = [];

document.addEventListener('DOMContentLoaded', function() {
    const videoFile = document.getElementById('videoFile');
    const processVideoButton = document.getElementById('processVideoButton');
    const framesPerSecondInput = document.getElementById('framesPerSecond');
    const startRecordingButton = document.getElementById('startRecording');
    const stopRecordingButton = document.getElementById('stopRecording');
    const generateDocumentationButton = document.getElementById('generateDocumentationButton');

    if (videoFile) {
        videoFile.addEventListener('change', handleVideoFileChange);
    }

    if (processVideoButton) {
        processVideoButton.addEventListener('click', processVideo);
    }

    if (framesPerSecondInput) {
        framesPerSecondInput.addEventListener('input', validateFramesPerSecond);
    }

    if (startRecordingButton) {
        startRecordingButton.addEventListener('click', startRecording);
    }

    if (stopRecordingButton) {
        stopRecordingButton.addEventListener('click', stopRecording);
    }

    if (generateDocumentationButton) {
        generateDocumentationButton.addEventListener('click', generateDocumentation);
    }
});

async function startRecording() {
    console.log('Start recording function called');
    try {
        const stream = await navigator.mediaDevices.getDisplayMedia({ video: { mediaSource: "screen" } });
        console.log('Display media obtained:', stream);
        
        // Use H264 codec for MP4 output
        const options = {mimeType: 'video/webm;codecs=h264'};
        mediaRecorder = new MediaRecorder(stream, options);
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
                console.log('Data chunk added, size:', event.data.size);
            }
        };

        mediaRecorder.onstop = handleRecordingStop;

        mediaRecorder.start();
        console.log('MediaRecorder started');
        document.getElementById('startRecording').disabled = true;
        document.getElementById('stopRecording').disabled = false;
    } catch (error) {
        console.error("Error starting recording:", error);
        alert("Error starting recording. Please make sure you've granted screen capture permissions and your browser supports H264 encoding.");
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        document.getElementById('startRecording').disabled = false;
        document.getElementById('stopRecording').disabled = true;
    }
}

function handleRecordingStop() {
    console.log('Recording stopped, chunks:', recordedChunks.length);
    const blob = new Blob(recordedChunks, { type: 'video/mp4' });
    console.log('Blob created, size:', blob.size, 'type:', blob.type);
    recordedChunks = [];
    displayRecordedVideo(blob);
}

function displayRecordedVideo(blob) {
    const videoURL = URL.createObjectURL(blob);
    const videoElement = document.createElement('video');
    videoElement.src = videoURL;
    videoElement.controls = true;
    videoElement.style.maxWidth = '100%';

    videoElement.onloadedmetadata = () => {
        console.log('Video metadata loaded:',
            'Duration:', videoElement.duration,
            'Width:', videoElement.videoWidth,
            'Height:', videoElement.videoHeight);
    };

    const videoPreview = document.getElementById('videoPreview');
    videoPreview.innerHTML = '';
    videoPreview.appendChild(videoElement);

    const uploadedVideoName = document.getElementById('uploadedVideoName');
    uploadedVideoName.textContent = 'Recorded Video: screen-recording.mp4';

    // Create a new File object
    const videoFile = new File([blob], 'screen-recording.mp4', { type: 'video/mp4' });
    console.log('File created:', videoFile.name, 'size:', videoFile.size, 'type:', videoFile.type);

    // Create a new FileList containing this File
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(videoFile);

    // Set the files property of the input element
    document.getElementById('videoFile').files = dataTransfer.files;
}

function handleVideoFileChange(event) {
    const file = event.target.files[0];
    if (file) {
        const uploadedVideoName = document.getElementById('uploadedVideoName');
        uploadedVideoName.textContent = `Uploaded Video: ${file.name}`;
        previewVideo(file);
    }
}

function previewVideo(file) {
    const videoPreview = document.getElementById('videoPreview');
    if (videoPreview) {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.controls = true;
        video.style.maxWidth = '100%';
        videoPreview.innerHTML = '';
        videoPreview.appendChild(video);
    } else {
        console.error('Video preview container not found');
    }
}

function processVideo() {
    const videoFile = document.getElementById('videoFile').files[0];
    const framesPerSecond = document.getElementById('framesPerSecond').value;
    const formData = new FormData();

    if (videoFile) {
        formData.append('video', videoFile);
    } else {
        const blob = new Blob(recordedChunks, { type: 'video/mp4' });
        formData.append('video', blob, 'screen-recording.mp4');
    }

    formData.append('frames_per_second', framesPerSecond);

    fetch('/process_video', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            displayProcessedFrames(data.frames);
            alert(`Video processed successfully. Created ${data.video_info.grids_created} grid images from ${data.video_info.extracted_frames} frames.`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while processing the video.');
    });
}

function displayProcessedFrames(frames) {
    const gridContainer = document.getElementById('gridContainer');
    gridContainer.innerHTML = '';
    frames.forEach((frame, index) => {
        const frameElement = document.createElement('div');
        frameElement.className = 'frame-item';
        frameElement.innerHTML = `
            <img src="data:image/jpeg;base64,${frame.image}" alt="Frame ${frame.frame_number}" class="img-fluid">
            <p class="mt-2">Frame ${frame.frame_number}</p>
        `;
        gridContainer.appendChild(frameElement);
    });
}

function generateDocumentation() {
    const documentationOutput = document.getElementById('documentationOutput');
    const downloadButton = document.getElementById('downloadButton');
    
    documentationOutput.innerHTML = 'Generating documentation...';
    downloadButton.style.display = 'none';
    
    fetch('/generate_documentation', {
        method: 'POST',
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        } else {
            documentationOutput.innerHTML = marked.parse(data.documentation);
            downloadButton.style.display = 'inline-block';
            downloadButton.onclick = () => downloadMarkdown(data.documentation);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        documentationOutput.innerHTML = `An error occurred while generating documentation: ${error.message}`;
    });
}

function downloadMarkdown(content) {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'README.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function validateFramesPerSecond() {
    const framesPerSecond = document.getElementById('framesPerSecond');
    if (framesPerSecond) {
        const value = parseInt(framesPerSecond.value);
        if (isNaN(value) || value < 1 || value > 30) {
            framesPerSecond.setCustomValidity('Please enter a number between 1 and 30');
        } else {
            framesPerSecond.setCustomValidity('');
        }
    }
}

console.log("app.js loaded and initialized");