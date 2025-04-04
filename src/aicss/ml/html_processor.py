"""
HTML processor for extracting and replacing inline styles.

This module provides functionality to parse HTML files,
extract inline style descriptions, and replace them with
generated CSS.
"""

import re  # Import regex at the module level to avoid UnboundLocalError
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Union
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
import shutil

# Disable tqdm progress bars if they're being used by any packages
try:
    import tqdm
    # Replace tqdm with a no-op version that just returns the iterator
    tqdm.tqdm = lambda *args, **kwargs: args[0] if args else None
except ImportError:
    pass

from bs4 import BeautifulSoup
import minify_html

from ..ml.engine import nl_to_css_fast

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_style_descriptions(html_content: str) -> List[Tuple[str, str, str]]:
    """
    Extract inline style descriptions from HTML content.
    
    Args:
        html_content: HTML content to process
        
    Returns:
        List of tuples (element_id, selector, description)
    """
    soup = BeautifulSoup(html_content, 'lxml')
    descriptions = []
    
    # Find elements with aicss attribute
    elements = soup.select('[aicss]')
    
    for i, element in enumerate(elements):
        description = element.get('aicss', '').strip()
        if not description:
            continue
        
        # Generate a unique ID for the element if it doesn't have one
        element_id = element.get('id')
        if not element_id:
            element_id = f"aicss-{i+1}"
            element['id'] = element_id
        
        # Determine the selector
        tag_name = element.name
        classes = element.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
        class_str = f".{'.'.join(classes)}" if classes else ""
        
        selector = f"#{element_id}"
        if class_str:
            # Also add a selector based on tag and classes, to help with reusability
            selector = f"{tag_name}{class_str}, {selector}"
        
        descriptions.append((element_id, selector, description))
    
    return descriptions


def _is_subpath(path, potential_parent):
    """Check if path is a subpath of potential_parent."""
    path = os.path.normpath(os.path.abspath(path))
    potential_parent = os.path.normpath(os.path.abspath(potential_parent))
    
    # Use os.path.commonpath to find the common prefix
    try:
        common_path = os.path.commonpath([path, potential_parent])
        return common_path == potential_parent
    except ValueError:
        # This happens when the paths are on different drives (Windows)
        return False


def _generate_semantic_class_name(element_id: str, element_tag: str, description: str) -> str:
    """
    Generate a semantic class name based on element information.
    
    Args:
        element_id: The element's ID
        element_tag: The element's HTML tag
        description: The styling description
        
    Returns:
        A semantic class name
    """
    # Start with the element tag
    class_name = element_tag.lower()
    
    # Add common semantic prefixes based on the description
    if "primary" in description.lower():
        class_name += "-primary"
    elif "secondary" in description.lower():
        class_name += "-secondary"
    elif "success" in description.lower():
        class_name += "-success"
    elif "danger" in description.lower() or "error" in description.lower():
        class_name += "-danger"
    elif "warning" in description.lower():
        class_name += "-warning"
    elif "info" in description.lower():
        class_name += "-info"
    
    # Add size indicators
    if "large" in description.lower():
        class_name += "-lg"
    elif "small" in description.lower():
        class_name += "-sm"
    
    # Add common style indicators
    if "rounded" in description.lower():
        class_name += "-rounded"
    elif "outline" in description.lower():
        class_name += "-outline"
    
    # If no modifiers were added, use a fallback with the element ID
    if class_name == element_tag.lower():
        # Add a unique suffix based on the element ID
        short_hash = hashlib.md5(element_id.encode()).hexdigest()[:4]
        class_name += f"-{short_hash}"
    
    return class_name


def preprocess_html_for_dangerous_entities(html_content: str) -> str:
    """
    Preprocesses the HTML content to remove dangerous entities before parsing.
    
    This aggressive preprocessing step is needed to avoid issues with HTML entities
    persisting in the final output.
    
    Args:
        html_content: The raw HTML content
        
    Returns:
        Preprocessed HTML content with dangerous entities replaced
    """
    # First, preserve HTML comments by replacing them with placeholders
    comment_placeholders = {}
    
    def replace_comment(match):
        placeholder = f"__COMMENT_PLACEHOLDER_{len(comment_placeholders)}__"
        # Clean HTML entities in comments before storing
        comment_content = match.group(0)
        # Ultra-aggressive cleaning for comments
        cleaned_comment = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;?', ' ', comment_content)
        cleaned_comment = re.sub(r'<ai[^>]*>[^<]*</ai[^>]*>', ' ', cleaned_comment)
        cleaned_comment = re.sub(r'<ai[^>]*/>', ' ', cleaned_comment)
        comment_placeholders[placeholder] = cleaned_comment
        return placeholder
    
    # Replace all HTML comments with placeholders
    html_content = re.sub(r'<!--.*?-->', replace_comment, html_content, flags=re.DOTALL)
    
    # Handle HTML entities in attributes by completely removing problematic attributes
    html_content = re.sub(r'\s+([a-z\-]+)="[^"]*&lt;/?[a-z0-9]+[^"]*"', r'', html_content)
    html_content = re.sub(r'\s+([a-z\-]+)=\'[^\']*&lt;/?[a-z0-9]+[^\']*\'', r'', html_content)
    
    # Special cleanup for class attributes with HTML entities
    html_content = re.sub(r'class="([^"]*&lt;/?[a-z0-9]+[^"]*)"', r'class=""', html_content)
    html_content = re.sub(r"class='([^']*&lt;/?[a-z0-9]+[^']*)'", r"class=''", html_content)
    
    # Replace data-* attributes with HTML entities (these often cause problems)
    html_content = re.sub(r'\s+data-[a-z\-]+="[^"]+"', r'', html_content)
    
    # For any remaining entities in text content, replace them
    html_content = re.sub(r'&lt;/[a-z0-9]+\s*', ' ', html_content)
    html_content = re.sub(r'&lt;[a-z0-9]+\s*', ' ', html_content)
    
    # More aggressive cleanup of HTML entities
    html_content = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;', ' ', html_content)
    
    # Clean up any escaped quotes in content strings
    html_content = re.sub(r'\\([\'"])', r'\1', html_content)
    
    # Handle style and content directives in text content
    html_content = re.sub(r'content\s+"([^"]*)"', r'\1', html_content)
    html_content = re.sub(r"content\s+'([^']*)'", r'\1', html_content)
    html_content = re.sub(r'with\s+style\s+"[^"]*"', r'', html_content)
    html_content = re.sub(r"with\s+style\s+'[^']*'", r'', html_content)
    
    # Restore comments
    for placeholder, comment in comment_placeholders.items():
        html_content = html_content.replace(placeholder, comment)
    
    return html_content

