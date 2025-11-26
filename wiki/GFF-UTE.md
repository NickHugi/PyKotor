# UTE (Encounter)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTE files define encounter templates which spawn creatures when triggered by the player. Encounters handle spawning logic, difficulty scaling, respawning, and faction settings for groups of enemies or neutral creatures.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/ute.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/ute.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this encounter |
| `Tag` | CExoString | Unique tag for script references |
| `LocalizedName` | CExoLocString | Encounter name (unused in game) |
| `Comment` | CExoString | Developer comment/notes |

## Spawn Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Encounter is currently active |
| `Difficulty` | Int | Difficulty setting (unused) |
| `DifficultyIndex` | Int | Difficulty scaling index |
| `Faction` | Word | Faction of spawned creatures |
| `MaxCreatures` | Int | Maximum concurrent creatures |
| `RecCreatures` | Int | Recommended number of creatures |
| `SpawnOption` | Int | Spawn behavior (0=Continuous, 1=Single Shot) |

**Spawn Behavior:**

- **Active**: If 0, encounter won't trigger until activated by script
- **MaxCreatures**: Hard limit on spawned entities to prevent overcrowding
- **RecCreatures**: Target number to maintain
- **SpawnOption**: Single Shot encounters fire once and disable

## Respawn Logic

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Reset` | Byte | Encounter resets after being cleared |
| `ResetTime` | Int | Time in seconds before reset |
| `Respawns` | Int | Number of times it can respawn (-1 = infinite) |

**Respawn System:**

- Allows for renewable enemy sources
- **ResetTime**: Cooldown period after players leave area
- **Respawns**: Limits farming/grinding

## Creature List

| Field | Type | Description |
| ----- | ---- | ----------- |
| `CreatureList` | List | List of creatures to spawn |

**CreatureList Struct Fields:**

- `ResRef` (ResRef): UTC template to spawn
- `Appearance` (Int): Appearance type (optional override)
- `CR` (Float): Challenge Rating
- `SingleSpawn` (Byte): Unique spawn flag

**Spawn Selection:**

- Engine selects from CreatureList based on CR and difficulty
- Random selection weighted by difficulty settings

## Trigger Logic

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PlayerOnly` | Byte | Only triggers for player (not NPCs) |
| `OnEntered` | ResRef | Script fires when trigger entered |
| `OnExit` | ResRef | Script fires when trigger exited |
| `OnExhausted` | ResRef | Script fires when spawns depleted |
| `OnHeartbeat` | ResRef | Script fires periodically |
| `OnUserDefined` | ResRef | Script fires on user events |

**Implementation Notes:**

- Encounters are volumes (geometry defined in GIT)
- Spawning happens when volume is entered
- Creatures spawn at specific spawn points (UTW) or random locations

