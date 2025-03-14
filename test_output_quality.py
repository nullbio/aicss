#!/usr/bin/env python3
"""
Comprehensive test script to validate the quality of HTML output from the AI CSS processor.
This checks for various edge cases, malformations, and typical failures.
"""

import re
import os
import sys
import glob
from html.parser import HTMLParser

# List of test files to check
TEST_FILES = [
    "examples/test/output/recursive_ai_elements.html",
    "examples/test/output/all_html_tags.html", 
    "examples/test/output/nested_structures.html",
    "examples/test/output/performance_stress.html"
]

class HTMLValidationError(Exception):
    """Custom exception for HTML validation errors."""
    pass

class EmptyTagValidator(HTMLParser):
    """Validator that checks for empty tags that should have content."""
    def __init__(self):
        super().__init__()
        self.empty_tags = []
        self.current_tag = None
        self.current_attrs = None
        self.has_content = False
        self.tag_stack = []
        
    def handle_starttag(self, tag, attrs):
        # Skip void elements that don't need closing tags
        if tag in ['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 
                   'link', 'meta', 'param', 'source', 'track', 'wbr']:
            return
            
        self.tag_stack.append((tag, attrs, self.getpos()))
        self.has_content = False
        
    def handle_endtag(self, tag):
        if not self.tag_stack:
            return
            
        if tag == self.tag_stack[-1][0]:
            start_tag, attrs, pos = self.tag_stack.pop()
            
            # If we've found an empty tag that shouldn't be empty
            if not self.has_content and start_tag not in ['script', 'style']:
                # Check if it has any meaningful attributes that suggest it's intentionally empty
                has_meaningful_attrs = False
                for attr in attrs:
                    if attr[0] in ['id', 'class', 'aicss', 'style']:
                        has_meaningful_attrs = True
                        
                if not has_meaningful_attrs:
                    self.empty_tags.append((start_tag, pos))
        
    def handle_data(self, data):
        if data.strip():  # If there's non-whitespace content
            self.has_content = True
            
    def get_empty_tags(self):
        return self.empty_tags

def check_for_empty_elements(html_content):
    """Check for empty elements in the HTML that should have content."""
    validator = EmptyTagValidator()
    validator.feed(html_content)
    return validator.get_empty_tags()

def check_for_unprocessed_ai_tags(html_content):
    """Check for any AI tags that weren't properly processed."""
    ai_tag_pattern = r'<ai[a-z]*[^>]*>.*?</ai[a-z]*>'
    unprocessed_tags = re.findall(ai_tag_pattern, html_content, re.DOTALL)
    return unprocessed_tags

def check_for_unprocessed_aicss_attributes(html_content):
    """Check for aicss attributes that appear in the output but weren't processed."""
    # We only care about unprocessed aicss attributes that still have their original value
    # Processed ones will be different, often containing things like CSS properties
    unprocessed_pattern = r'aicss="([^"]*with style[^"]*|[^"]*content[^"]*)"'
    unprocessed_attrs = re.findall(unprocessed_pattern, html_content)
    return unprocessed_attrs

def check_for_floating_quotes(html_content):
    """Check for floating quotes that might indicate parsing issues."""
    # We're looking for quotes or apostrophes that appear directly in content
    # This is a bit tricky as quotes are valid HTML content, so we look for 
    # suspicious patterns like single quotes not followed by valid words
    suspicious_patterns = [
        r'>\s*"\s*with\s+style',  # Literal quote followed by "with style"
        r'>\s*\'\s*with\s+style',  # Literal apostrophe followed by "with style"
        r'content\s+"[^"]*"\s*<',  # Literal content attribute not processed
        r'content\s+\'[^\']*\'\s*<',  # Literal content attribute not processed
        r'>\s*content\s+\'[^\']*\'\s*',  # Literal content attribute in element content
        r'>\s*content\s+"[^"]*"\s*',  # Literal content attribute in element content
    ]
    
    floating_quotes = []
    for pattern in suspicious_patterns:
        for match in re.finditer(pattern, html_content):
            start_pos = max(0, match.start() - 30)
            end_pos = min(len(html_content), match.end() + 30)
            context = html_content[start_pos:end_pos]
            matched_text = match.group(0)
            floating_quotes.append((matched_text, context))
    
    return floating_quotes

