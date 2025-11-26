# droiddischarge.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines droid discharge effect configurations. The engine uses this file to determine droid discharge properties.

**Row Index**: Droid Discharge ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Droid discharge label |
| `>>##HEADER##<<` | ResRef | Header resource reference |
| Additional columns | Various | Droid discharge properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:156`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L156) - ResRef column definition for droiddischarge.2da

---

