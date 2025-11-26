# tutorial_old.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines old tutorial message configurations (legacy). The engine uses this file to determine tutorial messages (replaced by `tutorial.2da` in newer versions).

**Row Index**: Tutorial Message ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tutorial message label |
| `message0` through `message2` | StrRef | String references for tutorial messages |
| Additional columns | Various | Tutorial message properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:147`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L147) - StrRef column definitions for tutorial_old.2da

---

