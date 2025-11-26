# pazaakdecks.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines Pazaak card decks for the Pazaak mini-game. The engine uses this file to determine which cards are available in opponent decks and player decks.

**Row Index**: Pazaak Deck ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Deck label |
| Additional columns | Various | Deck card definitions and properties |

**References**:

- [`vendor/KotOR.js/src/engine/rules/SWRuleSet.ts:178-185`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/engine/rules/SWRuleSet.ts#L178-L185) - Pazaak decks initialization from 2DA
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts:4438`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts#L4438) - StartPazaakGame function comment
- [`vendor/NorthernLights/nwscript.nss:3847`](https://github.com/th3w1zard1/NorthernLights/blob/master/nwscript.nss#L3847) - Comment referencing PazaakDecks.2da

---

