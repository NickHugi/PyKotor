# UTP (Placeable)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTP files define placeable object templates including containers, furniture, switches, workbenches, and interactive environmental objects. Placeables can have inventories, be destroyed, locked, trapped, and trigger scripts.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utp.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utp.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this placeable |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Placeable name (localized) |
| `Description` | CExoLocString | Placeable description |
| `Comment` | CExoString | Developer comment/notes |

## Appearance & Type

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | Index into `placeables.2da` |
| `Type` | Byte | Placeable type category |
| `AnimationState` | Byte | Current animation state |

**Appearance System:**

- `placeables.2da` defines models, lighting, and sounds
- Appearance determines visual model and interaction animation
- Type influences behavior (container, switch, generic)

## Inventory System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HasInventory` | Byte | Placeable contains items |
| `ItemList` | List | Items in inventory |
| `BodyBag` | Byte | Container for corpse loot |

**ItemList Struct Fields:**

- `InventoryRes` (ResRef): UTI template ResRef
- `Repos_PosX` (Word): Grid X position (optional)
- `Repos_Posy` (Word): Grid Y position (optional)
- `Dropable` (Byte): Can drop item

**Container Behavior:**

- **HasInventory=1**: Can be looted
- **BodyBag=1**: Corpse container (special loot rules)
- ItemList populated on placeable instantiation
- Empty containers can still be interacted with

## Locking & Security

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Placeable is currently locked |
| `Lockable` | Byte | Can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific key item |
| `KeyName` | CExoString | Tag of required key item |
| `AutoRemoveKey` | Byte | Key consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | Byte | Security DC to lock |
| `OpenLockDiff` (KotOR2) | Int | Additional difficulty modifier |
| `OpenLockDiffMod` (KotOR2) | Int | Modifier to difficulty |

**Lock Mechanics:**

- Identical to UTD door locking system
- Prevents access to inventory
- Can be picked or opened with key

## Hit Points & Durability

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | Byte | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (usually 0) |
| `Ref` | Byte | Reflex save (usually 0) |
| `Will` | Byte | Will save (usually 0) |

**Destructible Placeables:**

- Containers, crates, and terminals can have HP
- Some placeables reveal items when destroyed
- Hardness reduces incoming damage

## Interaction & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Static geometry (no interaction) |
| `Useable` | Byte | Can be clicked/used |
| `Conversation` | ResRef | Dialog file when used |
| `Faction` | Word | Faction identifier |
| `PartyInteract` | Byte | Requires party member selection |
| `NotBlastable` (KotOR2) | Byte | Immune to area damage |

**Usage Patterns:**

- **Useable=0**: Cannot be directly interacted with
- **Conversation**: Triggers dialog on use (terminals, panels)
- **PartyInteract**: Shows party selection GUI
- **Static**: Pure visual element, no gameplay

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnClosed` | ResRef | Fires when container closes |
| `OnDamaged` | ResRef | Fires when placeable takes damage |
| `OnDeath` | ResRef | Fires when placeable is destroyed |
| `OnDisarm` | ResRef | Fires when trap is disarmed |
| `OnEndDialogue` | ResRef | Fires when conversation ends |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnInvDisturbed` | ResRef | Fires when inventory changed |
| `OnLock` | ResRef | Fires when locked |
| `OnMeleeAttacked` | ResRef | Fires when attacked in melee |
| `OnOpen` | ResRef | Fires when opened |
| `OnSpellCastAt` | ResRef | Fires when spell cast at placeable |
| `OnUnlock` | ResRef | Fires when unlocked |
| `OnUsed` | ResRef | Fires when used/clicked |
| `OnUserDefined` | ResRef | Fires on user-defined events |
| `OnFailToOpen` (KotOR2) | ResRef | Fires when opening fails |

## Trap System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TrapDetectable` | Byte | Trap can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect trap |
| `TrapDisarmable` | Byte | Trap can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm trap |
| `TrapFlag` | Byte | Trap is active |
| `TrapOneShot` | Byte | Trap triggers only once |
| `TrapType` | Byte | Index into `traps.2da` |

**Trap Behavior:**

- Identical to door trap system
- Triggers on placeable use
- Common on containers and terminals

## Visual Customization

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**Model & Lighting:**

- Appearance determines model and light color
- Some placeables have animated components
- Light properties defined in `placeables.2da`

## Implementation Notes

**Placeable Categories:**

**Containers:**

- Footlockers, crates, corpses
- Have inventory (ItemList populated)
- Can be locked, trapped, destroyed
- `HasInventory=1`, `BodyBag` flag for corpses

**Switches & Terminals:**

- Trigger scripts or conversations
- No inventory typically
- `Useable=1`, `Conversation` or scripts set
- Common for puzzle activation

**Workbenches:**

- Special placeable type for crafting
- Opens crafting interface on use
- Defined by Type or Appearance

**Furniture:**

- Non-interactive decoration
- `Static=1` or `Useable=0`
- Pure visual elements

**Environmental Objects:**

- Explosive containers, power generators
- Can be destroyed with effects
- Often have HP and OnDeath scripts

**Instantiation Flow:**

1. **Template Load**: GFF parsed from UTP
2. **Appearance Setup**: Model loaded from `placeables.2da`
3. **Inventory Population**: ItemList instantiated
4. **Lock State**: Locked status applied
5. **Trap Activation**: Trap armed if configured
6. **Script Registration**: Event handlers registered

**Container Loot:**

- ItemList defines initial inventory
- Random loot can be added via script
- OnInvDisturbed fires when items taken
- BodyBag containers have special loot rules

**Conversation Placeables:**

- Terminals, control panels, puzzle interfaces
- Conversation property set to DLG file
- Use triggers dialog instead of direct interaction
- Dialog can have conditional responses

**Common Placeable Types:**

**Storage Containers:**

- Footlockers, crates, bins
- Standard inventory interface
- Often locked or trapped

**Corpses:**

- BodyBag flag set
- Contain enemy loot
- Disappear when looted (usually)

**Terminals:**

- Computer interfaces
- Trigger conversations or scripts
- May require Computer Use skill checks

**Switches:**

- Activate doors, puzzles, machinery
- Fire OnUsed script
- Visual feedback animation

**Workbenches:**

- Crafting interface activation
- Lab stations, upgrade benches
- Special Type value

**Decorative Objects:**

- No gameplay interaction
- Static or non-useable
- Environmental detail

**Mines (Special Case):**

- Placed as placeable or creature
- Trap properties define behavior
- Can be detected and disarmed
- Trigger on proximity or interaction

