# minglobalrim.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines minimum global RIM configurations. The engine uses this file to determine module resource references.

**Row Index**: Global RIM ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Global RIM label |
| `moduleresref` | ResRef | Module resource reference |
| Additional columns | Various | Global RIM properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:161`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L161) - ResRef column definition for minglobalrim.2da

---

