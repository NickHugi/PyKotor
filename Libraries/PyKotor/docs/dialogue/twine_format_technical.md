# Twine Format Technical Reference

This document details the internal implementation of Twine format support in PyKotor.

## Architecture

### Data Model

```
TwineStory
├── metadata: TwineMetadata
├── passages: list[TwinePassage]
└── start_pid: str

TwineMetadata
├── name: str
├── ifid: str
├── format: str
├── format_version: str
├── zoom: float
├── creator: str
├── creator_version: str
├── style: str
├── script: str
└── tag_colors: dict[str, Color]

TwinePassage
├── name: str
├── text: str
├── type: PassageType
├── pid: str
├── tags: list[str]
├── metadata: PassageMetadata
└── links: list[TwineLink]

PassageMetadata
├── position: Vector2
├── size: Vector2
├── speaker: str
├── animation_id: int
├── camera_angle: int
├── camera_id: int
├── fade_type: int
├── quest: str
├── sound: str
├── vo_resref: str
└── custom: dict[str, str]

TwineLink
├── text: str
├── target: str
├── is_child: bool
├── active_script: str
└── active_params: list[str]
```

### Format Conversion

#### DLG -> TwineStory

1. Node Conversion:

```python
def _dlg_to_story(dlg: DLG) -> TwineStory:
    # Create metadata
    story_meta = TwineMetadata(...)

    # Track processed nodes
    processed: set[DLGNode] = set()
    node_to_passage: dict[DLGNode, TwinePassage] = {}

    # Process nodes recursively
    def process_node(node: DLGNode, pid: str) -> TwinePassage:
        if node in processed:
            return node_to_passage[node]

        passage = TwinePassage(
            name=node.speaker if isinstance(node, DLGEntry) else f"Reply_{len(processed)}",
            text=node.text.get(Language.ENGLISH, Gender.MALE) or "",
            type=PassageType.ENTRY if isinstance(node, DLGEntry) else PassageType.REPLY,
            pid=pid,
        )

        # Process links
        for link in node.links:
            if link.node is not None:
                target = process_node(link.node, str(uuid.uuid4()))
                passage.links.append(TwineLink(...))

        return passage
```

2. Metadata Preservation:

```python
def store_kotor_metadata(passage: TwinePassage, dlg_node: DLGNode) -> None:
    meta = passage.metadata
    meta.animation_id = getattr(dlg_node, "animation_id", 0)
    meta.camera_angle = getattr(dlg_node, "camera_angle", 0)
    # ...etc
```

#### TwineStory -> DLG

1. Node Conversion:

```python
def _story_to_dlg(story: TwineStory) -> DLG:
    dlg = DLG()

    # Track created nodes
    nodes: dict[str, DLGNode] = {}

    # First pass: Create nodes
    for passage in story.passages:
        if passage.type == PassageType.ENTRY:
            node = DLGEntry()
            node.speaker = passage.name
        else:
            node = DLGReply()

        node.text.set_data(Language.ENGLISH, Gender.MALE, passage.text)
        nodes[passage.name] = node

    # Second pass: Create links
    for passage in story.passages:
        source = nodes[passage.name]
        for link in passage.links:
            if link.target in nodes:
                target = nodes[link.target]
                source.links.append(DLGLink(target))
```

2. Metadata Restoration:

```python
def restore_kotor_metadata(dlg_node: DLGNode, passage: TwinePassage) -> None:
    meta = passage.metadata
    for feature in KOTOR_FEATURES:
        if hasattr(meta, feature):
            setattr(dlg_node, feature, getattr(meta, feature))
```

### Format Handling

#### HTML Format

1. Reading:

```python
def _read_html(content: str) -> TwineStory:
    root = ElementTree.fromstring(content)
    story_data = root.find(".//tw-storydata")

    # Create metadata
    metadata = TwineMetadata(
        name=story_data.get("name", ""),
        format=story_data.get("format", ""),
        # ...etc
    )

    # Get style/script
    style = story_data.find(".//style[@type='text/twine-css']")
    script = story_data.find(".//script[@type='text/twine-javascript']")

    # Create passages
    passages = []
    for p_data in story_data.findall(".//tw-passagedata"):
        passage = TwinePassage(...)
        passages.append(passage)
```

