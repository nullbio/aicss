# ML Engine API Documentation

The ML Engine module provides functionality for natural language to CSS conversion using optimized machine learning models.

## Main Functions

### `nl_to_css(description, selector="element")`

Convert a natural language description to CSS, optimized for speed.

**Parameters:**
- `description` (str): Natural language description of styling
- `selector` (str, optional): CSS selector to use. Defaults to "element"

**Returns:**
- A CSS string with the converted styling

**Example:**
```python
from aicss import nl_to_css

# Generate CSS for a button
css = nl_to_css("blue background, white text, rounded corners", "button")
print(css)
```

### `initialize_engine(force_download=False, model_dir=None)`

Initialize the ML engine for CSS generation.

**Parameters:**
- `force_download` (bool, optional): Force re-download of models. Defaults to False
- `model_dir` (str, optional): Custom directory to store/load models. Defaults to None

**Returns:**
- True if initialization was successful, False otherwise

**Example:**
```python
from aicss.ml.engine import initialize_engine

# Initialize with default settings
initialize_engine()

# Force re-download of models to a custom directory
initialize_engine(force_download=True, model_dir="/path/to/models")
```

### `download_models(force_download=False, model_dir=None)`

Download optimized models for fast inference.

**Parameters:**
- `force_download` (bool, optional): Force re-download even if models exist. Defaults to False
- `model_dir` (str, optional): Custom directory to store models. Defaults to None

**Returns:**
- True if download was successful, False otherwise

**Example:**
```python
from aicss.ml.engine import download_models

# Download models to default location
download_models()

# Force re-download to a custom directory
download_models(force_download=True, model_dir="/path/to/models")
```

### `models_are_downloaded()`

Check if models are already downloaded.

**Returns:**
- True if models exist, False otherwise

**Example:**
```python
from aicss.ml.engine import models_are_downloaded

if models_are_downloaded():
    print("Models already downloaded")
else:
    print("Models need to be downloaded")
```

### `process_description(description)`

Process a natural language description into CSS properties.

**Parameters:**
- `description` (str): Natural language description of styling

**Returns:**
- Dictionary of CSS properties and values

**Example:**
```python
from aicss.ml.engine import process_description

# Generate CSS properties
properties = process_description("blue background, white text, rounded corners")
print(properties)
```