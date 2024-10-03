import os
import sys
from pathlib import Path
from huggingface_hub import snapshot_download
ROOT_DIR = Path(__file__).parents[2]

# make sure to login to huggingface before running this script, which requires a token from huggingface.co
# huggingface-cli login
class HuggingFaceDownloader:
    def __init__(self, model_name: str, local_dir: str):
        # Specify the repository ID and the local directory where you want to save the model
        self.model_name = model_name
        self.local_dir = local_dir

    def download(self):
        snapshot_download(
            repo_id=self.model_name,
            local_dir=self.local_dir
        )



if __name__ == "__main__":
    model_name = "meta-llama/Meta-Llama-3.2-11B-Vision-Instruct"
    # model_name = "meta-llama/Meta-Llama-3.2-3B"
    downloader = HuggingFaceDownloader(model_name, "weights/")
    downloader.download()
