"""
Video Processor Module

This module provides a class for processing video files into grid images.
It extracts frames from a video at specified intervals and arranges them
into a grid format for easier analysis and documentation generation.
"""

import cv2
import numpy as np
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    A class for processing video files into grid images.

    This class takes a video file, extracts frames at specified intervals,
    and creates grid images containing multiple frames for easier analysis.
    """

    def __init__(self, video_path, output_dir, fps=20, grid_size=10):
        """
        Initialize the VideoProcessor with video path and processing parameters.

        Args:
            video_path (str): Path to the input video file.
            output_dir (str): Directory to save the processed grid images.
            fps (int): Frames per second to extract from the video (default: 20).
            grid_size (int): Size of the grid (e.g., 10 for a 10x10 grid) (default: 10).
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.fps = fps
        self.grid_size = grid_size
        logger.info(f"VideoProcessor initialized with video: {video_path}, fps: {fps}, grid_size: {grid_size}x{grid_size}")

    def process_video(self):
        """
        Process the video file and create grid images.

        This method extracts frames from the video at specified intervals,
        creates grid images, and saves them to the output directory.

        Returns:
            list: A list of paths to the created grid images.

        Raises:
            RuntimeError: If there's an error opening the video file.
        """
        logger.info(f"Starting video processing for {self.video_path}")
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error("Error opening video file")
            raise RuntimeError("Could not open video file")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = frame_count // self.fps
        logger.info(f"Total frames to process: {total_frames}")

        frames = []
        processed_grids = []
        frame_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % self.fps == 0:
                frames.append(frame)
                logger.debug(f"Frame {len(frames)} captured")

            if len(frames) == self.grid_size * self.grid_size:
                grid_path = self._create_grid_image(frames, len(processed_grids) + 1)
                processed_grids.append(grid_path)
                frames = []

            frame_index += 1

        if frames:  # Process any remaining frames
            grid_path = self._create_grid_image(frames, len(processed_grids) + 1)
            processed_grids.append(grid_path)

        cap.release()
        logger.info(f"Video processing completed. Generated {len(processed_grids)} grid images.")
        return processed_grids

    def _create_grid_image(self, frames, grid_number):
        """
        Create a grid image from a list of frames.

        This method takes a list of frames and arranges them into a grid image.
        It also adds frame numbers to each cell in the grid.

        Args:
            frames (list): List of frames to arrange into a grid.
            grid_number (int): The number of the current grid being created.

        Returns:
            str: Path to the saved grid image.
        """
        logger.info(f"Creating grid image {grid_number}")
        grid_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        frame_width = 1000 // self.grid_size
        frame_height = 1000 // self.grid_size

        for i, frame in enumerate(frames):
            x = (i % self.grid_size) * frame_width
            y = (i // self.grid_size) * frame_height
            resized_frame = cv2.resize(frame, (frame_width, frame_height))
            grid_image[y:y+frame_height, x:x+frame_width] = resized_frame

            # Add frame number
            cv2.putText(grid_image, str(i+1), (x+5, y+15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        output_path = os.path.join(self.output_dir, f"grid_{grid_number}.jpg")
        cv2.imwrite(output_path, grid_image)
        logger.info(f"Grid image {grid_number} saved to {output_path}")
        return output_path
