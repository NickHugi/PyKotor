# camerastyle.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines camera styles for areas, including distance, pitch, view angle, and height settings. The engine uses this file to configure camera behavior in different areas.

**Row Index**: Camera Style ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Camera style label |
| `name` | String | Camera style name |
| `distance` | Float | Camera distance from target |
| `pitch` | Float | Camera pitch angle |
| `viewangle` | Float | Camera view angle |
| `height` | Float | Camera height offset |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:497`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L497) - TwoDARegistry.CAMERAS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:550`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L550) - GFF field mapping: "CameraStyle" -> camerastyle.2da
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:37`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L37) - ARE camera_style field documentation
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:123`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L123) - Camera style index comment
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:442`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L442) - CameraStyle field parsing from ARE GFF
- [`Libraries/PyKotor/src/pykotor/resource/generics/are.py:579`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/generics/are.py#L579) - CameraStyle field writing to ARE GFF

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:96`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L96) - HTInstallation.TwoDA_CAMERAS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/are.py:102`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/are.py#L102) - camerastyle.2da loading in ARE editor

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/camerastyles.cpp:29-42`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/camerastyles.cpp#L29-L42) - Camera style loading from 2DA
- [`vendor/reone/src/libs/game/object/area.cpp:140-148`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/area.cpp#L140-L148) - Camera style usage in areas

---

