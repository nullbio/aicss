# HTML Processor API Documentation

The HTML Processor module provides functionality for processing HTML files, extracting and replacing inline styles, and handling AI tag generation.

## Main Functions

### `extract_and_process(input_path, output_path)`

Process a file or directory, extracting and processing styles and AI tags.

**Parameters:**
- `input_path` (str): Path to input file or directory
- `output_path` (str): Path to output file or directory

**Returns:**
- True if successful, False otherwise

**Example:**
```python
from aicss.ml.html_processor import extract_and_process

# Process an HTML file
extract_and_process("input.html", "output.html")

# Process a directory of files
extract_and_process("input_dir", "output_dir")
```

### `process_html_file(file_path, output_path=None, extract_only=False)`

Process an HTML file to extract and optionally replace inline styles.

**Parameters:**
- `file_path` (str): Path to the HTML file
- `output_path` (str, optional): Path to write the processed HTML. Defaults to None
- `extract_only` (bool, optional): Only extract styles without replacing them. Defaults to False

**Returns:**
- A tuple of (processed_html, extracted_styles)

**Example:**
```python
from aicss.ml.html_processor import process_html_file

# Process an HTML file and write the result
html, styles = process_html_file("input.html", "output.html")

# Extract styles without writing the file
html, styles = process_html_file("input.html", extract_only=True)
```

### `extract_style_descriptions(html_content)`

Extract inline style descriptions from HTML content.

**Parameters:**
- `html_content` (str): HTML content to process

**Returns:**
- List of tuples (element_id, selector, description)

**Example:**
```python
from aicss.ml.html_processor import extract_style_descriptions

# Read an HTML file
with open("input.html", "r") as f:
    html_content = f.read()

# Extract style descriptions
descriptions = extract_style_descriptions(html_content)
```

### `process_ai_tags(html_content)`

Process <ai*> tags and replace them with generated HTML.

**Parameters:**
- `html_content` (str): HTML content to process

**Returns:**
- Processed HTML content

**Example:**
```python
from aicss.ml.html_processor import process_ai_tags

# Read an HTML file
with open("input.html", "r") as f:
    html_content = f.read()

# Process AI tags
processed_html = process_ai_tags(html_content)
```

### `generate_html_from_description(description)`

Generate HTML content from a natural language description.

**Parameters:**
- `description` (str): Natural language description of HTML content

**Returns:**
- Generated HTML content

**Example:**
```python
from aicss.ml.html_processor import generate_html_from_description

# Generate a contact form
html = generate_html_from_description("contact form with aicss='blue background'")
```

### `generate_html_from_tag(tag_name, description)`

Generate HTML content based on the AI tag name and description.

**Parameters:**
- `tag_name` (str): The AI tag name (e.g., aibutton, aidiv)
- `description` (str): Natural language description of the HTML content

**Returns:**
- Generated HTML content

**Example:**
```python
from aicss.ml.html_processor import generate_html_from_tag

# Generate a button element
html = generate_html_from_tag("aibutton", "text 'Submit' with style 'blue background'")
```

### `process_directory(directory_path, output_path=None, extract_only=False)`

Process all HTML files in a directory.

**Parameters:**
- `directory_path` (str): Path to the directory
- `output_path` (str, optional): Path to write processed files. Defaults to None
- `extract_only` (bool, optional): Only extract styles without replacing them. Defaults to False

**Returns:**
- True if successful, False otherwise

**Example:**
```python
from aicss.ml.html_processor import process_directory

# Process a directory of HTML files
process_directory("input_dir", "output_dir")
```

### `minify_html_file(input_file, output_file)`

Minify an HTML file.

**Parameters:**
- `input_file` (str): Path to the input HTML file
- `output_file` (str): Path to write the minified HTML

**Returns:**
- True if successful, False otherwise

**Example:**
```python
from aicss.ml.html_processor import minify_html_file

# Minify an HTML file
minify_html_file("input.html", "output.min.html")
```