"""
Video Processor Module

This module provides a class for processing video files into 2x2 grid images.
It extracts frames from a video at specified intervals and arranges them
into a 2x2 grid format for easier analysis and documentation generation.
"""

import cv2
import numpy as np
import os
import logging
import math

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    A class for processing video files into 2x2 grid images.

    This class takes a video file, extracts frames at specified intervals,
    and creates 2x2 grid images containing four frames for easier analysis.
    """

    def __init__(self, video_path, output_dir, frames_per_second=2):
        """
        Initialize the VideoProcessor with video path and processing parameters.

        Args:
            video_path (str): Path to the input video file.
            output_dir (str): Directory to save the processed grid images.
            frames_per_second (int): Frames per second to extract from the video (default: 2).
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.frames_per_second = frames_per_second
        self.grid_size = 2  # Fixed 2x2 grid
        logger.info(f"VideoProcessor initialized with video: {video_path}, fps: {frames_per_second}")

    def process_video(self):
        """
        Process the video file and create 2x2 grid images.

        This method extracts frames from the video at specified intervals,
        creates 2x2 grid images, and saves them to the output directory.

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

        video_fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Handle cases where video properties are not correctly read
        if video_fps <= 0 or total_frames <= 0:
            logger.warning("Invalid video properties detected. Using fallback values.")
            video_fps = 30  # Fallback to a common frame rate
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                # If we still can't get the frame count, we'll process the entire video
                total_frames = float('inf')

        video_duration = total_frames / video_fps if video_fps > 0 else 0
        frame_interval = max(1, round(video_fps / self.frames_per_second))

        logger.info(f"Video FPS: {video_fps}, Total frames: {total_frames}, "
                    f"Video duration: {video_duration:.2f}s, "
                    f"Frame interval: {frame_interval}")

        frames = []
        processed_grids = []
        frame_index = 0

        while frame_index < total_frames:
            ret, frame = cap.read()
            if not ret:
                logger.info(f"End of video reached at frame {frame_index}")
                break

            if frame_index % frame_interval == 0:
                frames.append(frame)
                logger.debug(f"Frame {frame_index} captured (Frame {len(frames)} in current grid)")

                if len(frames) == self.grid_size * self.grid_size:
                    grid_path = self._create_grid_image(frames, len(processed_grids) + 1)
                    processed_grids.append(grid_path)
                    frames = []  # Clear frames after creating a grid

            frame_index += 1

        # Process any remaining frames
        if frames:
            logger.info(f"Processing {len(frames)} remaining frames")
            while len(frames) < self.grid_size * self.grid_size:
                frames.append(np.zeros_like(frames[0]))
            grid_path = self._create_grid_image(frames, len(processed_grids) + 1)
            processed_grids.append(grid_path)

        cap.release()
        logger.info(f"Video processing completed. Generated {len(processed_grids)} grid images.")
        return processed_grids

    def _create_grid_image(self, frames, grid_number):
        """
        Create a 2x2 grid image from a list of frames.

        This method takes a list of four frames and arranges them into a 2x2 grid image.
        It also adds frame numbers to each cell in the grid.

        Args:
            frames (list): List of four frames to arrange into a grid.
            grid_number (int): The number of the current grid being created.

        Returns:
            str: Path to the saved grid image.
        """
        logger.info(f"Creating grid image {grid_number}")
        grid_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        frame_width = 500
        frame_height = 500

        for i, frame in enumerate(frames):
            x = (i % 2) * frame_width
            y = (i // 2) * frame_height
            resized_frame = cv2.resize(frame, (frame_width, frame_height))
            grid_image[y:y+frame_height, x:x+frame_width] = resized_frame

            # Add frame number
            cv2.putText(grid_image, str(i+1), (x+10, y+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        output_path = os.path.join(self.output_dir, f"grid_{grid_number}.jpg")
        cv2.imwrite(output_path, grid_image)
        logger.info(f"Grid image {grid_number} saved to {output_path}")
        return output_path

    def process_recorded_video(self):
        """Process video recorded from screen capture."""
        return self.process_video()

    def process_uploaded_video(self):
        """Process an uploaded video file."""
        # You might want to add specific processing for uploaded videos here
        # For now, we'll use the same process as recorded videos
        return self.process_video()