# UTS (Sound)

Part of the [GFF File Format Documentation](GFF-File-Format).


UTS files define sound object templates for ambient and environmental audio. These can be positional 3D sounds or global stereo sounds, with looping, randomization, and volume control.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/uts.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/uts.py)

## Core Identity Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `TemplateResRef` | ResRef | Template identifier for this sound |
| `Tag` | CExoString | Unique tag for script references |
| `LocName` | CExoLocString | Sound name (unused) |
| `Comment` | CExoString | Developer comment/notes |

## Playback Control

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Active` | Byte | Sound is currently active |
| `Continuous` | Byte | Sound plays continuously |
| `Looping` | Byte | Individual samples loop |
| `Positional` | Byte | Sound is 3D positional |
| `Random` | Byte | Randomly select from Sounds list |
| `Volume` | Byte | Volume level (0-127) |
| `VolumeVary` | Byte | Random volume variation |
| `PitchVary` | Byte | Random pitch variation |

## Timing & Interval

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Interval` | Int | Delay between plays (seconds) |
| `IntervalVary` | Int | Random interval variation |
| `Times` | Int | Times to play (unused) |

**Playback Modes:**

- **Continuous**: Loops one sample indefinitely (machinery, hum)
- **Interval**: Plays samples with delays (birds, random creaks)
- **Random**: Picks different sample each time

## Positioning

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Elevation` | Float | Height offset from ground |
| `MaxDistance` | Float | Distance where sound becomes inaudible |
| `MinDistance` | Float | Distance where sound is at full volume |
| `RandomPosition` | Byte | Randomize emitter position |
| `RandomRangeX` | Float | X-axis random range |
| `RandomRangeY` | Float | Y-axis random range |

**3D Audio:**

- **Positional=1**: Sound attenuates with distance and pans
- **Positional=0**: Global stereo sound (music, voiceover)
- **Min/Max Distance**: Controls falloff curve

## Sound List

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Sounds` | List | List of WAV/MP3 files to play |

**Sounds Struct Fields:**

- `Sound` (ResRef): Audio file resource

**Randomization:**

- If `Random=1`, engine picks one sound from list each interval
- Allows for varied ambience (e.g., 5 different bird calls)

