# JRL (Journal)

Part of the [GFF File Format Documentation](GFF-File-Format).


JRL files define the structure of the player's quest journal. They organize quests into categories and track progress through individual entries.

**Reference**: [`Libraries/PyKotor/src/pykotor/resource/generics/jrl.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/jrl.py)

## Quest Structure

JRL files contain a list of `Categories` (Quests), each containing a list of `EntryList` (States).

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Categories` | List | List of quests |

## Quest Category (JRLQuest)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `Tag` | CExoString | Unique quest identifier |
| `Name` | CExoLocString | Quest title |
| `Comment` | CExoString | Developer comment |
| `Priority` | Int | Sorting priority (0=Highest, 4=Lowest) |
| `PlotIndex` | Int | Legacy plot index |
| `PlanetID` | Int | Planet association (unused) |
| `EntryList` | List | List of quest states |

**Priority Levels:**

- **0 (Highest)**: Main quest line
- **1 (High)**: Important side quests
- **2 (Medium)**: Standard side quests
- **3 (Low)**: Minor tasks
- **4 (Lowest)**: Completed/Archived

## Quest Entry (JRLEntry)

| Field | Type | Description |
| ----- | ---- | ----------- |
| `ID` | Int | State identifier (referenced by scripts/dialogue) |
| `Text` | CExoLocString | Journal text displayed for this state |
| `End` | Byte | 1 if this state completes the quest |
| `XP_Percentage` | Float | XP reward multiplier for reaching this state |

**Quest Updates:**

- Scripts use `AddJournalQuestEntry("Tag", ID)` to update quests.
- Dialogues use `Quest` and `QuestEntry` fields.
- Only the highest ID reached is typically displayed (unless `AllowOverrideHigher` is set in `global.jrl` logic).
- `End=1` moves the quest to the "Completed" tab.

## Implementation Notes

- **global.jrl**: The master journal file for the entire game.
- **Module JRLs**: Not typically used; most quests are global.
- **XP Rewards**: `XP_Percentage` scales the `journal.2da` XP value for the quest.

---

