# prioritygroups.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines priority groups for sound effects, determining which sounds take precedence when multiple sounds are playing. The engine uses this file to calculate sound priority values.

**Row Index**: Priority Group ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Priority group label |
| `priority` | Integer | Priority value (higher = more important) |

**References**:

- [`vendor/reone/src/libs/game/object/sound.cpp:92-96`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/sound.cpp#L92-L96) - Priority group loading from 2DA

---

