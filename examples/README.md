# AI CSS Framework Examples

This directory contains examples demonstrating the AI CSS Framework in action.

## Natural Language CSS Examples

Here are some examples of natural language descriptions for CSS:

### Buttons

```
button: blue background, white text, large padding, rounded corners, bold text
```

```
submit button: green background, white text, bold, rounded, medium padding
```

```
cancel button: red background, white text, bold, rounded, medium padding
```

### Cards

```
card: white background, light gray border, small rounded corners, medium padding, drop shadow
```

```
pricing card: white background, primary color border top, rounded corners, shadow, padding large
```

### Inputs

```
input: full width, small padding, thin gray border, rounded corners
```

```
search input: full width, medium padding, light border, rounded corners, with search icon
```

### Layout

```
container: centered, width 80%, max width 1200px, padding large
```

```
sidebar: width 25%, padding medium, background light gray, height 100vh
```

### Text Styling

```
heading: dark blue color, center aligned, large font size, bold, margin bottom medium
```

```
paragraph: dark gray color, medium size, line height 1.6, margin bottom small
```

### Navigation

```
navbar: dark background, flex, space between, padding medium, sticky top
```

## File Examples

- `index.html`: Sample webpage with `aicss` attributes for styling
- `aihtml_example.html`: Example of using `<aihtml>` tags to generate components
- `ai_elements.html`: Example of using specialized `<ai*>` tags like `<aibutton>`
- `combined_example.html`: Comprehensive example with inline CSS, AI tags and attributes
- `styles.css`: Example CSS file with AI-generated classes

## Running Examples

Process any example file with:

```bash
python -m aicss.cli process examples/combined_example.html examples/output/processed.html
```