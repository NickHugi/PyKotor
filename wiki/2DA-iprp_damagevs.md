# iprp_damagevs.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to damage vs. specific creature type bonuses. The engine uses this file to determine damage bonuses against specific creature types.

**Row Index**: Item Property Value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| Additional columns | Various | Damage vs. creature type mappings |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:574`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L574) - GFF field mapping: "DamageVsType" -> iprp_damagevs.2da

---

