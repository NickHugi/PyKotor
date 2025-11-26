# UTT (Trigger)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTT files define trigger templates for invisible volumes that fire scripts when entered, exited, or used. Triggers are essential for area transitions, cutscenes, traps, and game logic.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/utt.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/utt.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this trigger |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Trigger name (localized) |
| `Comment` | CExoString | Developer comment/notes |

## Trigger Configuration

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Type` | Int | Trigger type (0=Generic, 1=Transition, 2=Trap) |
| `Faction` | Word | Faction identifier |
| `Cursor` | Int | Cursor icon when hovered (0=None, 1=Door, etc) |
| `HighlightHeight` | Float | Height of selection highlight |

**Trigger Types:**

- **Generic**: Script execution volume
- **Transition**: Loads new module or moves to waypoint
- **Trap**: Damages/effects entering object

## Transition Settings

| Field | Type | Description |
| ----- | ---- | ----------- |
| `LinkedTo` | CExoString | Destination waypoint tag |
| `LinkedToModule` | ResRef | Destination module ResRef |
| `LinkedToFlags` | Byte | Transition behavior flags |
| `LoadScreenID` | Word | Loading screen ID |
| `PortraitId` | Word | Portrait ID (unused) |

**Area Transitions:**

- **LinkedToModule**: Target module to load
- **LinkedTo**: Waypoint where player spawns
- **LoadScreenID**: Image displayed during load

## Trap System

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TrapFlag` | Byte | Trigger is a trap |
| `TrapType` | Byte | Index into `traps.2da` |
| `TrapDetectable` | Byte | Can be detected |
| `TrapDetectDC` | Byte | Awareness DC to detect |
| `TrapDisarmable` | Byte | Can be disarmed |
| `DisarmDC` | Byte | Security DC to disarm |
| `TrapOneShot` | Byte | Fires once then disables |
| `AutoRemoveKey` | Byte | Key removed on use |
| `KeyName` | CExoString | Key tag required to disarm/bypass |

**Trap Mechanics:**

- Floor traps (mines, pressure plates) are triggers
- Detection makes trap visible and clickable
- Entering without disarm triggers trap effect

## Script Hooks

| Field | Type | Description |
| ----- | ---- | ----------- |
| `OnClick` | ResRef | Fires when clicked |
| `OnDisarm` | ResRef | Fires when disarmed |
| `OnHeartbeat` | ResRef | Fires periodically |
| `OnScriptEnter` | ResRef | Fires when object enters |
| `OnScriptExit` | ResRef | Fires when object exits |
| `OnTrapTriggered` | ResRef | Fires when trap activates |
| `OnUserDefined` | ResRef | Fires on user event |

**Scripting:**

- **OnScriptEnter**: Most common hook (cutscenes, spawns)
- **OnHeartbeat**: Area-of-effect damage/buffs
- **OnClick**: Used for interactive transitions

