# modulesave.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines which modules should be included in save games. The engine uses this file to determine whether a module's state should be persisted when saving the game.

**Row Index**: Module Index (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Module label |
| `modulename` | String | Module filename (e.g., "001ebo") |
| `includeInSave` | Boolean | Whether module state should be saved (0 = false, 1 = true) |

**References**:

- [`vendor/KotOR.js/src/module/Module.ts:663-669`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts#L663-L669) - Module save inclusion check from 2DA

---

