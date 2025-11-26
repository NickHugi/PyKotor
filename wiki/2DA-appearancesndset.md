# appearancesndset.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines sound appearance types for creature appearances. The engine uses this file to determine which sound appearance type to use based on the creature's appearance.

**Row Index**: Sound Appearance Type ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Sound appearance type label |
| Additional columns | Various | Sound appearance type properties |

**References**:

- [`vendor/Kotor.NET/Kotor.NET/Tables/Appearance.cs:58-60`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Tables/Appearance.cs#L58-L60) - Comment referencing appearancesndset.2da for SoundAppTypeID

---

