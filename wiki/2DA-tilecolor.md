# tilecolor.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines tile colors for walkmesh rendering. The engine uses this file to determine color values for different walkmesh tiles.

**Row Index**: Tile Color ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Tile color label |
| Additional columns | Various | Color values and properties |

**References**:

- [`vendor/KotOR.js/src/odyssey/OdysseyWalkMesh.ts:618-626`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/OdysseyWalkMesh.ts#L618-L626) - Tile color loading from 2DA

---

