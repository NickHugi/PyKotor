# Other Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="addbonusforcepoints"></a>

## `AddBonusForcePoints(oCreature, nBonusFP)` - Routine 802

- `802. AddBonusForcePoints`
- RWT-OEI 02/06/04
- AddBonusForcePoints - This adds nBonusFP to the current total
- bonus that the player has. The Bonus Force Points are a pool
- of force points that will always be added after the player's
- total force points are calculated (based on level, force dice,

- `oCreature`: object
- `nBonusFP`: int

<a id="adjustcreatureattributes"></a>

## `AdjustCreatureAttributes(oObject, nAttribute, nAmount)`

- 833
- AWD-OEI 7/06/2004
- This function adjusts a creatures stats.
- oObject is the creature that will have it's attribute adjusted
- The following constants are acceptable for the nAttribute parameter:

- `oObject`: object
- `nAttribute`: int
- `nAmount`: int

<a id="assignpup"></a>

## `AssignPUP(nPUP, nNPC)`

- 838
- RWT-OEI 07/17/04
- This function assigns a PUPPET constant to a
- Party NPC.  The party NPC -MUST- be in the game
- before calling this.

- `nPUP`: int
- `nNPC`: int

<a id="changeobjectappearance"></a>

## `ChangeObjectAppearance(oObjectToChange, nAppearance)`

- 850
- ChangeObjectAppearance
- oObjectToChange = Object to change appearance of
- nAppearance = appearance to change to (from appearance.2da)

- `oObjectToChange`: object
- `nAppearance`: int

<a id="creatureflourishweapon"></a>

## `CreatureFlourishWeapon(oObject)`

- 847
- AWD-OEI 7/22/2004
- This causes a creature to flourish with it's currently equipped weapon.

- `oObject`: object

<a id="detonatemine"></a>

## `DetonateMine(oMine)`

- 857
- RWT-OEI 08/31/04
- This function schedules a mine to play its DETONATION
- animation once it is destroyed. Note that this detonates
- the mine immediately but has nothing to do with causing

- `oMine`: object

<a id="disablehealthregen"></a>

## `DisableHealthRegen(nFlag)`

- 858
- RWT-OEI 09/06/04
- This function turns off the innate health regeneration that all party
- members have. The health regen will *stay* off until it is turned back
- on by passing FALSE to this function.

- `nFlag`: int (default: `0`)

<a id="disablemap"></a>

## `DisableMap(nFlag)`

- 856
- RWT-OEI 08/31/04
- Passing TRUE into this function turns off the player's maps.
- Passing FALSE into this function re-enables them. This change
- is permanent once called, so it is important that there *is*

- `nFlag`: int (default: `0`)

<a id="enablerain"></a>

## `EnableRain(nFlag)`

- 863
- RWT-OEI 09/15/04
- This function enables or disables rain

- `nFlag`: int

<a id="enablerendering"></a>

## `EnableRendering(oObject, bEnable)`

- 871
- DJS-OEI 10/15/2004
- This function will allow the caller to modify the rendering behavior
- of the target object.
- oObject - The object to change rendering state on.

- `oObject`: object
- `bEnable`: int

<a id="forceheartbeat"></a>

## `ForceHeartbeat(oCreature)`

- 822
- DJS-OEI 5/4/2004
- Forces a Heartbeat on the given creature. THIS ONLY WORKS FOR CREATURES
- AT THE MOMENT. This heartbeat should force perception updates to occur.

- `oCreature`: object

<a id="getbonusforcepoints"></a>

## `GetBonusForcePoints(oCreature)` - Routine 803

- `803. GetBonusForcePoints`
- RWT-OEI 02/06/04
- GetBonusForcePoints - This returns the total number of bonus
- force points a player has. Bonus Force Points are a pool of
- points that are always added to a player's Max Force Points.
- ST: Please explain how a function returning VOID could return a

- `oCreature`: object

<a id="getchemicalpiecevalue"></a>

## `GetChemicalPieceValue()` - Routine 775

- `775. GetChemicalPieceValue`
- FAK-OEI 12/15/2003
- Get the number of chemicals for an item in pieces

<a id="getchemicals"></a>

## `GetChemicals()` - Routine 774

- `774. GetChemicals`
- FAK-OEI 12/15/2003
- Get the number of chemicals for an item

<a id="gethealtarget"></a>

## `GetHealTarget(oidHealer)`

- 814
- RWT-OEI 03/19/04
- Retrieves the Heal Target for the Healer AI script. Should probably
- not be used outside of the Healer AI script.

- `oidHealer`: object

<a id="getinfluence"></a>

## `GetInfluence(nNPC)` - Routine 795

- `795. GetInfluence`
- DJS-OEI 1/29/2004
- Gets the PC's influence on the alignment of a CNPC.
- Parameters:
- nNPC - NPC_* constant identifying the CNPC we're interested in.
- If this character is not an available party member, the return

- `nNPC`: int

<a id="getispuppet"></a>

## `GetIsPuppet(oPUP)`

- 842
- RWT-OEI 07/19/04
- Returns 1 if the creature is a Puppet in the party.
- Otherwise returns 0. It is possible for a 'party puppet'
- to exist without actually being in the party table.

- `oPUP`: object

<a id="getisxbox"></a>

## `GetIsXBox()`

- 851
- GetIsXBox
- Returns TRUE if this script is being executed on the X-Box. Returns FALSE
- if this is the PC build.

<a id="getlastforfeitviolation"></a>

## `GetLastForfeitViolation()`

- 827
- DJS-OEI 6/12/2004
- This function returns the last FORFEIT_* condition that the player
- has violated.

<a id="getpupowner"></a>

## `GetPUPOwner(oPUP)`

- 841
- RWT-OEI 07/19/04
- This returns the object ID of the puppet's owner.
- The Puppet's owner must exist and must be in the party
- in order to be found.

- `oPUP`: object

<a id="getracialsubtype"></a>

## `GetRacialSubType(oTarget)` - Routine 798

- `798. GetRacialSubType`
- FAK - OEI 2/3/04
- returns the racial sub-type of the oTarget object

- `oTarget`: object

<a id="getrandomdestination"></a>

## `GetRandomDestination(oCreature, rangeLimit)`

- 815
- RWT-OEI 03/23/04
- Returns a vector containing a random destination that the
- given creature can walk to that's within the range of the
- passed parameter.

- `oCreature`: object
- `rangeLimit`: int

<a id="getscriptparameter"></a>

## `GetScriptParameter(nIndex)` - Routine 768

- `768. GetScriptParameter`
- DJS-OEI
- This function will take the index of a script parameter
- and return the value associated with it. The index
- of the first parameter is 1.

- `nIndex`: int

<a id="getscriptstringparameter"></a>

## `GetScriptStringParameter()`

- DJS-OEI 6/21/2004
- 831
- This function will return the one CExoString parameter
- allowed for the currently running script.

<a id="getspellacquired"></a>

## `GetSpellAcquired(nSpell, oCreature)` - Routine 377

- `377. GetSpellAcquired`
- Determine whether oCreature has nSpell memorised.
- PLEASE NOTE!!! - This function will return FALSE if the target
- is not currently able to use the spell due to lack of sufficient
- Force Points. Use GetSpellAcquired() if you just want to

- `nSpell`: int
- `oCreature`: object

<a id="getspellbaseforcepointcost"></a>

## `GetSpellBaseForcePointCost(nSpellID)`

- 818
- DJS-OEI 3/29/2004
- Return the base number of Force Points required to cast
- the given spell. This does not take into account modifiers
- of any kind.

- `nSpellID`: int

<a id="getspellforcepointcost"></a>

## `GetSpellForcePointCost()` - Routine 776

- `776. GetSpellForcePointCost`
- DJS-OEI 12/30/2003
- Get the number of Force Points that were required to
- cast this spell. This includes modifiers such as Room Force
- Ratings and the Force Body power.
- - Return value on error: 0

<a id="getspellformmask"></a>

## `GetSpellFormMask(nSpellID)`

- 817
- DJS-OEI 3/28/2004
- Returns the Form Mask of the requested spell. This is used
- to determine if a spell is affected by various Forms, usually
- Consular forms that modify duration/range.

- `nSpellID`: int

<a id="grantspell"></a>

## `GrantSpell(nSpell, oCreature)` - Routine 787

- `787. GrantSpell`
- DJS-OEI 1/13/2004
- Grants the target a spell without regard for prerequisites.

- `nSpell`: int
- `oCreature`: object

<a id="haslineofsight"></a>

## `HasLineOfSight(vSource, vTarget, oSource, oTarget)`

- 820
- RWT-OEI 04/06/04
- This returns TRUE or FALSE if there is a clear line of sight from
- the source vector to the target vector. This is used in the AI to
- help the creatures using ranged weapons find better places to shoot

- `vSource`: vector
- `vTarget`: vector
- `oSource`: object
- `oTarget`: object

<a id="isformactive"></a>

## `IsFormActive(oCreature, nFormID)`

- 816
- DJS-OEI 3/25/2004
- Returns whether the given creature is currently in the
- requested Lightsaber/Consular Form and can make use of
- its benefits. This function will perform trumping checks

- `oCreature`: object
- `nFormID`: int

<a id="isintotaldefense"></a>

## `IsInTotalDefense(oCreature)`

- 812
- DJS-OEI 3/16/2004
- Determines if the given creature is using the Total Defense
- Stance.
- 0 = Creature is not in Total Defense.

- `oCreature`: object

<a id="ismeditating"></a>

## `IsMeditating(oCreature)`

- 811
- DJS-OEI 3/12/2004
- Determines if the given creature is using any Meditation Tree
- Force Power.
- 0 = Creature is not meditating.

- `oCreature`: object

<a id="isrunning"></a>

## `IsRunning(oCreature)`

- 824
- FAK - OEI 5/7/04
- gets the walk state of the creature: 0 walk or standing, 1 is running

- `oCreature`: object

<a id="isstealthed"></a>

## `IsStealthed(oCreature)`

- END PC CODE MERGER
- 810
- DJS-OEI 3/8/2004
- Determines if the given creature is in Stealth mode or not.
- 0 = Creature is not stealthed.

- `oCreature`: object

<a id="modifyfortitudesavingthrowbase"></a>

## `ModifyFortitudeSavingThrowBase(aObject, aModValue)`

- 829
- AWD-OEI 6/21/2004
- This function does not return a value.
- This function modifies the BASE value of the FORTITUDE saving throw for aObject

- `aObject`: object
- `aModValue`: int

<a id="modifyinfluence"></a>

## `ModifyInfluence(nNPC, nModifier)` - Routine 797

- `797. ModifyInfluence`
- DJS-OEI 1/29/2004
- Modifies the PC's influence on the alignment of a CNPC.
- Parameters:
- nNPC - NPC_* constant identifying the CNPC we're interested in.
- If this character is not an available party member, nothing

- `nNPC`: int
- `nModifier`: int

<a id="modifyreflexsavingthrowbase"></a>

## `ModifyReflexSavingThrowBase(aObject, aModValue)`

- 828
- AWD-OEI 6/21/2004
- This function does not return a value.
- This function modifies the BASE value of the REFLEX saving throw for aObject

- `aObject`: object
- `aModValue`: int

<a id="modifywillsavingthrowbase"></a>

## `ModifyWillSavingThrowBase(aObject, aModValue)`

- 830
- AWD-OEI 6/21/2004
- This function does not return a value.
- This function modifies the BASE value of the WILL saving throw for aObject

- `aObject`: object
- `aModValue`: int

<a id="removeheartbeat"></a>

## `RemoveHeartbeat(oPlaceable)`

- 866
- CTJ-OEI 09-29-04
- Removes the heartbeat script on the placeable.  Useful for
- placeables whose contents get populated in the heartbeat
- script and then the heartbeat no longer needs to be called.

- `oPlaceable`: object

<a id="resetcreatureailevel"></a>

## `ResetCreatureAILevel(oObject)`

- 835
- AWD-OEI 7/08/2004
- This function raises a creature's priority level.

- `oObject`: object

<a id="savenpcbyobject"></a>

## `SaveNPCByObject(nNPC, oidCharacter)`

- 873
- RWT-OEI 10/26/04
- This function saves the party member at that index with the object
- that is passed in.

- `nNPC`: int
- `oidCharacter`: object

<a id="savepupbyobject"></a>

## `SavePUPByObject(nPUP, oidPuppet)`

- 874
- RWT-OEI 10/26/04
- This function saves the party puppet at that index with the object
- that is passed in. For the Remote, just use '0' for nPUP

- `nPUP`: int
- `oidPuppet`: object

<a id="setbonusforcepoints"></a>

## `SetBonusForcePoints(oCreature, nBonusFP)` - Routine 801

- `801. SetBonusForcePoints`
- RWT-OEI 02/06/04
- SetBonusForcePoints - This sets the number of bonus force points
- that will always be added to that character's total calculated
- force points.

- `oCreature`: object
- `nBonusFP`: int

<a id="setcreatureailevel"></a>

## `SetCreatureAILevel(oObject, nPriority)`

- 834
- AWD-OEI 7/08/2004
- This function raises a creature's priority level.

- `oObject`: object
- `nPriority`: int

<a id="setcurrentform"></a>

## `SetCurrentForm(oCreature, nFormID)`

- 859
- DJS-OEI 9/7/2004
- This function sets the current Jedi Form on the given creature. This
- call will do nothing if the target does not know the Form itself.

- `oCreature`: object
- `nFormID`: int

<a id="setdisabletransit"></a>

## `SetDisableTransit(nFlag)`

- 860
- RWT-OEI 09/09/04
- This will disable or enable area transit

- `nFlag`: int (default: `0`)

<a id="setfadeuntilscript"></a>

## `SetFadeUntilScript()` - Routine 769

- `769. SetFadeUntilScript`
- RWT-OEI 12/10/03
- This script function will make it so that the fade cannot be lifted under any circumstances
- other than a call to the SetGlobalFadeIn() script.
- This function should be called AFTER the fade has already been called. For example, you would
- do a SetGlobalFadeOut() first, THEN do SetFadeUntilScript()

<a id="setforcealwaysupdate"></a>

## `SetForceAlwaysUpdate(oObject, nFlag)`

- 862
- RWT-OEI 09/15/04
- This script allows an object to recieve updates even if it is outside
- the normal range limit of 250.0f meters away from the player. This should
- ONLY be used for cutscenes that involve objects that are more than 250

- `oObject`: object
- `nFlag`: int

<a id="setforfeitconditions"></a>

## `SetForfeitConditions(nForfeitFlags)`

- DJS-OEI 6/12/2004
- These constants can be OR'ed together and sent to SetForfeitConditions()

- `nForfeitFlags`: int

<a id="sethealtarget"></a>

## `SetHealTarget(oidHealer, oidTarget)`

- 813
- RWT-OEI 03/19/04
- Stores a Heal Target for the Healer AI script. Should probably
- not be used outside of the Healer AI script.

- `oidHealer`: object
- `oidTarget`: object

<a id="setinfluence"></a>

## `SetInfluence(nNPC, nInfluence)` - Routine 796

- `796. SetInfluence`
- DJS-OEI 1/29/2004
- Sets the PC's influence on the alignment of a CNPC.
- Parameters:
- nNPC - NPC_* constant identifying the CNPC we're interested in.
- If this character is not an available party member, nothing

- `nNPC`: int
- `nInfluence`: int

<a id="setorientonclick"></a>

## `SetOrientOnClick(oCreature, nState)` - Routine 794

- `794. SetOrientOnClick`
- RWT-OEI 01/29/04
- Disables or Enables the Orient On Click behavior in creatures. If
- disabled, they will not orient to face the player when clicked on
- for dialogue. The default behavior is TRUE.

- `oCreature`: object
- `nState`: int (default: `1`)

<a id="showchemicalupgradescreen"></a>

## `ShowChemicalUpgradeScreen(oCharacter)` - Routine 773

- `773. ShowChemicalUpgradeScreen`
- FAK-OEI 12/15/2003
- Start the GUI for Chemical Workshop

- `oCharacter`: object

<a id="showdemoscreen"></a>

## `ShowDemoScreen(sTexture, nTimeout, nDisplayString, nDisplayX, nDisplayY)`

- 821
- FAK - OEI 5/3/04
- ShowDemoScreen, displays a texture, timeout, string and xy for string

- `sTexture`: string
- `nTimeout`: int
- `nDisplayString`: int
- `nDisplayX`: int
- `nDisplayY`: int

<a id="showswoopupgradescreen"></a>

## `ShowSwoopUpgradeScreen()` - Routine 785

- `785. ShowSwoopUpgradeScreen`
- FAK-OEI 1/12/2004
- Displays the Swoop Bike upgrade screen.

<a id="spawnavailablepup"></a>

## `SpawnAvailablePUP(nPUP, lLocation)`

- 839
- RWT-OEI 07/17/04
- This function spawns a Party PUPPET.
- This must be used whenever you want a copy
- of the puppet around to manipulate in the game

- `nPUP`: int
- `lLocation`: location

<a id="spawnmine"></a>

## `SpawnMine(nMineType, lPoint, nDetectDCBase, nDisarmDCBase, oCreator)` - Routine 788

- `788. SpawnMine`
- DJS-OEI 1/13/2004
- Places an active mine on the map.
- nMineType - Mine Type from Traps.2DA
- lPoint - The location in the world to place the mine.
- nDetectDCBase - This value, plus the "DetectDCMod" column in Traps.2DA

- `nMineType`: int
- `lPoint`: location
- `nDetectDCBase`: int
- `nDisarmDCBase`: int
- `oCreator`: object

<a id="swmg_destroyminigameobject"></a>

## `SWMG_DestroyMiniGameObject(oObject)` - Routine 792

- `792. SWMG_DestroyMiniGameObject`
- FAK - OEI 1/23/04
- minigame function that deletes a minigame object

- `oObject`: object

<a id="swmg_getswoopupgrade"></a>

## `SWMG_GetSwoopUpgrade(nSlot)` - Routine 782

- `782. SWMG_GetSwoopUpgrade`
- FAK - OEI 1/12/04
- Minigame grabs a swoop bike upgrade

- `nSlot`: int

<a id="swmg_gettrackposition"></a>

## `SWMG_GetTrackPosition(oFollower)` - Routine 789

- `789. SWMG_GetTrackPosition`
- FAK - OEI 1/15/04
- Yet another minigame function. Returns the object's track's position.

- `oFollower`: object

<a id="swmg_setfollowerposition"></a>

## `SWMG_SetFollowerPosition(vPos)` - Routine 790

- `790. SWMG_SetFollowerPosition`
- FAK - OEI 1/15/04
- minigame function that lets you psuedo-set the position of a follower object

- `vPos`: vector

<a id="swmg_setjumpspeed"></a>

## `SWMG_SetJumpSpeed(fSpeed)` - Routine 804

- `804. SWMG_SetJumpSpeed`
- FAK - OEI 2/11/04
- SWMG_SetJumpSpeed -- the sets the 'jump speed' for the swoop
- bike races. Gravity will act upon this velocity.

- `fSpeed`: float

<a id="unlockallsongs"></a>

## `UnlockAllSongs()`

- 855
- RWT-OEI 08/30/04
- UnlockAllSongs
- Calling this will set all songs as having been unlocked.
- It is INTENDED to be used in the end-game scripts to unlock

<a id="yavinhackdoorclose"></a>

## `YavinHackDoorClose(oCreature)`

- 808

- `oCreature`: object

