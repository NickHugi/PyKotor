# cursors.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines cursor types for different object interactions. The engine uses this file to determine which cursor to display when hovering over different object types.

**Row Index**: Cursor ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Cursor label |
| Additional columns | Various | Cursor properties and ResRefs |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:469`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L469) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:68`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L68) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utt.py:71-76`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utt.py#L71-L76) - Cursor selection in trigger editor

---

