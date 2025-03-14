# AI CSS Framework Documentation

Welcome to the AI CSS Framework documentation. This framework is designed to make CSS generation easier and more accurate for AI models by allowing you to use natural language descriptions.

## Contents

- [Getting Started](getting-started.md)
- [Natural Language Syntax](nl-syntax.md)
- [Components](components.md)
- [Themes](themes.md)
- [CLI Usage](cli.md)
- [API Reference](api.md)

## Overview

AI CSS Framework provides a natural language approach to CSS that is:

1. **Human-Readable**: Write CSS as you would describe it to another person
2. **AI-Friendly**: Designed for easy AI generation and parsing
3. **Semantic**: Meaningful component and modifier names
4. **Predictable**: Consistent patterns reduce ambiguity
5. **Convertible**: Easily converts to standard CSS

## Example

```python
from aicss import nl_to_css

# Sample natural language description
description = """
blue background, white text, large padding, 
rounded corners, bold, centered
"""

# Convert to standard CSS
css = nl_to_css(description, "button")
print(css)
```

Output:
```css
button {
  background-color: #0000ff;
  color: #ffffff;
  padding: 1.5rem;
  border-radius: 0.25rem;
  font-weight: bold;
  display: flex;
  justify-content: center;
  align-items: center;
}
```