def process_html_file(file_path: str, output_path: Optional[str] = None, extract_only: bool = False) -> Tuple[str, Dict[str, str]]:
    """
    Process an HTML file to extract and optionally replace inline styles.
    
    Args:
        file_path: Path to the HTML file
        output_path: Path to write the processed HTML (None to skip writing)
        extract_only: Only extract styles without replacing them
        
    Returns:
        Tuple of (processed_html, extracted_styles)
    """
    try:
        # Safety check to prevent recursive processing
        if output_path and os.path.exists(output_path):
            input_path_abs = os.path.abspath(file_path)
            output_path_abs = os.path.abspath(output_path)
            
            # Skip if output path is the same as input path
            if input_path_abs == output_path_abs:
                logger.warning(f"Skipping self-processing: {file_path}")
                return "", {}
            
            # Skip if the output is within a subdirectory of output_path
            if _is_subpath(input_path_abs, os.path.dirname(output_path_abs)):
                logger.warning(f"Skipping recursive processing: {file_path}")
                return "", {}
        
        start_time = time.time()
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Aggressive preprocessing to clean up potential issues before parsing
        html_content = preprocess_html_for_dangerous_entities(html_content)
        
        # Process <ai*> tags first - using the original HTML content to avoid missing tags
        processed_ai_html = process_ai_tags(html_content)
        
        # Handle any remaining AI tags with a more aggressive approach
        # This is for tags that might not have been caught in the first pass
        import re
        
        # Find all remaining AI tags with regex - more greedy to catch nested content
        ai_tag_pattern = r'<ai([^>]*)>(.*?)</ai[^>]*>'
        
        # Process in a loop to handle nested tags
        last_content = ""
        while processed_ai_html != last_content:
            last_content = processed_ai_html
            
            # Replace them with DIVs that have the same content
            def replace_ai_tag(match):
                tag_attrs = match.group(1)
                tag_content = match.group(2)
                
                # Extract the style from the content
                style_match = re.search(r'with\s+style\s+"([^"]+)"', tag_content)
                style_attr = f' aicss="{style_match.group(1)}"' if style_match else ""
                
                # Extract the actual content if specified
                content_match = re.search(r'content\s+"([^"]+)"', tag_content)
                if content_match:
                    # Use the content directly - it might have HTML
                    content = content_match.group(1)
                else:
                    # Use the whole content
                    content = tag_content
                
                return f'<div{style_attr}>{content}</div>'
            
            processed_ai_html = re.sub(ai_tag_pattern, replace_ai_tag, processed_ai_html, flags=re.DOTALL)
        
        # Handle self-closing AI tags
        ai_sc_tag_pattern = r'<ai([^>]*)\/>'
        processed_ai_html = re.sub(ai_sc_tag_pattern, r'<div\1></div>', processed_ai_html)
        
        # Re-parse the processed HTML to ensure all changes are properly represented
        soup = BeautifulSoup(processed_ai_html, 'html.parser')
        
        # Extract style descriptions
        style_descriptions = extract_style_descriptions(str(soup))
        
        # Generate CSS for each description
        styles = {}
        css_classes = {}  # Map element IDs to class names
        
        # Process style descriptions in parallel
        if style_descriptions:
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(
                    lambda x: (x[0], nl_to_css_fast(x[2], x[1])),
                    style_descriptions
                ))
                
                for element_id, css in results:
                    if css:
                        styles[element_id] = css
                        
                        # Get element tag for semantic class name
                        element = soup.find(id=element_id)
                        if element:
                            element_tag = element.name
                            
                            # Find the description for this element
                            description = next((desc for eid, _, desc in style_descriptions if eid == element_id), "")
                            
                            # Generate a semantic class name
                            class_name = _generate_semantic_class_name(element_id, element_tag, description)
                            css_classes[element_id] = class_name
        
        # If only extracting styles, return now
        if extract_only:
            return str(soup), styles
        
        # Replace inline styles with CSS classes
        elements_with_aicss = []
        
        # First, find all elements with aicss attributes (not just those with IDs)
        for element in soup.find_all(lambda tag: tag.has_attr('aicss')):
            description = element.get('aicss', '').strip()
            if not description:
                continue
                
            # Generate a unique ID for the element if it doesn't have one
            element_id = element.get('id')
            if not element_id:
                # Create a unique ID based on the element and its position
                element_id = f"aicss-{hashlib.md5((str(element) + str(len(elements_with_aicss))).encode()).hexdigest()[:8]}"
                element['id'] = element_id
                
            # Generate the selector
            selector = f"#{element_id}"
            
            # Generate CSS
            element_css = nl_to_css_fast(description, selector)
            if element_css:
                styles[element_id] = element_css
                
                # Generate a semantic class name
                class_name = _generate_semantic_class_name(element_id, element.name, description)
                css_classes[element_id] = class_name
                
                # Add the element to our list
                elements_with_aicss.append((element, element_id, class_name))
        
        # Now replace attributes with classes
        for element, element_id, class_name in elements_with_aicss:
            # Remove the aicss attribute
            del element['aicss']
            
            # Add the generated class
            if element.has_attr('class'):
                classes = element['class']
                if isinstance(classes, str):
                    classes = classes.split()
                if class_name not in classes:
                    classes.append(class_name)
                element['class'] = ' '.join(classes)
            else:
                element['class'] = class_name
                
            # Only keep ID if it was originally present
            if element_id.startswith('aicss-'):
                # Remove the auto-generated ID
                del element['id']
        
        # Add the extracted styles to the document
        if styles:
            # Create a style element
            style_tag = soup.new_tag('style')
            style_tag['type'] = 'text/css'
            style_tag.append('\n/* Generated by AI CSS Framework */\n')
            
            # Add all the CSS with class selectors
            for element_id, css in styles.items():
                class_name = css_classes.get(element_id)
                if class_name:
                    # Replace the ID selector with a class selector
                    css = css.replace(f"#{element_id}", f".{class_name}")
                    style_tag.append(css + '\n')
            
            # Add to the head
            head = soup.find('head')
            if head:
                # Check if we already have CSS from aistyle tags
                existing_styles = head.find_all('style')
                # If we do, append our CSS to the last style tag
                if existing_styles and existing_styles[-1].get('type') == 'text/css':
                    style_content = style_tag.decode_contents()
                    if style_content:
                        existing_styles[-1].append(style_content)
                else:
                    head.append(style_tag)
            else:
                # Create head if it doesn't exist
                head = soup.new_tag('head')
                head.append(style_tag)
                soup.html.insert(0, head)
                
        # Final pass to remove any remaining aicss attributes and auto-generated IDs
        for element in soup.find_all(lambda tag: tag.has_attr('aicss')):
            del element['aicss']
            
        # Remove any auto-generated aicss IDs
        for element in soup.find_all(lambda tag: tag.has_attr('id') and 
                                     isinstance(tag.get('id'), str) and
                                     tag.get('id').startswith('aicss-')):
            del element['id']
        
        # Get the processed HTML maintaining the original doctype
        processed_html = str(soup)
        
        # Write the processed HTML if output path is provided
        if output_path:
            output_dir = os.path.dirname(os.path.abspath(output_path))
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_html)
        
        end_time = time.time()
        logger.info(f"Processed {file_path} in {end_time - start_time:.3f} seconds")
        
        return processed_html, styles
    
    except Exception as e:
        logger.error(f"Error processing HTML file {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return "", {}


def generate_html_from_tag(tag_name: str, description: str) -> str:
    """
    Generate HTML content based on the AI tag name and description.
    
    Args:
        tag_name: The AI tag name (e.g., aibutton, aidiv)
        description: Natural language description of the HTML content
        
    Returns:
        Generated HTML content
    """
    # Extract the base tag without the 'ai' prefix
    base_tag = tag_name[2:] if tag_name.startswith('ai') else tag_name
    
    # Map special tags to appropriate HTML elements
    special_tags = {
        "button": """<button type="button">{text}</button>""",
        "input": """<input type="{input_type}" placeholder="{placeholder}">""",
        "textarea": """<textarea placeholder="{placeholder}">{content}</textarea>""",
        "div": """<div>{content}</div>""",
        "p": """<p>{text}</p>""",
        "h1": """<h1>{text}</h1>""",
        "h2": """<h2>{text}</h2>""",
        "h3": """<h3>{text}</h3>""",
        "img": """<img src="{src}" alt="{alt}">""",
        "a": """<a href="{href}">{text}</a>""",
    }
    
    # Extract directives using our helper function
    directives = extract_directives(description)
    
    # Determine attributes
    aicss_attr = f' aicss="{directives["style"]}"' if "style" in directives else ""
    
    # Extract class if present
    class_attr = ""
    if "class" in directives:
        class_name = directives["class"]
        # Remove quotes if they're present
        if class_name.startswith('"') and class_name.endswith('"'):
            class_name = class_name[1:-1]
        class_attr = f' class="{class_name}"'
    
    # Combine attributes
    attributes = aicss_attr + class_attr
    
    # Handle specific tag types
    if base_tag in special_tags:
        template = special_tags[base_tag]
        
        # Handle button
        if base_tag == "button":
            text = directives.get("text", "Button")
            return f"""<button type="button"{attributes}>{text}</button>"""
        
        # Handle input
        elif base_tag == "input":
            input_type = directives.get("type", "text")
            placeholder = directives.get("placeholder", "")
            return f"""<input type="{input_type}" placeholder="{placeholder}"{attributes}>"""
            
        # Handle textarea
        elif base_tag == "textarea":
            placeholder = directives.get("placeholder", "")
            content = directives.get("content", "")
            return f"""<textarea placeholder="{placeholder}"{attributes}>{content}</textarea>"""
        
        # Handle links
        elif base_tag == "a":
            href = directives.get("href", "#")
            text = directives.get("text", "Link")
            return f"""<a href="{href}"{attributes}>{text}</a>"""
        
        # Handle image
        elif base_tag == "img":
            src = directives.get("src", "https://via.placeholder.com/300x200")
            alt = directives.get("alt", "")
            return f"""<img src="{src}" alt="{alt}"{attributes}>"""
        
        # Handle text elements
        elif base_tag in ["p", "h1", "h2", "h3"]:
            text = directives.get("text", f"{base_tag.upper()} Text")
            return f"""<{base_tag}{attributes}>{text}</{base_tag}>"""
        
        # Handle div
        elif base_tag == "div":
            if "content" in directives:
                content = directives["content"]
            else:
                # Use remaining text after removing known directives
                content = get_remaining_text(description, directives)
                # If nothing meaningful remains, provide a generic fallback
                if not content or content.isspace():
                    content = "AI-generated content"
                    
            return f"""<div{attributes}>{content}</div>"""
    
    # For unknown tags, generate a generic div with remaining content after removing directives
    if "content" in directives:
        content = directives["content"]
    else:
        # Use remaining text after removing known directives
        content = get_remaining_text(description, directives)
        # If nothing meaningful remains, provide a generic fallback
        if not content or content.isspace():
            content = "AI-generated content"
            
    return f"""<div{attributes}>{content}</div>"""


def generate_html_from_description(description: str) -> str:
    """
    Generate HTML content from a natural language description.
    
    Args:
        description: Natural language description of HTML content
        
    Returns:
        Generated HTML content
    """
    # For simplicity, we'll just handle a few common patterns
    # In a real implementation, this would use an ML model for generation
    
    if "contact form" in description.lower():
        # Generate a contact form
        html = '<div class="contact-form">\n'
        html += '  <h3>Contact Us</h3>\n'
        html += '  <form>\n'
        html += '    <div class="form-group">\n'
        html += '      <label for="name">Name:</label>\n'
        html += '      <input type="text" id="name" name="name" placeholder="Your name" required>\n'
        html += '    </div>\n'
        html += '    <div class="form-group">\n'
        html += '      <label for="email">Email:</label>\n'
        html += '      <input type="email" id="email" name="email" placeholder="Your email" required>\n'
        html += '    </div>\n'
        html += '    <div class="form-group">\n'
        html += '      <label for="message">Message:</label>\n'
        html += '      <textarea id="message" name="message" placeholder="Your message" required></textarea>\n'
        html += '    </div>\n'
        
        # Extract button description if present
        button_match = re.search(r'submit button with aicss="([^"]+)"', description)
        if button_match:
            button_aicss = button_match.group(1)
            html += f'    <button type="submit" aicss="{button_aicss}">Submit</button>\n'
        else:
            html += '    <button type="submit">Submit</button>\n'
        
        html += '  </form>\n'
        html += '</div>'
        
        # Add form styling if described
        form_match = re.search(r'aicss="([^"]+)"', description)
        if form_match:
            form_aicss = form_match.group(1)
            html = html.replace('<div class="contact-form">', f'<div class="contact-form" aicss="{form_aicss}">')
        
        return html
    
    elif "navigation" in description.lower() or "navbar" in description.lower():
        # Generate a navigation bar
        html = '<nav class="navbar">\n'
        html += '  <div class="logo">Company Name</div>\n'
        html += '  <ul class="nav-links">\n'
        html += '    <li><a href="#">Home</a></li>\n'
        html += '    <li><a href="#">About</a></li>\n'
        html += '    <li><a href="#">Services</a></li>\n'
        html += '    <li><a href="#">Contact</a></li>\n'
        html += '  </ul>\n'
        html += '</nav>'
        
        # Add navbar styling if described
        nav_match = re.search(r'aicss="([^"]+)"', description)
        if nav_match:
            nav_aicss = nav_match.group(1)
            html = html.replace('<nav class="navbar">', f'<nav class="navbar" aicss="{nav_aicss}">')
        
        return html
    
    elif "gallery" in description.lower() or "images" in description.lower():
        # Generate an image gallery
        html = '<div class="gallery">\n'
        for i in range(1, 7):
            html += f'  <div class="gallery-item">\n'
            html += f'    <img src="https://via.placeholder.com/300x200?text=Image+{i}" alt="Image {i}">\n'
            html += f'    <div class="caption">Image {i} Caption</div>\n'
            html += f'  </div>\n'
        html += '</div>'
        
        # Add gallery styling if described
        gallery_match = re.search(r'aicss="([^"]+)"', description)
        if gallery_match:
            gallery_aicss = gallery_match.group(1)
            html = html.replace('<div class="gallery">', f'<div class="gallery" aicss="{gallery_aicss}">')
        
        return html
    
    # Extract directives from the description
    directives = extract_directives(description)
    
    # Default: generate a simple section with the description, but handle style and content better
    if "style" in directives:
        style_attr = f' aicss="{directives["style"]}"'
    else:
        style_attr = ''
    
    if "content" in directives:
        content = directives["content"]
    else:
        # Use remaining text after removing known directives
        content = get_remaining_text(description, directives)
        # If nothing meaningful remains, provide a generic fallback
        if not content or content.isspace():
            content = "AI-generated content"
    
    html = f'<div class="ai-generated"{style_attr}>\n'
    html += f'  {content}\n'
    html += '</div>'
    
    return html


def extract_directives(text):
    """
    Extract directives (content, style, etc.) from text.
    
    Args:
        text: The text to parse for directives
        
    Returns:
        Dictionary of directives (e.g., {"content": "...", "style": "..."})
    """
    directives = {}
    
    # More robust patterns with explicit support for single and double quotes
    patterns = {
        # Support both single and double quotes for content
        "content": [
            r'content\s+"((?:[^"\\]|\\.)*)"|content\s+\'((?:[^\'\\]|\\.)*)\''
        ],
        # Support both single and double quotes for style with optional 'with'
        "style": [
            r'(?:with\s+)?style\s+"([^"]+)"|(?:with\s+)?style\s+\'([^\']+)\''
        ],
        # Support both quote styles for text
        "text": [
            r'text\s+"([^"]+)"|text\s+\'([^\']+)\''
        ],
        # Support class with and without quotes
        "class": [
            r'class\s+([a-zA-Z0-9_-]+)|class\s+"([^"]+)"|class\s+\'([^\']+)\''
        ],
        # Other attributes with quote flexibility
        "href": [r'href\s+"([^"]+)"|href\s+\'([^\']+)\''],
        "src": [r'src\s+"([^"]+)"|src\s+\'([^\']+)\''],
        "alt": [r'alt\s+"([^"]+)"|alt\s+\'([^\']+)\''],
        "type": [r'type\s+"([^"]+)"|type\s+\'([^\']+)\''],
        "placeholder": [r'placeholder\s+"([^"]+)"|placeholder\s+\'([^\']+)\''],
    }
    
    # Extract each directive type
    for directive, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text)
            if match:
                # Find the first non-None group (accounting for multiple capture groups)
                for group_idx in range(1, len(match.groups()) + 1):
                    if match.group(group_idx) is not None:
                        directives[directive] = match.group(group_idx)
                        break
                # If we found a match, no need to try other patterns for this directive
                if directive in directives:
                    break
    
    # Advanced handle of content with nested quotes
    if "content" not in directives and ("content " in text or "content'" in text or "content\"" in text):
        # Recognize different patterns of content delimiters
        content_patterns = [
            (r'content\s+"', '"'),  # Double quotes
            (r'content\s+\'', '\''),  # Single quotes
        ]
        
        for start_pattern, end_char in content_patterns:
            content_match = re.search(start_pattern, text)
            if not content_match:
                continue
                
            start_pos = content_match.end()  # Position after the opening quote
            content_text = ""
            found_end = False
            nesting_level = 0  # For handling nested brackets and quotes
            in_escape = False
            
            # Iterate through the text to find matching end quote
            for i in range(start_pos, len(text)):
                char = text[i]
                
                # Handle escape sequences
                if char == '\\':
                    in_escape = not in_escape
                    content_text += char
                    continue
                
                # Handle potential closing quote
                if not in_escape and char == end_char:
                    # Check if this is likely the end of content
                    # Common patterns that indicate end of content
                    rest_of_text = text[i+1:].lstrip()
                    if (rest_of_text.startswith('with style') or 
                        rest_of_text.startswith('style') or
                        rest_of_text == '' or  # End of string
                        not rest_of_text[0].isalnum()):  # Followed by non-alphanum
                        
                        # We found a matching end quote
                        found_end = True
                        break
                
                # Add character to content
                content_text += char
                in_escape = False
            
            # If we found matching end quotes, use the content
            if found_end:
                directives["content"] = content_text
                break
    
    return directives

