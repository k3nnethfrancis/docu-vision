"""
Server module for the Screen Recording Documentation Generator.

This module sets up a Flask server that handles video processing and documentation generation
for screen recordings. It interfaces with the VideoProcessor and DocsGenerator classes to
process uploaded videos and generate documentation based on the processed frames.
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import logging
import time
from video_processor import VideoProcessor
from docs_generator import DocsGenerator
from transformers import MllamaForConditionalGeneration, AutoProcessor

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Set up paths
root_dir = os.path.dirname(os.path.abspath(__file__))
logger.info(f"Root directory: {root_dir}")

# Initialize AI model
model_id = "meta-llama/Llama-3.2-11B-Vision-Instruct"
model_path = os.path.join(root_dir, 'weights', model_id)
docs_generator = DocsGenerator(model_path)

@app.route('/')
def index():
    """Serve the main HTML page."""
    logger.info("Serving index.html")
    return send_from_directory('.', 'index.html')

@app.route('/app.js')
def serve_js():
    """Serve the JavaScript file."""
    logger.info("Serving app.js")
    return send_from_directory('.', 'app.js')

@app.route('/process_video', methods=['POST'])
def process_video():
    """
    Process the uploaded video.
    
    This function receives a video file, saves it, and then processes it using
    the VideoProcessor class to generate frame grids.
    """
    logger.info("Received /process_video POST request")
    try:
        video_file = request.files['video']
        video_path = os.path.join(root_dir, 'uploads', video_file.filename)
        video_file.save(video_path)
        logger.info(f"Video saved to {video_path}")

        output_dir = os.path.join(root_dir, 'processed_frames')
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Starting video processing...")
        video_processor = VideoProcessor(video_path, output_dir)
        processed_frames = video_processor.process_video()
        logger.info(f"Video processing completed. Generated {len(processed_frames)} frame grids.")

        return jsonify({"message": "Video processed successfully", "frames": processed_frames})
    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/generate_docs', methods=['POST'])
def generate_docs():
    """
    Generate documentation for a processed frame grid.
    
    This function receives information about a processed frame grid, loads the
    corresponding image, and uses the DocsGenerator to create documentation.
    """
    logger.info("Received /generate_docs POST request")
    try:
        request_data = request.json
        logger.info(f"Received request data: {request_data}")
        
        image_filename = request_data['image_path']
        grid_index = request_data['grid_index']
        
        # Construct the full path to the image
        image_path = os.path.join(root_dir, 'processed_frames', image_filename)
        logger.info(f"Constructed image path: {image_path}")
        
        logger.info(f"Generating documentation for grid {grid_index}...")
        documentation = docs_generator.generate_documentation(image_path, grid_index)
        logger.info(f"Documentation generated for grid {grid_index}")

        return jsonify({"documentation": documentation})
    except Exception as e:
        logger.error(f"Error in generate_docs: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/processed_frames')
def get_processed_frames():
    """
    Retrieve a list of processed frame grids.
    
    This function returns a list of filenames for all processed frame grids.
    """
    logger.info("Received request for processed frames")
    output_dir = os.path.join(root_dir, 'processed_frames')
    frames = [f for f in os.listdir(output_dir) if f.endswith('.jpg')]
    frames.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    return jsonify(frames)

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(debug=True, host='localhost', port=5555)