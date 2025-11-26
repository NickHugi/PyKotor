# texpacks.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines texture pack configurations for graphics settings (KotOR 2 only). The engine uses this file to determine available texture pack options in the graphics menu.

**Row Index**: Texture Pack ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Texture pack label |
| `strrefname` | StrRef | String reference for texture pack name |
| Additional columns | Various | Texture pack properties and settings |

**References**:

- [`vendor/KotOR.js/src/game/tsl/menu/MenuGraphicsAdvanced.ts:51-122`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/tsl/menu/MenuGraphicsAdvanced.ts#L51-L122) - Texture pack loading from 2DA for graphics menu (KotOR 2 only)
- [`vendor/KotOR.js/src/game/kotor/menu/MenuGraphicsAdvanced.ts:63-121`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/game/kotor/menu/MenuGraphicsAdvanced.ts#L63-L121) - Texture pack usage in KotOR 1 graphics menu

---

