# classpowergain.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines Force power progression by class and level. The engine uses this file to determine which Force powers are available to each class at each level.

**Row Index**: Level (integer, typically 1-20)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `level` | Integer | Character level |
| `jedi_guardian` | Integer | Jedi Guardian power gain |
| `jedi_consular` | Integer | Jedi Consular power gain |
| `jedi_sentinel` | Integer | Jedi Sentinel power gain |
| `soldier` | Integer | Soldier power gain |
| `scout` | Integer | Scout power gain |
| `scoundrel` | Integer | Scoundrel power gain |
| `jedi_guardian_prestige` | Integer (optional) | Jedi Guardian prestige power gain |
| `jedi_consular_prestige` | Integer (optional) | Jedi Consular prestige power gain |
| `jedi_sentinel_prestige` | Integer (optional) | Jedi Sentinel prestige power gain |

---

