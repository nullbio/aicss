# Getting Started with AI CSS Framework

This guide will help you get started with the natural language capabilities of the AI CSS Framework.

## Installation

Install AI CSS Framework using pip:

```bash
pip install aicss
```

## Basic Usage with Natural Language

### Python API

```python
from aicss import nl_to_css

# Convert natural language to CSS
description = "blue background, white text, rounded corners, large padding"
css = nl_to_css(description, "button")
print(css)
```

Output:
```css
button {
  background-color: #0000ff;
  color: #ffffff;
  border-radius: 0.25rem;
  padding: 1.5rem;
}
```

### Command Line Interface

Convert natural language directly:

```bash
python -m aicss.cli natural "blue background, white text, rounded corners" --selector button
```

Create component CSS:

```bash
python -m aicss.cli component "blue background, white text, rounded corners" --component button
```

## Creating a Natural Language CSS File

1. Create a file named `styles.txt` with the following content:

```
# Main elements
button: blue background, white text, rounded corners, bold, padding medium
card: white background, light gray border, rounded corners, shadow, padding large
input: full width, light gray border, rounded corners, padding medium

# Layout
container: centered, width 80%, max width 1200px
```

2. Convert it to standard CSS:

```bash
python -m aicss.cli convert_natural_file styles.txt styles.css
```

3. The output `styles.css` will contain the generated CSS based on your descriptions.

## Supported Natural Language Patterns

AI CSS Framework understands many common descriptive patterns:

- **Colors**: "blue background", "text color red"
- **Typography**: "bold text", "large font size", "center text"
- **Spacing**: "large padding", "small margin"
- **Borders**: "rounded corners", "thick red border"
- **Layout**: "flex", "centered", "in a column"
- **Dimensions**: "full width", "height 300px", "width 50%"

## Next Steps

- Read the [Natural Language Syntax Guide](nl-syntax.md) for more details on supported patterns
- Explore the [Components](components.md) documentation for component-specific styling
- Learn about [Themes](themes.md) for consistent styling