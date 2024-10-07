"""
Server module for the Screen Recording Documentation Generator.

This module sets up a Flask server that handles video processing and documentation generation
for screen recordings. It interfaces with the VideoProcessor and DocsGenerator classes to
process uploaded videos and generate documentation based on the processed frames.
"""

from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import logging
from video_processor import VideoProcessor
from docs_generator import DocsGenerator
import base64
import cv2

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Create a temporary upload folder
UPLOAD_FOLDER = os.path.join(current_dir, 'temp_uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask app
app = Flask(__name__, static_folder=current_dir, template_folder=current_dir)

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get the directory of the current file (server.py)
root_dir = os.path.dirname(os.path.abspath(__file__))
docs_generator = DocsGenerator(model_type='openai')
processed_grids = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/app.js')
def serve_js():
    return send_from_directory(current_dir, 'app.js')

@app.route('/process_video', methods=['POST'])
def process_video():
    global processed_grids
    try:
        logger.info("Received /process_video POST request")
        video = request.files.get('video')
        frames_per_second = int(request.form.get('frames_per_second', 4))
        
        if not video:
            return jsonify({"error": "No video file provided"}), 400
        
        logger.info(f"Processing video with {frames_per_second} frames per second.")
        logger.info(f"Received file: name={video.filename}, content_type={video.content_type}, size={video.content_length}")
        
        # Save the uploaded video temporarily
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_video.mp4')
        video.save(video_path)
        logger.info(f"Video saved to {video_path}") 
        
        # Log file information
        file_size = os.path.getsize(video_path)
        logger.info(f"Saved file size: {file_size} bytes")
        
        # Process the video
        video_processor = VideoProcessor(video_path, app.config['UPLOAD_FOLDER'], frames_per_second)
        grid_images, video_info = video_processor.process_video()
        
        if not grid_images:
            return jsonify({"error": "No frames could be extracted from the video"}), 400

        # Convert grid images to base64 for sending to client
        processed_frames = []
        for i, grid_image in enumerate(grid_images):
            _, buffer = cv2.imencode('.jpg', grid_image)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            processed_frames.append({
                'frame_number': i + 1,
                'image': jpg_as_text
            })
        
        processed_grids = processed_frames
        
        # Clean up temporary files
        os.remove(video_path)
        
        logger.info(f"Processed {len(processed_frames)} grids. Video info: {video_info}")
        return jsonify({"frames": processed_frames, "video_info": video_info})

    except Exception as e:
        logger.exception("An error occurred while processing the video")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_documentation', methods=['POST'])
def generate_documentation():
    try:
        global processed_grids
        
        if not processed_grids:
            logger.warning("No processed video frames available.")
            return jsonify({'error': 'No processed video frames available. Please process a video first.'}), 400
        
        docs_generator = DocsGenerator(model_type='openai')
        
        all_descriptions = []
        for i, grid_data in enumerate(processed_grids):
            image_bytes = base64.b64decode(grid_data['image'])
            description = docs_generator.generate_documentation(image_bytes, i+1)
            all_descriptions.append(description)
        
        final_summary = docs_generator.generate_final_summary(all_descriptions)
        
        return jsonify({'documentation': final_summary})
    
    except Exception as e:
        logger.exception("An error occurred while generating documentation")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)