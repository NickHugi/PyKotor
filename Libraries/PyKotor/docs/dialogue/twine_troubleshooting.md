# Twine Format Troubleshooting Guide

This guide helps diagnose and fix common issues when working with PyKotor's Twine format support.

## Common Errors

### Format Detection

#### Problem: "Invalid Twine format"
```python
ValueError: Invalid Twine format - must be HTML or JSON
```

**Causes:**
1. File has wrong extension
2. File content is corrupted
3. File is empty

**Solutions:**
1. Ensure file starts with `{` for JSON or `<` for HTML
2. Validate file content in text editor
3. Specify format explicitly:
```python
write_twine(dlg, "dialog.txt", format="json")
```

### Parsing Errors

#### Problem: "Invalid JSON"
```python
ValueError: Invalid JSON: Expecting property name enclosed in double quotes
```

**Solutions:**
1. Validate JSON using online tools
2. Check for missing quotes or commas
3. Use HTML format if editing manually

#### Problem: "Invalid HTML"
```python
ValueError: Invalid HTML: mismatched tag
```

**Solutions:**
1. Check for unclosed tags
2. Validate HTML structure
3. Use JSON format for programmatic use

### Data Issues

#### Problem: Missing Text
```python
AssertionError: Node text is empty
```

**Solutions:**
1. Set default text:
```python
def create_entry(speaker: str, text: str) -> DLGEntry:
    entry = DLGEntry()
    entry.speaker = speaker
    entry.text.set_data(Language.ENGLISH, Gender.MALE, text or "Default text")
    return entry
```

2. Add validation:
```python
def validate_node(node: DLGNode) -> None:
    text = node.text.get(Language.ENGLISH, Gender.MALE)
    if not text:
        raise ValueError(f"Empty text in node: {node}")
```

#### Problem: Duplicate Node Names
```python
KeyError: 'Node name already exists: NPC'
```

**Solutions:**
1. Use unique names:
```python
def make_unique_name(name: str, existing: set[str]) -> str:
    if name not in existing:
        return name
    i = 1
    while f"{name}_{i}" in existing:
        i += 1
    return f"{name}_{i}"
```

2. Track used names:
```python
used_names: set[str] = set()
for entry in dlg.all_entries():
    entry.speaker = make_unique_name(entry.speaker, used_names)
    used_names.add(entry.speaker)
```

### Link Issues

#### Problem: Broken Links
```python
AssertionError: Broken link in NPC
```

**Solutions:**
1. Validate links:
```python
def validate_links(dlg: DLG) -> None:
    for entry in dlg.all_entries():
        for link in entry.links:
            if link.node is None:
                raise ValueError(f"Broken link in {entry.speaker}")
```

2. Clean broken links:
```python
def clean_links(dlg: DLG) -> None:
    for entry in dlg.all_entries():
        entry.links = [link for link in entry.links if link.node is not None]
```

### Metadata Issues

#### Problem: Invalid Metadata
```python
ValueError: Invalid metadata format
```

**Solutions:**
1. Validate metadata structure:
```python
def validate_metadata(metadata: dict) -> None:
    required = {"name", "format", "format-version"}
    missing = required - set(metadata.keys())
    if missing:
        raise ValueError(f"Missing required metadata: {missing}")
```

2. Use default metadata:
```python
DEFAULT_METADATA = {
    "name": "Converted Dialog",
    "format": "Harlowe",
    "format-version": "3.3.7",
    "zoom": 1.0,
}

def get_metadata(custom: dict | None = None) -> dict:
    metadata = DEFAULT_METADATA.copy()
    if custom:
        metadata.update(custom)
    return metadata
```

## Performance Issues

### Memory Usage

#### Problem: Large Dialog Memory Usage

**Solutions:**
1. Use generators:
```python
def process_nodes(dlg: DLG):
    for entry in dlg.all_entries():
        yield entry
    for reply in dlg.all_replies():
        yield reply
```

2. Clear processed nodes:
```python
processed: set[DLGNode] = set()
for node in process_nodes(dlg):
    if node in processed:
        continue
    # Process node
    processed.add(node)
    if len(processed) > 1000:
        processed.clear()  # Clear cache periodically
```

### Speed Issues

#### Problem: Slow Conversion

**Solutions:**
1. Use JSON format:
```python
# JSON is faster than HTML for large dialogs
write_twine(dlg, "dialog.json", format="json")
```

2. Cache lookups:
```python
# Cache node lookups
node_cache: dict[str, DLGNode] = {}
for node in dlg.all_entries():
    node_cache[node.speaker] = node
```

## Best Practices

### Error Prevention

1. Always validate input:
```python
def validate_dlg(dlg: DLG) -> None:
    # Check nodes
    validate_nodes(dlg)
    # Check links
    validate_links(dlg)
    # Check metadata
    validate_metadata(dlg)
```

2. Use type hints:
```python
def process_node(
    node: DLGNode,
    metadata: dict[str, Any],
    *,
    validate: bool = True,
) -> None:
    ...
```

3. Handle cleanup:
```python
def safe_write(dlg: DLG, path: Path) -> None:
    temp_path = path.with_suffix(".tmp")
    try:
        write_twine(dlg, temp_path)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
```

### Debugging

1. Enable logging:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Processing node: %s", node.speaker)
```

2. Add debug info:
```python
def write_twine(
    dlg: DLG,
    path: Path,
    *,
    debug: bool = False,
) -> None:
    if debug:
        metadata["debug_info"] = {
            "entries": len(dlg.all_entries()),
            "replies": len(dlg.all_replies()),
            "timestamp": datetime.now().isoformat(),
        }
```

## Recovery

### Backup Original

```python
def safe_convert(src: Path, dst: Path) -> None:
    # Create backup
    backup = src.with_suffix(src.suffix + ".bak")
    shutil.copy2(src, backup)

    try:
        # Convert
        dlg = read_twine(src)
        write_twine(dlg, dst)
    except Exception as e:
        # Restore backup
        shutil.copy2(backup, src)
        raise
    finally:
        # Cleanup
        backup.unlink()
```

### Repair Corrupted Files

```python
def repair_json(path: Path) -> None:
    """Attempt to repair corrupted JSON."""
    with open(path) as f:
        content = f.read()

    try:
        # Try to parse
        data = json.loads(content)
    except json.JSONDecodeError as e:
        # Basic repair attempts
        if "Expecting property name" in str(e):
            # Fix missing quotes
            content = re.sub(r'(\w+):', r'"\1":', content)
        elif "Expecting ',' delimiter" in str(e):
            # Fix missing commas
            content = re.sub(r'}\s*{', '},{', content)

        # Write repaired content
        path.write_text(content)
```

## Getting Help

1. Check error messages:
   - Look for specific error types
   - Note line numbers and contexts
   - Check stack traces

2. Gather information:
   - File format (HTML/JSON)
   - File size
   - Number of nodes
   - Error details

3. Create minimal example:
   - Reduce to smallest case that shows issue
   - Remove unnecessary metadata
   - Clean up node structure

4. Report issues:
   - Include minimal example
   - Describe expected behavior
   - List steps to reproduce
   - Include error messages
