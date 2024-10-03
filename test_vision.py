"""
Test Vision Module

This script demonstrates how to use the MllamaForConditionalGeneration model
and AutoProcessor to analyze an image and generate a textual description.
It serves as a test and example for the vision-language capabilities of the model.
"""

import requests
import torch
from pathlib import Path
from PIL import Image
from transformers import MllamaForConditionalGeneration, AutoProcessor

# Set up paths
ROOT_DIR = Path(__file__).parent
MODEL_ID = "meta-llama/Llama-3.2-11B-Vision-Instruct"
MODEL_PATH = ROOT_DIR / "weights" / MODEL_ID

def load_model_and_processor():
    """
    Load the pre-trained model and processor.

    Returns:
        tuple: The loaded model and processor.
    """
    model = MllamaForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    return model, processor

def load_image(url):
    """
    Load an image from a given URL.

    Args:
        url (str): The URL of the image to load.

    Returns:
        PIL.Image: The loaded image.
    """
    return Image.open(requests.get(url, stream=True).raw)

def generate_description(model, processor, image):
    """
    Generate a description of the given image using the model and processor.

    Args:
        model: The pre-trained vision-language model.
        processor: The processor for preparing inputs.
        image (PIL.Image): The image to analyze.

    Returns:
        str: The generated description of the image.
    """
    messages = [
        {"role": "user", "content": [
            {"type": "image"},
            {"type": "text", "text": "Describe this image in detail."}
        ]}
    ]

    input_text = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(image, input_text, return_tensors="pt").to(model.device)

    output = model.generate(**inputs, max_new_tokens=100)
    return processor.decode(output[0], skip_special_tokens=True)

def main():
    """
    Main function to demonstrate the image analysis capabilities.
    """
    # Load the model and processor
    model, processor = load_model_and_processor()

    # Load an example image
    image_url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/0052a70beed5bf71b92610a43a52df6d286cd5f3/diffusers/rabbit.jpg"
    image = load_image(image_url)

    # Generate and print the description
    description = generate_description(model, processor, image)
    print('---')
    print('Generated Description:')
    print('---')
    print(description)

if __name__ == "__main__":
    main()