def get_remaining_text(text, directives):
    """
    Get the text with all known directives removed.
    
    Args:
        text: Original text
        directives: Dictionary of extracted directives
        
    Returns:
        Text with directives removed
    """
    result = text
    
    # More robust patterns to remove both single and double quoted content
    to_remove = [
        # Content patterns with both quote types and handling nested content
        r'content\s+"(?:[^"\\]|\\.)*"',
        r"content\s+'(?:[^'\\]|\\.)*'",
        # Style patterns
        r'with\s+style\s+"[^"]+"',
        r"with\s+style\s+'[^']+'",
        r'style\s+"[^"]+"',
        r"style\s+'[^']+'",
        # Text patterns
        r'text\s+"[^"]+"',
        r"text\s+'[^']+'",
        # Class patterns
        r'class\s+[a-zA-Z0-9_-]+',
        r'class\s+"[^"]+"',
        r"class\s+'[^']+'",
        # Other attributes with both quote types
        r'href\s+"[^"]+"', r"href\s+'[^']+'",
        r'src\s+"[^"]+"', r"src\s+'[^']+'",
        r'alt\s+"[^"]+"', r"alt\s+'[^']+'",
        r'type\s+"[^"]+"', r"type\s+'[^']+'",
        r'placeholder\s+"[^"]+"', r"placeholder\s+'[^']+'",
    ]
    
    # Remove each pattern
    for pattern in to_remove:
        result = re.sub(pattern, '', result)
    
    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Handle any HTML tag remnants that might be causing problems
    result = re.sub(r'</div>$', '', result)  # Remove trailing </div> that might be part of content
    result = re.sub(r'</?[a-z][^>]*>', '', result)  # Remove stray HTML tags
    
    return result