2. Writing:

```python
def _write_html(story: TwineStory, path: Path) -> None:
    root = ElementTree.Element("html")
    story_data = ElementTree.SubElement(root, "tw-storydata")

    # Set metadata
    story_data.set("name", story.metadata.name)
    # ...etc

    # Add style/script
    if story.metadata.style:
        style = ElementTree.SubElement(story_data, "style")
        style.set("type", "text/twine-css")
        style.text = story.metadata.style

    # Add passages
    for passage in story.passages:
        p_data = ElementTree.SubElement(story_data, "tw-passagedata")
        p_data.set("name", passage.name)
        p_data.set("tags", " ".join(passage.tags))
        p_data.text = passage.text
```

#### JSON Format

1. Reading:

```python
def _read_json(content: str) -> TwineStory:
    data = json.loads(content)

    # Create metadata
    metadata = TwineMetadata(
        name=data.get("name", ""),
        format=data.get("format", ""),
        # ...etc
    )

    # Create passages
    passages = []
    for p_data in data.get("passages", []):
        passage = TwinePassage(
            name=p_data.get("name", ""),
            text=p_data.get("text", ""),
            # ...etc
        )
        passages.append(passage)
```

2. Writing:

```python
def _write_json(story: TwineStory, path: Path) -> None:
    data = {
        "name": story.metadata.name,
        "format": story.metadata.format,
        # ...etc
        "passages": [],
    }

    for passage in story.passages:
        p_data = {
            "name": passage.name,
            "text": passage.text,
            "tags": passage.tags,
            # ...etc
        }
        data["passages"].append(p_data)

    path.write_text(json.dumps(data, indent=2))
```

### Error Handling

1. Format Detection:

```python
def read_twine(path: Path) -> DLG:
    content = path.read_text()
    if content.strip().startswith("{"):
        return _read_json(content)
    elif content.strip().startswith("<"):
        return _read_html(content)
    else:
        raise ValueError("Invalid Twine format")
```

2. Invalid Content:

```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON: {e}")

try:
    root = ElementTree.fromstring(content)
except ElementTree.ParseError as e:
    raise ValueError(f"Invalid HTML: {e}")
```

3. Missing Fields:

```python
story_data = root.find(".//tw-storydata")
if story_data is None:
    raise ValueError("No story data found")
```

### Type Safety

1. Generic Types:

```python
T = TypeVar("T", bound=DLGNode)

class DLGLink(Generic[T]):
    node: T
```

2. Runtime Checks:

```python
def process_node(node: DLGNode) -> None:
    if isinstance(node, DLGEntry):
        # Handle entry
    elif isinstance(node, DLGReply):
        # Handle reply
    else:
        raise TypeError(f"Unknown node type: {type(node)}")
```

3. Type Hints:

```python
def write_twine(
    dlg: DLG,
    path: str | Path,
    format: Literal["html", "json"] = "html",
    metadata: dict[str, Any] | None = None,
) -> None:
    ...
```

## Performance Considerations

1. Memory Usage:

- Use generators for large dialogs
- Avoid redundant data structures
- Clear processed nodes after use

2. Speed:

- Cache node lookups
- Minimize XML/JSON parsing
- Use efficient data structures

3. File Size:

- JSON format is more compact
- Minimize metadata duplication
- Use efficient encoding

## Testing Strategy

1. Unit Tests:

- Basic conversion
- Edge cases
- Format-specific features

2. Integration Tests:

- Round-trip conversion
- Large dialogs
- Real-world examples

3. Error Cases:

- Invalid formats
- Missing fields
- Malformed content

## Future Improvements

1. Planned Features:

   - Multi-language support
   - Custom metadata schemas
   - Advanced link types

1. Optimizations:

   - Parallel processing
   - Streaming I/O
   - Memory reduction

1. Extensions:

   - Custom format support
   - Validation rules
   - Migration tools
