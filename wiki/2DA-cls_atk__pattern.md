# cls_atk_*.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Base attack bonus progression tables for each class. Files are named `cls_atk_<classname>.2da` (e.g., `cls_atk_jedi_guardian.2da`). The engine uses these files to calculate attack bonuses for each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `attackbonus` | Integer | Base attack bonus at this level |

---

