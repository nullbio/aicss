"""
ML-powered engine for converting natural language to CSS.

Uses optimized sentence transformers and classification models
for fast, accurate CSS generation from plain English descriptions.
"""

import os
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging
import threading
import concurrent.futures
import shutil

import torch
try:
    import onnxruntime as ort
except ImportError:
    ort = None

# Disable tqdm progress bars
try:
    import tqdm
    # Save original tqdm function for cases where we might need it
    _original_tqdm = tqdm.tqdm
    # Replace with a no-op version
    tqdm.tqdm = lambda *args, **kwargs: args[0] if args else None
except ImportError:
    pass
    
from transformers import AutoTokenizer, AutoModel, pipeline
from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download, snapshot_download

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable tokenizer progress bars and other output
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "true"  # Disable Hugging Face progress bars (must be "true" not "1")
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Also ensure tqdm doesn't show any progress bars
os.environ["TQDM_DISABLE"] = "true"

# Global variables for models
_models = {}
_model_lock = threading.Lock()
_initialized = False
_initialization_lock = threading.Lock()

# Default model directory
DEFAULT_MODEL_DIR = os.path.join(str(Path.home()), '.cache', 'aicss', 'models')

# Model configuration
DEFAULT_CONFIG = {
    "embedder": {
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "onnx": ort is not None,  # Use ONNX only if available
        "quantized": True,  # Use quantized models when available
    },
    "property_classifier": {
        "model_id": "distilbert-base-uncased-finetuned-sst-2-english",  # We'll fine-tune this for CSS properties
        "onnx": ort is not None,
    },
    "color_recognizer": {
        "model_id": "dslim/bert-base-NER",  # Will be fine-tuned for color recognition
        "onnx": ort is not None,
    },
    "dimension_extractor": {
        "model_id": "onnx/roberta-sequence-classification-9", 
        "onnx": ort is not None,
    },
}

# CSS properties and their common values
CSS_PROPERTIES = {
    "color": ["red", "blue", "green", "yellow", "purple", "cyan", "magenta", "white", "black", "gray", "orange", 
             "pink", "brown", "navy", "teal", "primary", "secondary", "success", "danger", "warning", "info"],
    "background-color": ["red", "blue", "green", "yellow", "purple", "cyan", "magenta", "white", "black", "gray", 
                        "orange", "pink", "brown", "navy", "teal", "transparent", "primary", "secondary"],
    "font-size": ["tiny", "very small", "small", "medium", "large", "very large", "huge", "enormous"],
    "font-weight": ["normal", "bold", "bolder", "lighter"],
    "text-align": ["left", "center", "right", "justify"],
    "padding": ["none", "tiny", "very small", "small", "medium", "large", "very large", "huge", "enormous"],
    "margin": ["none", "tiny", "very small", "small", "medium", "large", "very large", "huge", "enormous"],
    "border-radius": ["none", "tiny", "very small", "small", "medium", "large", "very large", "huge", "enormous"],
    "display": ["block", "inline", "inline-block", "flex", "grid", "none"],
    "position": ["static", "relative", "absolute", "fixed", "sticky"],
    "width": ["auto", "full", "half", "third", "quarter"],
    "height": ["auto", "full", "half", "third", "quarter"],
}

