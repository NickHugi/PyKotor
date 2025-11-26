# Abilities and Stats

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="getabilitymodifier"></a>

## `GetAbilityModifier(nAbility, oCreature)` - Routine 331

- `331. GetAbilityModifier`
- Returns the ability modifier for the specified ability
- Get oCreature's ability modifier for nAbility.
- - nAbility: ABILITY_*
- - oCreature

- `nAbility`: int
- `oCreature`: object

<a id="getabilityscore"></a>

## `GetAbilityScore(oCreature, nAbilityType)` - Routine 139

- `139. GetAbilityScore`
- Get the ability score of type nAbility for a creature (otherwise 0)
- - oCreature: the creature whose ability score we wish to find out
- - nAbilityType: ABILITY_*
- Return value on error: 0

- `oCreature`: object
- `nAbilityType`: int

<a id="getnpcselectability"></a>

## `GetNPCSelectability(nNPC)` - Routine 709

- `709. GetNPCSelectability`
- GetNPCSelectability

- `nNPC`: int

<a id="setnpcselectability"></a>

## `SetNPCSelectability(nNPC, nSelectability)` - Routine 708

- `708. SetNPCSelectability`
- SetNPCSelectability

- `nNPC`: int
- `nSelectability`: int

<a id="swmg_startinvulnerability"></a>

## `SWMG_StartInvulnerability(oFollower)` - Routine 666

- `666. SWMG_StartInvulnerability`
- StartInvulnerability
- This will begin a period of invulnerability (as defined by Invincibility)

- `oFollower`: object

