#!/usr/bin/env python3
"""
AI CSS Framework - Main Entry Point

A simplified entry point to the AICSS CLI with direct model download.
"""

import sys
import os
import shutil
import time
import json
import argparse
from pathlib import Path
import logging
import requests
from aicss.cli import main

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define default model directory
DEFAULT_MODEL_DIR = os.path.join(str(Path.home()), '.cache', 'aicss', 'models')

def direct_download_model(force=False, model_dir=None):
    """
    Download the sentence-transformer model directly using HTTP requests
    instead of relying on huggingface_hub.
    
    Args:
        force: Force re-download even if models exist
        model_dir: Custom directory to store models
    
    Returns:
        True if successful, False otherwise
    """
    # Set model directory
    models_dir = Path(model_dir or DEFAULT_MODEL_DIR)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Models will be stored in: {models_dir}")
    
    # Model files to download
    model_files = {
        "config.json": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/config.json",
        "pytorch_model.bin": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/pytorch_model.bin",
        "tokenizer_config.json": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/tokenizer_config.json",
        "vocab.txt": "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/raw/main/vocab.txt",
    }
    
    try:
        # Create sentence-transformer directory
        model_path = models_dir / "sentence-transformer"
        
        # Remove existing directory if forcing download
        if force and model_path.exists():
            logger.info("Removing existing model files...")
            shutil.rmtree(str(model_path), ignore_errors=True)
        
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Download each file
        for filename, url in model_files.items():
            file_path = model_path / filename
            
            # Skip if file exists and not forcing download
            if file_path.exists() and not force:
                logger.info(f"File {filename} already exists, skipping download")
                continue
            
            logger.info(f"Downloading {filename}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded {filename}")
        
        # Create a config file to mark successful download
        config_path = models_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                "version": "0.1.0",
                "embedder": "sentence-transformers/all-MiniLM-L6-v2",
                "download_timestamp": time.time()
            }, f, indent=2)
        
        logger.info("Models downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        return False

if __name__ == "__main__":
    # Check for direct-download command
    if len(sys.argv) > 1 and sys.argv[1] == "direct-download":
        # Parse arguments
        parser = argparse.ArgumentParser(description="Download models directly without huggingface_hub")
        parser.add_argument("--force", action="store_true", help="Force re-download even if models exist")
        parser.add_argument("--model-dir", help="Custom directory to store models")
        args, _ = parser.parse_known_args(sys.argv[2:])
        
        # Download models
        success = direct_download_model(args.force, args.model_dir)
        sys.exit(0 if success else 1)
    
    # Regular CLI processing
    sys.exit(main())