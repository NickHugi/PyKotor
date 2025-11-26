# ai_styles.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines AI behavior styles for creatures. The engine uses this file to determine AI behavior patterns and combat strategies.

**Row Index**: AI Style ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AI style label |
| Additional columns | Various | AI behavior parameters |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:572`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L572) - GFF field mapping: "AIStyle" -> ai_styles.2da

---

