# upgrade.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines item upgrade types and properties. The engine uses this file to determine which upgrades can be applied to items and their effects.

**Row Index**: Upgrade Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Upgrade type label |
| Additional columns | Various | Upgrade properties and effects |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:473`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L473) - TwoDARegistry definition
- [`Tools/HolocronToolset/src/toolset/data/installation.py:72`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L72) - HTInstallation constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:632-639`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L632-L639) - Upgrade selection in item editor

---

