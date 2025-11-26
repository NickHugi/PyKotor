# gamespyrooms.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines GameSpy room configurations for multiplayer (if supported). The engine uses this file to determine GameSpy room names and properties.

**Row Index**: GameSpy Room ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | GameSpy room label |
| `str_ref` | StrRef | String reference for GameSpy room name |
| Additional columns | Various | GameSpy room properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:85`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L85) - StrRef column definition for gamespyrooms.2da

---

