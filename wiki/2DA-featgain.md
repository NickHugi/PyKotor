# featgain.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines feat gain progression by class and level. The engine uses this file to determine which feats are available to each class at each level.

**Row Index**: Feat Gain Entry ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Feat gain entry label |
| Additional columns | Various | Feat gain progression by class and level |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:101-105`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L101-L105) - Feat gain initialization from 2DA

---