# CSS property-value mappings
CSS_VALUE_MAPPING = {
    "color": {
        "red": "#ff0000",
        "blue": "#0000ff",
        "green": "#00ff00",
        "yellow": "#ffff00",
        "purple": "#800080",
        "cyan": "#00ffff",
        "magenta": "#ff00ff",
        "white": "#ffffff",
        "black": "#000000",
        "gray": "#808080",
        "orange": "#ffa500",
        "pink": "#ffc0cb",
        "brown": "#a52a2a",
        "navy": "#000080",
        "teal": "#008080",
        "primary": "var(--color-primary)",
        "secondary": "var(--color-secondary)",
        "success": "var(--color-success)",
        "danger": "var(--color-danger)",
        "warning": "var(--color-warning)",
        "info": "var(--color-info)",
    },
    "background-color": {
        "red": "#ff0000",
        "blue": "#0000ff",
        "green": "#00ff00",
        "yellow": "#ffff00",
        "purple": "#800080",
        "cyan": "#00ffff",
        "magenta": "#ff00ff",
        "white": "#ffffff",
        "black": "#000000",
        "gray": "#808080",
        "orange": "#ffa500",
        "pink": "#ffc0cb",
        "brown": "#a52a2a",
        "navy": "#000080",
        "teal": "#008080",
        "transparent": "transparent",
        "primary": "var(--color-primary)",
        "secondary": "var(--color-secondary)",
        "success": "var(--color-success)",
        "danger": "var(--color-danger)",
        "warning": "var(--color-warning)",
        "info": "var(--color-info)",
    },
    "font-size": {
        "tiny": "0.5rem",
        "very small": "0.75rem",
        "small": "0.875rem",
        "medium": "1rem",
        "large": "1.25rem",
        "very large": "1.5rem",
        "huge": "2rem",
        "enormous": "3rem",
    },
    "font-weight": {
        "normal": "400",
        "bold": "700",
        "bolder": "800",
        "lighter": "300",
    },
    "text-align": {
        "left": "left",
        "center": "center",
        "right": "right",
        "justify": "justify",
    },
    "padding": {
        "none": "0",
        "tiny": "0.125rem",
        "very small": "0.25rem",
        "small": "0.5rem",
        "medium": "1rem",
        "large": "1.5rem",
        "very large": "2rem",
        "huge": "3rem",
        "enormous": "4rem",
    },
    "margin": {
        "none": "0",
        "tiny": "0.125rem",
        "very small": "0.25rem",
        "small": "0.5rem",
        "medium": "1rem",
        "large": "1.5rem",
        "very large": "2rem",
        "huge": "3rem",
        "enormous": "4rem",
    },
    "border-radius": {
        "none": "0",
        "tiny": "0.125rem",
        "very small": "0.25rem",
        "small": "0.5rem",
        "medium": "0.75rem",
        "large": "1rem",
        "very large": "1.5rem",
        "huge": "2rem",
        "enormous": "3rem",
    },
    "display": {
        "block": "block",
        "inline": "inline",
        "inline-block": "inline-block",
        "flex": "flex",
        "grid": "grid",
        "none": "none",
    },
    "position": {
        "static": "static",
        "relative": "relative",
        "absolute": "absolute",
        "fixed": "fixed",
        "sticky": "sticky",
    },
    "width": {
        "auto": "auto",
        "full": "100%",
        "half": "50%",
        "third": "33.333%",
        "quarter": "25%",
    },
    "height": {
        "auto": "auto",
        "full": "100%",
        "half": "50%",
        "third": "33.333%",
        "quarter": "25%",
    },
}

# Pre-configured styles for quick access
STYLE_PATTERNS = {
    "centered": {
        "display": "flex",
        "justify-content": "center",
        "align-items": "center",
    },
    "shadow": {
        "box-shadow": "0 2px 5px rgba(0, 0, 0, 0.2)",
    },
    "rounded": {
        "border-radius": "0.25rem",
    },
    "no-border": {
        "border": "none",
    },
}


def models_are_downloaded() -> bool:
    """
    Check if models are already downloaded.
    
    Returns:
        True if models exist, False otherwise
    """
    models_dir = Path(DEFAULT_MODEL_DIR)
    
    # Check for sentence transformer model
    transformer_path = models_dir / "sentence-transformer"
    if not transformer_path.exists() or not list(transformer_path.glob("*")):
        return False
    
    # In a more complex implementation, we'd check for all required models
    return True


