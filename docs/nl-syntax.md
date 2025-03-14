# Natural Language Syntax Guide

AI CSS Framework allows you to create CSS using plain English descriptions. This guide explains the supported patterns and terminology.

## Basic Syntax

Natural language descriptions can be provided as a comma-separated list of styling instructions:

```
blue background, white text, rounded corners, large padding
```

Each part of the description is analyzed and converted to appropriate CSS properties.

## Supported Patterns

### Colors

```
text color blue
color is red
color primary
background blue
background color is gray
background is secondary
```

Special color keywords: primary, secondary, success, danger, warning, info

### Typography

```
text size large
font size small
bold
italic
underline
all caps
lowercase
center text
align left
text right
```

Size keywords: tiny, very small, small, medium, large, very large, huge, enormous

### Spacing

```
padding large
pad small
margin medium
margin is none
gap small
space between medium
```

Spacing keywords: none, tiny, very small, small, medium, large, very large, huge, enormous

### Display & Layout

```
flex
use grid
display flex
row
column
in a row
in a column
centered
align center
hidden
hide
```

### Borders

```
rounded
rounded corners
round corners with radius large
border red
border thin blue
thick border
no border
borderless
```

### Dimensions

```
width 100px
width 50%
width half
height 200px
height 100%
full width
entire width
full height
```

Dimension keywords: half, third, quarter, full/whole

### Shadows

```
shadow
box shadow
with shadow
no shadow
without shadow
```

### Position

```
absolute
position relative
fixed
position sticky
```

## Examples

### Button

```
blue background, white text, rounded corners, bold, padding medium
```

Generates:

```css
button {
  background-color: #0000ff;
  color: #ffffff;
  border-radius: 0.25rem;
  font-weight: bold;
  padding: 1rem;
}
```

### Card

```
white background, light gray border, rounded corners, shadow, padding large
```

Generates:

```css
.card {
  background-color: #ffffff;
  border: 1px solid #808080;
  border-radius: 0.25rem;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  padding: 1.5rem;
}
```

### Flex Container

```
flex, space between, padding medium
```

Generates:

```css
.container {
  display: flex;
  justify-content: space-between;
  padding: 1rem;
}
```