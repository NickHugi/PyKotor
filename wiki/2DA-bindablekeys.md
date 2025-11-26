# bindablekeys.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines bindable key actions and their string references. The engine uses this file to determine key action names for the key binding interface.

**Row Index**: Bindable Key ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Bindable key label |
| `keynamestrref` | StrRef | String reference for key name |
| Additional columns | Various | Key binding properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L74) - StrRef column definition for bindablekeys.2da

---

