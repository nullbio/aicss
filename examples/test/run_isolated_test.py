#!/usr/bin/env python3
"""
This script processes just the isolated test HTML file and validates the output.
It focuses specifically on the issues related to malformed HTML entities, unprocessed AI tags,
and content directive processing problems.
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.aicss.ml.html_processor import process_html_file
from bs4 import BeautifulSoup

# The isolated test file
TEST_FILE = "html/isolated_test.html"
OUTPUT_DIR = "output"
OUTPUT_FILE = f"{OUTPUT_DIR}/isolated_test.html"


def clear_output_directory():
    """Clear any old output files."""
    output_path = Path(__file__).parent / OUTPUT_DIR
    if output_path.exists():
        for file in output_path.glob("*.html"):
            file.unlink()
    else:
        output_path.mkdir(exist_ok=True)


def process_file():
    """Process the isolated test file and return the time taken."""
    input_path = Path(__file__).parent / TEST_FILE
    output_path = Path(__file__).parent / OUTPUT_FILE
    
    print(f"Processing {input_path.name}...")
    start_time = time.time()
    
    html_content, styles = process_html_file(str(input_path), str(output_path))
    
    end_time = time.time()
    return end_time - start_time


def validate_output():
    """Validate the processed HTML output for specific issues."""
    output_path = Path(__file__).parent / OUTPUT_FILE
    
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    issues = []
    
    # 1. Check for malformed HTML entities like &lt;/div
    import re
    malformed_entities = re.findall(r'&lt;/[a-z]+', content)
    if malformed_entities:
        issues.append(f"Found {len(malformed_entities)} malformed HTML entities:")
        for entity in malformed_entities:
            # Find context
            match = re.search(f"{re.escape(entity)}[^<>]*", content)
            if match:
                context = match.group(0)[:50]  # Get up to 50 chars for context
                issues.append(f"  - {entity} (Context: {context})")
            else:
                issues.append(f"  - {entity}")
    
    # 2. Check for unprocessed AI tags
    ai_tags = soup.find_all(lambda tag: tag.name and tag.name.startswith('ai'))
    if ai_tags:
        issues.append(f"Found {len(ai_tags)} unprocessed AI tags:")
        for tag in ai_tags[:5]:  # Show first 5
            issues.append(f"  - <{tag.name}...>")
    
    # 3. Check for content and style directives that weren't processed
    content_directives = re.findall(r'>\s*content\s+[\'"][^<>]*[\'"]', content)
    if content_directives:
        issues.append(f"Found {len(content_directives)} unprocessed content directives:")
        for directive in content_directives[:3]:
            issues.append(f"  - {directive[:50]}...")
    
    style_directives = re.findall(r'>\s*with\s+style\s+[\'"][^<>]*[\'"]', content)
    if style_directives:
        issues.append(f"Found {len(style_directives)} unprocessed style directives:")
        for directive in style_directives[:3]:
            issues.append(f"  - {directive[:50]}...")
    
    # 4. Check for floating quotes (quotes not properly processed)
    floating_quotes = re.findall(r'>\s*[\'"][^<>]*[\'"](?!\s*<)', content)
    if floating_quotes:
        issues.append(f"Found {len(floating_quotes)} instances of floating quotes:")
        for quote in floating_quotes[:3]:
            issues.append(f"  - {quote[:50]}...")
    
    # 5. Check for classes with HTML entities
    bad_classes = []
    for tag in soup.find_all(lambda t: t.has_attr('class')):
        classes = tag.get('class', [])
        if isinstance(classes, list):
            for cls in classes:
                if '&lt;' in cls:
                    bad_classes.append((tag.name, cls))
        elif isinstance(classes, str) and '&lt;' in classes:
            bad_classes.append((tag.name, classes))
    
    if bad_classes:
        issues.append(f"Found {len(bad_classes)} elements with HTML entities in class names:")
        for tag_name, cls in bad_classes[:5]:
            issues.append(f"  - <{tag_name} class='{cls}'>")
    
    # Display results
    if issues:
        print("\n===== Validation Issues =====")
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n===== Validation Passed =====")
        print("No issues found in the processed HTML.")
        return True


def main():
    """Main function to run the test."""
    clear_output_directory()
    
    # Process the file
    processing_time = process_file()
    
    print(f"Processing completed in {processing_time:.2f} seconds.")
    
    # Validate the output
    is_valid = validate_output()
    
    # Print final result
    print("\n===== Test Result =====")
    if is_valid:
        print("PASS: All issues were successfully fixed!")
        return 0
    else:
        print("FAIL: Some issues were found in the output.")
        return 1


if __name__ == "__main__":
    sys.exit(main())