def clean_html_entities_in_attributes(soup):
    """
    Completely new approach to cleaning HTML entities in attributes.
    
    This function aggressively removes or cleans attributes with HTML entities.
    """
    # First, find all elements with attributes
    for element in soup.find_all(lambda tag: tag.attrs):
        # Check each attribute
        attrs_to_remove = []
        attrs_to_update = {}
        
        for attr_name, attr_value in element.attrs.items():
            if isinstance(attr_value, str):
                # Check if attribute value contains HTML entities
                if '&lt;' in attr_value or '&gt;' in attr_value:
                    # Completely remove href attributes with HTML entities
                    if attr_name in ['href', 'src', 'data-', 'alt', 'title', 'id', 'controls']:
                        attrs_to_remove.append(attr_name)
                    # For class attributes, remove HTML entities but keep the rest
                    elif attr_name == 'class':
                        # Even more aggressive cleaning for class attributes
                        cleaned_value = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;?', '', attr_value)
                        cleaned_value = re.sub(r'[<>]', '', cleaned_value)  # Also remove raw < and >
                        # Remove any quotes that might be part of the class name
                        cleaned_value = re.sub(r'[\'"]', '', cleaned_value)
                        
                        if cleaned_value.strip():
                            attrs_to_update[attr_name] = cleaned_value
                        else:
                            attrs_to_remove.append(attr_name)
                    # Other attributes, just remove
                    else:
                        attrs_to_remove.append(attr_name)
            elif isinstance(attr_value, list):
                # Handle list attributes like classes
                cleaned_values = []
                has_entities = False
                
                for value in attr_value:
                    if isinstance(value, str) and ('&lt;' in value or '&gt;' in value or '<' in value or '>' in value):
                        has_entities = True
                        # More aggressive cleaning for class attributes
                        cleaned = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;?', '', value)
                        cleaned = re.sub(r'[<>]', '', cleaned)  # Also remove raw < and >
                        cleaned = re.sub(r'[\'"]', '', cleaned)  # Remove quotes
                        
                        if cleaned.strip():
                            cleaned_values.append(cleaned)
                    else:
                        cleaned_values.append(value)
                
                if has_entities:
                    if cleaned_values:
                        attrs_to_update[attr_name] = cleaned_values
                    else:
                        attrs_to_remove.append(attr_name)
        
        # Apply the changes
        for attr_name in attrs_to_remove:
            del element[attr_name]
            
        for attr_name, attr_value in attrs_to_update.items():
            element[attr_name] = attr_value

