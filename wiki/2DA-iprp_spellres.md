# iprp_spellres.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to spell resistance calculations. The engine uses this file to determine spell resistance calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Spell resistance mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:592`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L592) - GFF field mapping: "SpellResistance" -> iprp_spellres.2da

---

