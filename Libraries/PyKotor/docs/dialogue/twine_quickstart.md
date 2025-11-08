# Twine Format Quick Start Guide

This guide provides quick examples for common tasks using PyKotor's Twine format support.

## Installation

PyKotor includes Twine support by default. No additional installation is needed.

## Basic Usage

### Converting KotOR Dialog to Twine

```python
from pykotor.resource.generics.dlg import read_twine, write_twine

# Load existing dialog
dlg = construct_dlg(gff_data)

# Export to Twine
write_twine(dlg, "dialog.html")  # HTML format
write_twine(dlg, "dialog.json", format="json")  # JSON format
```

### Converting Twine to KotOR Dialog

```python
# Import from Twine
dlg = read_twine("dialog.html")  # or dialog.json

# Convert to GFF
gff = dismantle_dlg(dlg)
```

## Common Tasks

### Adding Metadata

```python
# Add style and script
metadata = {
    "name": "My Dialog",
    "style": """
        body { font-family: Arial; }
        .passage { background: #eee; }
    """,
    "script": """
        window.setup = {
            debug: true
        };
    """,
}

write_twine(dlg, "dialog.html", metadata=metadata)
```

### Preserving Node Positions

```python
# Store positions in metadata
entry = DLGEntry()
entry.comment = json.dumps({
    "position": "100,200",  # x,y coordinates
    "size": "100,100",     # width,height
})
```

### Handling Multiple Languages

```python
# Create multi-language entry
entry = DLGEntry()
entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello!")
entry.text.set_data(Language.FRENCH, Gender.MALE, "Bonjour!")
entry.text.set_data(Language.GERMAN, Gender.MALE, "Hallo!")

# Note: Twine will use English (Male) text by default
```

### Custom Tags

```python
metadata = {
    "tag-colors": {
        "entry": "green",
        "reply": "blue",
        "important": "red",
    }
}

write_twine(dlg, "dialog.html", metadata=metadata)
```

## Error Handling

```python
try:
    dlg = read_twine("dialog.html")
except ValueError as e:
    print(f"Invalid format: {e}")
except FileNotFoundError:
    print("File not found")
```

## Format Examples

### HTML Format

```html
<tw-storydata name="My Dialog" startnode="1">
    <style type="text/twine-css">
        body { color: red; }
    </style>
    <tw-passagedata pid="1" name="NPC" tags="entry">
        Hello there!
        [[Continue->Reply_1]]
    </tw-passagedata>
</tw-storydata>
```

### JSON Format

```json
{
    "name": "My Dialog",
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
        }
    ]
}
```

## Tips & Tricks

1. Use JSON for:
   - Programmatic manipulation
   - Smaller file sizes
   - Better performance

2. Use HTML for:
   - Manual editing in Twine
   - Visual layout
   - Custom styling

3. Preserve metadata:

   ```python
   # Read existing metadata
   with open("dialog.html") as f:
       content = f.read()
       root = ElementTree.fromstring(content)
       style = root.find(".//style").text
       script = root.find(".//script").text

   # Use in new export
   metadata = {
       "style": style,
       "script": script,
   }
   write_twine(dlg, "new_dialog.html", metadata=metadata)
   ```

4. Handle large dialogs:

   ```python
   # Process in chunks
   for entry in dlg.all_entries():
       # Process each entry
       pass

   for reply in dlg.all_replies():
       # Process each reply
       pass
   ```

5. Validate structure:

   ```python
   # Check for broken links
   for entry in dlg.all_entries():
       for link in entry.links:
           assert link.node is not None, f"Broken link in {entry.speaker}"
   ```

## Common Issues

1. Missing Text

   ```python
   # Always set text for new nodes
   entry = DLGEntry()
   entry.text.set_data(Language.ENGLISH, Gender.MALE, "Default text")
   ```

2. Duplicate Names

   ```python
   # Use unique names
   entry1.speaker = "NPC_1"
   entry2.speaker = "NPC_2"
   ```

3. Invalid Links

   ```python
   # Verify links exist
   if link.target in nodes:
       source.links.append(DLGLink(nodes[link.target]))
   ```

## Next Steps

1. Read the full [documentation](twine_format.md)
2. Check the [technical reference](twine_format_technical.md)
3. Look at the test cases for more examples
