# skills.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines all skills available in the game, including which classes can use them, their key ability scores, and skill descriptions. The engine uses this file to determine skill availability, skill point costs, and skill checks.

**Row Index**: Skill ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Skill label |
| `name` | StrRef | String reference for skill name |
| `description` | StrRef | String reference for skill description |
| `keyability` | Integer | Key ability score (STR, DEX, INT, etc.) |
| `armorcheckpenalty` | Boolean | Whether armor check penalty applies |
| `allclassescanuse` | Boolean | Whether all classes can use this skill |
| `category` | Integer | Skill category identifier |
| `maxrank` | Integer | Maximum skill rank |
| `untrained` | Boolean | Whether skill can be used untrained |
| `constant` | Integer (optional) | Constant modifier |
| `hostileskill` | Boolean | Whether skill is hostile |
| `icon` | ResRef (optional) | Skill icon ResRef |

**Column Details** (from reone implementation):

The following columns are accessed by the reone engine:

- `name`: String reference for skill name
- `description`: String reference for skill description
- `icon`: Icon ResRef
- Dynamic class skill columns: For each class, there is a column named `{classname}_class` (e.g., `jedi_guardian_class`) that contains `1` if the skill is a class skill for that class
- `droidcanuse`: Boolean - whether droids can use this skill
- `npccanuse`: Boolean - whether NPCs can use this skill

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:148`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L148) - StrRef column definitions for skills.2da (K1: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:326`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L326) - StrRef column definitions for skills.2da (K2: name, description)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:472`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L472) - TwoDARegistry.SKILLS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:563`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L563) - GFF field mapping: "SkillID" -> skills.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:71`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L71) - HTInstallation.TwoDA_SKILLS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:129`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L129) - Skills table widget in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:511-519`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L511-L519) - Skills table population in save game editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:542-543`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L542-L543) - Skills table update logic

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/d20/skills.cpp:32-48`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/skills.cpp#L32-L48) - Skill loading from 2DA
- [`vendor/reone/src/libs/game/d20/class.cpp:58-65`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/d20/class.cpp#L58-L65) - Class skill checking using dynamic column names
- [`vendor/KotOR.js/src/talents/TalentSkill.ts:38-49`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/talents/TalentSkill.ts#L38-L49) - Skill loading from 2DA with droidcanuse and npccanuse columns

---

