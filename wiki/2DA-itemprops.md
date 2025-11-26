# itemprops.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Master table defining all item property types available in the game. Each row represents a property type (damage bonuses, ability score bonuses, skill bonuses, etc.) with their cost calculations and effect parameters. The engine uses this file to determine item property costs, effects, and availability.

**Row Index**: Item property ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Property label |
| `name` | StrRef | String reference for property name |
| `costtable` | String | Cost calculation table reference |
| `param1` | String | Parameter 1 label |
| `param2` | String | Parameter 2 label |
| `subtype` | Integer | Property subtype identifier |
| `costvalue` | Integer | Base cost value |
| `param1value` | Integer | Parameter 1 default value |
| `param2value` | Integer | Parameter 2 default value |
| `description` | StrRef | Property description string reference |

**References**:

**PyKotor:**

- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:135`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L135) - StrRef column definition for itemprops.2da (K1: stringref)
- [`Libraries/PyKotor/src/pykotor/extract/twoda.py:313`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/extract/twoda.py#L313) - StrRef column definition for itemprops.2da (K2: stringref)

**HolocronToolset:**

- [`Tools/HolocronToolset/src/toolset/data/installation.py:74`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/data/installation.py#L74) - HTInstallation.TwoDA_ITEM_PROPERTIES constant
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:107-111`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L107-L111) - itemprops.2da loading in UTI editor
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:278-287`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L278-L287) - itemprops.2da usage for property cost table and parameter lookups
- [`Tools/HolocronToolset/src/toolset/gui/editors/uti.py:449-465`](https://github.com/th3w1zard1/PyKotor/blob/master/Tools/HolocronToolset/src/toolset/gui/editors/uti.py#L449-L465) - itemprops.2da usage in property selection and loading

---

