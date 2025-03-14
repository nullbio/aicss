"""
Tests for the HTML processor module.
"""

import pytest
import os
import tempfile
from bs4 import BeautifulSoup
from aicss.ml.html_processor import (
    extract_style_descriptions,
    process_html_file,
    process_aihtml_tags,
    generate_html_from_description
)


def test_extract_style_descriptions():
    """Test extracting style descriptions from HTML."""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <div id="test" aicss="blue background, white text"></div>
        <button aicss="red background, white text, rounded"></button>
    </body>
    </html>
    """
    
    descriptions = extract_style_descriptions(html)
    
    assert len(descriptions) == 2
    assert descriptions[0][0] == "test"  # element ID
    assert "blue background" in descriptions[0][2]  # description
    assert descriptions[1][2] == "red background, white text, rounded"


def test_extract_style_descriptions_empty():
    """Test extracting style descriptions from HTML with no aicss attributes."""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <div id="test"></div>
        <button></button>
    </body>
    </html>
    """
    
    descriptions = extract_style_descriptions(html)
    
    assert len(descriptions) == 0


def test_process_aihtml_tags():
    """Test processing aihtml tags."""
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <aihtml>contact form with aicss="blue background"</aihtml>
    </body>
    </html>
    """
    
    processed_html = process_aihtml_tags(html)
    
    # Should replace aihtml tag with generated HTML
    assert "<aihtml>" not in processed_html
    assert "contact-form" in processed_html


def test_generate_html_from_description():
    """Test generating HTML from a description."""
    description = "contact form with aicss=\"blue background\""
    html = generate_html_from_description(description)
    
    # Should generate a contact form
    assert "<form>" in html
    assert "<input" in html
    assert "blue background" in html


def test_process_html_file():
    """Test processing an HTML file."""
    # Create a temporary HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp:
        temp.write(b"""
        <!DOCTYPE html>
        <html>
        <head><title>Test</title></head>
        <body>
            <div id="test" aicss="blue background, white text"></div>
        </body>
        </html>
        """)
    
    try:
        # Process the file
        output_file = temp.name + ".output.html"
        html, styles = process_html_file(temp.name, output_file)
        
        # Check the results
        assert len(styles) == 1
        assert "test" in styles
        assert os.path.exists(output_file)
        
        # Read the output file
        with open(output_file, "r") as f:
            output_html = f.read()
        
        # Check that the aicss attribute was replaced
        assert "aicss=" not in output_html
        assert "class=" in output_html
        assert "background-color: #0000ff;" in output_html
        
        # Clean up
        os.remove(output_file)
    finally:
        # Clean up the temp file
        os.remove(temp.name)