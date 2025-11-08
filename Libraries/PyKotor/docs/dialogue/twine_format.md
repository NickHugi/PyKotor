# Twine Format Support

PyKotor supports importing and exporting dialogs in Twine 2 format, allowing for easier editing and visualization of dialog structures.

## Overview

[Twine](https://twinery.org/) is an open-source tool for creating interactive, nonlinear stories. PyKotor supports both HTML and JSON formats from Twine 2, enabling:

- Importing Twine stories into KotOR dialogs
- Exporting KotOR dialogs to Twine for easier editing
- Round-trip conversion between formats

## Usage

### Basic Usage

```python
from pykotor.resource.generics.dlg import read_twine, write_twine

# Read from Twine
dlg = read_twine("story.html")  # or story.json

# Write to Twine
write_twine(dlg, "story.html", format="html")  # or format="json"
```

### With Metadata

```python
metadata = {
    "name": "My Dialog",
    "format": "Harlowe",
    "format-version": "3.3.7",
    "tag-colors": {"reply": "green"},
    "style": "body { color: red; }",
    "script": "window.setup = {};",
    "zoom": 1.5,
}

write_twine(dlg, "story.html", format="html", metadata=metadata)
```

## Format Details

### HTML Format
The HTML format follows Twine 2's standard format:

```html
<tw-storydata name="My Dialog" startnode="1">
    <style type="text/twine-css">
        body { color: red; }
    </style>
    <script type="text/twine-javascript">
        window.setup = {};
    </script>
    <tw-passagedata pid="1" name="NPC" tags="entry">
        Hello there!
        [[Continue->Reply_1]]
    </tw-passagedata>
    <tw-passagedata pid="2" name="Reply_1" tags="reply">
        General Kenobi!
    </tw-passagedata>
</tw-storydata>
```

### JSON Format
The JSON format provides a more compact representation:

```json
{
    "name": "My Dialog",
    "format": "Harlowe",
    "format-version": "3.3.7",
    "passages": [
        {
            "name": "NPC",
            "text": "Hello there!\n[[Continue->Reply_1]]",
            "tags": ["entry"],
            "pid": "1",
            "metadata": {
                "position": "100,200",
                "size": "100,100"
            }
        },
        {
            "name": "Reply_1",
            "text": "General Kenobi!",
            "tags": ["reply"],
            "pid": "2"
        }
    ]
}
```

## Feature Mapping

### KotOR -> Twine
- Dialog entries become passages with `entry` tag
- Dialog replies become passages with `reply` tag
- Links preserve their child status and activation scripts
- Camera/animation/sound data stored in passage metadata
- Quest/VO data stored in passage metadata

### Twine -> KotOR
- Passages with `entry` tag become dialog entries
- Passages with `reply` tag become dialog replies
- Link text becomes the node text
- Passage positions preserved in editor
- Custom metadata mapped to appropriate KotOR fields

## Metadata Preservation

Both formats preserve:
- Node positions in Twine editor
- Node sizes
- Tag colors
- Story format settings
- Custom styles/scripts

### KotOR-specific Features
The following KotOR features are preserved in Twine metadata:
- Animation IDs
- Camera settings
- Fade effects
- Quest data
- Sound/VO data

### Twine-specific Features
The following Twine features are preserved in KotOR metadata:
- Custom CSS
- Custom JavaScript
- Tag colors
- Editor layout

## Best Practices

1. Use meaningful passage names:
```python
entry = DLGEntry()
entry.speaker = "Bastila"  # Will become passage name
```

2. Preserve metadata:
```python
metadata = {
    "style": existing_style,
    "script": existing_script,
    "tag-colors": existing_colors,
}
write_twine(dlg, "story.html", metadata=metadata)
```

3. Handle errors:
```python
try:
    dlg = read_twine("story.html")
except ValueError as e:
    print(f"Invalid Twine format: {e}")
except FileNotFoundError:
    print("File not found")
```

## Limitations

1. Language Support
   - Twine primarily supports single-language content
   - When converting from KotOR, English (Male) text is used by default
   - Other languages/genders are preserved but not displayed in Twine

2. KotOR Features
   - Some KotOR-specific features (like camera angles) are stored as metadata
   - These features won't be visible/editable in Twine but are preserved

3. Twine Features
   - Some Twine features (like variables) aren't supported
   - Focus is on dialog structure and basic metadata

## Contributing

When adding features:
1. Add proper type hints
2. Include tests for edge cases
3. Update documentation
4. Follow existing code style

## References

- [Twine 2 HTML Output Specification](https://github.com/iftechfoundation/twine-specs/blob/master/twine-2-htmloutput-spec.md)
- [Twine 2 JSON Output Documentation](https://github.com/iftechfoundation/twine-specs/blob/master/twine-2-jsonoutput-doc.md)
- [Twine 2 Story Formats Specification](https://github.com/iftechfoundation/twine-specs/blob/master/twine-2-storyformats-spec.md)
