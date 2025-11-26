# loadscreenhints.2da

Part of the [2DA File Format Documentation](2DA-File-Format).


**Engine Usage**: Defines loading screen hints displayed during area transitions. The engine uses this file to show helpful tips and hints to players while loading.

**Row Index**: Loading Screen Hint ID (integer)

**Column Structure**:

| Column Name | Type | Description |
|------------|------|-------------|
| `label` | String | Hint label |
| `strref` | StrRef | String reference for hint text |

**References**:

- [`vendor/xoreos/src/engines/kotor/gui/loadscreen/loadscreen.cpp:45`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotor/gui/loadscreen/loadscreen.cpp#L45) - Loading screen hints TODO comment (KotOR-specific)

---

