"""
Documentation Generator Module

This module provides a class for generating documentation from images using either a pre-trained
vision-language model from HuggingFace or the OpenAI Vision model. It supports both local model
inference and API-based generation.
"""

from transformers import MllamaForConditionalGeneration, AutoProcessor
import torch
from PIL import Image
import logging
import time
import os
import base64
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DocsGenerator:
    """
    A class for generating documentation from images using either a local vision-language model
    or the OpenAI Vision API.

    This class initializes the chosen model and provides methods to generate
    documentation for given images.
    """

    def __init__(self, model_type='huggingface', model_path=None):
        """
        Initialize the DocsGenerator with either a local model or OpenAI API setup.

        Args:
            model_type (str): Either 'huggingface' or 'openai'.
            model_path (str): Path to the pre-trained model weights (for HuggingFace model only).
        """
        logger.info(f"Initializing DocsGenerator with model type: {model_type}")
        self.model_type = model_type

        if model_type == 'huggingface':
            self._init_huggingface_model(model_path)
        elif model_type == 'openai':
            self._init_openai_api()
        else:
            raise ValueError("Invalid model_type. Choose 'huggingface' or 'openai'.")

    def _init_huggingface_model(self, model_path):
        """Initialize the HuggingFace model."""
        logger.info(f"Initializing DocsGenerator with model path: {model_path}")
        start_time = time.time()

        # Ensure MPS is available and set it as the default device
        assert torch.backends.mps.is_available(), "MPS should be available on M2 Mac"
        device = torch.device("mps")
        logger.info("Using MPS (Metal Performance Shaders) for acceleration")

        # Load the model with optimizations
        self.model = MllamaForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.float16,  # Use float16 for optimal performance
            # low_cpu_mem_usage=True,
            max_memory={0: "50GB"},
        ).to(device)

        # Load the processor
        self.processor = AutoProcessor.from_pretrained(model_path)

        # Optimize the model for inference
        self.model.eval()

        end_time = time.time()
        logger.info(f"Model and processor loaded successfully in {end_time - start_time:.2f} seconds")

    def _init_openai_api(self):
        """Initialize the OpenAI API setup."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not found in .env file")
        self.client = OpenAI(api_key=self.openai_api_key)
        logger.info("OpenAI API setup initialized successfully")

    def generate_documentation(self, image_path, grid_index):
        """
        Generate documentation for a given image.

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

        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            raise FileNotFoundError(f"Image file does not exist: {image_path}")

        if self.model_type == 'huggingface':
            documentation = self._generate_huggingface(image_path, grid_index)
        else:  # OpenAI
            documentation = self._generate_openai(image_path, grid_index)

        end_time = time.time()
        logger.info(f"Total analysis time for grid {grid_index}: {end_time - start_time:.2f} seconds")

        return documentation

    def _generate_huggingface(self, image_path, grid_index):
        """Generate documentation using the HuggingFace model."""
        logger.info(f"Attempting to open image at path: {image_path}")
        image = Image.open(image_path)
        logger.info(f"Image opened successfully. Size: {image.size}, Mode: {image.mode}")

        prompt = self._create_prompt(grid_index)

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
        output = self.model.generate(**inputs, max_new_tokens=2000)
        logger.info(f"\n---\nOutput: {output}\n---\n")
        logger.info(f"Model output generated successfully. Shape: {output.shape}")

        documentation = self.processor.decode(output[0], skip_special_tokens=True)
        processed_documentation = self._process_output(documentation)

        logger.info(f"\n---\nProcessed Documentation: {processed_documentation}\n---\n")
        logger.info(f"Output decoded successfully. Length: {len(processed_documentation)}")

        return processed_documentation

    def _generate_openai(self, image_path, grid_index):
        """Generate documentation using the OpenAI Vision API."""
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        prompt = self._create_prompt(grid_index)

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        return response.choices[0].message.content

    def _create_prompt(self, grid_index):
        """
        Create a prompt for the given grid index.

        Args:
            grid_index (int): Index of the current grid in the series.

        Returns:
            str: The generated prompt.
        """
        return f"""
        This is grid {grid_index} of a series of 2x2 grids of screenshots from a screen recording, numbered in order. 
        Analyze these four frames and provide a detailed commentary on the process or workflow shown. 
        Describe what's happening in each frame, noting any significant changes or actions between frames.

        The global objective is to analyze multiple 2x2 grids like these to build a coherent picture of a bigger process. 
        You do not always have complete frames of the whole process, so be sure to only explain what you can see objectively.
        
        ####
        Example:

        Frame 1: User is on a webpage with a search bar and a submit button.
        Frame 2: User has entered "Hello" in the search bar.
        Frame 3: The submit button is clicked.
        Frame 4: The webpage displays a search results page with a list of links.
        ####
        
        ####
        Commentary:
        The user is performing a web search.
        They start on a search page, enter their query, submit the search, and then view the results.
        This grid captures the entire search process from start to finish.
        
        ####
        Now, analyze the following 2x2 grid:
        """

    def _process_output(self, raw_output):
        """
        Process the raw output to extract only the assistant's response.

        Args:
            raw_output (str): The raw output from the model.

        Returns:
            str: The processed output containing only the assistant's response.
        """
        parts = raw_output.split('assistant', 1)
        if len(parts) > 1:
            return parts[1].strip()
        return raw_output.strip()

    def generate_documentation_batch(self, image_paths, grid_indices, batch_size=4):
        """
        Generate documentation for a batch of images.

        Args:
            image_paths (list): List of paths to image files.
            grid_indices (list): List of grid indices corresponding to the images.
            batch_size (int): Number of images to process in parallel (only for HuggingFace model).

        Returns:
            list: Generated documentation for each image.
        """
        if self.model_type == 'huggingface':
            results = []
            for i in range(0, len(image_paths), batch_size):
                batch_paths = image_paths[i:i+batch_size]
                batch_indices = grid_indices[i:i+batch_size]
                
                images = [Image.open(path) for path in batch_paths]
                prompts = [self._create_prompt(idx) for idx in batch_indices]
                
                inputs = self.processor(images=images, text=prompts, return_tensors="pt", padding=True).to(self.model.device)
                
                with torch.no_grad():
                    outputs = self.model.generate(**inputs, max_new_tokens=2000)
                
                batch_results = self.processor.batch_decode(outputs, skip_special_tokens=True)
                results.extend(batch_results)
            
            return results
        else:  # OpenAI
            results = []
            for image_path, grid_index in zip(image_paths, grid_indices):
                documentation = self.generate_documentation(image_path, grid_index)
                results.append(documentation)
            return results

    def generate_final_summary(self, all_descriptions):
        """
        Generate a final summary based on all grid descriptions.

        Args:
            all_descriptions (list): List of strings containing descriptions for each grid.

        Returns:
            str: A coherent summary of the entire process.
        """
        logger.info("Generating final summary")
        prompt = self._create_final_summary_prompt(all_descriptions)

        if self.model_type == 'huggingface':
            summary = self._generate_huggingface_summary(prompt)
        else:  # OpenAI
            summary = self._generate_openai_summary(prompt)

        logger.info("Final summary generated successfully")
        return summary

    def _create_final_summary_prompt(self, all_descriptions):
        """
        Create a prompt for the final summary generation.

        Args:
            all_descriptions (list): List of strings containing descriptions for each grid.

        Returns:
            str: The generated prompt.
        """
        descriptions_text = "\n\n".join(all_descriptions)
        return f"""
        Based on the following descriptions of multiple 2x2 grids of screenshots from a screen recording, 
        please provide a coherent and detailed documentation of the entire process or workflow shown. 
        Synthesize the information from all grids to create a comprehensive overview of the actions and steps taken.

        Grid Descriptions:
        {descriptions_text}

        Please provide a clear, step-by-step summary of the entire process, highlighting key actions, 
        transitions, and any significant observations. Your summary should give a reader a clear 
        understanding of the workflow or task that was performed across the entire video.
        """

    def _generate_openai_summary(self, prompt):
        """Generate final summary using the OpenAI API."""
        response = self.client.chat.completions.create(
            model="gpt-4",  # You might want to use a more powerful model for this task
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content

    def _generate_huggingface_summary(self, prompt):
        """Generate final summary using the HuggingFace model."""
        # Implement this if you're using a HuggingFace model
        # This would be similar to the _generate_huggingface method, 
        # but without the image input
        pass

# Example usage
if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(root_dir, 'weights', 'meta-llama/Llama-3.2-11B-Vision-Instruct') # HuggingFace example
    img_path = os.path.join(root_dir, 'static', 'grid_image.jpg')


    # hf_docs_generator = DocsGenerator(model_type='huggingface', model_path=model_path)
    # hf_documentation = hf_docs_generator.generate_documentation(img_path, 1)
    # print("HuggingFace Documentation:", hf_documentation)

    # OpenAI example
    openai_docs_generator = DocsGenerator(model_type='openai')
    
    openai_documentation = openai_docs_generator.generate_documentation(img_path, 1)
    print("OpenAI Documentation:", openai_documentation)