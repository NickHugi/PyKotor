# videoeffects.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines video/camera effects for dialog conversations. The engine uses this file to determine which visual effect to apply during dialog camera shots.

**Row Index**: Video Effect ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Video effect label |
| Additional columns | Various | Video effect properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:493`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L493) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:92`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L92) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py:1263-1298`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/dlg/editor.py#L1263-L1298) - Video effect loading in dialog editor

---

