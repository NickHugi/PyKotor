# UTC (Creature)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTC files define creature templates including NPCs, party members, enemies, and the player character. They are comprehensive GFF files containing all data needed to spawn and control a creature in the game world.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utc.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utc.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this creature |
| `Tag` | CExoString | Unique tag for script/conversation references |
| `FirstName` | CExoLocString | Creature's first name (localized) |
| `LastName` | CExoLocString | Creature's last name (localized) |
| `Comment` | CExoString | Developer comment/notes |

## Appearance & Visuals

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance_Type` | DWord | Index into `appearance.2da` |
| `PortraitId` | Word | Index into `portraits.2da` |
| `Gender` | Byte | 0=Male, 1=Female, 2=Both, 3=Other, 4=None |
| `Race` | Word | Index into `racialtypes.2da` |
| `SubraceIndex` | Byte | Subrace identifier |
| `BodyVariation` | Byte | Body model variation (0-9) |
| `TextureVar` | Byte | Texture variation (1-9) |
| `SoundSetFile` | Word | Index into sound set table |

## Core Stats & Attributes

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Str` | Byte | Strength score (3-255) |
| `Dex` | Byte | Dexterity score (3-255) |
| `Con` | Byte | Constitution score (3-255) |
| `Int` | Byte | Intelligence score (3-255) |
| `Wis` | Byte | Wisdom score (3-255) |
| `Cha` | Byte | Charisma score (3-255) |
| `HitPoints` | Short | Current hit points |
| `CurrentHitPoints` | Short | Alias for hit points |
| `MaxHitPoints` | Short | Maximum hit points |
| `ForcePoints` | Short | Current Force points (KotOR specific) |
| `CurrentForce` | Short | Alias for Force points |
| `MaxForcePoints` | Short | Maximum Force points |

## Character Progression

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ClassList` | List | List of character classes with levels |
| `Experience` | DWord | Total experience points |
| `LevelUpStack` | List | Pending level-up choices |
| `SkillList` | List | Skill ranks (index + rank) |
| `FeatList` | List | Acquired feats |
| `SpecialAbilityList` | List | Special abilities/powers |

**ClassList Struct Fields:**

- `Class` (Int): Index into `classes.2da`
- `ClassLevel` (Short): Levels in this class

**SkillList Struct Fields:**

- `Rank` (Byte): Skill rank value

**FeatList Struct Fields:**

- `Feat` (Word): Index into `feat.2da`

## Combat & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `FactionID` | Word | Faction identifier (determines hostility) |
| `NaturalAC` | Byte | Natural armor class bonus |
| `ChallengeRating` | Float | CR for encounter calculations |
| `PerceptionRange` | Byte | Perception distance category |
| `WalkRate` | Int | Movement speed identifier |
| `Interruptable` | Byte | Can be interrupted during actions |
| `NoPermDeath` | Byte | Cannot permanently die |
| `IsPC` | Byte | Is player character |
| `Plot` | Byte | Plot-critical (cannot die) |
| `MinOneHP` | Byte | Cannot drop below 1 HP |
| `PartyInteract` | Byte | Shows party selection interface |
| `Hologram` | Byte | Rendered as hologram |

## Equipment & Inventory

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ItemList` | List | Inventory items |
| `Equip_ItemList` | List | Equipped items with slots |
| `EquippedRes` | ResRef | Deprecated equipment field |

**ItemList Struct Fields:**

- `InventoryRes` (ResRef): UTI template ResRef
- `Repos_PosX` (Word): Inventory grid X position
- `Repos_Posy` (Word): Inventory grid Y position
- `Dropable` (Byte): Can be dropped/removed

**Equip_ItemList Struct Fields:**

- `EquippedRes` (ResRef): UTI template ResRef
- Equipment slots reference `equipmentslots.2da`

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ScriptAttacked` | ResRef | Fires when attacked |
| `ScriptDamaged` | ResRef | Fires when damaged |
| `ScriptDeath` | ResRef | Fires on death |
| `ScriptDialogue` | ResRef | Fires when conversation starts |
| `ScriptDisturbed` | ResRef | Fires when inventory disturbed |
| `ScriptEndRound` | ResRef | Fires at combat round end |
| `ScriptEndDialogue` | ResRef | Fires when conversation ends |
| `ScriptHeartbeat` | ResRef | Fires periodically |
| `ScriptOnBlocked` | ResRef | Fires when movement blocked |
| `ScriptOnNotice` | ResRef | Fires when notices something |
| `ScriptRested` | ResRef | Fires after rest |
| `ScriptSpawn` | ResRef | Fires on spawn |
| `ScriptSpellAt` | ResRef | Fires when spell cast at creature |
| `ScriptUserDefine` | ResRef | Fires on user-defined events |

## KotOR-Specific Features

**Alignment:**

- `GoodEvil` (Byte): 0-100 scale (0=Dark, 100=Light)
- `LawfulChaotic` (Byte): Unused in KotOR

**Multiplayer (Unused in KotOR):**

- `Deity` (CExoString)
- `Subrace` (CExoString)
- `Morale` (Byte)
- `MorealBreak` (Byte)

**Special Abilities:**

- Stored in `SpecialAbilityList` referencing `spells.2da` or feat-based abilities

## Implementation Notes

UTC files are loaded during module initialization or creature spawning. The engine:

1. **Reads template data** from the UTC GFF structure
2. **Applies appearance** based on `appearance.2da` lookup
3. **Calculates derived stats** (AC, saves, attack bonuses) from attributes and equipment
4. **Loads inventory** by instantiating UTI templates
5. **Applies effects** from equipped items and active powers
6. **Registers scripts** for the creature's event handlers

**Performance Considerations:**

- Complex creatures with many items/feats increase load time
- Script hooks fire frequently - keep handlers optimized
- Large SkillList/FeatList structures add memory overhead

**Common Use Cases:**

- **Party Members**: Full UTC with all progression data, complex equipment
- **Plot NPCs**: Basic stats, specific appearance, dialogue scripts
- **Generic Enemies**: Minimal data, shared appearance, basic AI scripts
- **Vendors**: Specialized with store inventory, merchant scripts
- **Placeables As Creatures**: Invisible creatures for complex scripting

