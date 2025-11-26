# heads.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines head models and textures for player characters and NPCs. The engine uses this file when loading character heads, determining which 3D model and textures to apply.

**Row Index**: Head ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `head` | ResRef (optional) | Head model ResRef |
| `headtexe` | ResRef (optional) | Head texture E ResRef |
| `headtexg` | ResRef (optional) | Head texture G ResRef |
| `headtexve` | ResRef (optional) | Head texture VE ResRef |
| `headtexvg` | ResRef (optional) | Head texture VG ResRef |
| `headtexvve` | ResRef (optional) | Head texture VVE ResRef |
| `headtexvvve` | ResRef (optional) | Head texture VVVE ResRef |
| `alttexture` | ResRef (optional) | Alternative texture ResRef |

**Column Details**:

The complete column structure is defined in reone's heads parser:

- `head`: Optional ResRef - head model ResRef
- `alttexture`: Optional ResRef - alternative texture ResRef
- `headtexe`: Optional ResRef - head texture for evil alignment
- `headtexg`: Optional ResRef - head texture for good alignment
- `headtexve`: Optional ResRef - head texture for very evil alignment
- `headtexvg`: Optional ResRef - head texture for very good alignment
- `headtexvve`: Optional ResRef - head texture for very very evil alignment
- `headtexvvve`: Optional ResRef - head texture for very very very evil alignment

**References**:

- [`vendor/reone/src/libs/resource/parser/2da/heads.cpp:29-39`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/heads.cpp#L29-L39) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/creature.cpp:1223-1228`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/creature.cpp#L1223-L1228) - Head loading from 2DA

---

