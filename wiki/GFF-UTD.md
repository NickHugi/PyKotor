# UTD (Door)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTD files define door templates for all interactive doors in the game world. Doors can be locked, require keys, have hit points, conversations, and various gameplay interactions.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utd.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utd.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this door |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Door name (localized) |
| `Description` | CExoLocString | Door description |
| `Comment` | CExoString | Developer comment/notes |

## Door Appearance & Type

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Appearance` | DWord | Index into `genericdoors.2da` |
| `GenericType` | DWord | Generic door type category |
| `AnimationState` | Byte | Current animation state (always 0 in templates) |

**Appearance System:**

- `genericdoors.2da` defines door models and animations
- Different appearance types support different behaviors
- Opening animation determined by appearance entry

## Locking & Security

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Locked` | Byte | Door is currently locked |
| `Lockable` | Byte | Door can be locked/unlocked |
| `KeyRequired` | Byte | Requires specific key item |
| `KeyName` | CExoString | Tag of required key item |
| `AutoRemoveKey` | Byte | Key consumed on use |
| `OpenLockDC` | Byte | Security skill DC to pick lock |
| `CloseLockDC` (KotOR2) | Byte | Security skill DC to lock door |

**Lock Mechanics:**

- **Locked**: Door cannot be opened normally
- **KeyRequired**: Must have key in inventory
- **OpenLockDC**: Player rolls Security skill vs. DC
- **AutoRemoveKey**: Key destroyed after successful use

## Hit Points & Durability

| Field | Type | Description |
| ----- | ---- | ----------- |
| `HP` | Short | Maximum hit points |
| `CurrentHP` | Short | Current hit points |
| `Hardness` | Byte | Damage reduction |
| `Min1HP` (KotOR2) | Byte | Cannot drop below 1 HP |
| `Fort` | Byte | Fortitude save (always 0) |
| `Ref` | Byte | Reflex save (always 0) |
| `Will` | Byte | Will save (always 0) |

**Destructible Doors:**

- Doors with HP can be attacked and destroyed
- **Hardness** reduces each hit's damage
- **Min1HP** prevents destruction (plot doors)
- Save values unused in KotOR

## Interaction & Behavior

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Plot` | Byte | Plot-critical (cannot be destroyed) |
| `Static` | Byte | Door is static geometry (no interaction) |
| `Interruptable` | Byte | Opening can be interrupted |
| `Conversation` | ResRef | Dialog file when used |
| `Faction` | Word | Faction identifier |
| `AnimationState` | Byte | Starting animation (0=closed, other values unused) |

**Conversation Doors:**

- When clicked, triggers dialogue instead of opening
- Useful for password entry, NPC interactions
- Dialog can conditionally open door via script

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnOpen` | ResRef | Fires when door opens |
| `OnClose` | ResRef | Fires when door closes |
| `OnClosed` | ResRef | Fires after door finishes closing |
| `OnDamaged` | ResRef | Fires when door takes damage |
| `OnDeath` | ResRef | Fires when door is destroyed |
| `OnDisarm` | ResRef | Fires when trap is disarmed |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnLock` | ResRef | Fires when door is locked |
| `OnMeleeAttacked` | ResRef | Fires when attacked in melee |
| `OnSpellCastAt` | ResRef | Fires when spell cast at door |
| `OnUnlock` | ResRef | Fires when door is unlocked |
| `OnUserDefined` | ResRef | Fires on user-defined events |
| `OnClick` | ResRef | Fires when clicked |
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

**Trap Mechanics:**

1. **Detection**: Player rolls Awareness vs. `TrapDetectDC`
2. **Disarm**: Player rolls Security vs. `DisarmDC`
3. **Trigger**: If not detected/disarmed, trap fires on door use
4. **One-Shot**: Trap disabled after first trigger

## Load-Bearing Doors (KotOR2)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LoadScreenID` (KotOR2) | Word | Loading screen to show |
| `LinkedTo` (KotOR2) | CExoString | Destination module tag |
| `LinkedToFlags` (KotOR2) | Byte | Transition behavior flags |
| `LinkedToModule` (KotOR2) | ResRef | Destination module ResRef |
| `TransitionDestin` (KotOR2) | CExoLocString | Destination label |

**Transition System:**

- Doors can load new modules/areas
- Loading screen displayed during transition
- Linked destination defines spawn point

## Appearance Customization

| Field | Type | Description |
| ----- | ---- | ----------- |
| `PortraitId` | Word | Portrait icon identifier |
| `PaletteID` | Byte | Toolset palette category |

**Visual Representation:**

- `Appearance` determines 3D model
- Some doors have customizable textures
- Portrait used in UI elements

## Implementation Notes

**Door State Machine:**

Doors maintain runtime state:

1. **Closed**: Default state, blocking
2. **Opening**: Animation playing, becoming non-blocking
3. **Open**: Fully open, non-blocking
4. **Closing**: Animation playing, becoming blocking
5. **Locked**: Closed and cannot open
6. **Destroyed**: Hit points depleted, permanently open

**Opening Sequence:**

1. Player clicks door
2. If conversation set, start dialog
3. If locked, check for key or Security skill
4. If trapped, check for detection/disarm
5. Fire `OnOpen` script
6. Play opening animation
7. Transition to "open" state

**Locking System:**

- **Lockable=0**: Door cannot be locked (always opens)
- **Locked=1, KeyRequired=1**: Must have specific key
- **Locked=1, OpenLockDC>0**: Can pick lock with Security skill
- **Locked=1, KeyRequired=0, OpenLockDC=0**: Locked via script only

**Common Door Types:**

**Standard Doors:**

- Simple open/close
- No lock, HP, or trap
- Used for interior navigation

**Locked Doors:**

- Requires key or Security skill
- Quest progression gates
- May have conversation for passwords

**Destructible Doors:**

- Have HP and Hardness
- Can be bashed down
- Alternative to lockpicking

**Trapped Doors:**

- Trigger trap on opening
- Require detection and disarming
- Often in hostile areas

**Transition Doors:**

- Load new modules/areas
- Show loading screens
- Used for major location changes

**Conversation Doors:**

- Trigger dialog on click
- May open after conversation
- Used for password entry, riddles

