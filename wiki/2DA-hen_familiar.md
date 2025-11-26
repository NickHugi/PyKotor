# hen_familiar.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines familiar configurations (HEN - Henchman system). The engine uses this file to determine familiar base resource references (not used in game engine).

**Row Index**: Familiar ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Familiar label |
| `baseresref` | ResRef | Base resource reference for familiar (not used in game engine) |
| Additional columns | Various | Familiar properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:158`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L158) - ResRef column definition for hen_familiar.2da (baseresref, not used in engine)

---

