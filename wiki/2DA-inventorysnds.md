# inventorysnds.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines inventory sound configurations. The engine uses this file to determine inventory sound effects for item interactions.

**Row Index**: Inventory Sound ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Inventory sound label |
| `inventorysound` | ResRef | Inventory sound ResRef |
| Additional columns | Various | Inventory sound properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:201`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L201) - Sound ResRef column definition for inventorysnds.2da

---

