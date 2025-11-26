# planetary.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines planetary information for the galaxy map and travel system. The engine uses this file to determine planet names, descriptions, and travel properties.

**Row Index**: Planet ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Planet label |
| Additional columns | Various | Planet properties and travel information |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:495`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L495) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:94`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L94) - HTInstallation constant

---

