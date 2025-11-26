# Combat Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="getcombatactionspending"></a>

## `GetCombatActionsPending(oCreature)`

- 872
- RWT-OEI 10/19/04
- This function returns TRUE if the creature has actions in its
- Combat Action queue.

- `oCreature`: object

<a id="setfakecombatstate"></a>

## `SetFakeCombatState(oObject, nEnable)` - Routine 791

- `791. SetFakeCombatState`
- RWT-OEI 01/16/04
- A function to put the character into a true combat state but the reason set to
- not real combat. This should help us control animations in cutscenes with a bit
- more precision. -- Not totally sure this is doing anything just yet. Seems
- the combat condition gets cleared shortly after anyway.

- `oObject`: object
- `nEnable`: int

