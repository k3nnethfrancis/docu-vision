# Screen Recording Documentation Generator

## Overview

The Screen Recording Documentation Generator is a web-based application that allows users to record their screen, process the recording, and automatically generate detailed documentation of the recorded process. This tool is particularly useful for creating step-by-step guides, tutorials, or documenting complex workflows.

## Features

- Screen recording functionality
- Automatic video processing and frame extraction
- AI-powered documentation generation
- User-friendly web interface

### To Do
- Quantize the model weights
- Find optimal frame selection and grid size
- Develop automated stream of video chunks to model for continuous documentation generation
- Improve UI

## System Requirements

- Python 3.7+
- Node.js and npm
- Modern web browser with screen capture capabilities

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/k3nnethfrance/docu-vision.git
   cd docu-vision
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Download the AI model weights:
   ```
   python download_model.py
   ```

## Usage

1. Start the Flask server:
   ```
   python server.py
   ```

2. Open a web browser and navigate to `http://localhost:5000/`

3. Use the web interface to:
   - Start and stop screen recording
   - Generate documentation from the recorded video

## How It Works

1. **Screen Recording**: The application uses the browser's `MediaRecorder` API to capture the user's screen.

2. **Video Processing**: The recorded video is sent to the server, where it's processed using OpenCV. The video is divided into frames, and these frames are arranged into grid images for easier analysis.

3. **Documentation Generation**: The processed grid images are fed into an AI model (Llama-3.2-11B-Vision-Instruct) which generates detailed descriptions of the actions and processes shown in the frames.

4. **Result Display**: The generated documentation is sent back to the client and displayed on the web page.

## Project Structure

- `server.py`: Flask server handling API requests and coordinating video processing and documentation generation.
- `video_processor.py`: Handles video frame extraction and grid image creation.
- `docs_generator.py`: Interfaces with the AI model to generate documentation from grid images.
- `app.js`: Client-side JavaScript for handling user interactions and communication with the server.
- `index.html`: Main web interface.

## API Endpoints

- `POST /process_video`: Accepts a video file and returns processed frame information.
- `POST /generate_docs`: Accepts a frame grid image and returns generated documentation.
- `GET /processed_frames`: Returns a list of processed frame grid images.

## Troubleshooting

- Ensure you have granted necessary screen capture permissions in your browser.
- Check the browser console and server logs for detailed error messages.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.