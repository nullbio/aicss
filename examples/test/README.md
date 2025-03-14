# AI CSS Framework Test Suite

This directory contains comprehensive test files for the AI CSS Framework. The tests are designed to ensure all features work correctly and to catch potential regressions.

## Test Structure

The test suite includes:

- **HTML files** in the `html/` directory that test different aspects of the framework
- **Output files** in the `output/` directory (automatically generated when running tests)
- A Python test runner script (`run_tests.py`) that processes all test files and validates the results

## Test Files

The test files cover the following aspects:

1. `basic_elements.html` - Tests all standard HTML elements with AICSS attributes
2. `ai_elements.html` - Tests all AI element variants (`<ai*>` tags)
3. `nested_structures.html` - Tests deeply nested structures with AICSS
4. `edge_cases.html` - Tests edge cases and potentially problematic patterns
5. `all_html_tags.html` - Tests every HTML tag with AI elements and attributes
6. `css_testing.html` - Tests all CSS properties and values
7. `recursive_ai_elements.html` - Tests recursive processing of AI elements
8. `extreme_nesting.html` - Tests extremely deep nesting (7+ levels), complex attributes, and circular references
9. `unusual_language.html` - Tests unusual natural language descriptions (colloquial terms, slang, metaphors, technical jargon, etc.)
10. `performance_stress.html` - Tests performance with high-volume elements, extremely large content, and complex transformations

## Running the Tests

To run the full test suite:

```bash
cd examples/test
python run_tests.py
```

This will:
1. Process all HTML test files and generate outputs in the `output/` directory
2. Validate the output files to ensure correct processing
3. Perform additional validations (style consistency, HTML validity, etc.)
4. Generate a summary report

## Validation Checks

The validation checks include:

1. **Basic Validation**
   - No AICSS attributes remain in the output
   - No `<ai*>` tags remain in the output
   - Style tags are properly generated
   - CSS classes are added to elements

2. **Style Consistency**
   - All CSS classes used in elements are defined in the CSS
   - No duplicate class definitions

3. **Extended Validation**
   - No empty elements
   - No duplicate IDs
   - No CSS syntax errors
   - No unclosed braces in CSS
   - No empty CSS rules

## Adding New Tests

To add a new test:

1. Create a new HTML file in the `html/` directory
2. Ensure it tests a specific aspect of the framework
3. Run the test suite to validate it

## Test Structure Guidelines

When creating new tests:

- Each test file should focus on a specific aspect of the framework
- Include HTML comments explaining what each test is checking
- Use all AI CSS features to ensure comprehensive coverage
- Include edge cases and potential problem areas
- Keep test files small and focused for easier debugging

## Expected Results

After running the tests:

- All output files should be valid HTML
- No AICSS attributes or AI elements should remain
- All styles should be correctly applied
- All CSS classes should be properly defined
- No HTML or CSS syntax errors