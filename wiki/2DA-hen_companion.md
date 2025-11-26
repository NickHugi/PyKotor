# hen_companion.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines companion configurations (HEN - Henchman system). The engine uses this file to determine companion names and base resource references.

**Row Index**: Companion ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Companion label |
| `strref` | StrRef | String reference for companion name |
| `baseresref` | ResRef | Base resource reference for companion (not used in game engine) |
| Additional columns | Various | Companion properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:87`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L87) - StrRef column definition for hen_companion.2da
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L157) - ResRef column definition for hen_companion.2da (baseresref, not used in engine)

---

