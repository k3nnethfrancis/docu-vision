"""
Server module for the Screen Recording Documentation Generator.

This module sets up a Flask server that handles video processing and documentation generation
for screen recordings. It interfaces with the VideoProcessor and DocsGenerator classes to
process uploaded videos and generate documentation based on the processed frames.
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import logging
from video_processor import VideoProcessor
from docs_generator import DocsGenerator
import base64

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

root_dir = os.path.dirname(os.path.abspath(__file__))
docs_generator = DocsGenerator(model_type='openai')
processed_grids = []

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/app.js')
def serve_js():
    return send_from_directory('.', 'app.js')

@app.route('/process_video', methods=['POST'])
def process_video():
    global processed_grids
    logger.info("Received /process_video POST request")
    try:
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file uploaded"}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            logger.error("No selected video file")
            return jsonify({"error": "No selected video file"}), 400

        frames_per_second = int(request.form.get('frames_per_second', 4))
        is_uploaded_video = request.form.get('is_uploaded_video', 'false').lower() == 'true'
        logger.info(f"Processing video with {frames_per_second} frames per second. Uploaded video: {is_uploaded_video}")

        video_path = os.path.join(root_dir, 'uploads', 'video.webm')
        video_file.save(video_path)
        logger.info(f"Video saved to {video_path}")

        output_dir = os.path.join(root_dir, 'processed_frames')
        os.makedirs(output_dir, exist_ok=True)

        video_processor = VideoProcessor(video_path, output_dir, frames_per_second=frames_per_second)
        
        grid_paths = video_processor.process_video()
        
        logger.info(f"Created {len(grid_paths)} grid images")

        processed_grids = []
        for i, grid_path in enumerate(grid_paths):
            with open(grid_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            processed_grids.append({
                'grid_number': i + 1,
                'image': encoded_image
            })

        logger.info(f"Processed {len(processed_grids)} grids successfully")
        return jsonify(processed_grids)

    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/generate_documentation', methods=['POST'])
def generate_documentation():
    global processed_grids
    logger.info("Received /generate_documentation POST request")
    try:
        results = []
        all_descriptions = []
        for grid in processed_grids:
            documentation = docs_generator.generate_documentation(f"processed_frames/grid_{grid['grid_number']}.jpg", grid['grid_number'])
            results.append({
                'grid_number': grid['grid_number'],
                'documentation': documentation,
                'image': grid['image']
            })
            all_descriptions.append(f"Grid {grid['grid_number']}: {documentation}")

        logger.info(f"Generated documentation for {len(results)} grids successfully")

        # Generate final summary
        final_summary = docs_generator.generate_final_summary(all_descriptions)
        logger.info("Generated final summary successfully")

        return jsonify({
            'grid_results': results,
            'final_summary': final_summary
        })

    except Exception as e:
        logger.error(f"Error in generate_documentation: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask server")
    app.run(debug=True, host='localhost', port=5555)