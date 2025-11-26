# Party Management

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="addavailablenpcbyobject"></a>

## `AddAvailableNPCByObject(nNPC, oCreature)` - Routine 694

- `694. AddAvailableNPCByObject`
- This adds a NPC to the list of available party members using
- a game object as the template
- Returns if true if successful, false if the NPC had already
- been added or the object specified is invalid

- `nNPC`: int
- `oCreature`: object

<a id="addavailablenpcbytemplate"></a>

## `AddAvailableNPCByTemplate(nNPC, sTemplate)` - Routine 697

- `697. AddAvailableNPCByTemplate`
- This adds a NPC to the list of available party members using
- a template
- Returns if true if successful, false if the NPC had already
- been added or the template specified is invalid

- `nNPC`: int
- `sTemplate`: string

<a id="addpartymember"></a>

## `AddPartyMember(nNPC, oCreature)` - Routine 574

- `574. AddPartyMember`
- Adds a creature to the party
- Returns whether the addition was successful
- AddPartyMember

- `nNPC`: int
- `oCreature`: object

<a id="addtoparty"></a>

## `AddToParty(oPC, oPartyLeader)` - Routine 572

- `572. AddToParty`
- Add oPC to oPartyLeader's party.  This will only work on two PCs.
- - oPC: player to add to a party
- - oPartyLeader: player already in the party

- `oPC`: object
- `oPartyLeader`: object

<a id="getpartyaistyle"></a>

## `GetPartyAIStyle()` - Routine 704

- `704. GetPartyAIStyle`
- Returns the party ai style

<a id="getpartymemberbyindex"></a>

## `GetPartyMemberByIndex(nIndex)` - Routine 577

- `577. GetPartyMemberByIndex`
- Returns the party member at a given index in the party.
- The order of members in the party can vary based on
- who the current leader is (member 0 is always the current
- party leader).
- GetPartyMemberByIndex

- `nIndex`: int

<a id="getpartymembercount"></a>

## `GetPartyMemberCount()` - Routine 126

- `126. GetPartyMemberCount`
- GetPartyMemberCount
- Returns a count of how many members are in the party including the player character

<a id="isnpcpartymember"></a>

## `IsNPCPartyMember(nNPC)` - Routine 699

- `699. IsNPCPartyMember`
- Returns if a given NPC constant is in the party currently

- `nNPC`: int

<a id="isobjectpartymember"></a>

## `IsObjectPartyMember(oCreature)` - Routine 576

- `576. IsObjectPartyMember`
- Returns whether a specified creature is a party member
- IsObjectPartyMember

- `oCreature`: object

<a id="removefromparty"></a>

## `RemoveFromParty(oPC)` - Routine 573

- `573. RemoveFromParty`
- Remove oPC from their current party. This will only work on a PC.
- - oPC: removes this player from whatever party they're currently in.

- `oPC`: object

<a id="removepartymember"></a>

## `RemovePartyMember(nNPC)` - Routine 575

- `575. RemovePartyMember`
- Removes a creature from the party
- Returns whether the removal was syccessful
- RemovePartyMember

- `nNPC`: int

<a id="setpartyaistyle"></a>

## `SetPartyAIStyle(nStyle)` - Routine 706

- `706. SetPartyAIStyle`
- Sets the party ai style

- `nStyle`: int

<a id="setpartyleader"></a>

## `SetPartyLeader(nNPC)` - Routine 13

- `13. SetPartyLeader`
- Sets (by NPC constant) which party member should be the controlled
- character

- `nNPC`: int

<a id="showpartyselectiongui"></a>

## `ShowPartySelectionGUI(sExitScript, nForceNPC1, nForceNPC2)` - Routine 712

- `712. ShowPartySelectionGUI`
- ShowPartySelectionGUI
- Brings up the party selection GUI for the player to
- select the members of the party from
- if exit script is specified, will be executed when
- the GUI is exited

- `sExitScript`: string (default: ``)
- `nForceNPC1`: int
- `nForceNPC2`: int

<a id="switchplayercharacter"></a>

## `SwitchPlayerCharacter(nNPC)` - Routine 11

- `11. SwitchPlayerCharacter`
- Switches the main character to a specified NPC
- -1 specifies to switch back to the original PC

- `nNPC`: int

