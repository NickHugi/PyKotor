# ambientsound.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines ambient sound effects for areas. The engine uses this file to play ambient sounds in areas.

**Row Index**: Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound label |
| `sound` | ResRef | Sound file ResRef |
| `resource` | ResRef | Sound resource ResRef |
| `description` | StrRef | Sound description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:72`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L72) - StrRef column definition for ambientsound.2da (K1: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:184`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L184) - Sound ResRef column definition for ambientsound.2da (K1: resource)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:247`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L247) - StrRef column definition for ambientsound.2da (K2: description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:376`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L376) - Sound ResRef column definition for ambientsound.2da (K2: resource)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py:6986-6988`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py#L6986-L6988) - AmbientSoundPlay function comment

---

