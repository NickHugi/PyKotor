# iprp_attackmod.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to attack modifier bonuses. The engine uses this file to determine attack bonus calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Attack modifier mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:575`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L575) - GFF field mapping: "AttackModifier" -> iprp_attackmod.2da

---

