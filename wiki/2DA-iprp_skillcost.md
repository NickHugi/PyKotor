# iprp_skillcost.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to skill bonus calculations. The engine uses this file to determine skill bonus cost calculations for item properties.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Skill bonus mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:584`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L584) - GFF field mapping: "SkillBonus" -> iprp_skillcost.2da

---

