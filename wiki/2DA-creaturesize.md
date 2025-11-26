# creaturesize.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines creature size categories and their properties. The engine uses this file to determine size-based combat modifiers, reach, and other size-related calculations.

**Row Index**: Size Category ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Size category label |
| Additional columns | Various | Size category properties and modifiers |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:42-44`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L42-L44) - Comment referencing creaturesize.2da for SizeCategoryID

---

