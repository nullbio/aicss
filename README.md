# AI CSS Framework

An ML-powered CSS framework that converts plain English descriptions into optimized CSS. Write styles in natural language directly in your HTML and let AI do the rest.

## Features

- **Natural Language Styling**: Write CSS in plain English
- **HTML Integration**: Add styles directly in your HTML with the `aicss` attribute
- **AI HTML Generation**: Generate HTML components with `<aihtml>` tags or `<ai*>` elements
- **Ultra-Fast Processing**: Optimized ML models with <500ms generation time
- **File Watcher**: Automatically process HTML files as you edit them
- **Easy to Use**: No need to learn CSS syntax or memorize properties

## Installation

```bash
pip install aicss
```

## Usage

### HTML Styling with Natural Language

Add the `aicss` attribute to any HTML element:

```html
<button aicss="blue background, white text, rounded corners, bold">
  Click Me
</button>
```

### AI HTML Generation

Use `<aihtml>` tags to generate components from descriptions:

```html
<aihtml>
  contact form with aicss="modern gradient and black background and white text".
  submit button with aicss="white background, red text"
</aihtml>
```

Or use specific `<ai*>` elements for more control:

```html
<aibutton>text "Submit" with style "primary color, white text, rounded"</aibutton>
<aiinput>type "email" placeholder "Your email" with style "full width, rounded"</aiinput>
```

### Command Line

Process HTML files with AI styling:

```bash
aicss process index.html output.html
```

Watch a directory for changes:

```bash
aicss watch src/ -o build/
```

Download models for offline use:

```bash
aicss download
```

### Python API

```python
from aicss import nl_to_css

# Generate CSS from a description
css = nl_to_css("blue background, white text, rounded corners", "button")
print(css)
```

## Natural Language Syntax

AI CSS Framework understands a wide range of styling descriptions:

- **Colors**: "blue background", "white text", "primary color"
- **Typography**: "bold", "large text", "center aligned"
- **Spacing**: "large padding", "small margin", "gap medium"
- **Layout**: "flex", "centered", "space between"
- **Dimensions**: "full width", "half width", "80% width"
- **Borders**: "rounded corners", "thin gray border"
- **Effects**: "with shadow", "no border"

## Examples

See the [examples](examples/) directory for more demos and usage patterns.