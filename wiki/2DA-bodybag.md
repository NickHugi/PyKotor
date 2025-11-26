# bodybag.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines body bag appearances for creatures when they die. The engine uses this file to determine which appearance to use for the body bag container that appears when a creature is killed.

**Row Index**: Body Bag ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Body bag label |
| `name` | StrRef | String reference for body bag name |
| `appearance` | Integer | Appearance ID for the body bag model |
| `corpse` | Boolean | Whether the body bag represents a corpse |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:536`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L536) - GFF field mapping: "BodyBag" -> bodybag.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:296-298`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L296-L298) - UTC bodybag_id field documentation (not used by game engine)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:438`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L438) - UTC bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:555-556`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L555-L556) - BodyBag field parsing from UTC GFF (deprecated)
- [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py:944`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py#L944) - BodyBag field writing to UTC GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:105`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L105) - UTP bodybag_id field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:179`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L179) - UTP bodybag_id field initialization
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:254`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L254) - BodyBag field parsing from UTP GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py:341`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py#L341) - BodyBag field writing to UTP GFF

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/object/creature.cpp:1357-1366`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1357-L1366) - Body bag loading from 2DA

---

