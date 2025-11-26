# Effects System

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="effectblind"></a>

## `EffectBlind()` - Routine 778

- `778. EffectBlind`
- DJS-OEI 1/3/2004
- Create a Blind effect.

<a id="effectcrush"></a>

## `EffectCrush()` - Routine 781

- `781. EffectCrush`
- DJS-OEI 1/9/2004
- Create a Force Crush effect.

<a id="effectdroidconfused"></a>

## `EffectDroidConfused()`

- 809
- new function for droid confusion so inherint mind immunity can be
- avoided.

<a id="effectdroidscramble"></a>

## `EffectDroidScramble()`

- 852
- Create a Droid Scramble effect

<a id="effectfactionmodifier"></a>

## `EffectFactionModifier(nNewFaction)`

- 849
- Create a Faction Modifier effect.

- `nNewFaction`: int

<a id="effectforcebody"></a>

## `EffectForceBody(nLevel)` - Routine 770

- `770. EffectForceBody`
- DJS-OEI 12/15/2003
- Create a Force Body effect
- - nLevel: The level of the Force Body effect.
- 0 = Force Body
- 1 = Improved Force Body

- `nLevel`: int

<a id="effectforcesight"></a>

## `EffectForceSight()`

- 823
- DJS-OEI 5/5/2004
- Creates a Force Sight effect.

<a id="effectfpregenmodifier"></a>

## `EffectFPRegenModifier(nPercent)` - Routine 779

- `779. EffectFPRegenModifier`
- DJS-OEI 1/4/2004
- Create an FP regeneration modifier effect.

- `nPercent`: int

<a id="effectfury"></a>

## `EffectFury()` - Routine 777

- `777. EffectFury`
- DJS-OEI 1/2/2004
- Create a Fury effect.

<a id="effectmindtrick"></a>

## `EffectMindTrick()`

- 848
- Create a Mind Trick effect

<a id="effectvpregenmodifier"></a>

## `EffectVPRegenModifier(nPercent)` - Routine 780

- `780. EffectVPRegenModifier`
- DJS-OEI 1/4/2004
- Create a VP regeneration modifier effect.

- `nPercent`: int

<a id="removeeffectbyexactmatch"></a>

## `RemoveEffectByExactMatch(oCreature, eEffect)`

- 868
- RWT-OEI 10/07/04
- This script removes an effect by an identical match
- based on:
- Must have matching EffectID types.

- `oCreature`: object
- `eEffect`: effect

<a id="removeeffectbyid"></a>

## `RemoveEffectByID(oCreature, nEffectID)`

- 867
- JF-OEI 10-07-2004
- Remove an effect by ID

- `oCreature`: object
- `nEffectID`: int

