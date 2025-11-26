# textures.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines texture variation configurations. The engine uses this file to determine texture variation assignments for objects that support texture variations.

**Row Index**: Texture Variation ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Texture variation label |
| Additional columns | Various | Texture variation properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:540`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L540) - GFF field mapping: "TextureVar" -> textures.2da

---

