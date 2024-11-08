# PyKotor Dialog System

The dialog system handles game conversations in both native KotOR formats (GFF) and Twine 2 formats (HTML/JSON).

## Formats Supported

### GFF Format

The native KotOR dialog format using GFF (Generic File Format). This is the primary format used by the game engine.

### Twine 2 Format

Support for both HTML and JSON formats from Twine 2. This allows:

- Importing Twine stories into KotOR dialogs
- Exporting KotOR dialogs to Twine for easier editing
- Round-trip conversion between formats

## Usage Examples

### Loading a Dialog

```python
from pykotor.resource.generics.dlg import DLG, read_twine, construct_dlg

# From GFF
dlg = construct_dlg(gff_data)

# From Twine (auto-detects HTML or JSON)
dlg = read_twine("story.html")
```

### Saving a Dialog

```python
from pykotor.resource.generics.dlg import write_twine, dismantle_dlg

# To GFF
gff = dismantle_dlg(dlg)

# To Twine HTML
write_twine(dlg, "story.html", format="html")

# To Twine JSON
write_twine(dlg, "story.json", format="json")
```

### Creating a Dialog Programmatically

```python
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGReply, DLGLink
from pykotor.common.language import Language, Gender

# Create dialog
dlg = DLG()

# Create nodes
entry = DLGEntry()
entry.speaker = "NPC"
entry.text.set_data(Language.ENGLISH, Gender.MALE, "Hello there!")

reply = DLGReply()
reply.text.set_data(Language.ENGLISH, Gender.MALE, "General Kenobi!")

# Link nodes
entry.links.append(DLGLink(reply))

# Set starting node
dlg.starters.append(DLGLink(entry))
```

## Twine Format Details

### HTML Format

Uses Twine 2's HTML output format:

- Dialog entries become passages with `entry` tag
- Dialog replies become passages with `reply` tag
- Links are preserved using Twine's `[[text]]` or `[[display->link]]` syntax
- Node metadata (position, size) stored in passage metadata
- Story metadata (format, version, etc.) preserved

### JSON Format

Uses Twine 2's JSON format:

- More compact than HTML
- Easier to parse/generate
- Contains same information as HTML format
- Useful for programmatic manipulation

### Metadata Preservation

Both formats preserve:

- Node positions in Twine editor
- Node sizes
- Tag colors
- Story format settings
- Custom styles/scripts

## Type Safety

The dialog system uses Python's type hints throughout:

- Generic types for links (DLGLink[T])
- Proper type variance for collections
- Runtime type checking where needed
- Full mypy/pylance compatibility

## Best Practices

1. Always use type hints:

```python
from pykotor.resource.generics.dlg import DLG, DLGEntry, DLGLink

dlg: DLG = DLG()
entry: DLGEntry = DLGEntry()
link: DLGLink[DLGEntry] = DLGLink(entry)
```

2. Use proper error handling:

```python
try:
    dlg = read_twine("story.html")
except ValueError as e:
    print(f"Invalid Twine format: {e}")
```

3. Validate dialog structure:

```python
# Ensure all links point to valid nodes
for entry in dlg.all_entries():
    for link in entry.links:
        assert link.node is not None, "Broken link detected"
```

4. Use metadata appropriately:

```python
# Store position in Twine editor
entry.comment = json.dumps({
    "position": "100,200",
    "size": "100,100"
})
```

## Contributing

When adding features:

1. Add proper type hints
2. Include tests for edge cases
3. Update documentation
4. Follow existing code style
