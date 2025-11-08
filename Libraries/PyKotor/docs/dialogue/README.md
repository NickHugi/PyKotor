# Dialog System Documentation

PyKotor's dialog system supports multiple formats for handling game conversations:

## Native Format

- GFF (Generic File Format) - The primary format used by KotOR games

## Twine Format Support

- [Quick Start Guide](twine_quickstart.md) - Get started with Twine format
- [Format Documentation](twine_format.md) - Detailed format documentation
- [Technical Reference](twine_format_technical.md) - Implementation details
- [Troubleshooting Guide](twine_troubleshooting.md) - Common issues and solutions

## Features

### Format Support

- Native KotOR GFF format
- Twine 2 HTML format
- Twine 2 JSON format

### Conversion

- GFF ↔ Twine conversion
- Metadata preservation
- Link structure preservation

### Editor Support

- Visual editing in Twine
- Node positioning
- Custom styling
- Tag colors

### Extensibility

- Custom metadata
- Format validation
- Error handling

## Getting Started

1. Basic Usage:

```python
from pykotor.resource.generics.dlg import read_twine, write_twine

# Convert KotOR to Twine
write_twine(dlg, "dialog.html")

# Convert Twine to KotOR
dlg = read_twine("dialog.html")
```

2. Check the [Quick Start Guide](twine_quickstart.md) for more examples

3. Read the [Format Documentation](twine_format.md) for details

4. See the [Troubleshooting Guide](twine_troubleshooting.md) if you run into issues

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
