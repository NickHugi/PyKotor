# doortypes.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines door type configurations and their properties. The engine uses this file to determine door type names, models, and behaviors.

**Row Index**: Door Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Door type label |
| `stringrefgame` | StrRef | String reference for door type name |
| `model` | ResRef | Model ResRef for the door type |
| Additional columns | Various | Door type properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:78`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L78) - StrRef column definition for doortypes.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:177`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L177) - Model ResRef column definition for doortypes.2da

---

