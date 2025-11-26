# stringtokens.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines string token configurations. The engine uses this file to determine string token values for various game systems.

**Row Index**: String Token ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | String token label |
| `strref1` through `strref4` | StrRef | String references for token values |
| Additional columns | Various | String token properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:144`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L144) - StrRef column definitions for stringtokens.2da

---