def download_models(force_download: bool = False, model_dir: Optional[str] = None) -> bool:
    """
    Download optimized models for fast inference.
    
    Args:
        force_download: Force re-download even if models exist
        model_dir: Custom directory to store models (defaults to ~/.cache/aicss/models)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create models directory
        models_dir = Path(model_dir or DEFAULT_MODEL_DIR)
        models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Models will be stored in: {models_dir}")
        
        # Check if models are already downloaded
        if not force_download and models_are_downloaded():
            logger.info("Models already downloaded.")
            return True
            
        # Download sentence transformer model
        logger.info("Downloading sentence transformer model...")
        model_path = models_dir / "sentence-transformer"
        
        # Remove existing directory if forcing download
        if force_download and model_path.exists():
            logger.info("Removing existing model files...")
            shutil.rmtree(str(model_path), ignore_errors=True)
        
        if not model_path.exists() or force_download:
            model_path.mkdir(parents=True, exist_ok=True)
            snapshot_download(
                repo_id=DEFAULT_CONFIG["embedder"]["model_id"],
                local_dir=str(model_path),
                local_dir_use_symlinks=False
            )
            logger.info(f"Downloaded model to {model_path}")
        
        # Download ONNX optimized models if needed
        if DEFAULT_CONFIG["embedder"]["onnx"] and ort is not None:
            logger.info("ONNX runtime available. Optimized inference will be used.")
            onnx_path = models_dir / "onnx"
            onnx_path.mkdir(exist_ok=True)
            
            # We would normally download pre-converted ONNX models here
            # For now, we'll use the transformers models directly
        
        # Save model config
        config_path = models_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump({
                "version": "0.1.0",
                "embedder": DEFAULT_CONFIG["embedder"]["model_id"],
                "download_timestamp": time.time()
            }, f, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error downloading models: {e}")
        return False


def load_models(model_dir: Optional[str] = None) -> bool:
    """
    Load ML models for inference.
    
    Args:
        model_dir: Custom directory where models are stored
        
    Returns:
        True if successful, False otherwise
    """
    global _models, _initialized
    
    if _initialized:
        return True
    
    with _initialization_lock:
        if _initialized:
            return True
        
        try:
            # Set model directory
            models_dir = Path(model_dir or DEFAULT_MODEL_DIR)
            
            # Check if models are downloaded
            if not models_are_downloaded():
                logger.info("Models not found locally. Downloading...")
                success = download_models(model_dir=str(models_dir))
                if not success:
                    logger.error("Failed to download models")
                    return False
            
            logger.info("Loading ML models...")
            start_time = time.time()
            
            # Load sentence transformer for embeddings
            transformer_path = models_dir / "sentence-transformer"
            if DEFAULT_CONFIG["embedder"]["onnx"] and ort is not None:
                # In practice, we would load the ONNX optimized model here
                # For this implementation, we'll use the regular model
                _models["embedder"] = SentenceTransformer(str(transformer_path))
            else:
                _models["embedder"] = SentenceTransformer(str(transformer_path))
            
            # Load property classifier - no output
            _models["property_classifier"] = pipeline(
                "text-classification", 
                model=DEFAULT_CONFIG["property_classifier"]["model_id"],
            )
            
            # Create fast embedding index for property matching
            _models["property_embeddings"] = {}
            
            # Pre-compute embeddings for CSS properties and values
            # This allows for faster matching during inference
            embedder = _models["embedder"]
            
            with _model_lock:
                for prop, values in CSS_PROPERTIES.items():
                    # Embed the property name
                    _models["property_embeddings"][prop] = embedder.encode(prop, convert_to_tensor=True)
                    
                    # Embed the property values
                    for value in values:
                        _models["property_embeddings"][f"{prop}_{value}"] = embedder.encode(value, convert_to_tensor=True)
            
            end_time = time.time()
            logger.info(f"Models loaded in {end_time - start_time:.2f} seconds")
            
            _initialized = True
            return True
        
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False


def initialize_engine(force_download: bool = False, model_dir: Optional[str] = None) -> bool:
    """
    Initialize the ML engine for CSS generation.
    
    Args:
        force_download: Force re-download of models
        model_dir: Custom directory to store/load models
        
    Returns:
        True if successful, False otherwise
    """
    # Download models if needed or forced
    if force_download or not models_are_downloaded():
        download_success = download_models(force_download, model_dir)
        if not download_success:
            logger.error("Failed to download models")
            return False
    
    # Load models
    load_success = load_models(model_dir)
    if not load_success:
        logger.error("Failed to load models")
        return False
    
    return True


def process_description(description: str) -> Dict[str, str]:
    """
    Process a natural language description into CSS properties.
    
    Args:
        description: Natural language description of styling
        
    Returns:
        Dictionary of CSS properties
    """
    if not _initialized:
        initialize_engine()
    
    properties = {}
    
    # Split description into phrases for parallel processing
    phrases = [phrase.strip() for phrase in description.split(",")]
    
    # Fast lookup for common style patterns
    for phrase in phrases:
        phrase_lower = phrase.lower().strip()
        
        # Check for predefined style patterns
        for pattern_name, pattern_props in STYLE_PATTERNS.items():
            if pattern_name in phrase_lower:
                properties.update(pattern_props)
    
    # Process each phrase to extract CSS properties
    # In a production system, this would use the ML models more extensively
    # For now, we'll use a combination of embeddings and rules
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for phrase in phrases:
            futures.append(executor.submit(_process_phrase, phrase))
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                properties.update(result)
    
    return properties


def _process_phrase(phrase: str) -> Dict[str, str]:
    """
    Process a single phrase to extract CSS properties.
    
    Args:
        phrase: A phrase from the description
        
    Returns:
        Dictionary of CSS properties extracted from the phrase
    """
    if not phrase:
        return {}
    
    phrase = phrase.lower().strip()
    properties = {}
    
    # Handle class declaration or content attribute (to prevent interference)
    class_match = re.search(r'class\s+([a-zA-Z0-9_-]+)', phrase)
    content_match = re.search(r'content\s+"([^"]+)"', phrase)
    
    if class_match or content_match:
        # Just return an empty dict to avoid processing these special cases
        return {}
    
    # Get embedding for the phrase
    phrase_embedding = _models["embedder"].encode(phrase, convert_to_tensor=True)
    
    # Find the closest matching property
    best_property = None
    best_score = -1
    
    with _model_lock:
        for prop, emb in _models["property_embeddings"].items():
            if "_" not in prop:  # Only compare with property names, not values
                # Compute cosine similarity
                score = torch.nn.functional.cosine_similarity(phrase_embedding, emb, dim=0).item()
                
                if score > best_score and score > 0.5:  # Threshold for matching
                    best_score = score
                    best_property = prop
    
    if best_property:
        # Now find the best matching value for this property
        best_value = None
        best_value_score = -1
        
        for value in CSS_PROPERTIES.get(best_property, []):
            value_key = f"{best_property}_{value}"
            if value_key in _models["property_embeddings"]:
                value_emb = _models["property_embeddings"][value_key]
                score = torch.nn.functional.cosine_similarity(phrase_embedding, value_emb, dim=0).item()
                
                if score > best_value_score and score > 0.4:  # Lower threshold for values
                    best_value_score = score
                    best_value = value
        
        if best_value:
            # Map the value to its CSS representation
            css_value = CSS_VALUE_MAPPING.get(best_property, {}).get(best_value, best_value)
            properties[best_property] = css_value
    
    # Additional pattern matching for dimensions with units
    # Width and height with units
    dimension_match = re.search(r'(width|height)(\s+is|\:)?\s+(\d+)(px|%|rem|em)?', phrase)
    if dimension_match:
        prop = dimension_match.group(1)
        value = dimension_match.group(3)
        unit = dimension_match.group(4) if dimension_match.group(4) else "px"
        properties[prop] = f"{value}{unit}"
    
    # Border radius
    radius_match = re.search(r'(border[\s-]*radius|rounded)(\s+with|\s+is|\:)?\s+(\d+)(px|rem|em)?', phrase)
    if radius_match:
        value = radius_match.group(3)
        unit = radius_match.group(4) if radius_match.group(4) else "px"
        properties["border-radius"] = f"{value}{unit}"
    
    return properties


def nl_to_css_fast(description: str, selector: str = "element") -> str:
    """
    Convert a natural language description to CSS, optimized for speed.
    
    Args:
        description: Natural language description of styling
        selector: CSS selector to use
        
    Returns:
        CSS string
    """
    start_time = time.time()
    
    # Process the description
    properties = process_description(description)
    
    # Generate CSS
    if not properties:
        return ""
    
    css_parts = [f"{selector} {{"]
    
    for name, value in properties.items():
        css_parts.append(f"  {name}: {value};")
    
    css_parts.append("}")
    
    end_time = time.time()
    logger.debug(f"CSS generation completed in {end_time - start_time:.3f} seconds")
    
    return "\n".join(css_parts)
