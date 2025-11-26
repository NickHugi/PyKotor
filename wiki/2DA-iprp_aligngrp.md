# iprp_aligngrp.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to alignment group restrictions. The engine uses this file to determine alignment restrictions for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Alignment group mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:479`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L479) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L78) - HTInstallation constant

---