def process_ai_tags(html_content: str) -> str:
    """
    Process <ai*> tags and replace them with generated HTML.
    
    Args:
        html_content: HTML content to process
        
    Returns:
        Processed HTML content
    """
    # Use html.parser to better preserve the document structure
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all <aistyle> tags for global styling
    aistyle_tags = soup.find_all('aistyle')
    
    # Create a single style tag for all aistyle content
    if aistyle_tags:
        all_css_parts = []
        
        for tag in aistyle_tags:
            description = tag.string.strip() if tag.string else ""
            if description:
                # Extract CSS selectors and properties from the description
                # Format: "selector: style description..."
                lines = description.split("\n")
                
                for line in lines:
                    line = line.strip()
                    if ":" in line:
                        selector_part, style_part = line.split(":", 1)
                        selector = selector_part.strip()
                        style_desc = style_part.strip()
                        
                        # Fix for "class" in selector (e.g., "body class:")
                        if "class" in selector:
                            # Extract the actual selector without the word "class"
                            base_selector = selector.replace("class", "").strip()
                            # Generate better CSS for body styles
                            if base_selector == "body":
                                # Parse the description for common body styles
                                properties = {}
                                if "font family" in style_desc.lower():
                                    properties["font-family"] = "'Segoe UI', system-ui, sans-serif"
                                if "line height" in style_desc.lower():
                                    match = re.search(r'line height (?:is )?(\d+\.?\d*)', style_desc.lower())
                                    if match:
                                        properties["line-height"] = match.group(1)
                                    else:
                                        properties["line-height"] = "1.6"
                                if "color" in style_desc.lower():
                                    match = re.search(r'color (?:is )?(#[0-9a-f]{3,6})', style_desc.lower())
                                    if match:
                                        properties["color"] = match.group(1)
                                    else:
                                        properties["color"] = "#444444"
                                if "padding" in style_desc.lower():
                                    if "lots" in style_desc.lower() or "large" in style_desc.lower():
                                        properties["padding"] = "2rem"
                                
                                # Generate CSS manually
                                if properties:
                                    css = f"body {{\n"
                                    for prop, value in properties.items():
                                        css += f"  {prop}: {value};\n"
                                    css += "}"
                                    all_css_parts.append(css)
                            else:
                                # Use ML for other selectors
                                css = nl_to_css_fast(style_desc, base_selector)
                                if css:
                                    all_css_parts.append(css)
                        else:
                            # Generate CSS with the original selector
                            css = nl_to_css_fast(style_desc, selector)
                            if css:
                                all_css_parts.append(css)
            
            # Remove the original tag
            tag.extract()
        
        # If we have generated CSS, add the style tag
        if all_css_parts:
            style_tag = soup.new_tag('style')
            style_tag['type'] = 'text/css'
            style_content = "\n/* AI-generated styles */\n" + "\n".join(all_css_parts)
            style_tag.string = style_content
            
            # Add to the head
            head = soup.find('head')
            if head:
                head.append(style_tag)
    
    # Process all HTML content in multiple passes to handle nested AI tags
    def process_html_recursively(html_content, max_depth=5, current_depth=0):
        """Process HTML content recursively to handle nested AI tags."""
        if current_depth >= max_depth:
            # Avoid infinite recursion
            return html_content
            
        soup = BeautifulSoup(html_content, 'html.parser')
        has_changes = False
        
        # First process <aihtml> tags
        aihtml_tags = soup.find_all('aihtml')
        for tag in aihtml_tags:
            description = tag.string.strip() if tag.string else ""
            if description:
                # Generate HTML from the description
                generated_html = generate_html_from_description(description)
                # Replace the <aihtml> tag with the generated HTML
                new_content = BeautifulSoup(generated_html, 'html.parser')
                tag.replace_with(new_content)
                has_changes = True
        
        # Then process other AI tags
        for tag_name in [tag.name for tag in soup.find_all() if tag.name and tag.name.startswith('ai') and 
                        tag.name not in ['aistyle']]:
            # Find all tags with this name
            for tag in soup.find_all(tag_name):
                # Get the content/description from the tag
                description = tag.string.strip() if tag.string else ""
                if description:
                    # Generate HTML based on the tag type and description
                    generated_html = generate_html_from_tag(tag.name, description)
                    # Parse the generated HTML
                    new_content = BeautifulSoup(generated_html, 'html.parser')
                    
                    # Extract elements from the new content
                    if new_content.contents:
                        if len(new_content.contents) == 1 and new_content.contents[0].name:
                            # Replace with single element
                            tag.replace_with(new_content.contents[0])
                        else:
                            # If there are multiple elements, handle them
                            wrapper = soup.new_tag('div')
                            wrapper['class'] = 'ai-generated-wrapper'
                            
                            # Move content to wrapper
                            for content in new_content.contents:
                                if hasattr(content, 'name') and content.name:
                                    wrapper.append(content)
                            
                            # Replace tag with wrapper
                            tag.replace_with(wrapper)
                    else:
                        # If no content, use a placeholder div
                        placeholder = soup.new_tag('div')
                        placeholder['class'] = 'ai-generated'
                        tag.replace_with(placeholder)
                    
                    has_changes = True
                elif tag.get('with') and 'style' in tag.get('with'):
                    # Handle self-closing tags with style attribute
                    style_match = re.search(r'style\s*=\s*["\']([^"\']+)["\']', tag.get('with'))
                    if style_match:
                        style_value = style_match.group(1)
                        # Create a div with the style
                        div = soup.new_tag('div')
                        div['class'] = 'ai-generated'
                        div['style'] = f"/* AI Style: {style_value} */"
                        
                        # Copy any other attributes
                        for attr, value in tag.attrs.items():
                            if attr != 'with' and attr != 'style':
                                div[attr] = value
                        
                        tag.replace_with(div)
                        has_changes = True
        
        # Also handle self-closing AI tags
        for tag in soup.find_all(lambda tag: tag.name and tag.name.startswith('ai') and tag.is_empty_element):
            # Create a div replacement
            div = soup.new_tag('div')
            div['class'] = 'ai-generated'
            # Copy attributes
            for attr, value in tag.attrs.items():
                if attr != 'style':
                    div[attr] = value
            tag.replace_with(div)
            has_changes = True
        
        # If changes were made, process again to handle newly revealed AI tags
        if has_changes and current_depth < max_depth - 1:
            return process_html_recursively(str(soup), max_depth, current_depth + 1)
        
        return str(soup)
    
    # Process the HTML content recursively
    processed_html = process_html_recursively(str(soup), max_depth=5)
    
    # Final pass with regex for any remaining AI tags
    # This handles any tags that might be part of attributes or not properly parsed
    def replace_ai_tag(match):
        tag_attrs = match.group(1)
        tag_content = match.group(2)
        
        # Extract directives using our helper function
        directives = extract_directives(tag_content)
        
        # Determine style attribute
        style_attr = f' aicss="{directives["style"]}"' if "style" in directives else ""
        
        # Determine content with better handling
        if "content" in directives:
            # Use explicitly defined content
            content = directives["content"]
            
            # Remove any HTML tag debris that might not belong
            content = re.sub(r'</div>\s*$', '', content)  # Remove trailing </div>
            
            # Check if content ends with style directive and fix if needed
            if "style" in directives:
                style_text = directives["style"]
                if content.endswith(f'with style "{style_text}"') or content.endswith(f"with style '{style_text}'"):
                    content = content[:-(len(f'with style "{style_text}"'))]
                elif content.endswith(f'style "{style_text}"') or content.endswith(f"style '{style_text}'"):
                    content = content[:-(len(f'style "{style_text}"'))]
        elif "text" in directives:
            # Use text as content if available
            content = directives["text"]
        else:
            # Use remaining text after removing known directives
            content = get_remaining_text(tag_content, directives)
            # If nothing meaningful remains, provide a generic fallback
            if not content or content.isspace():
                content = "AI-generated content"
        
        return f'<div{style_attr}>{content}</div>'
    
    # First fix any known common issues that cause problems
    html_soup = BeautifulSoup(processed_html, 'html.parser')
    
    # Apply the improved replacement function - use a non-greedy pattern to better handle nested tags
    processed_html = re.sub(r'<ai([^>]*)>(.*?)</ai[^>]*?>', replace_ai_tag, processed_html, flags=re.DOTALL)
    
    # Handle self-closing AI tags more robustly
    processed_html = re.sub(r'<ai([^/>]*)/>', r'<div class="ai-generated"></div>', processed_html)
    
    # Handle complex processing by using a safer final-pass approach
    # Create a new soup parsing with 'html5lib' for better error recovery
    try:
        final_soup = BeautifulSoup(processed_html, 'html5lib')
        
        # Look for and fix specific problem patterns in the final HTML
        
        # 1. Fix classes with HTML entities
        for element in final_soup.find_all(lambda tag: tag.name and tag.get('class') and '&lt;/div' in ' '.join(tag.get('class', []))):
            element['class'] = [c for c in element.get('class', []) if '&lt;' not in c]
        
        # 2. Fix elements with content + style text inside them
        for element in final_soup.find_all(string=lambda text: text and '" with style "' in text):
            # Get the parent element
            parent = element.parent
            if parent:
                # Extract the style from the element text
                style_match = re.search(r'with style "([^"]+)"', element)
                if style_match:
                    style_text = style_match.group(1)
                    # Set the aicss attribute
                    parent['aicss'] = style_text
                    # Clean up the element text
                    new_text = re.sub(r'\s*with style "([^"]+)"', '', element)
                    element.replace_with(new_text)
        
        # 3. Fix single-quoted version
        for element in final_soup.find_all(string=lambda text: text and "' with style '" in text):
            parent = element.parent
            if parent:
                style_match = re.search(r"with style '([^']+)'", element)
                if style_match:
                    style_text = style_match.group(1)
                    parent['aicss'] = style_text
                    new_text = re.sub(r"\s*with style '([^']+)'", '', element)
                    element.replace_with(new_text)
                    
        # 4. Fix "content" text fragments
        for element in final_soup.find_all(string=lambda text: text and text.strip().startswith('content "')):
            parent = element.parent
            if parent:
                # Try to extract the content between quotes
                content_match = re.search(r'content "([^"]*)"', element)
                if content_match:
                    content_text = content_match.group(1)
                    new_text = re.sub(r'content "([^"]*)"', r'\1', element)
                    element.replace_with(new_text)
        
        # 4b. Fix 'content' in single quotes
        for element in final_soup.find_all(string=lambda text: text and text.strip().startswith("content '")):
            parent = element.parent
            if parent:
                content_match = re.search(r"content '([^']*)'", element)
                if content_match:
                    content_text = content_match.group(1)
                    new_text = re.sub(r"content '([^']*)'", r'\1', element)
                    element.replace_with(new_text)
        
        # 5. Fix empty elements - add placeholder content
        # This special check helps us find really empty elements to fix
        empty_elements = []
        for tag_name in ['div', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'button', 'li', 'td', 'th', 'textarea']:
            # Find all elements of this tag type
            for element in final_soup.find_all(tag_name):
                # Super aggressive empty check - if there's nothing at all, or just whitespace text nodes
                is_empty = False
                
                # Check if element has no text content
                if not element.get_text(strip=True):
                    # Check for children that actually have content
                    child_elements = list(element.children)
                    has_content = False
                    
                    for child in child_elements:
                        # Check if it's a tag with actual content
                        if hasattr(child, 'name') and child.name and child.get_text(strip=True):
                            has_content = True
                            break
                        # Check if it's non-whitespace text
                        elif isinstance(child, str) and child.strip():
                            has_content = True
                            break
                    
                    if not has_content:
                        is_empty = True
                
                if is_empty:
                    empty_elements.append(element)
        
        # Now fix all the empty elements we found
        for element in empty_elements:
            tag_name = element.name
            # Clear any existing content
            element.clear()
            
            # Add appropriate placeholder content based on element type
            if tag_name == 'a':
                element.string = "Link"
            elif tag_name == 'button':
                element.string = "Button"
            elif tag_name.startswith('h'):
                element.string = f"Heading {tag_name[1]}"
            elif tag_name == 'textarea':
                element.string = "Enter your message here"
            else:
                element.string = "Content placeholder"
        
        # Fix all text nodes with HTML entities - even more aggressive cleanup
        for element in final_soup.find_all(string=lambda text: text and ('&lt;/' in text or '&lt;' in text or '&gt;' in text)):
            parent = element.parent
            if parent:
                # Ultra-aggressive cleanup of HTML entities in text
                new_text = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;?', ' ', element.string)
                new_text = re.sub(r'&[a-z]+;', ' ', new_text)  # Remove all HTML entities
                
                # Also clean up "content" directives with various quote patterns
                new_text = re.sub(r'content\s+\'([^\']*)\'\s*', r'\1', new_text)
                new_text = re.sub(r'content\s+"([^"]*)"', r'\1', new_text)
                new_text = re.sub(r'content\s+', '', new_text)
                
                # Clean up style directives with various quote patterns
                new_text = re.sub(r'\s+with\s+style\s+\'[^\']*\'', '', new_text)
                new_text = re.sub(r'\s+with\s+style\s+"[^"]*"', '', new_text)
                new_text = re.sub(r'\s+style\s+\'[^\']*\'', '', new_text)
                new_text = re.sub(r'\s+style\s+"[^"]*"', '', new_text)
                
                # Clean up any remaining quotes or special characters
                new_text = re.sub(r'^\s*[\'"]', '', new_text)  # Quotes at start
                new_text = re.sub(r'[\'"]$', '', new_text)     # Quotes at end$', '', new_text)     # Quotes at end
                
                # Remove any escaped quotes
                new_text = new_text.replace('\\"', '"').replace('\\\'', '\'')
                
                element.replace_with(new_text)
        
        # Use the new HTML entity attribute cleaner
        clean_html_entities_in_attributes(final_soup)
        
        # Find and fix any text nodes that have content directives
        for element in final_soup.find_all(string=lambda text: text and ('content ' in text)):
            parent = element.parent
            if parent:
                # More aggressive cleanup of content directives
                new_text = re.sub(r'content\s+\'([^\']*)\'\s*', r'\1', element.string)
                new_text = re.sub(r'content\s+"([^"]*)"', r'\1', new_text)
                new_text = re.sub(r'content\s+', '', new_text)
                # Clean up style directives as well
                new_text = re.sub(r'\s+with\s+style\s+\'[^\']*\'', '', new_text)
                new_text = re.sub(r'\s+with\s+style\s+"[^"]*"', '', new_text)
                element.replace_with(new_text)
                
        # Find and fix nested quotes
        for element in final_soup.find_all(string=lambda text: text and ('"' in text or "'" in text)):
            parent = element.parent
            if parent:
                # Replace quoted sections with their content
                new_text = re.sub(r'"\s*([^"]*)\s*"', r'\1', element.string)
                new_text = re.sub(r"'\s*([^']*)\s*'", r'\1', new_text)
                if new_text != element.string:
                    element.replace_with(new_text)
        
        # Use the cleaned soup as the final HTML
        processed_html = str(final_soup)
        
    except Exception as e:
        # Fall back to regex-based cleaning if BeautifulSoup approach fails
        logger.warning(f"Error using soup-based cleanup, falling back to regex: {e}")
        
        # Multiple passes of regex cleanup
        for _ in range(3):  # Apply multiple passes to catch nested issues
            # Fix HTML entities in attributes - more aggressive patterns
            
            # Complete removal approach - remove any attribute with HTML entities
            processed_html = re.sub(r'\s+([a-z\-]+)="[^"]*&lt;/?[a-z0-9]+[^"]*"', r'', processed_html)
            processed_html = re.sub(r'\s+([a-z\-]+)=\'[^\']*&lt;/?[a-z0-9]+[^\']*\'', r'', processed_html)
            
            # Remove any remaining &lt; entities in content - very aggressive
            processed_html = re.sub(r'&lt;/?[a-z0-9]+[^&]*&gt;?', '', processed_html)
            
            # Also clean up content directive text
            processed_html = re.sub(r'content\s+"([^"]*)"', r'\1', processed_html)
            processed_html = re.sub(r"content\s+'([^']*)'", r'\1', processed_html)
            processed_html = re.sub(r'>\s*content\s+"([^"]*)"', r'>\1', processed_html)
            processed_html = re.sub(r">\s*content\s+'([^']*)'", r'>\1', processed_html)
            processed_html = re.sub(r'>\s*content\s+', '>', processed_html)
            
            # Clean up style directives
            processed_html = re.sub(r'\s+with\s+style\s+"[^"]*"', '', processed_html)
            processed_html = re.sub(r"\s+with\s+style\s+'[^']*'", '', processed_html)
            
            # Remove extra quotes in content
            processed_html = re.sub(r'>\s*"([^"<>]*)"', r'>\1', processed_html)
            processed_html = re.sub(r">\s*'([^'<>]*)'", r'>\1', processed_html)
            processed_html = re.sub(r'"\s+with\s+style\s+"[^"]*"', '', processed_html)
            processed_html = re.sub(r"'\s+with\s+style\s+'[^']*'", '', processed_html)
            
            # Fix content with trailing style directives
            processed_html = re.sub(r'"\s+with style "([^"]+)"</div>', r'</div>', processed_html)
            processed_html = re.sub(r"'\s+with style '([^']+)'</div>", r'</div>', processed_html)
            
            # Fix duplicate quotes from complex nested content
            processed_html = re.sub(r'content "([^"]*)" with style', r'content \1 with style', processed_html)
            processed_html = re.sub(r"content '([^']*)' with style", r'content \1 with style', processed_html)
            processed_html = re.sub(r'>\s*content\s+"([^"]+)"\s*<', r'>\1<', processed_html)
            processed_html = re.sub(r">\s*content\s+'([^']+)'\s*<", r'>\1<', processed_html)
            
            # Fix stray closing div tags
            processed_html = re.sub(r'</div>\s*"\s+with style', r'" with style', processed_html)
            
            # Fix any other common malformed patterns
            processed_html = re.sub(r'<div>\s*content\s+"([^"]+)"\s+with style\s+"([^"]+)"', r'<div aicss="\2">\1', processed_html)
            processed_html = re.sub(r'<div>\s*content\s+\'([^\']+)\'\s+with style\s+\'([^\']+)\'', r'<div aicss="\2">\1', processed_html)
            
            # Fix floating quotes and content directives - much more aggressive patterns
            processed_html = re.sub(r'>\s*content\s+"([^"]+)"\s*<', r'>\1<', processed_html)
            processed_html = re.sub(r">\s*content\s+'([^']+)'\s*<", r'>\1<', processed_html)
            processed_html = re.sub(r'>\s*content\s+\'([^\']*)\'\s+', r'>', processed_html)
            processed_html = re.sub(r'>\s*content\s+"([^"]*)"\s+', r'>', processed_html)
            processed_html = re.sub(r'>\s*content\s+Level\s+', '> Level ', processed_html)
            processed_html = re.sub(r'\s+with\s+style\s+"([^"]+)"\s*(?=</)', ' ', processed_html)
            processed_html = re.sub(r'\s+with\s+style\s+\'([^\']+)\'\s*(?=</)', ' ', processed_html)
            
            # Fix any leftover floating quotes in content
            processed_html = re.sub(r'>\s*"\s*([^"<>]*?)"\s*<', r'>\1<', processed_html)
            processed_html = re.sub(r">\s*'\s*([^'<>]*?)'\s*<", r'>\1<', processed_html)
            
            # Fix empty elements - be even more aggressive
            for tag in ['div', 'span', 'p', 'button', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th']:
                # First pass for completely empty tags
                processed_html = re.sub(f'<{tag}([^>]*)>\s*</{tag}>', f'<{tag}\\1>Content placeholder</{tag}>', processed_html)
                # Second pass for tags with just non-breaking spaces
                processed_html = re.sub(f'<{tag}([^>]*)>\s*(?:&nbsp;|&#160;)\s*</{tag}>', f'<{tag}\\1>Content placeholder</{tag}>', processed_html)
                # Third pass for tags with just invisible markup
                processed_html = re.sub(f'<{tag}([^>]*)>\s*(?:<br>|<br/>|<br />)\s*</{tag}>', f'<{tag}\\1>Content placeholder</{tag}>', processed_html)
                # Fourth pass for tags with just whitespace
                processed_html = re.sub(f'<{tag}([^>]*)>(\s*)</{tag}>', f'<{tag}\\1>Content placeholder</{tag}>', processed_html)
            
            # Special handling for textarea - these have different placeholder text
            processed_html = re.sub(r'<textarea([^>]*)>\s*</textarea>', r'<textarea\1>Enter your message here</textarea>', processed_html)
            processed_html = re.sub(r'<textarea([^>]*)>\s*(?:&nbsp;|&#160;)\s*</textarea>', r'<textarea\1>Enter your message here</textarea>', processed_html)
            processed_html = re.sub(r'<textarea([^>]*)>\s*(?:<br>|<br/>|<br />)\s*</textarea>', r'<textarea\1>Enter your message here</textarea>', processed_html)
            processed_html = re.sub(r'<textarea([^>]*)>(\s*)</textarea>', r'<textarea\1>Enter your message here</textarea>', processed_html)
    
    return processed_html


def minify_html_file(input_file: str, output_file: str) -> bool:
    """
    Minify an HTML file.
    
    Args:
        input_file: Path to the input HTML file
        output_file: Path to write the minified HTML
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Minify the HTML
        minified = minify_html.minify(
            html_content,
            minify_css=True,
            remove_processing_instructions=True
        )
        
        # Write the minified HTML
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        return True
    
    except Exception as e:
        logger.error(f"Error minifying HTML file {input_file}: {e}")
        return False


def extract_and_process(input_path: str, output_path: str) -> bool:
    """
    Process a file or directory, extracting and processing styles and AI tags.
    
    Args:
        input_path: Path to input file or directory
        output_path: Path to output file or directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if input exists
        if not os.path.exists(input_path):
            logger.error(f"Input path does not exist: {input_path}")
            return False
        
        # Convert to absolute paths
        input_path_abs = os.path.abspath(input_path)
        output_path_abs = os.path.abspath(output_path)
        
        # Safety check: Don't overwrite input file accidentally
        if input_path_abs == output_path_abs and os.path.isfile(input_path_abs):
            logger.error(f"Input and output paths are the same file: {input_path_abs}")
            return False
        
        # Handle directories
        if os.path.isdir(input_path):
            # Ensure output_path is also treated as a directory
            if not output_path.endswith('/') and not output_path.endswith('\\'):
                # If it doesn't end with a slash, append one
                output_path = os.path.join(output_path, '')
            
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Log for debugging
            logger.info(f"Processing directory: {input_path} -> {output_path}")
            
            # Process all HTML files
            return process_directory(input_path, output_path)
        
        # Handle individual files
        elif os.path.isfile(input_path):
            # Determine file type
            _, ext = os.path.splitext(input_path)
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path_abs)
            os.makedirs(output_dir, exist_ok=True)
            
            # Process HTML files
            if ext.lower() in ['.html', '.htm']:
                _, styles = process_html_file(input_path, output_path)
                logger.info(f"Processed HTML file with {len(styles)} style sections")
                return True
            
            # Process CSS files
            elif ext.lower() == '.css':
                # For CSS files, just copy to output
                shutil.copy2(input_path, output_path)
                logger.info(f"Copied CSS file {input_path} to {output_path}")
                return True
            
            # Unsupported file type
            else:
                logger.error(f"Unsupported file type: {ext}")
                return False
        
        logger.error(f"Path is neither a file nor a directory: {input_path}")
        return False
    
    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        raise  # Re-raise the exception for more detailed error reporting


