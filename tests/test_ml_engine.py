"""
Tests for the ML engine module.
"""

import pytest
from aicss.ml.engine import process_description, nl_to_css_fast


def test_process_description_basic():
    """Test processing a basic description."""
    description = "blue background, white text"
    properties = process_description(description)
    
    assert "background-color" in properties
    assert "color" in properties
    assert properties["background-color"] == "#0000ff"
    assert properties["color"] == "#ffffff"


def test_process_description_empty():
    """Test processing an empty description."""
    description = ""
    properties = process_description(description)
    
    assert not properties


def test_process_description_unknown():
    """Test processing an unknown description."""
    description = "xyzabc"
    properties = process_description(description)
    
    # Should not crash, but may not produce any properties
    assert isinstance(properties, dict)


def test_nl_to_css_fast_basic():
    """Test converting a basic natural language to CSS."""
    description = "blue background, white text"
    css = nl_to_css_fast(description)
    
    assert "element {" in css
    assert "background-color: #0000ff;" in css
    assert "color: #ffffff;" in css


def test_nl_to_css_fast_with_selector():
    """Test converting natural language to CSS with a custom selector."""
    description = "blue background, white text"
    css = nl_to_css_fast(description, "button")
    
    assert "button {" in css
    assert "background-color: #0000ff;" in css
    assert "color: #ffffff;" in css


def test_nl_to_css_fast_empty():
    """Test converting empty natural language to CSS."""
    description = ""
    css = nl_to_css_fast(description)
    
    assert css == ""


def test_process_description_with_dimensions():
    """Test processing dimensions in a description."""
    description = "width 100px, height 200px"
    properties = process_description(description)
    
    assert "width" in properties
    assert "height" in properties
    assert properties["width"] == "100px"
    assert properties["height"] == "200px"


def test_process_description_with_pattern():
    """Test processing a description with a predefined pattern."""
    description = "centered, with shadow"
    properties = process_description(description)
    
    assert "display" in properties
    assert "justify-content" in properties
    assert "align-items" in properties
    assert "box-shadow" in properties
    assert properties["display"] == "flex"
    assert properties["justify-content"] == "center"
    assert properties["align-items"] == "center"