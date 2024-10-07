"""
Video Processor Module

This module provides a VideoProcessor class for processing video files into grid images.
It extracts frames from a video at specified intervals and arranges them into a grid format
for easier analysis and documentation generation.

The main features of this module include:
1. Extracting frames from a video at a specified frame rate
2. Arranging extracted frames into grid images
3. Resizing frames to fit within a specified maximum grid width
4. Saving grid images to disk

Usage:
    processor = VideoProcessor(video_path, output_dir)
    processor.set_frames_per_second(4)
    grid_paths, video_info = processor.process_video()
"""

import cv2
import os
import logging
import numpy as np
from PIL import Image
import subprocess
from math import ceil

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, video_path, output_dir, frames_per_second, grid_size=(2, 2), max_grid_width=800):
        """
        Initialize the VideoProcessor.

        Args:
            video_path (str): Path to the input video file.
            output_dir (str): Directory to save processed frames and grids.
            frames_per_second (int): Frames per second to extract from the video.
            grid_size (tuple): Size of the grid for frame arrangement (default: (2, 2)).
            max_grid_width (int): Maximum width of each grid image in pixels (default: 800).
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.frames_per_second = frames_per_second
        self.grid_size = grid_size
        self.max_grid_width = max_grid_width

    def set_frames_per_second(self, fps):
        """
        Set the number of frames to extract per second.

        Args:
            fps (int): Frames per second to extract from the video.
        """
        self.frames_per_second = fps
 
    def extract_frames(self):
        frames_dir = os.path.join(self.output_dir, 'temp_frames')
        os.makedirs(frames_dir, exist_ok=True)
        
        command = [
            'ffmpeg',
            '-i', self.video_path,
            '-vf', f'fps={self.frames_per_second}',
            '-q:v', '2',  # High quality
            f'{frames_dir}/frame_%04d.jpg'
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Frames extracted successfully to {frames_dir}")
            return frames_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting frames: {e.stderr}")
            raise

    def process_video(self):
        """
        Process the video: extract frames, create grids, and save them.

        This method performs the following steps:
        1. Extracts frames at the specified interval using FFmpeg
        2. Reads the extracted frames using OpenCV
        3. Creates grid images from the extracted frames
        4. Calculates video information using FFprobe for accurate duration
        5. Saves the grid images to disk

        Returns:
            tuple: (grid_paths, video_info)
                grid_paths (list): List of paths to saved grid images.
                video_info (dict): Dictionary containing video information:
                    - total_frames: Total number of frames in the original video
                    - original_fps: Original frames per second of the video
                    - duration: Duration of the video in seconds
                    - extracted_frames: Number of frames extracted
                    - grids_created: Number of grid images created
                    - processed_fps: Frames per second used for processing
        """
        try:
            frames_dir = self.extract_frames()
            frame_files = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
            
            extracted_frames = []
            for frame_file in frame_files:
                frame_path = os.path.join(frames_dir, frame_file)
                frame = cv2.imread(frame_path)
                if frame is not None:
                    extracted_frames.append(frame)
                else:
                    logger.warning(f"Failed to read frame: {frame_path}")

            logger.info(f"Extracted {len(extracted_frames)} frames")

            grid_images = self.create_grid_images(extracted_frames)

            # Calculate duration based on extracted frames and FPS
            duration = len(extracted_frames) / self.frames_per_second

            video_info = {
                'total_frames': len(extracted_frames),
                'original_fps': self.frames_per_second,
                'duration': duration,
                'extracted_frames': len(extracted_frames),
                'grids_created': len(grid_images),
                'processed_fps': self.frames_per_second
            }

            logger.info(f"Video processing complete. Created {len(grid_images)} grid images.")
            
            # Clean up temporary files
            for frame_file in frame_files:
                os.remove(os.path.join(frames_dir, frame_file))
            os.rmdir(frames_dir)
            
            return grid_images, video_info

        except Exception as e:
            logger.exception("An error occurred during video processing")
            raise

    def create_grid_images(self, frames):
        """
        Create grid images from extracted frames.

        This method performs the following steps:
        1. Calculates the number of grids needed based on the number of frames
        2. Resizes frames to fit within the specified maximum grid width
        3. Creates grid images by arranging resized frames
        4. Saves each grid image to disk

        Args:
            frames (list): List of extracted frames as numpy arrays.

        Returns:
            list: Paths to saved grid images.
        """
        grid_images = []
        frames_per_grid = self.grid_size[0] * self.grid_size[1]
        
        # Find the target aspect ratio (use the most common aspect ratio)
        aspect_ratios = [frame.shape[1] / frame.shape[0] for frame in frames]
        target_aspect_ratio = max(set(aspect_ratios), key=aspect_ratios.count)
        
        # Pad all frames to the target aspect ratio
        padded_frames = [self.pad_image(frame, target_aspect_ratio) for frame in frames]
        
        # Find the most common frame size after padding
        heights, widths = zip(*[frame.shape[:2] for frame in padded_frames])
        common_height = max(set(heights), key=heights.count)
        common_width = max(set(widths), key=widths.count)
        
        # Resize all frames to the common size
        resized_frames = [cv2.resize(frame, (common_width, common_height)) for frame in padded_frames]
        
        for i in range(0, len(resized_frames), frames_per_grid):
            grid_frames = resized_frames[i:i+frames_per_grid]
            if len(grid_frames) < frames_per_grid:
                blank_frame = np.zeros((common_height, common_width, 3), dtype=np.uint8)
                grid_frames.extend([blank_frame] * (frames_per_grid - len(grid_frames)))
            
            rows = []
            for j in range(0, frames_per_grid, self.grid_size[1]):
                row = np.hstack(grid_frames[j:j+self.grid_size[1]])
                rows.append(row)
            grid = np.vstack(rows)
            
            if grid.shape[1] > self.max_grid_width:
                scale_factor = self.max_grid_width / grid.shape[1]
                new_height = int(grid.shape[0] * scale_factor)
                grid = cv2.resize(grid, (self.max_grid_width, new_height))
            
            grid_images.append(grid)

        return grid_images

    def pad_image(self, image, target_aspect_ratio):
        height, width = image.shape[:2]
        current_aspect_ratio = width / height
        
        if current_aspect_ratio > target_aspect_ratio:
            # Pad height
            new_height = int(width / target_aspect_ratio)
            pad_top = (new_height - height) // 2
            pad_bottom = new_height - height - pad_top
            padded_image = cv2.copyMakeBorder(image, pad_top, pad_bottom, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        else:
            # Pad width
            new_width = int(height * target_aspect_ratio)
            pad_left = (new_width - width) // 2
            pad_right = new_width - width - pad_left
            padded_image = cv2.copyMakeBorder(image, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
        
        return padded_image