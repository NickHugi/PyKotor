# iprp_monstdam.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to monster damage bonuses. The engine uses this file to determine damage bonus calculations for monster weapons.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Monster damage mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:580`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L580) - GFF field mapping: "MonsterDamage" -> iprp_monstdam.2da

---

