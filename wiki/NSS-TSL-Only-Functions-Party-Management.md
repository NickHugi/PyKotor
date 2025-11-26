# Party Management

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="addavailablepupbyobject"></a>

## `AddAvailablePUPByObject(nPUP, oPuppet)`

- 837
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- creature ID
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `oPuppet`: object

<a id="addavailablepupbytemplate"></a>

## `AddAvailablePUPByTemplate(nPUP, sTemplate)`

- 836
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- template.
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `sTemplate`: string

<a id="addpartypuppet"></a>

## `AddPartyPuppet(nPUP, oidCreature)`

- 840
- RWT-OEI 07/18/04
- This adds an existing puppet object to the party. The
- puppet object must already exist via SpawnAvailablePUP
- and must already be available via AddAvailablePUP*

- `nPUP`: int
- `oidCreature`: object

<a id="getispartyleader"></a>

## `GetIsPartyLeader(oCharacter)`

- 844
- RWT-OEI 07/21/04
- Returns TRUE if the object ID passed is the character
- that the player is actively controlling at that point.
- Note that this function is *NOT* able to return correct

- `oCharacter`: object

<a id="getpartyleader"></a>

## `GetPartyLeader()`

- 845
- RWT-OEI 07/21/04
- Returns the object ID of the character that the player
- is actively controlling. This is the 'Party Leader'.
- Returns object Invalid on error

<a id="removenpcfrompartytobase"></a>

## `RemoveNPCFromPartyToBase(nNPC)`

- 846
- JAB-OEI 07/22/04
- Will remove the CNPC from the 3 person party, and remove
- him/her from the area, effectively sending the CNPC back
- to the base. The CNPC data is still stored in the

- `nNPC`: int

