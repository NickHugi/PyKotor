# cls_savthr_*.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Saving throw progression tables for each class. Files are named `cls_savthr_<classname>.2da` (e.g., `cls_savthr_jedi_guardian.2da`). The engine uses these files to calculate saving throw bonuses for each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `fortitude` | Integer | Fortitude save bonus |
| `reflex` | Integer | Reflex save bonus |
| `will` | Integer | Will save bonus |

---

