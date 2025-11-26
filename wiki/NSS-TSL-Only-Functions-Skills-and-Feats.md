# Skills and Feats

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="adjustcreatureskills"></a>

## `AdjustCreatureSkills(oObject, nSkill, nAmount)`

- 869
- DJS-OEI 10/9/2004
- This function adjusts a creature's skills.
- oObject is the creature that will have its skill adjusted
- The following constants are acceptable for the nSkill parameter:

- `oObject`: object
- `nSkill`: int
- `nAmount`: int

<a id="getfeatacquired"></a>

## `GetFeatAcquired(nFeat, oCreature)` - Routine 285

- `285. GetFeatAcquired`
- Determine whether oCreature has nFeat, and nFeat is useable.
- PLEASE NOTE!!! - This function will return FALSE if the target
- is not currently able to use the feat due to daily limits or
- other restrictions. Use GetFeatAcquired() if you just want to

- `nFeat`: int
- `oCreature`: object

<a id="getownerdemolitionsskill"></a>

## `GetOwnerDemolitionsSkill(oObject)` - Routine 793

- `793. GetOwnerDemolitionsSkill`
- DJS-OEI 1/26/2004
- Returns the Demolitions skill of the creature that
- placed this mine. This will often be 0. This function accepts
- the object that the mine is attached to (Door, Placeable, or Trigger)
- and will determine which one it actually is at runtime.

- `oObject`: object

<a id="getskillrankbase"></a>

## `GetSkillRankBase(nSkill, oObject)`

- 870
- DJS-OEI 10/10/2004
- This function returns the base Skill Rank for the requested
- skill. It does not include modifiers from effects/items.
- The following constants are acceptable for the nSkill parameter:

- `nSkill`: int
- `oObject`: object

<a id="grantfeat"></a>

## `GrantFeat(nFeat, oCreature)` - Routine 786

- `786. GrantFeat`
- DJS-OEI 1/13/2004
- Grants the target a feat without regard for prerequisites.

- `nFeat`: int
- `oCreature`: object

