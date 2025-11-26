# placeables.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines placeable objects (containers, usable objects, interactive elements) with their models, properties, and behaviors. The engine uses this file when loading placeable objects in areas, determining their models, hit detection, and interaction properties.

**Row Index**: Placeable type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String (optional) | Placeable type label |
| `modelname` | ResRef (optional) | 3D model ResRef |
| `strref` | Integer | String reference for placeable name |
| `bodybag` | Boolean | Whether placeable can contain bodies |
| `canseeheight` | Float | Can-see height for line of sight |
| `hitcheck` | Boolean | Whether hit detection is enabled |
| `hostile` | Boolean | Whether placeable is hostile |
| `ignorestatichitcheck` | Boolean | Whether to ignore static hit checks |
| `lightcolor` | String (optional) | Light color RGB values |
| `lightoffsetx` | String (optional) | Light X offset |
| `lightoffsety` | String (optional) | Light Y offset |
| `lightoffsetz` | String (optional) | Light Z offset |
| `lowgore` | String (optional) | Low gore model ResRef |
| `noncull` | Boolean | Whether to disable culling |
| `preciseuse` | Boolean | Whether precise use is enabled |
| `shadowsize` | Boolean | Whether shadow size is enabled |
| `soundapptype` | Integer (optional) | Sound appearance type |
| `usesearch` | Boolean | Whether placeable can be searched |

**Column Details**:

The complete column structure is defined in reone's placeables parser:

- `label`: Optional label string
- `modelname`: 3D model ResRef
- `strref`: String reference for placeable name
- `bodybag`: Boolean - whether placeable can contain bodies
- `canseeheight`: Float - can-see height for line of sight
- `hitcheck`: Boolean - whether hit detection is enabled
- `hostile`: Boolean - whether placeable is hostile
- `ignorestatichitcheck`: Boolean - whether to ignore static hit checks
- `lightcolor`: Optional string - light color RGB values
- `lightoffsetx`: Optional string - light X offset
- `lightoffsety`: Optional string - light Y offset
- `lightoffsetz`: Optional string - light Z offset
- `lowgore`: Optional string - low gore model ResRef
- `noncull`: Boolean - whether to disable culling
- `preciseuse`: Boolean - whether precise use is enabled
- `shadowsize`: Boolean - whether shadow size is enabled
- `soundapptype`: Optional integer - sound appearance type
- `usesearch`: Boolean - whether placeable can be searched

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:141`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L141) - StrRef column definition for placeables.2da (K1: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:170`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L170) - Model ResRef column definition for placeables.2da (K1: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:319`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L319) - StrRef column definition for placeables.2da (K2: strref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:349`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L349) - Model ResRef column definition for placeables.2da (K2: modelname)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:467`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L467) - TwoDARegistry.PLACEABLES constant definition
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:542`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L542) - GFF field mapping: "Appearance" -> placeables.2da

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:66`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L66) - HTInstallation.TwoDA_PLACEABLES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:52`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L52) - placeables.2da cache initialization comment
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:62`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L62) - placeables.2da cache loading
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:121-131`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L121-L131) - placeables.2da usage in appearance selection combobox
- [`Tools/HolocronToolset/src/toolset/gui/editors/utp.py:471`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/utp.py#L471) - placeables.2da usage for model name lookup

**Vendor Implementations:**

- [`vendor/reone/src/libs/resource/parser/2da/placeables.cpp:29-49`](https://github.com/th3w1zard1/reone/blob/master/src/libs/resource/parser/2da/placeables.cpp#L29-L49) - Complete column parsing implementation with all column names
- [`vendor/reone/src/libs/game/object/placeable.cpp:59-60`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/object/placeable.cpp#L59-L60) - Placeable loading from 2DA

---