def check_for_floating_quotes_simple(html_content):
    """A simpler version that just returns matched patterns."""
    suspicious_patterns = [
        r'>\s*"\s*with\s+style',
        r'>\s*\'\s*with\s+style',
        r'content\s+"[^"]*"\s*<',
        r'content\s+\'[^\']*\'\s*<',
        r'>\s*content\s+\'[^\']*\'\s*',
        r'>\s*content\s+"[^"]*"\s*',
    ]
    
    floating_quotes = []
    for pattern in suspicious_patterns:
        matches = re.findall(pattern, html_content)
        floating_quotes.extend(matches)
    
    return floating_quotes

def check_for_malformed_html_entities(html_content):
    """Check for malformed HTML entities like &lt;/div."""
    entity_pattern = r'&lt;/[a-z]+'
    
    # Extract more context to help with debugging
    context_matches = []
    for match in re.finditer(entity_pattern, html_content):
        start_pos = max(0, match.start() - 50)
        end_pos = min(len(html_content), match.end() + 50)
        context = html_content[start_pos:end_pos]
        entity = match.group(0)
        context_matches.append((entity, context))
    
    return [match[0] for match in context_matches]

def check_for_malformed_html_entities_with_context(html_content):
    """Get context around malformed HTML entities."""
    entity_pattern = r'&lt;/[a-z]+'
    
    # Extract more context to help with debugging
    context_matches = []
    for match in re.finditer(entity_pattern, html_content):
        start_pos = max(0, match.start() - 50)
        end_pos = min(len(html_content), match.end() + 50)
        context = html_content[start_pos:end_pos]
        entity = match.group(0)
        context_matches.append((entity, context))
    
    return context_matches

def validate_html_file(filepath):
    """Validate an HTML file for various issues."""
    if not os.path.exists(filepath):
        print(f"[ERROR] File does not exist: {filepath}")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors = []
    
    # Check for empty elements
    empty_elements = check_for_empty_elements(content)
    if empty_elements:
        errors.append(f"Found {len(empty_elements)} empty elements")
        for elem, pos in empty_elements[:5]:  # Show first 5 only
            errors.append(f"  - Empty {elem} element at line {pos[0]}")
    
    # Check for unprocessed AI tags
    unprocessed_tags = check_for_unprocessed_ai_tags(content)
    if unprocessed_tags:
        errors.append(f"Found {len(unprocessed_tags)} unprocessed AI tags")
        for tag in unprocessed_tags[:3]:  # Show first 3 only
            errors.append(f"  - {tag[:50]}...")
    
    # Check for unprocessed aicss attributes
    unprocessed_attrs = check_for_unprocessed_aicss_attributes(content)
    if unprocessed_attrs:
        errors.append(f"Found {len(unprocessed_attrs)} unprocessed aicss attributes")
        for attr in unprocessed_attrs[:3]:  # Show first 3 only
            errors.append(f"  - {attr[:50]}...")
    
    # Check for floating quotes
    floating_quotes = check_for_floating_quotes(content)
    if floating_quotes:
        errors.append(f"Found {len(floating_quotes)} instances of floating quotes")
        for quote_text, context in floating_quotes[:3]:  # Show first 3 only
            errors.append(f"  - {quote_text}")
            errors.append(f"    Context: {context}")
    
    # Check for malformed HTML entities
    malformed_entities = check_for_malformed_html_entities(content)
    malformed_entities_with_context = check_for_malformed_html_entities_with_context(content)
    if malformed_entities:
        errors.append(f"Found {len(malformed_entities)} malformed HTML entities")
        for entity, context in malformed_entities_with_context[:5]:  # Show first 5 only
            errors.append(f"  - {entity}")
            errors.append(f"    Context: {context}")
    
    if errors:
        print(f"[FAIL] {os.path.basename(filepath)}")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print(f"[PASS] {os.path.basename(filepath)}")
        return True

def main():
    """Main function to run the tests."""
    all_passed = True
    
    # Process each test file
    for test_file in TEST_FILES:
        if not validate_html_file(test_file):
            all_passed = False
    
    # Exit with appropriate status code
    if not all_passed:
        print("\nSome tests failed. See errors above.")
        sys.exit(1)
    else:
        print("\nAll tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
