# aiscripts.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines AI script templates and their properties. The engine uses this file to determine AI script names and descriptions (KotOR 1 only; KotOR 2 uses `name_strref` only).

**Row Index**: AI Script ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | AI script label |
| `name_strref` | StrRef | String reference for AI script name |
| `description_strref` | StrRef | String reference for AI script description (KotOR 1 only) |
| Additional columns | Various | AI script properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:71`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L71) - StrRef column definitions for aiscripts.2da (K1: name_strref, description_strref; K2: name_strref only)

---

