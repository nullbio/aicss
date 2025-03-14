# AI CSS API Reference

This document provides a reference for the AI CSS Framework Python API.

## Main API

### convert

Convert AI CSS to standard CSS.

```python
from aicss import convert

css = convert("button.primary[large]; color: white;")
print(css)
```

### parse

Parse AI CSS into an intermediate representation.

```python
from aicss.parser import parse

rules = parse("button.primary[large]; color: white;")
print(rules)
```

## Components API

### get_component

Get a pre-defined component by name.

```python
from aicss.components import get_component

button = get_component("button")
print(button.css_template)
```

### COMPONENTS

Dictionary of all pre-defined components.

```python
from aicss.components import COMPONENTS

for name, component in COMPONENTS.items():
    print(f"{name}: {component.description}")
```

## Themes API

### get_theme

Get a theme by name (returns default theme if not found).

```python
from aicss.themes import get_theme

theme = get_theme("dark")
print(theme.colors)
```

### apply_theme_to_css

Apply a theme to CSS by adding CSS variables.

```python
from aicss.themes import apply_theme_to_css

css = "button { color: var(--color-primary); }"
themed_css = apply_theme_to_css(css, "dark")
print(themed_css)
```

### THEMES

Dictionary of all pre-defined themes.

```python
from aicss.themes import THEMES

for name, theme in THEMES.items():
    print(f"{name}: {theme.colors['primary']}")
```

## Data Classes

### Selector

Represents a CSS selector.

```python
from aicss.parser import Selector

selector = Selector()
selector.element = "button"
selector.classes = ["primary"]
selector.modifiers = ["large", "rounded"]
```

### StyleRule

Represents a CSS style rule with selectors and properties.

```python
from aicss.parser import StyleRule

rule = StyleRule()
rule.selectors = [selector]
rule.properties = {"color": "white", "background-color": "blue"}
```

### Component

Represents a UI component with pre-defined styles.

```python
from aicss.components import Component

component = Component(
    name="custom",
    description="Custom component",
    modifiers=["large", "small"],
    css_template=".custom { color: blue; }"
)
```

### Theme

Represents a theme with colors, spacing, and typography settings.

```python
from aicss.themes import Theme

theme = Theme(
    name="custom",
    colors={"primary": "#ff0000"},
    spacing={"md": "1rem"},
    typography={"font-size-base": "16px"},
    border_radius={"md": "0.25rem"}
)
print(theme.get_css_variables())
```