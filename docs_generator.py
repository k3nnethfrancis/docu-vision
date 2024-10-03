"""
Documentation Generator Module

This module provides a class for generating documentation from images using a pre-trained
vision-language model. It uses the MllamaForConditionalGeneration model and AutoProcessor
from the transformers library to analyze images and generate textual descriptions.
"""

from transformers import MllamaForConditionalGeneration, AutoProcessor
import torch
from PIL import Image
import logging
import time
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DocsGenerator:
    """
    A class for generating documentation from images using a vision-language model.

    This class initializes the model and processor, and provides a method to generate
    documentation for a given image.
    """

    def __init__(self, model_path):
        """
        Initialize the DocsGenerator with a pre-trained model.

        Args:
            model_path (str): Path to the pre-trained model weights.
        """
        logger.info(f"Initializing DocsGenerator with model path: {model_path}")
        start_time = time.time()
        self.model = MllamaForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.processor = AutoProcessor.from_pretrained(model_path)
        end_time = time.time()
        logger.info(f"Model and processor loaded successfully in {end_time - start_time:.2f} seconds")

    def generate_documentation(self, image_path, grid_index):
        """
        Generate documentation for a given image.

        This method takes an image path and a grid index, processes the image,
        and generates a textual description using the pre-trained model.

        Args:
            image_path (str): Path to the image file.
            grid_index (int): Index of the current grid in the series.

        Returns:
            str: Generated documentation for the image.

        Raises:
            FileNotFoundError: If the image file does not exist.
        """
        logger.info(f"Generating documentation for grid {grid_index}")
        start_time = time.time()

        logger.info(f"Attempting to open image at path: {image_path}")
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        image = Image.open(image_path)
        logger.info(f"Image opened successfully. Size: {image.size}, Mode: {image.mode}")

        prompt = f"This is grid {grid_index} of a series of 10x10 grids of screenshots from a screen recording, numbered in order. Analyze these frames and provide a detailed commentary on the process or workflow shown. Describe what's happening in each major step, noting any significant changes or actions between frames."

        messages = [
            {"role": "user", "content": [
                {"type": "image"},
                {"type": "text", "text": prompt}
            ]}
        ]

        logger.info("Preparing input for the model")
        input_text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(images=image, text=input_text, return_tensors="pt").to(self.model.device)
        logger.info(f"Inputs prepared successfully. Shape: {inputs['input_ids'].shape}")

        logger.info("Generating output from the model")
        output = self.model.generate(**inputs, max_new_tokens=1000)
        logger.info(f"Model output generated successfully. Shape: {output.shape}")

        documentation = self.processor.decode(output[0], skip_special_tokens=True)
        logger.info(f"Output decoded successfully. Length: {len(documentation)}")

        end_time = time.time()
        logger.info(f"Total analysis time for grid {grid_index}: {end_time - start_time:.2f} seconds")

        return documentation
