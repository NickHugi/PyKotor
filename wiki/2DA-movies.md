# movies.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines movie/cutscene configurations. The engine uses this file to determine movie names and descriptions.

**Row Index**: Movie ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Movie label |
| `strrefname` | StrRef | String reference for movie name |
| `strrefdesc` | StrRef | String reference for movie description |
| Additional columns | Various | Movie properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:140`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L140) - StrRef column definitions for movies.2da

---

