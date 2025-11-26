# portraits.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Maps portrait IDs to portrait image ResRefs for character selection screens and character sheets. The engine uses this file to display character portraits in the UI.

**Row Index**: Portrait ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Portrait label |
| `baseresref` | ResRef | Base portrait image ResRef |
| `appearancenumber` | Integer | Associated appearance ID |
| `appearance_s` | Integer | Small appearance ID |
| `appearance_l` | Integer | Large appearance ID |
| `forpc` | Boolean | Whether portrait is for player character |
| `sex` | Integer | Gender (0=male, 1=female) |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:455`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L455) - TwoDARegistry.PORTRAITS constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:523`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L523) - GFF field mapping: "PortraitId" -> portraits.2da
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:66`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L66) - Party portraits documentation comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:226-228`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L226-L228) - Portrait rotation logic documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:241`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L241) - Party portraits field documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:391`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L391) - Portraits parsing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:456`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L456) - Portraits writing comment
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2157`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2157) - SAVENFO.res portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2309`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2309) - Party portraits documentation
- [`Libraries/PyKotor/src/pykotor/extract/savedata.py:2370`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/savedata.py#L2370) - Portrait debug print

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:54`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L54) - HTInstallation.TwoDA_PORTRAITS constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utc.py:140-152`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utc.py#L140-L152) - portraits.2da usage for portrait selection with alignment-based variant selection (baseresref, baseresrefe, baseresrefve, baseresrefvve, baseresrefvvve)
- [`Tools/HolocronToolset/src/ui/editors/utc.ui:407`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/utc.ui#L407) - Portrait selection combobox in UTC editor UI
- [`Tools/HolocronToolset/src/toolset/gui/editors/savegame.py:51`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/savegame.py#L51) - Portraits documentation in save game editor
- [`Tools/HolocronToolset/src/ui/editors/savegame.ui:94-98`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/ui/editors/savegame.ui#L94-L98) - Portraits group box in save game editor UI

**Vendor Implementations:**

- [`vendor/reone/src/libs/game/portraits.cpp:33-51`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/portraits.cpp#L33-L51) - Portrait loading from 2DA with all column access

---