def process_directory(directory_path: str, output_path: Optional[str] = None, extract_only: bool = False) -> bool:
    """
    Process all HTML files in a directory.
    
    Args:
        directory_path: Path to the directory
        output_path: Path to write processed files (None to skip writing)
        extract_only: Only extract styles without replacing them
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert to absolute paths
        dir_path_abs = os.path.abspath(directory_path)
        output_path_abs = os.path.abspath(output_path) if output_path else None
        
        # Safety check: Don't process if output path is a subdirectory of input path
        # This would cause an infinite loop as we'd keep processing our own output
        if output_path_abs and output_path_abs.startswith(dir_path_abs):
            # Only warn if they're not the same directory (which is actually fine)
            if output_path_abs != dir_path_abs:
                logger.warning(f"Output path {output_path_abs} is a subdirectory of input {dir_path_abs}")
                logger.warning("This could cause recursion. Consider using a separate output directory.")
        
        # Create output directory if it doesn't exist
        if output_path_abs:
            os.makedirs(output_path_abs, exist_ok=True)
            logger.info(f"Created output directory: {output_path_abs}")
        
        # Find all HTML files in the directory
        html_files = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.html') or file.endswith('.htm'):
                    # Skip files in the output path to prevent recursion
                    file_path = os.path.join(root, file)
                    file_path_abs = os.path.abspath(file_path)
                    
                    # Only process if not in output path or if paths are the same (we're updating in place)
                    if (output_path_abs and 
                        _is_subpath(file_path_abs, output_path_abs) and
                        not os.path.commonprefix([file_path_abs, dir_path_abs]) == dir_path_abs):
                        logger.info(f"Skipping file in output directory: {file_path}")
                        continue
                    
                    html_files.append(file_path)
        
        if not html_files:
            logger.warning(f"No HTML files found in {directory_path}")
            return True  # Not a failure, just nothing to do
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        # Process each file
        results = {}
        
        with ThreadPoolExecutor() as executor:
            futures = []
            out_files = []
            
            for file_path in html_files:
                relative_path = os.path.relpath(file_path, directory_path)
                
                if output_path:
                    # Determine output file path
                    out_file = os.path.join(output_path, relative_path)
                    # Create parent directories if needed
                    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
                else:
                    out_file = None
                
                out_files.append(out_file)
                futures.append(
                    executor.submit(process_html_file, file_path, out_file, extract_only)
                )
            
            success = True
            processed_files = 0
            total_styles = 0
            
            for i, future in enumerate(futures):
                try:
                    _, styles = future.result()
                    if styles:
                        results[html_files[i]] = styles
                        processed_files += 1
                        total_styles += len(styles)
                    else:
                        logger.warning(f"No styles found in {html_files[i]}")
                except Exception as e:
                    logger.error(f"Error processing {html_files[i]}: {e}")
                    success = False
        
        # Print summary
        logger.info(f"Successfully processed {processed_files} of {len(html_files)} HTML files")
        logger.info(f"Extracted {total_styles} style descriptions in total")
        
        return success
    
    except Exception as e:
        logger.error(f"Error processing directory {directory_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False