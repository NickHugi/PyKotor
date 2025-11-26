# alienvo.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines alien voice-over configurations (KotOR 2 only). The engine uses this file to determine alien voice-over sound effects for various emotional states and situations.

**Row Index**: Alien Voice-Over ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Alien voice-over label |
| `angry_long`, `angry_medium`, `angry_short` | ResRef | Angry voice-over sound ResRefs |
| `comment_generic_long`, `comment_generic_medium`, `comment_generic_short` | ResRef | Generic comment voice-over sound ResRefs |
| `greeting_medium`, `greeting_short` | ResRef | Greeting voice-over sound ResRefs |
| `happy_thankful_long`, `happy_thankful_medium`, `happy_thankful_short` | ResRef | Happy/thankful voice-over sound ResRefs |
| `laughter_normal`, `laughter_mocking_medium`, `laughter_mocking_short`, `laughter_long`, `laughter_short` | ResRef | Laughter voice-over sound ResRefs |
| `pleading_medium`, `pleading_short` | ResRef | Pleading voice-over sound ResRefs |
| `question_long`, `question_medium`, `question_short` | ResRef | Question voice-over sound ResRefs |
| `sad_long`, `sad_medium`, `sad_short` | ResRef | Sad voice-over sound ResRefs |
| `scared_long`, `scared_medium`, `scared_short` | ResRef | Scared voice-over sound ResRefs |
| `seductive_long`, `seductive_medium`, `seductive_short` | ResRef | Seductive voice-over sound ResRefs |
| `silence` | ResRef | Silence voice-over sound ResRef |
| `wounded_medium`, `wounded_small` | ResRef | Wounded voice-over sound ResRefs |
| `screaming_medium`, `screaming_small` | ResRef | Screaming voice-over sound ResRefs |
| Additional columns | Various | Alien voice-over properties |

**References**:

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:363-375`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L363-L375) - Sound ResRef column definitions for alienvo.2da (KotOR 2 only)

---

