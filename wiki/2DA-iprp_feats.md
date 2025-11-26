# iprp_feats.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps item property values to feat bonuses. When an item grants a feat bonus, this table determines which feat is granted based on the property value.

**Row Index**: Item property value (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property value label |
| `feat` | Integer | Feat ID granted by this property value |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L102) - StrRef column definition for iprp_feats.2da (K1: name)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:280`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L280) - StrRef column definition for iprp_feats.2da (K2: name)

---

