# disease.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines disease effect configurations. The engine uses this file to determine disease names, scripts, and properties.

**Row Index**: Disease ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Disease label |
| `name` | StrRef | String reference for disease name (KotOR 2) |
| `end_incu_script` | ResRef | Script ResRef for end incubation period |
| `24_hour_script` | ResRef | Script ResRef for 24-hour disease effect |
| Additional columns | Various | Disease properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:255`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L255) - StrRef column definition for disease.2da (KotOR 2)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:238,431`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L238) - Script ResRef column definitions for disease.2da

---

