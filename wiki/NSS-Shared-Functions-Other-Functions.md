# Other Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="abs"></a>

## `abs(nValue)` - Routine 77

- `77. abs`
- Maths operation: integer absolute value of nValue
- - Return value on error: 0

- `nValue`: int

<a id="acos"></a>

## `acos(fValue)` - Routine 71

- `71. acos`
- Maths operation: arccosine of fValue
- - Returns zero if fValue > 1 or fValue < -1

- `fValue`: float

<a id="addjournalquestentry"></a>

## `AddJournalQuestEntry(szPlotID, nState, bAllowOverrideHigher)` - Routine 367

- `367. AddJournalQuestEntry`
- Add a journal quest entry to the player.
- - szPlotID: the plot identifier used in the toolset's Journal Editor
- - nState: the state of the plot as seen in the toolset's Journal Editor
- - bAllowOverrideHigher: If this is TRUE, you can set the state to a lower
- number than the one it is currently on

- `szPlotID`: string
- `nState`: int
- `bAllowOverrideHigher`: int (default: `0`)

<a id="addjournalworldentry"></a>

## `AddJournalWorldEntry(nIndex, szEntry, szTitle)` - Routine 669

- `669. AddJournalWorldEntry`
- AddJournalWorldEntry
- Adds a user entered entry to the world notices

- `nIndex`: int
- `szEntry`: string
- `szTitle`: string (default: `World Entry`)

<a id="addjournalworldentrystrref"></a>

## `AddJournalWorldEntryStrref(strref, strrefTitle)` - Routine 670

- `670. AddJournalWorldEntryStrref`
- AddJournalWorldEntryStrref
- Adds an entry to the world notices using stringrefs

- `strref`: int
- `strrefTitle`: int

<a id="adjustreputation"></a>

## `AdjustReputation(oTarget, oSourceFactionMember, nAdjustment)` - Routine 209

- `209. AdjustReputation`
- Adjust how oSourceFactionMember's faction feels about oTarget by the
- specified amount.
- Note: This adjusts Faction Reputation, how the entire faction that
- oSourceFactionMember is in, feels about oTarget.
- - No return value

- `oTarget`: object
- `oSourceFactionMember`: object
- `nAdjustment`: int

<a id="angletovector"></a>

## `AngleToVector(fAngle)` - Routine 144

- `144. AngleToVector`
- Convert fAngle to a vector

- `fAngle`: float

<a id="asin"></a>

## `asin(fValue)` - Routine 72

- `72. asin`
- Maths operation: arcsine of fValue
- - Returns zero if fValue >1 or fValue < -1

- `fValue`: float

<a id="assigncommand"></a>

## `AssignCommand(oActionSubject, aActionToAssign)` - Routine 6

- `6. AssignCommand`
- Assign aActionToAssign to oActionSubject.
- - No return value, but if an error occurs, the log file will contain
- "AssignCommand failed."
- (If the object doesn't exist, nothing happens.)

- `oActionSubject`: object
- `aActionToAssign`: action

<a id="atan"></a>

## `atan(fValue)` - Routine 73

- `73. atan`
- Maths operation: arctan of fValue

- `fValue`: float

<a id="aurpoststring"></a>

## `AurPostString(sString, nX, nY, fLife)` - Routine 582

- `582. AurPostString`
- post a string to the screen at column nX and row nY for fLife seconds

- `sString`: string
- `nX`: int
- `nY`: int
- `fLife`: float

<a id="awardstealthxp"></a>

## `AwardStealthXP(oTarget)` - Routine 480

- `480. AwardStealthXP`
- Award the stealth xp to the given oTarget.  This will only work on creatures.

- `oTarget`: object

<a id="changefaction"></a>

## `ChangeFaction(oObjectToChangeFaction, oMemberOfFactionToJoin)` - Routine 173

- `173. ChangeFaction`
- Make oObjectToChangeFaction join the faction of oMemberOfFactionToJoin.
- NB. **This will only work for two NPCs**

- `oObjectToChangeFaction`: object
- `oMemberOfFactionToJoin`: object

<a id="changefactionbyfaction"></a>

## `ChangeFactionByFaction(nFactionFrom, nFactionTo)` - Routine 737

- `737. ChangeFactionByFaction`
- This affects all creatures in the area that are in faction nFactionFrom.
- making them change to nFactionTo

- `nFactionFrom`: int
- `nFactionTo`: int

<a id="changetostandardfaction"></a>

## `ChangeToStandardFaction(oCreatureToChange, nStandardFaction)` - Routine 412

- `412. ChangeToStandardFaction`
- Make oCreatureToChange join one of the standard factions.
- **This will only work on an NPC**
- - nStandardFaction: STANDARD_FACTION_*

- `oCreatureToChange`: object
- `nStandardFaction`: int

<a id="clearallactions"></a>

## `ClearAllActions()` - Routine 9

- `9. ClearAllActions`
- Clear all the actions of the caller. (This will only work on Creatures)
- - No return value, but if an error occurs, the log file will contain
- "ClearAllActions failed.".

<a id="cos"></a>

## `cos(fValue)` - Routine 68

- `68. cos`
- Maths operation: cosine of fValue

- `fValue`: float

<a id="cutscenemove"></a>

## `CutsceneMove(oObject, vPosition, nRun)` - Routine 507

- `507. CutsceneMove`
- CutsceneMoveToPoint
- Used by the cutscene system to allow designers to script combat

- `oObject`: object
- `vPosition`: vector
- `nRun`: int

<a id="d10"></a>

## `d10(nNumDice)` - Routine 100

- `100. d10`
- Get the total from rolling (nNumDice x d10 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d100"></a>

## `d100(nNumDice)` - Routine 103

- `103. d100`
- Get the total from rolling (nNumDice x d100 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d12"></a>

## `d12(nNumDice)` - Routine 101

- `101. d12`
- Get the total from rolling (nNumDice x d12 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d2"></a>

## `d2(nNumDice)` - Routine 95

- `95. d2`
- Get the total from rolling (nNumDice x d2 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d20"></a>

## `d20(nNumDice)` - Routine 102

- `102. d20`
- Get the total from rolling (nNumDice x d20 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d3"></a>

## `d3(nNumDice)` - Routine 96

- `96. d3`
- Get the total from rolling (nNumDice x d3 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d4"></a>

## `d4(nNumDice)` - Routine 97

- `97. d4`
- Get the total from rolling (nNumDice x d4 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d6"></a>

## `d6(nNumDice)` - Routine 98

- `98. d6`
- Get the total from rolling (nNumDice x d6 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="d8"></a>

## `d8(nNumDice)` - Routine 99

- `99. d8`
- Get the total from rolling (nNumDice x d8 dice).
- - nNumDice: If this is less than 1, the value 1 will be used.

- `nNumDice`: int (default: `1`)

<a id="delaycommand"></a>

## `DelayCommand(fSeconds, aActionToDelay)` - Routine 7

- `7. DelayCommand`
- Delay aActionToDelay by fSeconds.
- - No return value, but if an error occurs, the log file will contain
- "DelayCommand failed.".

- `fSeconds`: float
- `aActionToDelay`: action

<a id="deletejournalworldallentries"></a>

## `DeleteJournalWorldAllEntries()` - Routine 672

- `672. DeleteJournalWorldAllEntries`
- DeleteJournalWorldAllEntries
- Nuke's 'em all, user entered or otherwise.

<a id="deletejournalworldentry"></a>

## `DeleteJournalWorldEntry(nIndex)` - Routine 673

- `673. DeleteJournalWorldEntry`
- DeleteJournalWorldEntry
- Deletes a user entered world notice

- `nIndex`: int

<a id="deletejournalworldentrystrref"></a>

## `DeleteJournalWorldEntryStrref(strref)` - Routine 674

- `674. DeleteJournalWorldEntryStrref`
- DeleteJournalWorldEntryStrref
- Deletes the world notice pertaining to the string ref

- `strref`: int

<a id="dodooraction"></a>

## `DoDoorAction(oTargetDoor, nDoorAction)` - Routine 338

- `338. DoDoorAction`
- Perform nDoorAction on oTargetDoor.

- `oTargetDoor`: object
- `nDoorAction`: int

<a id="doplaceableobjectaction"></a>

## `DoPlaceableObjectAction(oPlaceable, nPlaceableAction)` - Routine 547

- `547. DoPlaceableObjectAction`
- The caller performs nPlaceableAction on oPlaceable.
- - oPlaceable
- - nPlaceableAction: PLACEABLE_ACTION_*

- `oPlaceable`: object
- `nPlaceableAction`: int

<a id="duplicateheadappearance"></a>

## `DuplicateHeadAppearance(oidCreatureToChange, oidCreatureToMatch)` - Routine 500

- `500. DuplicateHeadAppearance`

- `oidCreatureToChange`: object
- `oidCreatureToMatch`: object

<a id="endgame"></a>

## `EndGame(nShowEndGameGui)` - Routine 564

- `564. EndGame`
- Immediately ends the currently running game and returns to the start screen.
- nShowEndGameGui: Set TRUE to display the death gui.

- `nShowEndGameGui`: int (default: `1`)

<a id="eventspellcastat"></a>

## `EventSpellCastAt(oCaster, nSpell, bHarmful)` - Routine 244

- `244. EventSpellCastAt`
- Create an event which triggers the "SpellCastAt" script

- `oCaster`: object
- `nSpell`: int
- `bHarmful`: int (default: `1`)

<a id="eventuserdefined"></a>

## `EventUserDefined(nUserDefinedEventNumber)` - Routine 132

- `132. EventUserDefined`
- Create an event of the type nUserDefinedEventNumber

- `nUserDefinedEventNumber`: int

<a id="executescript"></a>

## `ExecuteScript(sScript, oTarget, nScriptVar)` - Routine 8

- `8. ExecuteScript`
- Make oTarget run sScript and then return execution to the calling script.
- If sScript does not specify a compiled script, nothing happens.
- - nScriptVar: This value will be returned by calls to GetRunScriptVar.

- `sScript`: string
- `oTarget`: object
- `nScriptVar`: int

<a id="exportallcharacters"></a>

## `ExportAllCharacters()` - Routine 557

- `557. ExportAllCharacters`
- Force all the characters of the players who are currently in the game to
- be exported to their respective directories i.e. LocalVault/ServerVault/ etc.

<a id="fabs"></a>

## `fabs(fValue)` - Routine 67

- `67. fabs`
- Maths operation: absolute value of fValue

- `fValue`: float

<a id="faceobjectawayfromobject"></a>

## `FaceObjectAwayFromObject(oFacer, oObjectToFaceAwayFrom)` - Routine 553

- `553. FaceObjectAwayFromObject`
- FaceObjectAwayFromObject
- This will cause the object oFacer to face away from oObjectToFaceAwayFrom.
- The objects must be in the same area for this to work.

- `oFacer`: object
- `oObjectToFaceAwayFrom`: object

<a id="feettometers"></a>

## `FeetToMeters(fFeet)` - Routine 218

- `218. FeetToMeters`
- Convert fFeet into a number of meters.

- `fFeet`: float

<a id="findsubstring"></a>

## `FindSubString(sString, sSubString)` - Routine 66

- `66. FindSubString`
- Find the position of sSubstring inside sString
- - Return value on error: -1

- `sString`: string
- `sSubString`: string

<a id="floatingtextstringoncreature"></a>

## `FloatingTextStringOnCreature(sStringToDisplay, oCreatureToFloatAbove, bBroadcastToFaction)` - Routine 526

- `526. FloatingTextStringOnCreature`
- Display floaty text above the specified creature.
- The text will also appear in the chat buffer of each player that receives the
- floaty text.
- - sStringToDisplay: String
- - oCreatureToFloatAbove

- `sStringToDisplay`: string
- `oCreatureToFloatAbove`: object
- `bBroadcastToFaction`: int (default: `1`)

<a id="floatingtextstrrefoncreature"></a>

## `FloatingTextStrRefOnCreature(nStrRefToDisplay, oCreatureToFloatAbove, bBroadcastToFaction)` - Routine 525

- `525. FloatingTextStrRefOnCreature`
- Display floaty text above the specified creature.
- The text will also appear in the chat buffer of each player that receives the
- floaty text.
- - nStrRefToDisplay: String ref (therefore text is translated)
- - oCreatureToFloatAbove

- `nStrRefToDisplay`: int
- `oCreatureToFloatAbove`: object
- `bBroadcastToFaction`: int (default: `1`)

<a id="floattoint"></a>

## `FloatToInt(fFloat)` - Routine 231

- `231. FloatToInt`
- Convert fFloat into the nearest integer.

- `fFloat`: float

<a id="floattostring"></a>

## `FloatToString(fFloat, nWidth, nDecimals)` - Routine 3

- `3. FloatToString`
- Convert fFloat into a string.
- - nWidth should be a value from 0 to 18 inclusive.
- - nDecimals should be a value from 0 to 9 inclusive.

- `fFloat`: float
- `nWidth`: int (default: `18`)
- `nDecimals`: int (default: `9`)

<a id="fortitudesave"></a>

## `FortitudeSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 108

- `108. FortitudeSave`
- Do a Fortitude Save check for the given DC
- - oCreature
- - nDC: Difficulty check
- - nSaveType: SAVING_THROW_TYPE_*
- - oSaveVersus

- `oCreature`: object
- `nDC`: int
- `nSaveType`: int (default: `0`)
- `oSaveVersus`: object

<a id="getac"></a>

## `GetAC(oObject, nForFutureUse)` - Routine 116

- `116. GetAC`
- If oObject is a creature, this will return that creature's armour class
- If oObject is an item, door or placeable, this will return zero.
- - nForFutureUse: this parameter is not currently used
- - Return value if oObject is not a creature, item, door or placeable: -1

- `oObject`: object
- `nForFutureUse`: int (default: `0`)

<a id="getappearancetype"></a>

## `GetAppearanceType(oCreature)` - Routine 524

- `524. GetAppearanceType`
- Returns the appearance type of oCreature (0 if creature doesn't exist)
- - oCreature

- `oCreature`: object

<a id="getattemptedmovementtarget"></a>

## `GetAttemptedMovementTarget()` - Routine 489

- `489. GetAttemptedMovementTarget`
- the will get the last attmpted movment target

<a id="getattemptedspelltarget"></a>

## `GetAttemptedSpellTarget()` - Routine 375

- `375. GetAttemptedSpellTarget`
- Get the target at which the caller attempted to cast a spell.
- This value is set every time a spell is cast and is reset at the end of
- combat.
- - Returns OBJECT_INVALID if the caller is not a valid creature.

<a id="getblockingcreature"></a>

## `GetBlockingCreature(oTarget)` - Routine 490

- `490. GetBlockingCreature`
- this function returns the bloking creature for the k_def_CBTBlk01 script

- `oTarget`: object

<a id="getblockingdoor"></a>

## `GetBlockingDoor()` - Routine 336

- `336. GetBlockingDoor`
- Get the last blocking door encountered by the caller of this function.
- - Returns OBJECT_INVALID if the caller is not a valid creature.

<a id="getbuttonmashcheck"></a>

## `GetButtonMashCheck()` - Routine 267

- `267. GetButtonMashCheck`
- GetButtonMashCheck
- This function returns whether the button mash check, used for the combat tutorial, is on

<a id="getcasterlevel"></a>

## `GetCasterLevel(oCreature)` - Routine 84

- `84. GetCasterLevel`
- Get the Caster Level of oCreature.
- - Return value on error: 0;

- `oCreature`: object

<a id="getcategoryfromtalent"></a>

## `GetCategoryFromTalent(tTalent)` - Routine 735

- `735. GetCategoryFromTalent`
- Get the Category of tTalent.

- `tTalent`: talent

<a id="getchallengerating"></a>

## `GetChallengeRating(oCreature)` - Routine 494

- `494. GetChallengeRating`
- Get oCreature's challenge rating.
- - Returns 0.0 if oCreature is invalid.

- `oCreature`: object

<a id="getcheatcode"></a>

## `GetCheatCode(nCode)` - Routine 764

- `764. GetCheatCode`
- Returns true if cheat code has been enabled

- `nCode`: int

<a id="getclickingobject"></a>

## `GetClickingObject()` - Routine 326

- `326. GetClickingObject`
- Use this in a trigger's OnClick event script to get the object that last
- clicked on it.
- This is identical to GetEnteringObject.

<a id="getcommandable"></a>

## `GetCommandable(oTarget)` - Routine 163

- `163. GetCommandable`
- Determine whether oTarget's action stack can be modified.

- `oTarget`: object

<a id="getcreaturehastalent"></a>

## `GetCreatureHasTalent(tTalent, oCreature)` - Routine 306

- `306. GetCreatureHasTalent`
- Determine whether oCreature has tTalent.

- `tTalent`: talent
- `oCreature`: object

<a id="getcreaturemovmenttype"></a>

## `GetCreatureMovmentType(oidCreature)` - Routine 566

- `566. GetCreatureMovmentType`
- This function returns a value that matches one of the MOVEMENT_SPEED_... constants
- if the OID passed in is not found or not a creature then it will return
- MOVEMENT_SPEED_IMMOBILE.

- `oidCreature`: object

<a id="getcreaturesize"></a>

## `GetCreatureSize(oCreature)` - Routine 479

- `479. GetCreatureSize`
- Get the size (CREATURE_SIZE_*) of oCreature.

- `oCreature`: object

<a id="getcreaturetalentbest"></a>

## `GetCreatureTalentBest(nCategory, nCRMax, oCreature, nInclusion, nExcludeType, nExcludeId)` - Routine 308

- `308. GetCreatureTalentBest`
- Get the best talent (i.e. closest to nCRMax without going over) of oCreature,
- within nCategory.
- - nCategory: TALENT_CATEGORY_*
- - nCRMax: Challenge Rating of the talent
- - oCreature

- `nCategory`: int
- `nCRMax`: int
- `oCreature`: object
- `nInclusion`: int (default: `0`)
- `nExcludeType`: int
- `nExcludeId`: int

<a id="getcreaturetalentrandom"></a>

## `GetCreatureTalentRandom(nCategory, oCreature, nInclusion)` - Routine 307

- `307. GetCreatureTalentRandom`
- Get a random talent of oCreature, within nCategory.
- - nCategory: TALENT_CATEGORY_*
- - oCreature
- - nInclusion: types of talent to include

- `nCategory`: int
- `oCreature`: object
- `nInclusion`: int (default: `0`)

<a id="getcurrentaction"></a>

## `GetCurrentAction(oObject)` - Routine 522

- `522. GetCurrentAction`
- Get the current action (ACTION_*) that oObject is executing.

- `oObject`: object

<a id="getcurrentforcepoints"></a>

## `GetCurrentForcePoints(oObject)` - Routine 55

- `55. GetCurrentForcePoints`
- returns the current force points for the creature

- `oObject`: object

<a id="getcurrenthitpoints"></a>

## `GetCurrentHitPoints(oObject)` - Routine 49

- `49. GetCurrentHitPoints`
- Get the current hitpoints of oObject
- - Return value on error: 0

- `oObject`: object

<a id="getcurrentstealthxp"></a>

## `GetCurrentStealthXP()` - Routine 474

- `474. GetCurrentStealthXP`
- Returns the current amount of stealth xp available in the area.

<a id="getdamagedealtbytype"></a>

## `GetDamageDealtByType(nDamageType)` - Routine 344

- `344. GetDamageDealtByType`
- Get the amount of damage of type nDamageType that has been dealt to the caller.
- - nDamageType: DAMAGE_TYPE_*

- `nDamageType`: int

<a id="getdifficultymodifier"></a>

## `GetDifficultyModifier()` - Routine 523

- `523. GetDifficultyModifier`

<a id="getdistancebetween"></a>

## `GetDistanceBetween(oObjectA, oObjectB)` - Routine 151

- `151. GetDistanceBetween`
- Get the distance in metres between oObjectA and oObjectB.
- - Return value if either object is invalid: 0.0f

- `oObjectA`: object
- `oObjectB`: object

<a id="getdistancebetween2d"></a>

## `GetDistanceBetween2D(oObjectA, oObjectB)` - Routine 319

- `319. GetDistanceBetween2D`
- Get the distance in metres between oObjectA and oObjectB in 2D.
- - Return value if either object is invalid: 0.0f

- `oObjectA`: object
- `oObjectB`: object

<a id="getdistancebetweenlocations"></a>

## `GetDistanceBetweenLocations(lLocationA, lLocationB)` - Routine 298

- `298. GetDistanceBetweenLocations`
- Get the distance between lLocationA and lLocationB.

- `lLocationA`: location
- `lLocationB`: location

<a id="getdistancebetweenlocations2d"></a>

## `GetDistanceBetweenLocations2D(lLocationA, lLocationB)` - Routine 334

- `334. GetDistanceBetweenLocations2D`
- Get the distance between lLocationA and lLocationB. in 2D

- `lLocationA`: location
- `lLocationB`: location

<a id="getdistancetoobject"></a>

## `GetDistanceToObject(oObject)` - Routine 41

- `41. GetDistanceToObject`
- Get the distance from the caller to oObject in metres.
- - Return value on error: -1.0f

- `oObject`: object

<a id="getdistancetoobject2d"></a>

## `GetDistanceToObject2D(oObject)` - Routine 335

- `335. GetDistanceToObject2D`
- Get the distance from the caller to oObject in metres.
- - Return value on error: -1.0f

- `oObject`: object

<a id="getencounteractive"></a>

## `GetEncounterActive(oEncounter)` - Routine 276

- `276. GetEncounterActive`
- Determine whether oEncounter is active.

- `oEncounter`: object

<a id="getencounterdifficulty"></a>

## `GetEncounterDifficulty(oEncounter)` - Routine 297

- `297. GetEncounterDifficulty`
- Get the difficulty level of oEncounter.

- `oEncounter`: object

<a id="getencounterspawnscurrent"></a>

## `GetEncounterSpawnsCurrent(oEncounter)` - Routine 280

- `280. GetEncounterSpawnsCurrent`
- Get the number of times that oEncounter has spawned so far

- `oEncounter`: object

<a id="getencounterspawnsmax"></a>

## `GetEncounterSpawnsMax(oEncounter)` - Routine 278

- `278. GetEncounterSpawnsMax`
- Get the maximum number of times that oEncounter will spawn.

- `oEncounter`: object

<a id="getenteringobject"></a>

## `GetEnteringObject()` - Routine 25

- `25. GetEnteringObject`
- The value returned by this function depends on the object type of the caller:
- 1) If the caller is a door or placeable it returns the object that last
- triggered it.
- 2) If the caller is a trigger, area of effect, module, area or encounter it
- returns the object that last entered it.

<a id="getexitingobject"></a>

## `GetExitingObject()` - Routine 26

- `26. GetExitingObject`
- Get the object that last left the caller.  This function works on triggers,
- areas of effect, modules, areas and encounters.
- - Return value on error: OBJECT_INVALID

<a id="getfacing"></a>

## `GetFacing(oTarget)` - Routine 28

- `28. GetFacing`
- Get the direction in which oTarget is facing, expressed as a float between
- 0f and 360.0f
- - Return value on error: -1.0f

- `oTarget`: object

<a id="getfacingfromlocation"></a>

## `GetFacingFromLocation(lLocation)` - Routine 225

- `225. GetFacingFromLocation`
- Get the orientation value from lLocation.

- `lLocation`: location

<a id="getfactionaveragelevel"></a>

## `GetFactionAverageLevel(oFactionMember)` - Routine 189

- `189. GetFactionAverageLevel`
- Get the average level of the members of the faction.
- - Return value on error: -1

- `oFactionMember`: object

<a id="getfactionaveragereputation"></a>

## `GetFactionAverageReputation(oSourceFactionMember, oTarget)` - Routine 186

- `186. GetFactionAverageReputation`
- Get an integer between 0 and 100 (inclusive) that represents how
- oSourceFactionMember's faction feels about oTarget.
- - Return value on error: -1

- `oSourceFactionMember`: object
- `oTarget`: object

<a id="getfactionaveragexp"></a>

## `GetFactionAverageXP(oFactionMember)` - Routine 190

- `190. GetFactionAverageXP`
- Get the average XP of the members of the faction.
- - Return value on error: -1

- `oFactionMember`: object

<a id="getfactionbestac"></a>

## `GetFactionBestAC(oFactionMember, bMustBeVisible)` - Routine 193

- `193. GetFactionBestAC`
- Get the object faction member with the highest armour class.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfactionequal"></a>

## `GetFactionEqual(oFirstObject, oSecondObject)` - Routine 172

- `172. GetFactionEqual`
- - Returns TRUE if the Faction Ids of the two objects are the same

- `oFirstObject`: object
- `oSecondObject`: object

<a id="getfactiongold"></a>

## `GetFactionGold(oFactionMember)` - Routine 185

- `185. GetFactionGold`
- Get the amount of gold held by oFactionMember's faction.
- - Returns -1 if oFactionMember's faction is invalid.

- `oFactionMember`: object

<a id="getfactionleader"></a>

## `GetFactionLeader(oMemberOfFaction)` - Routine 562

- `562. GetFactionLeader`
- Get the leader of the faction of which oMemberOfFaction is a member.
- - Returns OBJECT_INVALID if oMemberOfFaction is not a valid creature.

- `oMemberOfFaction`: object

<a id="getfactionleastdamagedmember"></a>

## `GetFactionLeastDamagedMember(oFactionMember, bMustBeVisible)` - Routine 184

- `184. GetFactionLeastDamagedMember`
- Get the member of oFactionMember's faction that has taken the fewest hit
- points of damage.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfactionmostdamagedmember"></a>

## `GetFactionMostDamagedMember(oFactionMember, bMustBeVisible)` - Routine 183

- `183. GetFactionMostDamagedMember`
- Get the member of oFactionMember's faction that has taken the most hit points
- of damage.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfactionstrongestmember"></a>

## `GetFactionStrongestMember(oFactionMember, bMustBeVisible)` - Routine 182

- `182. GetFactionStrongestMember`
- Get the strongest member of oFactionMember's faction.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfactionweakestmember"></a>

## `GetFactionWeakestMember(oFactionMember, bMustBeVisible)` - Routine 181

- `181. GetFactionWeakestMember`
- Get the weakest member of oFactionMember's faction.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfactionworstac"></a>

## `GetFactionWorstAC(oFactionMember, bMustBeVisible)` - Routine 192

- `192. GetFactionWorstAC`
- Get the object faction member with the lowest armour class.
- - Returns OBJECT_INVALID if oFactionMember's faction is invalid.

- `oFactionMember`: object
- `bMustBeVisible`: int (default: `1`)

<a id="getfirstfactionmember"></a>

## `GetFirstFactionMember(oMemberOfFaction, bPCOnly)` - Routine 380

- `380. GetFirstFactionMember`
- Get the first member of oMemberOfFaction's faction (start to cycle through
- oMemberOfFaction's faction).
- - Returns OBJECT_INVALID if oMemberOfFaction's faction is invalid.

- `oMemberOfFaction`: object
- `bPCOnly`: int (default: `1`)

<a id="getfirstinpersistentobject"></a>

## `GetFirstInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`

- These are for GetFirstInPersistentObject() and GetNextInPersistentObject()

- `oPersistentObject`: object
- `nResidentObjectType`: int (default: `1`)
- `nPersistentZone`: int (default: `0`)

<a id="getfirstobjectinshape"></a>

## `GetFirstObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 128

- `128. GetFirstObjectInShape`
- Get the first object in nShape
- - nShape: SHAPE_*
- - fSize:
- -> If nShape == SHAPE_SPHERE, this is the radius of the sphere
- -> If nShape == SHAPE_SPELLCYLINDER, this is the radius of the cylinder

- `nShape`: int
- `fSize`: float
- `lTarget`: location
- `bLineOfSight`: int (default: `0`)
- `nObjectFilter`: int (default: `1`)
- `vOrigin`: vector

<a id="getfirstpc"></a>

## `GetFirstPC()` - Routine 548

- `548. GetFirstPC`
- Get the first PC in the player list.
- This resets the position in the player list for GetNextPC().

<a id="getfortitudesavingthrow"></a>

## `GetFortitudeSavingThrow(oTarget)` - Routine 491

- `491. GetFortitudeSavingThrow`
- Get oTarget's base fortitude saving throw value (this will only work for
- creatures, doors, and placeables).
- - Returns 0 if oTarget is invalid.

- `oTarget`: object

<a id="getfoundenemycreature"></a>

## `GetFoundEnemyCreature(oTarget)` - Routine 495

- `495. GetFoundEnemyCreature`
- Returns the found enemy creature on a pathfind.

- `oTarget`: object

<a id="getgamedifficulty"></a>

## `GetGameDifficulty()` - Routine 513

- `513. GetGameDifficulty`
- Get the game difficulty (GAME_DIFFICULTY_*).

<a id="getgender"></a>

## `GetGender(oCreature)` - Routine 358

- `358. GetGender`
- Get the gender of oCreature.

- `oCreature`: object

<a id="getgold"></a>

## `GetGold(oTarget)` - Routine 418

- `418. GetGold`
- Get the amount of gold possessed by oTarget.

- `oTarget`: object

<a id="getgoldpiecevalue"></a>

## `GetGoldPieceValue(oItem)` - Routine 311

- `311. GetGoldPieceValue`
- Get the gold piece value of oItem.
- - Returns 0 if oItem is not a valid item.

- `oItem`: object

<a id="getgoodevilvalue"></a>

## `GetGoodEvilValue(oCreature)` - Routine 125

- `125. GetGoodEvilValue`
- Get an integer between 0 and 100 (inclusive) to represent oCreature's
- Good/Evil alignment
- (100=good, 0=evil)
- - Return value if oCreature is not a valid creature: -1

- `oCreature`: object

<a id="gethasinventory"></a>

## `GetHasInventory(oObject)` - Routine 570

- `570. GetHasInventory`
- Determine whether oObject has an inventory.
- - Returns TRUE for creatures and stores, and checks to see if an item or placeable object is a container.
- - Returns FALSE for all other object types.

- `oObject`: object

<a id="gethasspell"></a>

## `GetHasSpell(nSpell, oCreature)` - Routine 377

- `377. GetHasSpell`
- Determine whether oCreature has nSpell memorised.
- - nSpell: SPELL_*
- - oCreature

- `nSpell`: int
- `oCreature`: object

<a id="gethitdice"></a>

## `GetHitDice(oCreature)` - Routine 166

- `166. GetHitDice`
- Get the number of hitdice for oCreature.
- - Return value if oCreature is not a valid creature: 0

- `oCreature`: object

<a id="getidentified"></a>

## `GetIdentified(oItem)` - Routine 332

- `332. GetIdentified`
- Determined whether oItem has been identified.

- `oItem`: object

<a id="getidfromtalent"></a>

## `GetIdFromTalent(tTalent)` - Routine 363

- `363. GetIdFromTalent`
- Get the ID of tTalent.  This could be a SPELL_*, FEAT_* or SKILL_*.

- `tTalent`: talent

<a id="getinventorydisturbtype"></a>

## `GetInventoryDisturbType()` - Routine 352

- `352. GetInventoryDisturbType`
- Get the type of disturbance (INVENTORY_DISTURB_*) that caused the caller's
- OnInventoryDisturbed script to fire.  This will only work for creatures and
- placeables.

<a id="getisdawn"></a>

## `GetIsDawn()` - Routine 407

- `407. GetIsDawn`
- - Returns TRUE if it is currently dawn.

<a id="getisday"></a>

## `GetIsDay()` - Routine 405

- `405. GetIsDay`
- - Returns TRUE if it is currently day.

<a id="getisdead"></a>

## `GetIsDead(oCreature)` - Routine 140

- `140. GetIsDead`
- - Returns TRUE if oCreature is a dead NPC, dead PC or a dying PC.

- `oCreature`: object

<a id="getisdebilitated"></a>

## `GetIsDebilitated(oCreature)` - Routine 732

- `732. GetIsDebilitated`
- Returns whether the given object is debilitated or not

- `oCreature`: object

<a id="getisdooractionpossible"></a>

## `GetIsDoorActionPossible(oTargetDoor, nDoorAction)` - Routine 337

- `337. GetIsDoorActionPossible`
- - oTargetDoor
- - nDoorAction: DOOR_ACTION_*
- - Returns TRUE if nDoorAction can be performed on oTargetDoor.

- `oTargetDoor`: object
- `nDoorAction`: int

<a id="getisdusk"></a>

## `GetIsDusk()` - Routine 408

- `408. GetIsDusk`
- - Returns TRUE if it is currently dusk.

<a id="getisencountercreature"></a>

## `GetIsEncounterCreature(oCreature)` - Routine 409

- `409. GetIsEncounterCreature`
- - Returns TRUE if oCreature was spawned from an encounter.

- `oCreature`: object

<a id="getisenemy"></a>

## `GetIsEnemy(oTarget, oSource)` - Routine 235

- `235. GetIsEnemy`
- - Returns TRUE if oSource considers oTarget as an enemy.

- `oTarget`: object
- `oSource`: object

<a id="getisfriend"></a>

## `GetIsFriend(oTarget, oSource)` - Routine 236

- `236. GetIsFriend`
- - Returns TRUE if oSource considers oTarget as a friend.

- `oTarget`: object
- `oSource`: object

<a id="getisimmune"></a>

## `GetIsImmune(oCreature, nImmunityType, oVersus)` - Routine 274

- `274. GetIsImmune`
- - oCreature
- - nImmunityType: IMMUNITY_TYPE_*
- - oVersus: if this is specified, then we also check for the race and
- alignment of oVersus
- - Returns TRUE if oCreature has immunity of type nImmunity versus oVersus.

- `oCreature`: object
- `nImmunityType`: int
- `oVersus`: object

<a id="getislinkimmune"></a>

## `GetIsLinkImmune(oTarget, eEffect)` - Routine 390

- `390. GetIsLinkImmune`
- Tests a linked effect to see if the target is immune to it.
- If the target is imune to any of the linked effect then he is immune to all of it

- `oTarget`: object
- `eEffect`: effect

<a id="getislistening"></a>

## `GetIsListening(oObject)` - Routine 174

- `174. GetIsListening`
- - Returns TRUE if oObject is listening for something

- `oObject`: object

<a id="getislivecontentavailable"></a>

## `GetIsLiveContentAvailable(nPkg)` - Routine 748

- `748. GetIsLiveContentAvailable`
- GetIsLiveContentAvailable
- Determines whether a given live content package is available
- nPkg = LIVE_CONTENT_PKG1, LIVE_CONTENT_PKG2, ..., LIVE_CONTENT_PKG6

- `nPkg`: int

<a id="getisneutral"></a>

## `GetIsNeutral(oTarget, oSource)` - Routine 237

- `237. GetIsNeutral`
- - Returns TRUE if oSource considers oTarget as neutral.

- `oTarget`: object
- `oSource`: object

<a id="getisnight"></a>

## `GetIsNight()` - Routine 406

- `406. GetIsNight`
- - Returns TRUE if it is currently night.

<a id="getisobjectvalid"></a>

## `GetIsObjectValid(oObject)` - Routine 42

- `42. GetIsObjectValid`
- - Returns TRUE if oObject is a valid object.

- `oObject`: object

<a id="getisopen"></a>

## `GetIsOpen(oObject)` - Routine 443

- `443. GetIsOpen`
- - Returns TRUE if oObject (which is a placeable or a door) is currently open.

- `oObject`: object

<a id="getisplaceableobjectactionpossible"></a>

## `GetIsPlaceableObjectActionPossible(oPlaceable, nPlaceableAction)` - Routine 546

- `546. GetIsPlaceableObjectActionPossible`
- - oPlaceable
- - nPlaceableAction: PLACEABLE_ACTION_*
- - Returns TRUE if nPlacebleAction is valid for oPlaceable.

- `oPlaceable`: object
- `nPlaceableAction`: int

<a id="getispoisoned"></a>

## `GetIsPoisoned(oObject)` - Routine 751

- `751. GetIsPoisoned`
- GetIsPoisoned
- Returns TRUE if the object specified is poisoned.

- `oObject`: object

<a id="getistalentvalid"></a>

## `GetIsTalentValid(tTalent)` - Routine 359

- `359. GetIsTalentValid`
- - Returns TRUE if tTalent is valid.

- `tTalent`: talent

<a id="getistrapped"></a>

## `GetIsTrapped(oObject)` - Routine 551

- `551. GetIsTrapped`
- Note: Only placeables, doors and triggers can be trapped.
- - Returns TRUE if oObject is trapped.

- `oObject`: object

<a id="getjournalentry"></a>

## `GetJournalEntry(szPlotID)` - Routine 369

- `369. GetJournalEntry`
- Gets the State value of a journal quest.  Returns 0 if no quest entry has been added for this szPlotID.
- - szPlotID: the plot identifier used in the toolset's Journal Editor

- `szPlotID`: string

<a id="getjournalquestexperience"></a>

## `GetJournalQuestExperience(szPlotID)` - Routine 384

- `384. GetJournalQuestExperience`
- Get the experience assigned in the journal editor for szPlotID.

- `szPlotID`: string

<a id="getlastassociatecommand"></a>

## `GetLastAssociateCommand(oAssociate)` - Routine 321

- `321. GetLastAssociateCommand`
- Get the last command (ASSOCIATE_COMMAND_*) issued to oAssociate.

- `oAssociate`: object

<a id="getlastclosedby"></a>

## `GetLastClosedBy()` - Routine 260

- `260. GetLastClosedBy`
- Use this in an OnClosed script to get the object that closed the door or placeable.
- - Returns OBJECT_INVALID if the caller is not a valid door or placeable.

<a id="getlastdamager"></a>

## `GetLastDamager()` - Routine 346

- `346. GetLastDamager`
- Get the last object that damaged the caller.
- - Returns OBJECT_INVALID if the caller is not a valid object.

<a id="getlastdisarmed"></a>

## `GetLastDisarmed()` - Routine 347

- `347. GetLastDisarmed`
- Get the last object that disarmed the trap on the caller.
- - Returns OBJECT_INVALID if the caller is not a valid placeable, trigger or
- door.

<a id="getlastdisturbed"></a>

## `GetLastDisturbed()` - Routine 348

- `348. GetLastDisturbed`
- Get the last object that disturbed the inventory of the caller.
- - Returns OBJECT_INVALID if the caller is not a valid creature or placeable.

<a id="getlastforcepowerused"></a>

## `GetLastForcePowerUsed(oAttacker)` - Routine 723

- `723. GetLastForcePowerUsed`
- Returns the last force power used (as a spell number that indexes the Spells.2da) by the given object

- `oAttacker`: object

<a id="getlasthostileactor"></a>

## `GetLastHostileActor(oVictim)` - Routine 556

- `556. GetLastHostileActor`
- Get the last object that was sent as a GetLastAttacker(), GetLastDamager(),
- GetLastSpellCaster() (for a hostile spell), or GetLastDisturbed() (when a
- creature is pickpocketed).
- Note: Return values may only ever be:
- 1) A Creature

- `oVictim`: object

<a id="getlasthostiletarget"></a>

## `GetLastHostileTarget(oAttacker)` - Routine 721

- `721. GetLastAttackTarget`
- Returns the last attack target for a given object

- `oAttacker`: object

<a id="getlastlocked"></a>

## `GetLastLocked()` - Routine 349

- `349. GetLastLocked`
- Get the last object that locked the caller.
- - Returns OBJECT_INVALID if the caller is not a valid door or placeable.

<a id="getlastopenedby"></a>

## `GetLastOpenedBy()` - Routine 376

- `376. GetLastOpenedBy`
- Get the last creature that opened the caller.
- - Returns OBJECT_INVALID if the caller is not a valid door or placeable.

<a id="getlastpazaakresult"></a>

## `GetLastPazaakResult()` - Routine 365

- `365. GetLastPazaakResult`
- Returns result of last Pazaak game.  Should be used only in an EndScript sent to PlayPazaak.
- - Returns 0 if player loses, 1 if player wins.

<a id="getlastperceived"></a>

## `GetLastPerceived()` - Routine 256

- `256. GetLastPerceived`
- Use this in an OnPerception script to get the object that was perceived.
- - Returns OBJECT_INVALID if the caller is not a valid creature.

<a id="getlastperceptionheard"></a>

## `GetLastPerceptionHeard()` - Routine 257

- `257. GetLastPerceptionHeard`
- Use this in an OnPerception script to determine whether the object that was
- perceived was heard.

<a id="getlastperceptioninaudible"></a>

## `GetLastPerceptionInaudible()` - Routine 258

- `258. GetLastPerceptionInaudible`
- Use this in an OnPerception script to determine whether the object that was
- perceived has become inaudible.

<a id="getlastperceptionseen"></a>

## `GetLastPerceptionSeen()` - Routine 259

- `259. GetLastPerceptionSeen`
- Use this in an OnPerception script to determine whether the object that was
- perceived was seen.

<a id="getlastperceptionvanished"></a>

## `GetLastPerceptionVanished()` - Routine 261

- `261. GetLastPerceptionVanished`
- Use this in an OnPerception script to determine whether the object that was
- perceived has vanished.

<a id="getlastrespawnbuttonpresser"></a>

## `GetLastRespawnButtonPresser()` - Routine 419

- `419. GetLastRespawnButtonPresser`
- Use this in an OnRespawnButtonPressed module script to get the object id of
- the player who last pressed the respawn button.

<a id="getlastspell"></a>

## `GetLastSpell()` - Routine 246

- `246. GetLastSpell`
- This is for use in a "Spell Cast" script, it gets the ID of the spell that
- was cast.

<a id="getlastspellcaster"></a>

## `GetLastSpellCaster()` - Routine 245

- `245. GetLastSpellCaster`
- This is for use in a "Spell Cast" script, it gets who cast the spell.
- The spell could have been cast by a creature, placeable or door.
- - Returns OBJECT_INVALID if the caller is not a creature, placeable or door.

<a id="getlastspellharmful"></a>

## `GetLastSpellHarmful()` - Routine 423

- `423. GetLastSpellHarmful`
- Use this in a SpellCast script to determine whether the spell was considered
- harmful.
- - Returns TRUE if the last spell cast was harmful.

<a id="getlasttrapdetected"></a>

## `GetLastTrapDetected(oTarget)` - Routine 486

- `486. GetLastTrapDetected`
- Get the last trap detected by oTarget.
- - Return value on error: OBJECT_INVALID

- `oTarget`: object

<a id="getlastunlocked"></a>

## `GetLastUnlocked()` - Routine 350

- `350. GetLastUnlocked`
- Get the last object that unlocked the caller.
- - Returns OBJECT_INVALID if the caller is not a valid door or placeable.

<a id="getlastusedby"></a>

## `GetLastUsedBy()` - Routine 330

- `330. GetLastUsedBy`
- Get the last object that used the placeable object that is calling this function.
- - Returns OBJECT_INVALID if it is called by something other than a placeable or
- a door.

<a id="getlastweaponused"></a>

## `GetLastWeaponUsed(oCreature)` - Routine 328

- `328. GetLastWeaponUsed`
- Get the last weapon that oCreature used in an attack.
- - Returns OBJECT_INVALID if oCreature did not attack, or has no weapon equipped.

- `oCreature`: object

<a id="getlevelbyposition"></a>

## `GetLevelByPosition(nClassPosition, oCreature)` - Routine 342

- `342. GetLevelByPosition`
- A creature can have up to three classes.  This function determines the
- creature's class level based on nClass Position.
- - nClassPosition: 1, 2 or 3
- - oCreature
- - Returns 0 if oCreature does not have a class in nClassPosition

- `nClassPosition`: int
- `oCreature`: object

<a id="getlistenpatternnumber"></a>

## `GetListenPatternNumber()` - Routine 195

- `195. GetListenPatternNumber`
- In an onConversation script this gets the number of the string pattern
- matched (the one that triggered the script).
- - Returns -1 if no string matched

<a id="getloadfromsavegame"></a>

## `GetLoadFromSaveGame()` - Routine 251

- `251. GetLoadFromSaveGame`
- Returns whether this script is being run
- while a load game is in progress

<a id="getlocation"></a>

## `GetLocation(oObject)` - Routine 213

- `213. GetLocation`
- Get the location of oObject.

- `oObject`: object

<a id="getlocked"></a>

## `GetLocked(oTarget)` - Routine 325

- `325. GetLocked`
- Get the locked state of oTarget, which can be a door or a placeable object.

- `oTarget`: object

<a id="getlockkeyrequired"></a>

## `GetLockKeyRequired(oObject)` - Routine 537

- `537. GetLockKeyRequired`
- - Returns TRUE if a specific key is required to open the lock on oObject.

- `oObject`: object

<a id="getlockkeytag"></a>

## `GetLockKeyTag(oObject)` - Routine 538

- `538. GetLockKeyTag`
- Get the tag of the key that will open the lock on oObject.

- `oObject`: object

<a id="getlocklockable"></a>

## `GetLockLockable(oObject)` - Routine 539

- `539. GetLockLockable`
- - Returns TRUE if the lock on oObject is lockable.

- `oObject`: object

<a id="getlocklockdc"></a>

## `GetLockLockDC(oObject)` - Routine 541

- `541. GetLockLockDC`
- Get the DC for locking oObject.

- `oObject`: object

<a id="getlockunlockdc"></a>

## `GetLockUnlockDC(oObject)` - Routine 540

- `540. GetLockUnlockDC`
- Get the DC for unlocking oObject.

- `oObject`: object

<a id="getmatchedsubstring"></a>

## `GetMatchedSubstring(nString)` - Routine 178

- `178. GetMatchedSubstring`
- Get the appropriate matched string (this should only be used in
- OnConversation scripts).
- - Returns the appropriate matched string, otherwise returns ""

- `nString`: int

<a id="getmatchedsubstringscount"></a>

## `GetMatchedSubstringsCount()` - Routine 179

- `179. GetMatchedSubstringsCount`
- Get the number of string parameters available.
- - Returns -1 if no string matched (this could be because of a dialogue event)

<a id="getmaxforcepoints"></a>

## `GetMaxForcePoints(oObject)` - Routine 56

- `56. GetMaxForcePoints`
- returns the Max force points for the creature

- `oObject`: object

<a id="getmaxhitpoints"></a>

## `GetMaxHitPoints(oObject)` - Routine 50

- `50. GetMaxHitPoints`
- Get the maximum hitpoints of oObject
- - Return value on error: 0

- `oObject`: object

<a id="getmaxstealthxp"></a>

## `GetMaxStealthXP()` - Routine 464

- `464. GetMaxStealthXP`
- Returns the maximum amount of stealth xp available in the area.

<a id="getminonehp"></a>

## `GetMinOneHP(oObject)` - Routine 715

- `715. GetMinOneHP`
- Checks to see if oObject has the MinOneHP Flag set on them.

- `oObject`: object

<a id="getmovementrate"></a>

## `GetMovementRate(oCreature)` - Routine 496

- `496. GetMovementRate`
- Get oCreature's movement rate.
- - Returns 0 if oCreature is invalid.

- `oCreature`: object

<a id="getname"></a>

## `GetName(oObject)` - Routine 253

- `253. GetName`
- Get the name of oObject.

- `oObject`: object

<a id="getnextfactionmember"></a>

## `GetNextFactionMember(oMemberOfFaction, bPCOnly)` - Routine 381

- `381. GetNextFactionMember`
- Get the next member of oMemberOfFaction's faction (continue to cycle through
- oMemberOfFaction's faction).
- - Returns OBJECT_INVALID if oMemberOfFaction's faction is invalid.

- `oMemberOfFaction`: object
- `bPCOnly`: int (default: `1`)

<a id="getnextinpersistentobject"></a>

## `GetNextInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`

- These are for GetFirstInPersistentObject() and GetNextInPersistentObject()

- `oPersistentObject`: object
- `nResidentObjectType`: int (default: `1`)
- `nPersistentZone`: int (default: `0`)

<a id="getnextobjectinshape"></a>

## `GetNextObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 129

- `129. GetNextObjectInShape`
- Get the next object in nShape
- - nShape: SHAPE_*
- - fSize:
- -> If nShape == SHAPE_SPHERE, this is the radius of the sphere
- -> If nShape == SHAPE_SPELLCYLINDER, this is the radius of the cylinder

- `nShape`: int
- `fSize`: float
- `lTarget`: location
- `bLineOfSight`: int (default: `0`)
- `nObjectFilter`: int (default: `1`)
- `vOrigin`: vector

<a id="getnextpc"></a>

## `GetNextPC()` - Routine 548

- `548. GetNextPC`
- Get the first PC in the player list.
- This resets the position in the player list for GetNextPC().

<a id="getnpcaistyle"></a>

## `GetNPCAIStyle(oCreature)` - Routine 705

- `705. GetNPCAIStyle`
- Returns the party members ai style

- `oCreature`: object

<a id="getpclevellingup"></a>

## `GetPCLevellingUp()` - Routine 542

- `542. GetPCLevellingUp`
- Get the last PC that levelled up.

<a id="getplaceableillumination"></a>

## `GetPlaceableIllumination(oPlaceable)` - Routine 545

- `545. GetPlaceableIllumination`
- - Returns TRUE if the illumination for oPlaceable is on

- `oPlaceable`: object

<a id="getplanetavailable"></a>

## `GetPlanetAvailable(nPlanet)` - Routine 743

- `743. GetPlanetAvailable`
- GetPlanetAvailable
- Returns wheter or not 'nPlanet' is available.

- `nPlanet`: int

<a id="getplanetselectable"></a>

## `GetPlanetSelectable(nPlanet)` - Routine 741

- `741. GetPlanetSelectable`
- GetPlanetSelectable
- Returns wheter or not 'nPlanet' is selectable.

- `nPlanet`: int

<a id="getplotflag"></a>

## `GetPlotFlag(oTarget)` - Routine 455

- `455. GetPlotFlag`
- Determine whether oTarget is a plot object.

- `oTarget`: object

<a id="getposition"></a>

## `GetPosition(oTarget)` - Routine 27

- `27. GetPosition`
- Get the position of oTarget
- - Return value on error: vector (0.0f, 0.0f, 0.0f)

- `oTarget`: object

<a id="getpositionfromlocation"></a>

## `GetPositionFromLocation(lLocation)` - Routine 223

- `223. GetPositionFromLocation`
- Get the position vector from lLocation.

- `lLocation`: location

<a id="getracialtype"></a>

## `GetRacialType(oCreature)` - Routine 107

- `107. GetRacialType`
- Get the racial type (RACIAL_TYPE_*) of oCreature
- - Return value if oCreature is not a valid creature: RACIAL_TYPE_INVALID

- `oCreature`: object

<a id="getreflexadjusteddamage"></a>

## `GetReflexAdjustedDamage(nDamage, oTarget, nDC, nSaveType, oSaveVersus)` - Routine 299

- `299. GetReflexAdjustedDamage`
- Use this in spell scripts to get nDamage adjusted by oTarget's reflex and
- evasion saves.
- - nDamage
- - oTarget
- - nDC: Difficulty check

- `nDamage`: int
- `oTarget`: object
- `nDC`: int
- `nSaveType`: int (default: `0`)
- `oSaveVersus`: object

<a id="getreflexsavingthrow"></a>

## `GetReflexSavingThrow(oTarget)` - Routine 493

- `493. GetReflexSavingThrow`
- Get oTarget's base reflex saving throw value (this will only work for
- creatures, doors, and placeables).
- - Returns 0 if oTarget is invalid.

- `oTarget`: object

<a id="getreputation"></a>

## `GetReputation(oSource, oTarget)` - Routine 208

- `208. GetReputation`
- Get an integer between 0 and 100 (inclusive) that represents how oSource
- feels about oTarget.
- -> 0-10 means oSource is hostile to oTarget
- -> 11-89 means oSource is neutral to oTarget
- -> 90-100 means oSource is friendly to oTarget

- `oSource`: object
- `oTarget`: object

<a id="getrunscriptvar"></a>

## `GetRunScriptVar()` - Routine 565

- `565. GetRunScriptVar`
- Get a variable passed when calling console debug runscript

<a id="getselectedplanet"></a>

## `GetSelectedPlanet()` - Routine 744

- `744. GetSelectedPlanet`
- GetSelectedPlanet
- Returns the ID of the currently selected planet.  Check Planetary.2da
- for which planet the return value corresponds to. If the return is -1
- no planet is selected.

<a id="getsolomode"></a>

## `GetSoloMode()` - Routine 462

- `462. GetSoloMode`
- Returns: TRUE if the player is in 'solo mode' (ie. the party is not supposed to follow the player).
- FALSE otherwise.

<a id="getspellid"></a>

## `GetSpellId()` - Routine 248

- `248. GetSpellId`
- This is for use in a Spell script, it gets the ID of the spell that is being
- cast (SPELL_*).

<a id="getspellsavedc"></a>

## `GetSpellSaveDC()` - Routine 111

- `111. GetSpellSaveDC`
- Get the DC to save against for a spell (10 + spell level + relevant ability
- bonus).  This can be called by a creature or by an Area of Effect object.

<a id="getspelltarget"></a>

## `GetSpellTarget(oCreature)` - Routine 752

- `752. GetSpellTarget`
- GetSpellTarget
- Returns the object id of the spell target

- `oCreature`: object

<a id="getspelltargetlocation"></a>

## `GetSpellTargetLocation()` - Routine 222

- `222. GetSpellTargetLocation`
- Get the location of the caller's last spell target.

<a id="getstandardfaction"></a>

## `GetStandardFaction(oObject)` - Routine 713

- `713. GetStandardFaction`
- GetStandardFaction
- Find out which standard faction oObject belongs to.
- - Returns INVALID_STANDARD_FACTION if oObject does not belong to
- a Standard Faction, or an error has occurred.

- `oObject`: object

<a id="getstartinglocation"></a>

## `GetStartingLocation()` - Routine 411

- `411. GetStartingLocation`
- Get the starting location of the module.

<a id="getstealthxpdecrement"></a>

## `GetStealthXPDecrement()` - Routine 498

- `498. GetStealthXPDecrement`
- Returns the amount the stealth xp bonus gets decreased each time the player is detected.

<a id="getstealthxpenabled"></a>

## `GetStealthXPEnabled()` - Routine 481

- `481. GetStealthXPEnabled`
- Returns whether or not the stealth xp bonus is enabled (ie. whether or not
- AwardStealthXP() will actually award any available stealth xp).

<a id="getstringbystrref"></a>

## `GetStringByStrRef(nStrRef)` - Routine 239

- `239. GetStringByStrRef`
- Get a string from the talk table using nStrRef.

- `nStrRef`: int

<a id="getstringleft"></a>

## `GetStringLeft(sString, nCount)` - Routine 63

- `63. GetStringLeft`
- Get nCounter characters from the left end of sString
- - Return value on error: ""

- `sString`: string
- `nCount`: int

<a id="getstringlength"></a>

## `GetStringLength(sString)` - Routine 59

- `59. GetStringLength`
- Get the length of sString
- - Return value on error: -1

- `sString`: string

<a id="getstringlowercase"></a>

## `GetStringLowerCase(sString)` - Routine 61

- `61. GetStringLowerCase`
- Convert sString into lower case
- - Return value on error: ""

- `sString`: string

<a id="getstringright"></a>

## `GetStringRight(sString, nCount)` - Routine 62

- `62. GetStringRight`
- Get nCount characters from the right end of sString
- - Return value on error: ""

- `sString`: string
- `nCount`: int

<a id="getstringuppercase"></a>

## `GetStringUpperCase(sString)` - Routine 60

- `60. GetStringUpperCase`
- Convert sString into upper case
- - Return value on error: ""

- `sString`: string

<a id="getsubrace"></a>

## `GetSubRace(oCreature)` - Routine 497

- `497. GetSubRace`
- GetSubRace of oCreature
- Returns SUBRACE_*

- `oCreature`: object

<a id="getsubscreenid"></a>

## `GetSubScreenID()` - Routine 53

- `53. GetSubScreenID`
- Returns the ID of the subscreen that is currently onscreen.  This will be one of the
- SUBSCREEN_ID_* constant values.

<a id="getsubstring"></a>

## `GetSubString(sString, nStart, nCount)` - Routine 65

- `65. GetSubString`
- Get nCount characters from sString, starting at nStart
- - Return value on error: ""

- `sString`: string
- `nStart`: int
- `nCount`: int

<a id="gettag"></a>

## `GetTag(oObject)` - Routine 168

- `168. GetTag`
- Get the Tag of oObject
- - Return value if oObject is not a valid object: ""

- `oObject`: object

<a id="gettimehour"></a>

## `GetTimeHour()` - Routine 16

- `16. GetTimeHour`
- Get the current hour.

<a id="gettimemillisecond"></a>

## `GetTimeMillisecond()` - Routine 19

- `19. GetTimeMillisecond`
- Get the current millisecond

<a id="gettimeminute"></a>

## `GetTimeMinute()` - Routine 17

- `17. GetTimeMinute`
- Get the current minute

<a id="gettimesecond"></a>

## `GetTimeSecond()` - Routine 18

- `18. GetTimeSecond`
- Get the current second

<a id="gettotaldamagedealt"></a>

## `GetTotalDamageDealt()` - Routine 345

- `345. GetTotalDamageDealt`
- Get the total amount of damage that has been dealt to the caller.

<a id="gettransitiontarget"></a>

## `GetTransitionTarget(oTransition)` - Routine 198

- `198. GetTransitionTarget`
- Get the destination (a waypoint or a door) for a trigger or a door.
- - Returns OBJECT_INVALID if oTransition is not a valid trigger or door.

- `oTransition`: object

<a id="gettrapbasetype"></a>

## `GetTrapBaseType(oTrapObject)` - Routine 531

- `531. GetTrapBaseType`
- Get the trap base type (TRAP_BASE_TYPE_*) of oTrapObject.
- - oTrapObject: a placeable, door or trigger

- `oTrapObject`: object

<a id="gettrapcreator"></a>

## `GetTrapCreator(oTrapObject)` - Routine 533

- `533. GetTrapCreator`
- Get the creator of oTrapObject, the creature that set the trap.
- - oTrapObject: a placeable, door or trigger
- - Returns OBJECT_INVALID if oTrapObject was created in the toolset.

- `oTrapObject`: object

<a id="gettrapdetectable"></a>

## `GetTrapDetectable(oTrapObject)` - Routine 528

- `528. GetTrapDetectable`
- - oTrapObject: a placeable, door or trigger
- - Returns TRUE if oTrapObject is detectable.

- `oTrapObject`: object

<a id="gettrapdetectdc"></a>

## `GetTrapDetectDC(oTrapObject)` - Routine 536

- `536. GetTrapDetectDC`
- Get the DC for detecting oTrapObject.
- - oTrapObject: a placeable, door or trigger

- `oTrapObject`: object

<a id="gettrapdetectedby"></a>

## `GetTrapDetectedBy(oTrapObject, oCreature)` - Routine 529

- `529. GetTrapDetectedBy`
- - oTrapObject: a placeable, door or trigger
- - oCreature
- - Returns TRUE if oCreature has detected oTrapObject

- `oTrapObject`: object
- `oCreature`: object

<a id="gettrapdisarmable"></a>

## `GetTrapDisarmable(oTrapObject)` - Routine 527

- `527. GetTrapDisarmable`
- - oTrapObject: a placeable, door or trigger
- - Returns TRUE if oTrapObject is disarmable.

- `oTrapObject`: object

<a id="gettrapdisarmdc"></a>

## `GetTrapDisarmDC(oTrapObject)` - Routine 535

- `535. GetTrapDisarmDC`
- Get the DC for disarming oTrapObject.
- - oTrapObject: a placeable, door or trigger

- `oTrapObject`: object

<a id="gettrapflagged"></a>

## `GetTrapFlagged(oTrapObject)` - Routine 530

- `530. GetTrapFlagged`
- - oTrapObject: a placeable, door or trigger
- - Returns TRUE if oTrapObject has been flagged as visible to all creatures.

- `oTrapObject`: object

<a id="gettrapkeytag"></a>

## `GetTrapKeyTag(oTrapObject)` - Routine 534

- `534. GetTrapKeyTag`
- Get the tag of the key that will disarm oTrapObject.
- - oTrapObject: a placeable, door or trigger

- `oTrapObject`: object

<a id="gettraponeshot"></a>

## `GetTrapOneShot(oTrapObject)` - Routine 532

- `532. GetTrapOneShot`
- - oTrapObject: a placeable, door or trigger
- - Returns TRUE if oTrapObject is one-shot (i.e. it does not reset itself
- after firing.

- `oTrapObject`: object

<a id="gettypefromtalent"></a>

## `GetTypeFromTalent(tTalent)` - Routine 362

- `362. GetTypeFromTalent`
- Get the type (TALENT_TYPE_*) of tTalent.

- `tTalent`: talent

<a id="getuseractionspending"></a>

## `GetUserActionsPending()` - Routine 514

- `514. GetUserActionsPending`
- This will test the combat action queu to see if the user has placed any actions on the queue.
- will only work during combat.

<a id="getuserdefinedeventnumber"></a>

## `GetUserDefinedEventNumber()` - Routine 247

- `247. GetUserDefinedEventNumber`
- This is for use in a user-defined script, it gets the event number.

<a id="getwasforcepowersuccessful"></a>

## `GetWasForcePowerSuccessful(oAttacker)` - Routine 726

- `726. GetWasForcePowerSuccessful`
- Returns whether the last force power used was successful or not

- `oAttacker`: object

<a id="getwaypointbytag"></a>

## `GetWaypointByTag(sWaypointTag)` - Routine 197

- `197. GetWaypointByTag`
- Get the first waypoint with the specified tag.
- - Returns OBJECT_INVALID if the waypoint cannot be found.

- `sWaypointTag`: string

<a id="getweaponranged"></a>

## `GetWeaponRanged(oItem)` - Routine 511

- `511. GetWeaponRanged`
- - Returns TRUE if oItem is a ranged weapon.

- `oItem`: object

<a id="getwillsavingthrow"></a>

## `GetWillSavingThrow(oTarget)` - Routine 492

- `492. GetWillSavingThrow`
- Get oTarget's base will saving throw value (this will only work for creatures,
- doors, and placeables).
- - Returns 0 if oTarget is invalid.

- `oTarget`: object

<a id="getxp"></a>

## `GetXP(oCreature)` - Routine 395

- `395. GetXP`
- Get oCreature's experience.

- `oCreature`: object

<a id="givegoldtocreature"></a>

## `GiveGoldToCreature(oCreature, nGP)` - Routine 322

- `322. GiveGoldToCreature`
- Give nGP gold to oCreature.

- `oCreature`: object
- `nGP`: int

<a id="giveplotxp"></a>

## `GivePlotXP(sPlotName, nPercentage)` - Routine 714

- `714. GivePlotXP`
- GivePlotXP
- Give nPercentage% of the experience associated with plot sPlotName
- to the party
- - sPlotName
- - nPercentage

- `sPlotName`: string
- `nPercentage`: int

<a id="givexptocreature"></a>

## `GiveXPToCreature(oCreature, nXpAmount)` - Routine 393

- `393. GiveXPToCreature`
- Gives nXpAmount to oCreature.

- `oCreature`: object
- `nXpAmount`: int

<a id="hourstoseconds"></a>

## `HoursToSeconds(nHours)` - Routine 122

- `122. HoursToSeconds`
- Convert nHours into a number of seconds
- The result will depend on how many minutes there are per hour (game-time)

- `nHours`: int

<a id="insertstring"></a>

## `InsertString(sDestination, sString, nPosition)` - Routine 64

- `64. InsertString`
- Insert sString into sDestination at nPosition
- - Return value on error: ""

- `sDestination`: string
- `sString`: string
- `nPosition`: int

<a id="inttofloat"></a>

## `IntToFloat(nInteger)` - Routine 230

- `230. IntToFloat`
- Convert nInteger into a floating point number.

- `nInteger`: int

<a id="inttohexstring"></a>

## `IntToHexString(nInteger)` - Routine 396

- `396. IntToHexString`
- Convert nInteger to hex, returning the hex value as a string.
- - Return value has the format "0x????????" where each ? will be a hex digit
- (8 digits in total).

- `nInteger`: int

<a id="inttostring"></a>

## `IntToString(nInteger)` - Routine 92

- `92. IntToString`
- Convert nInteger into a string.
- - Return value on error: ""

- `nInteger`: int

<a id="isavailablecreature"></a>

## `IsAvailableCreature(nNPC)` - Routine 696

- `696. IsAvailableNPC`
- This returns whether a NPC is in the list of available party members

- `nNPC`: int

<a id="iscreditsequenceinprogress"></a>

## `IsCreditSequenceInProgress()` - Routine 519

- `519. IsCreditSequenceInProgress`
- IsCreditSequenceInProgress
- Returns TRUE if the credits sequence is currently in progress, FALSE otherwise.

<a id="jumptolocation"></a>

## `JumpToLocation(lDestination)` - Routine 313

- `313. JumpToLocation`
- Jump to lDestination.  The action is added to the TOP of the action queue.

- `lDestination`: location

<a id="jumptoobject"></a>

## `JumpToObject(oToJumpTo, nWalkStraightLineToPoint)` - Routine 385

- `385. JumpToObject`
- Jump to oToJumpTo (the action is added to the top of the action queue).

- `oToJumpTo`: object
- `nWalkStraightLineToPoint`: int (default: `1`)

<a id="location"></a>

## `Location(vPosition, fOrientation)` - Routine 215

- `215. Location`
- Create a location.

- `vPosition`: vector
- `fOrientation`: float

<a id="log"></a>

## `log(fValue)` - Routine 74

- `74. log`
- Maths operation: log of fValue
- - Returns zero if fValue <= zero

- `fValue`: float

<a id="noclicksfor"></a>

## `NoClicksFor(fDuration)` - Routine 759

- `759. NoClicksFor`
- NoClicksFor()

- `fDuration`: float

<a id="objecttostring"></a>

## `ObjectToString(oObject)` - Routine 272

- `272. ObjectToString`
- Convert oObject into a hexadecimal string.

- `oObject`: object

<a id="openstore"></a>

## `OpenStore(oStore, oPC, nBonusMarkUp, nBonusMarkDown)` - Routine 378

- `378. OpenStore`
- Open oStore for oPC.

- `oStore`: object
- `oPC`: object
- `nBonusMarkUp`: int (default: `0`)
- `nBonusMarkDown`: int (default: `0`)

<a id="pausegame"></a>

## `PauseGame(bPause)` - Routine 57

- `57. PauseGame`
- Pauses the game if bPause is TRUE.  Unpauses if bPause is FALSE.

- `bPause`: int

<a id="popupdeathguipanel"></a>

## `PopUpDeathGUIPanel(oPC, bRespawnButtonEnabled, bWaitForHelpButtonEnabled, nHelpStringReference, sHelpString)` - Routine 554

- `554. PopUpDeathGUIPanel`
- Spawn in the Death GUI.
- The default (as defined by BioWare) can be spawned in by PopUpGUIPanel, but
- if you want to turn off the "Respawn" or "Wait for Help" buttons, this is the
- function to use.
- - oPC

- `oPC`: object
- `bRespawnButtonEnabled`: int (default: `1`)
- `bWaitForHelpButtonEnabled`: int (default: `1`)
- `nHelpStringReference`: int (default: `0`)
- `sHelpString`: string (default: ``)

<a id="popupguipanel"></a>

## `PopUpGUIPanel(oPC, nGUIPanel)` - Routine 388

- `388. PopUpGUIPanel`
- Spawn a GUI panel for the client that controls oPC.
- - oPC
- - nGUIPanel: GUI_PANEL_*
- - Nothing happens if oPC is not a player character or if an invalid value is
- used for nGUIPanel.

- `oPC`: object
- `nGUIPanel`: int

<a id="pow"></a>

## `pow(fValue, fExponent)` - Routine 75

- `75. pow`
- Maths operation: fValue is raised to the power of fExponent
- - Returns zero if fValue ==0 and fExponent <0

- `fValue`: float
- `fExponent`: float

<a id="printfloat"></a>

## `PrintFloat(fFloat, nWidth, nDecimals)` - Routine 2

- `2. PrintFloat`
- Output a formatted float to the log file.
- - nWidth should be a value from 0 to 18 inclusive.
- - nDecimals should be a value from 0 to 9 inclusive.

- `fFloat`: float
- `nWidth`: int (default: `18`)
- `nDecimals`: int (default: `9`)

<a id="printinteger"></a>

## `PrintInteger(nInteger)` - Routine 4

- `4. PrintInteger`
- Output nInteger to the log file.

- `nInteger`: int

<a id="printobject"></a>

## `PrintObject(oObject)` - Routine 5

- `5. PrintObject`
- Output oObject's ID to the log file.

- `oObject`: object

<a id="printstring"></a>

## `PrintString(sString)` - Routine 1

- `1. PrintString`
- Output sString to the log file.

- `sString`: string

<a id="printvector"></a>

## `PrintVector(vVector, bPrepend)` - Routine 141

- `141. PrintVector`
- Output vVector to the logfile.
- - vVector
- - bPrepend: if this is TRUE, the message will be prefixed with "PRINTVECTOR:"

- `vVector`: vector
- `bPrepend`: int

<a id="queuemovie"></a>

## `QueueMovie(sMovie, bSkippable)` - Routine 769

- `769. QueueMovie`
- Queues up a movie to be played using PlayMovieQueue.
- If bSkippable is TRUE, the player can cancel the movie by hitting escape.
- If bSkippable is FALSE, the player cannot cancel the movie and must wait
- for it to finish playing.

- `sMovie`: string
- `bSkippable`: int

<a id="random"></a>

## `Random(nMaxInteger)`

- `0. Random`
- Get an integer between 0 and nMaxInteger-1.
- Return value on error: 0

- `nMaxInteger`: int

<a id="randomname"></a>

## `RandomName()` - Routine 249

- `249. RandomName`
- Generate a random name.

<a id="reflexsave"></a>

## `ReflexSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 109

- `109. ReflexSave`
- Does a Reflex Save check for the given DC
- - oCreature
- - nDC: Difficulty check
- - nSaveType: SAVING_THROW_TYPE_*
- - oSaveVersus

- `oCreature`: object
- `nDC`: int
- `nSaveType`: int (default: `0`)
- `oSaveVersus`: object

<a id="removeavailablenpc"></a>

## `RemoveAvailableNPC(nNPC)` - Routine 695

- `695. RemoveAvailableNPC`
- This removes a NPC from the list of available party members
- Returns whether it was successful or not

- `nNPC`: int

<a id="removejournalquestentry"></a>

## `RemoveJournalQuestEntry(szPlotID)` - Routine 368

- `368. RemoveJournalQuestEntry`
- Remove a journal quest entry from the player.
- - szPlotID: the plot identifier used in the toolset's Journal Editor

- `szPlotID`: string

<a id="resistforce"></a>

## `ResistForce(oSource, oTarget)` - Routine 169

- `169. ResistForce`
- Do a Force Resistance check between oSource and oTarget, returning TRUE if
- the force was resisted.
- - Return value if oSource or oTarget is an invalid object: FALSE

- `oSource`: object
- `oTarget`: object

<a id="revealmap"></a>

## `RevealMap(vPoint, nRadius)` - Routine 515

- `515. RevealMap`
- RevealMap
- Reveals the map at the given WORLD point 'vPoint' with a MAP Grid Radius 'nRadius'
- If this function is called with no parameters it will reveal the entire map.
- (NOTE: if this function is called with a valid point but a default radius, ie. 'nRadius' of -1
- then the entire map will be revealed)

- `vPoint`: vector
- `nRadius`: int

<a id="roundstoseconds"></a>

## `RoundsToSeconds(nRounds)` - Routine 121

- `121. RoundsToSeconds`
- Convert nRounds into a number of seconds
- A round is always 6.0 seconds

- `nRounds`: int

<a id="savenpcstate"></a>

## `SaveNPCState(nNPC)` - Routine 734

- `734. SaveNPCState`
- Tells the party table to save the state of a party member NPC

- `nNPC`: int

<a id="sendmessagetopc"></a>

## `SendMessageToPC(oPlayer, szMessage)` - Routine 374

- `374. SendMessageToPC`
- Send a server message (szMessage) to the oPlayer.

- `oPlayer`: object
- `szMessage`: string

<a id="setassociatelistenpatterns"></a>

## `SetAssociateListenPatterns(oTarget)` - Routine 327

- `327. SetAssociateListenPatterns`
- Initialise oTarget to listen for the standard Associates commands.

- `oTarget`: object

<a id="setavailablenpcid"></a>

## `SetAvailableNPCId()` - Routine 767

- `767. SetAvailableNPCId`
- This will set the object id that should be used for a specific available NPC

<a id="setbuttonmashcheck"></a>

## `SetButtonMashCheck(nCheck)` - Routine 268

- `268. SetButtonMashCheck`
- SetButtonMashCheck
- This function sets the button mash check variable, and is used for turning the check on and off

- `nCheck`: int

<a id="setcamerafacing"></a>

## `SetCameraFacing(fDirection)` - Routine 45

- `45. SetCameraFacing`
- Change the direction in which the camera is facing
- - fDirection is expressed as anticlockwise degrees from Due East.
- (0.0f=East, 90.0f=North, 180.0f=West, 270.0f=South)
- This can be used to change the way the camera is facing after the player
- emerges from an area transition.

- `fDirection`: float

<a id="setcameramode"></a>

## `SetCameraMode(oPlayer, nCameraMode)` - Routine 504

- `504. SetCameraMode`
- Set the camera mode for oPlayer.
- - oPlayer
- - nCameraMode: CAMERA_MODE_*
- - If oPlayer is not player-controlled or nCameraMode is invalid, nothing
- happens.

- `oPlayer`: object
- `nCameraMode`: int

<a id="setcommandable"></a>

## `SetCommandable(bCommandable, oTarget)` - Routine 162

- `162. SetCommandable`
- Set whether oTarget's action stack can be modified

- `bCommandable`: int
- `oTarget`: object

<a id="setcurrentstealthxp"></a>

## `SetCurrentStealthXP(nCurrent)` - Routine 478

- `478. SetCurrentStealthXP`
- Set the current amount of stealth xp available in the area.

- `nCurrent`: int

<a id="setcustomtoken"></a>

## `SetCustomToken(nCustomTokenNumber, sTokenValue)` - Routine 284

- `284. SetCustomToken`
- Set the value for a custom token.

- `nCustomTokenNumber`: int
- `sTokenValue`: string

<a id="setencounteractive"></a>

## `SetEncounterActive(nNewValue, oEncounter)` - Routine 277

- `277. SetEncounterActive`
- Set oEncounter's active state to nNewValue.
- - nNewValue: TRUE/FALSE
- - oEncounter

- `nNewValue`: int
- `oEncounter`: object

<a id="setencounterdifficulty"></a>

## `SetEncounterDifficulty(nEncounterDifficulty, oEncounter)` - Routine 296

- `296. SetEncounterDifficulty`
- Set the difficulty level of oEncounter.
- - nEncounterDifficulty: ENCOUNTER_DIFFICULTY_*
- - oEncounter

- `nEncounterDifficulty`: int
- `oEncounter`: object

<a id="setencounterspawnscurrent"></a>

## `SetEncounterSpawnsCurrent(nNewValue, oEncounter)` - Routine 281

- `281. SetEncounterSpawnsCurrent`
- Set the number of times that oEncounter has spawned so far

- `nNewValue`: int
- `oEncounter`: object

<a id="setencounterspawnsmax"></a>

## `SetEncounterSpawnsMax(nNewValue, oEncounter)` - Routine 279

- `279. SetEncounterSpawnsMax`
- Set the maximum number of times that oEncounter can spawn

- `nNewValue`: int
- `oEncounter`: object

<a id="setfacing"></a>

## `SetFacing(fDirection)` - Routine 10

- `10. SetFacing`
- Cause the caller to face fDirection.
- - fDirection is expressed as anticlockwise degrees from Due East.
- DIRECTION_EAST, DIRECTION_NORTH, DIRECTION_WEST and DIRECTION_SOUTH are
- predefined. (0.0f=East, 90.0f=North, 180.0f=West, 270.0f=South)

- `fDirection`: float

<a id="setfacingpoint"></a>

## `SetFacingPoint(vTarget)` - Routine 143

- `143. SetFacingPoint`
- Cause the caller to face vTarget

- `vTarget`: vector

<a id="setforcepowerunsuccessful"></a>

## `SetForcePowerUnsuccessful(nResult, oCreature)` - Routine 731

- `731. SetForcePowerUnsuccessful`
- Sets the reason (through a constant) for why a force power failed

- `nResult`: int
- `oCreature`: object

<a id="setformation"></a>

## `SetFormation(oAnchor, oCreature, nFormationPattern, nPosition)` - Routine 729

- `729. SetFormation`
- Put oCreature into the nFormationPattern about oAnchor at position nPosition
- - oAnchor: The formation is set relative to this object
- - oCreature: This is the creature that you wish to join the formation
- - nFormationPattern: FORMATION_*
- - nPosition: Integer from 1 to 10 to specify which position in the formation

- `oAnchor`: object
- `oCreature`: object
- `nFormationPattern`: int
- `nPosition`: int

<a id="setgoodevilvalue"></a>

## `SetGoodEvilValue(oCreature, nAlignment)` - Routine 750

- `750. SetGoodEvilValue`
- SetAlignmentGoodEvil
- Set oCreature's alignment value

- `oCreature`: object
- `nAlignment`: int

<a id="setidentified"></a>

## `SetIdentified(oItem, bIdentified)` - Routine 333

- `333. SetIdentified`
- Set whether oItem has been identified.

- `oItem`: object
- `bIdentified`: int

<a id="setisdestroyable"></a>

## `SetIsDestroyable(bDestroyable, bRaiseable, bSelectableWhenDead)` - Routine 323

- `323. SetIsDestroyable`
- Set the destroyable status of the caller.
- - bDestroyable: If this is FALSE, the caller does not fade out on death, but
- sticks around as a corpse.
- - bRaiseable: If this is TRUE, the caller can be raised via resurrection.
- - bSelectableWhenDead: If this is TRUE, the caller is selectable after death.

- `bDestroyable`: int
- `bRaiseable`: int (default: `1`)
- `bSelectableWhenDead`: int (default: `0`)

<a id="setjournalquestentrypicture"></a>

## `SetJournalQuestEntryPicture(szPlotID, oObject, nPictureIndex, bAllPartyMemebers, bAllPlayers)` - Routine 678

- `678. SetJournalQuestEntryPicture`
- SetJournalQuestEntryPicture
- Sets the picture for the quest entry on this object (creature)

- `szPlotID`: string
- `oObject`: object
- `nPictureIndex`: int
- `bAllPartyMemebers`: int (default: `1`)
- `bAllPlayers`: int (default: `0`)

<a id="setlightsaberpowered"></a>

## `SetLightsaberPowered(oCreature, bOverride, bPowered, bShowTransition)` - Routine 421

- `421. SetLightsaberPowered`
- SetLightsaberPowered
- Allows a script to set the state of the lightsaber.  This will override any
- game determined lightsaber powerstates.

- `oCreature`: object
- `bOverride`: int
- `bPowered`: int (default: `1`)
- `bShowTransition`: int (default: `0`)

<a id="setlistening"></a>

## `SetListening(oObject, bValue)` - Routine 175

- `175. SetListening`
- Set whether oObject is listening.

- `oObject`: object
- `bValue`: int

<a id="setlistenpattern"></a>

## `SetListenPattern(oObject, sPattern, nNumber)` - Routine 176

- `176. SetListenPattern`
- Set the string for oObject to listen for.
- Note: this does not set oObject to be listening.

- `oObject`: object
- `sPattern`: string
- `nNumber`: int (default: `0`)

<a id="setlocked"></a>

## `SetLocked(oTarget, bLocked)` - Routine 324

- `324. SetLocked`
- Set the locked state of oTarget, which can be a door or a placeable object.

- `oTarget`: object
- `bLocked`: int

<a id="setmappinenabled"></a>

## `SetMapPinEnabled(oMapPin, nEnabled)` - Routine 386

- `386. SetMapPinEnabled`
- Set whether oMapPin is enabled.
- - oMapPin
- - nEnabled: 0=Off, 1=On

- `oMapPin`: object
- `nEnabled`: int

<a id="setmaxhitpoints"></a>

## `SetMaxHitPoints(oObject, nMaxHP)` - Routine 758

- `758. SetMaxHitPoints`
- SetMaxHitPoints
- Set the maximum hitpoints of oObject
- The objects maximum AND current hitpoints will be nMaxHP after the function is called

- `oObject`: object
- `nMaxHP`: int

<a id="setmaxstealthxp"></a>

## `SetMaxStealthXP(nMax)` - Routine 468

- `468. SetMaxStealthXP`
- Set the maximum amount of stealth xp available in the area.

- `nMax`: int

<a id="setminonehp"></a>

## `SetMinOneHP(oObject, nMinOneHP)` - Routine 716

- `716. SetMinOneHP`
- Sets/Removes the MinOneHP Flag on oObject.

- `oObject`: object
- `nMinOneHP`: int

<a id="setnpcaistyle"></a>

## `SetNPCAIStyle(oCreature, nStyle)` - Routine 707

- `707. SetNPCAIStyle`
- Sets the party members ai style

- `oCreature`: object
- `nStyle`: int

<a id="setplaceableillumination"></a>

## `SetPlaceableIllumination(oPlaceable, bIlluminate)` - Routine 544

- `544. SetPlaceableIllumination`
- Set the status of the illumination for oPlaceable.
- - oPlaceable
- - bIlluminate: if this is TRUE, oPlaceable's illumination will be turned on.
- If this is FALSE, oPlaceable's illumination will be turned off.
- Note: You must call RecomputeStaticLighting() after calling this function in

- `oPlaceable`: object
- `bIlluminate`: int (default: `1`)

<a id="setplanetavailable"></a>

## `SetPlanetAvailable(nPlanet, bAvailable)` - Routine 742

- `742. SetPlanetAvailable`
- SetPlanetAvailable
- Sets 'nPlanet' available on the Galaxy Map Gui.

- `nPlanet`: int
- `bAvailable`: int

<a id="setplanetselectable"></a>

## `SetPlanetSelectable(nPlanet, bSelectable)` - Routine 740

- `740. SetPlanetSelectable`
- SetPlanetSelectable
- Sets 'nPlanet' selectable on the Galaxy Map Gui.

- `nPlanet`: int
- `bSelectable`: int

<a id="setplotflag"></a>

## `SetPlotFlag(oTarget, nPlotFlag)` - Routine 456

- `456. SetPlotFlag`
- Set oTarget's plot object status.

- `oTarget`: object
- `nPlotFlag`: int

<a id="setreturnstrref"></a>

## `SetReturnStrref(bShow, srStringRef, srReturnQueryStrRef)` - Routine 152

- `152. SetReturnStrref`
- SetReturnStrref
- This function will turn on/off the display of the 'return to ebon hawk' option
- on the map screen and allow the string to be changed to an arbitrary string ref
- srReturnQueryStrRef is the string ref that will be displayed in the query pop
- up confirming that you wish to return to the specified location.

- `bShow`: int
- `srStringRef`: int (default: `0`)
- `srReturnQueryStrRef`: int (default: `0`)

<a id="setsolomode"></a>

## `SetSoloMode(bActivate)` - Routine 753

- `753. SetSoloMode`
- SetSoloMode
- Activates/Deactivates solo mode for the player's party.

- `bActivate`: int

<a id="setstealthxpdecrement"></a>

## `SetStealthXPDecrement(nDecrement)` - Routine 499

- `499. SetStealthXPDecrement`
- Sets the amount the stealth xp bonus gets decreased each time the player is detected.

- `nDecrement`: int

<a id="setstealthxpenabled"></a>

## `SetStealthXPEnabled(bEnabled)` - Routine 482

- `482. SetStealthXPEnabled`
- Sets whether or not the stealth xp bonus is enabled (ie. whether or not
- AwardStealthXP() will actually award any available stealth xp).

- `bEnabled`: int

<a id="settime"></a>

## `SetTime(nHour, nMinute, nSecond, nMillisecond)` - Routine 12

- `12. SetTime`
- Set the time to the time specified.
- - nHour should be from 0 to 23 inclusive
- - nMinute should be from 0 to 59 inclusive
- - nSecond should be from 0 to 59 inclusive
- - nMillisecond should be from 0 to 999 inclusive

- `nHour`: int
- `nMinute`: int
- `nSecond`: int
- `nMillisecond`: int

<a id="settrapdetectedby"></a>

## `SetTrapDetectedBy(oTrap, oDetector)` - Routine 550

- `550. SetTrapDetectedBy`
- Set oDetector to have detected oTrap.

- `oTrap`: object
- `oDetector`: object

<a id="settrapdisabled"></a>

## `SetTrapDisabled(oTrap)` - Routine 555

- `555. SetTrapDisabled`
- Disable oTrap.
- - oTrap: a placeable, door or trigger.

- `oTrap`: object

<a id="settutorialwindowsenabled"></a>

## `SetTutorialWindowsEnabled(bEnabled)` - Routine 516

- `516. SetTutorialWindowsEnabled`
- SetTutorialWindowsEnabled
- Sets whether or not the tutorial windows are enabled (ie. whether or not they will
- appear when certain things happen for the first time).

- `bEnabled`: int

<a id="setxp"></a>

## `SetXP(oCreature, nXpAmount)` - Routine 394

- `394. SetXP`
- Sets oCreature's experience to nXpAmount.

- `oCreature`: object
- `nXpAmount`: int

<a id="shipbuild"></a>

## `ShipBuild()` - Routine 761

- `761. ShipBuild`
- ShipBuild()

<a id="showgalaxymap"></a>

## `ShowGalaxyMap(nPlanet)` - Routine 739

- `739. ShowGalaxyMap`
- ShowGalaxyMap
- Brings up the Galaxy Map Gui, with 'nPlanet' selected.  'nPlanet' can only be a planet
- that has already been set available and selectable.

- `nPlanet`: int

<a id="showlevelupgui"></a>

## `ShowLevelUpGUI()` - Routine 265

- `265. ShowLevelUpGUI`
- Brings up the level up GUI for the player.  The GUI will only show up
- if the player has gained enough experience points to level up.
- - Returns TRUE if the GUI was successfully brought up; FALSE if not.

<a id="showtutorialwindow"></a>

## `ShowTutorialWindow(nWindow)` - Routine 517

- `517. ShowTutorialWindow`
- ShowTutorialWindow
- Pops up the specified tutorial window.  If the tutorial window has already popped
- up once before, this will do nothing.

- `nWindow`: int

<a id="showupgradescreen"></a>

## `ShowUpgradeScreen(oItem)` - Routine 354

- `354. ShowUpgradeScreen`
- Displays the upgrade screen where the player can modify weapons and armor

- `oItem`: object

<a id="signalevent"></a>

## `SignalEvent(oObject, evToRun)` - Routine 131

- `131. SignalEvent`
- Cause oObject to run evToRun

- `oObject`: object
- `evToRun`: event

<a id="sin"></a>

## `sin(fValue)` - Routine 69

- `69. sin`
- Maths operation: sine of fValue

- `fValue`: float

<a id="spawnavailablenpc"></a>

## `SpawnAvailableNPC(nNPC, lPosition)` - Routine 698

- `698. SpawnAvailableNPC`
- This spawns a NPC from the list of available creatures
- Returns a pointer to the creature object

- `nNPC`: int
- `lPosition`: location

<a id="sqrt"></a>

## `sqrt(fValue)` - Routine 76

- `76. sqrt`
- Maths operation: square root of fValue
- - Returns zero if fValue <0

- `fValue`: float

<a id="startcreditsequence"></a>

## `StartCreditSequence(bTransparentBackground)` - Routine 518

- `518. StartCreditSequence`
- StartCreditSequence
- Starts the credits sequence.  If bTransparentBackground is TRUE, the credits will be displayed
- with a transparent background, allowing whatever is currently onscreen to show through.  If it
- is set to FALSE, the credits will be displayed on a black background.

- `bTransparentBackground`: int

<a id="stoprumblepattern"></a>

## `StopRumblePattern(nPattern)` - Routine 371

- `371. StopRumblePattern`
- StopRumblePattern
- Stops a defined rumble pattern

- `nPattern`: int

<a id="stringtofloat"></a>

## `StringToFloat(sNumber)` - Routine 233

- `233. StringToFloat`
- Convert sNumber into a floating point number.

- `sNumber`: string

<a id="stringtoint"></a>

## `StringToInt(sNumber)` - Routine 232

- `232. StringToInt`
- Convert sNumber into an integer.

- `sNumber`: string

<a id="suppressstatussummaryentry"></a>

## `SuppressStatusSummaryEntry(nNumEntries)` - Routine 763

- `763. SuppressStatusSummaryEntry`
- This will prevent the next n entries that should have shown up in the status summary
- from being added
- This will not add on to any existing summary suppressions, but rather replace it.  So
- to clear the supression system pass 0 as the entry value

- `nNumEntries`: int (default: `1`)

<a id="surrenderbyfaction"></a>

## `SurrenderByFaction(nFactionFrom, nFactionTo)` - Routine 736

- `736. SurrenderByFaction`
- This affects all creatures in the area that are in faction nFactionFrom...
- - Makes them join nFactionTo
- - Clears all actions
- - Disables combat mode

- `nFactionFrom`: int
- `nFactionTo`: int

<a id="surrenderretainbuffs"></a>

## `SurrenderRetainBuffs()` - Routine 762

- `762. SurrenderRetainBuffs`
- SurrenderRetainBuffs()

<a id="surrendertoenemies"></a>

## `SurrenderToEnemies()` - Routine 476

- `476. SurrenderToEnemies`
- Use this on an NPC to cause all creatures within a 10-metre radius to stop
- what they are doing and sets the NPC's enemies within this range to be
- neutral towards the NPC. If this command is run on a PC or an object that is
- not a creature, nothing will happen.

<a id="swmg_adjustfollowerhitpoints"></a>

## `SWMG_AdjustFollowerHitPoints(oFollower, nHP, nAbsolute)` - Routine 590

- `590. SWMG_AdjustFollowerHitPoints`
- adjusts a followers hit points, can specify the absolute value to set to
- SWMG_AdjustFollowerHitPoints

- `oFollower`: object
- `nHP`: int
- `nAbsolute`: int (default: `0`)

<a id="swmg_getcamerafarclip"></a>

## `SWMG_GetCameraFarClip()` - Routine 609

- `609. SWMG_GetCameraFarClip`
- SWMG_GetCameraFarClip

<a id="swmg_getcameranearclip"></a>

## `SWMG_GetCameraNearClip()` - Routine 608

- `608. SWMG_GetCameraNearClip`
- SWMG_GetCameraNearClip

<a id="swmg_getenemy"></a>

## `SWMG_GetEnemy(nEntry)` - Routine 613

- `613. SWMG_GetEnemy`
- SWMG_GetEnemy

- `nEntry`: int

<a id="swmg_getenemycount"></a>

## `SWMG_GetEnemyCount()` - Routine 612

- `612. SWMG_GetEnemyCount`
- SWMG_GetEnemyCount

<a id="swmg_getgunbankbulletmodel"></a>

## `SWMG_GetGunBankBulletModel(oFollower, nGunBank)` - Routine 625

- `625. SWMG_GetGunBankBulletModel`
- SWMG_GetGunBankBulletModel

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbankcount"></a>

## `SWMG_GetGunBankCount(oFollower)` - Routine 624

- `624. SWMG_GetGunBankCount`
- SWMG_GetGunBankCount

- `oFollower`: object

<a id="swmg_getgunbankdamage"></a>

## `SWMG_GetGunBankDamage(oFollower, nGunBank)` - Routine 627

- `627. SWMG_GetGunBankDamage`
- SWMG_GetGunBankDamage

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbankgunmodel"></a>

## `SWMG_GetGunBankGunModel(oFollower, nGunBank)` - Routine 626

- `626. SWMG_GetGunBankGunModel`
- SWMG_GetGunBankGunModel

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbankhorizontalspread"></a>

## `SWMG_GetGunBankHorizontalSpread(oEnemy, nGunBank)` - Routine 657

- `657. SWMG_GetGunBankHorizontalSpread`
- SWMG_GetGunBankHorizontalSpread

- `oEnemy`: object
- `nGunBank`: int

<a id="swmg_getgunbankinaccuracy"></a>

## `SWMG_GetGunBankInaccuracy(oEnemy, nGunBank)` - Routine 660

- `660. SWMG_GetGunBankInaccuracy`
- SWMG_GetGunBankInaccuracy

- `oEnemy`: object
- `nGunBank`: int

<a id="swmg_getgunbanklifespan"></a>

## `SWMG_GetGunBankLifespan(oFollower, nGunBank)` - Routine 629

- `629. SWMG_GetGunBankLifespan`
- SWMG_GetGunBankLifespan

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbanksensingradius"></a>

## `SWMG_GetGunBankSensingRadius(oEnemy, nGunBank)` - Routine 659

- `659. SWMG_GetGunBankSensingRadius`
- SWMG_GetGunBankSensingRadius

- `oEnemy`: object
- `nGunBank`: int

<a id="swmg_getgunbankspeed"></a>

## `SWMG_GetGunBankSpeed(oFollower, nGunBank)` - Routine 630

- `630. SWMG_GetGunBankSpeed`
- SWMG_GetGunBankSpeed

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbanktarget"></a>

## `SWMG_GetGunBankTarget(oFollower, nGunBank)` - Routine 631

- `631. SWMG_GetGunBankTarget`
- SWMG_GetGunBankTarget

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbanktimebetweenshots"></a>

## `SWMG_GetGunBankTimeBetweenShots(oFollower, nGunBank)` - Routine 628

- `628. SWMG_GetGunBankTimeBetweenShots`
- SWMG_GetGunBankTimeBetweenShots

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_getgunbankverticalspread"></a>

## `SWMG_GetGunBankVerticalSpread(oEnemy, nGunBank)` - Routine 658

- `658. SWMG_GetGunBankVerticalSpread`
- SWMG_GetGunBankVerticalSpread

- `oEnemy`: object
- `nGunBank`: int

<a id="swmg_gethitpoints"></a>

## `SWMG_GetHitPoints(oFollower)` - Routine 616

- `616. SWMG_GetHitPoints`
- SWMG_GetHitPoints

- `oFollower`: object

<a id="swmg_getisinvulnerable"></a>

## `SWMG_GetIsInvulnerable(oFollower)` - Routine 665

- `665. SWMG_GetIsInvulnerable`
- GetIsInvulnerable
- This returns whether the follower object is currently invulnerable to damage

- `oFollower`: object

<a id="swmg_getlastbulletfireddamage"></a>

## `SWMG_GetLastBulletFiredDamage()` - Routine 595

- `595. SWMG_GetLastBulletFiredDamage`
- gets information about the last bullet fired
- SWMG_GetLastBulletFiredDamage

<a id="swmg_getlastbulletfiredtarget"></a>

## `SWMG_GetLastBulletFiredTarget()` - Routine 596

- `596. SWMG_GetLastBulletFiredTarget`
- SWMG_GetLastBulletFiredTarget

<a id="swmg_getlastbullethitdamage"></a>

## `SWMG_GetLastBulletHitDamage()` - Routine 587

- `587. SWMG_GetLastBulletHitDamage`
- OnHitBullet
- get the damage, the target type (see TARGETflags), and the shooter
- SWMG_GetLastBulletHitDamage

<a id="swmg_getlastbullethitpart"></a>

## `SWMG_GetLastBulletHitPart()` - Routine 639

- `639. SWMG_GetLastBulletHitPart`
- SWMG_GetLastBulletHitPart

<a id="swmg_getlastbullethitshooter"></a>

## `SWMG_GetLastBulletHitShooter()` - Routine 589

- `589. SWMG_GetLastBulletHitShooter`
- SWMG_GetLastBulletHitShooter

<a id="swmg_getlastbullethittarget"></a>

## `SWMG_GetLastBulletHitTarget()` - Routine 588

- `588. SWMG_GetLastBulletHitTarget`
- SWMG_GetLastBulletHitTarget

<a id="swmg_getlastevent"></a>

## `SWMG_GetLastEvent()` - Routine 583

- `583. SWMG_GetLastEvent`
- OnAnimKey
- get the event and the name of the model on which the event happened
- SWMG_GetLastEvent

<a id="swmg_getlasteventmodelname"></a>

## `SWMG_GetLastEventModelName()` - Routine 584

- `584. SWMG_GetLastEventModelName`
- SWMG_GetLastEventModelName

<a id="swmg_getlastfollowerhit"></a>

## `SWMG_GetLastFollowerHit()` - Routine 593

- `593. SWMG_GetLastFollowerHit`
- returns the last follower and obstacle hit
- SWMG_GetLastFollowerHit

<a id="swmg_getlasthpchange"></a>

## `SWMG_GetLastHPChange()` - Routine 606

- `606. SWMG_GetLastHPChange`
- SWMG_GetLastHPChange

<a id="swmg_getlastobstaclehit"></a>

## `SWMG_GetLastObstacleHit()` - Routine 594

- `594. SWMG_GetLastObstacleHit`
- SWMG_GetLastObstacleHit

<a id="swmg_getlateralaccelerationpersecond"></a>

## `SWMG_GetLateralAccelerationPerSecond()` - Routine 521

- `521. SWMG_GetLateralAccelerationPerSecond`
- Returns the minigame lateral acceleration/sec value

<a id="swmg_getmaxhitpoints"></a>

## `SWMG_GetMaxHitPoints(oFollower)` - Routine 617

- `617. SWMG_GetMaxHitPoints`
- SWMG_GetMaxHitPoints

- `oFollower`: object

<a id="swmg_getnumloops"></a>

## `SWMG_GetNumLoops(oFollower)` - Routine 621

- `621. SWMG_GetNumLoops`
- SWMG_GetNumLoops

- `oFollower`: object

<a id="swmg_getobstacle"></a>

## `SWMG_GetObstacle(nEntry)` - Routine 615

- `615. SWMG_GetObstacle`
- SWMG_GetObstacle

- `nEntry`: int

<a id="swmg_getobstaclecount"></a>

## `SWMG_GetObstacleCount()` - Routine 614

- `614. SWMG_GetObstacleCount`
- SWMG_GetObstacleCount

<a id="swmg_getposition"></a>

## `SWMG_GetPosition(oFollower)` - Routine 623

- `623. SWMG_GetPosition`
- SWMG_GetPosition

- `oFollower`: object

<a id="swmg_getsphereradius"></a>

## `SWMG_GetSphereRadius(oFollower)` - Routine 619

- `619. SWMG_GetSphereRadius`
- SWMG_GetSphereRadius

- `oFollower`: object

<a id="swmg_isenemy"></a>

## `SWMG_IsEnemy(oid)` - Routine 601

- `601. SWMG_IsEnemy`
- SWMG_IsEnemy

- `oid`: object

<a id="swmg_isfollower"></a>

## `SWMG_IsFollower(oid)` - Routine 599

- `599. SWMG_IsFollower`
- a bunch of Is functions for your pleasure
- SWMG_IsFollower

- `oid`: object

<a id="swmg_isgunbanktargetting"></a>

## `SWMG_IsGunBankTargetting(oFollower, nGunBank)` - Routine 640

- `640. SWMG_IsGunBankTargetting`
- SWMG_IsGunBankTargetting

- `oFollower`: object
- `nGunBank`: int

<a id="swmg_isobstacle"></a>

## `SWMG_IsObstacle(oid)` - Routine 603

- `603. SWMG_IsObstacle`
- SWMG_IsObstacle

- `oid`: object

<a id="swmg_istrigger"></a>

## `SWMG_IsTrigger(oid)` - Routine 602

- `602. SWMG_IsTrigger`
- SWMG_IsTrigger

- `oid`: object

<a id="swmg_onbullethit"></a>

## `SWMG_OnBulletHit()` - Routine 591

- `591. SWMG_OnBulletHit`
- the default implementation of OnBulletHit
- SWMG_OnBulletHit

<a id="swmg_ondamage"></a>

## `SWMG_OnDamage()` - Routine 605

- `605. SWMG_OnDamage`
- SWMG_OnDamage

<a id="swmg_ondeath"></a>

## `SWMG_OnDeath()` - Routine 598

- `598. SWMG_OnDeath`
- the default implementation of OnDeath
- SWMG_OnDeath

<a id="swmg_onobstaclehit"></a>

## `SWMG_OnObstacleHit()` - Routine 592

- `592. SWMG_OnObstacleHit`
- the default implementation of OnObstacleHit
- SWMG_OnObstacleHit

<a id="swmg_removeanimation"></a>

## `SWMG_RemoveAnimation(oObject, sAnimName)` - Routine 607

- `607. SWMG_RemoveAnimation`
- SWMG_RemoveAnimation

- `oObject`: object
- `sAnimName`: string

<a id="swmg_setcameraclip"></a>

## `SWMG_SetCameraClip(fNear, fFar)` - Routine 610

- `610. SWMG_SetCameraClip`
- SWMG_SetCameraClip

- `fNear`: float
- `fFar`: float

<a id="swmg_setfollowerhitpoints"></a>

## `SWMG_SetFollowerHitPoints(oFollower, nHP)` - Routine 604

- `604. SWMG_SetFollowerHitPoints`
- SWMG_SetFollowerHitPoints

- `oFollower`: object
- `nHP`: int

<a id="swmg_setgunbankbulletmodel"></a>

## `SWMG_SetGunBankBulletModel(oFollower, nGunBank, sBulletModel)` - Routine 632

- `632. SWMG_SetGunBankBulletModel`
- SWMG_SetGunBankBulletModel

- `oFollower`: object
- `nGunBank`: int
- `sBulletModel`: string

<a id="swmg_setgunbankdamage"></a>

## `SWMG_SetGunBankDamage(oFollower, nGunBank, nDamage)` - Routine 634

- `634. SWMG_SetGunBankDamage`
- SWMG_SetGunBankDamage

- `oFollower`: object
- `nGunBank`: int
- `nDamage`: int

<a id="swmg_setgunbankgunmodel"></a>

## `SWMG_SetGunBankGunModel(oFollower, nGunBank, sGunModel)` - Routine 633

- `633. SWMG_SetGunBankGunModel`
- SWMG_SetGunBankGunModel

- `oFollower`: object
- `nGunBank`: int
- `sGunModel`: string

<a id="swmg_setgunbankhorizontalspread"></a>

## `SWMG_SetGunBankHorizontalSpread(oEnemy, nGunBank, fHorizontalSpread)` - Routine 661

- `661. SWMG_SetGunBankHorizontalSpread`
- SWMG_SetGunBankHorizontalSpread

- `oEnemy`: object
- `nGunBank`: int
- `fHorizontalSpread`: float

<a id="swmg_setgunbankinaccuracy"></a>

## `SWMG_SetGunBankInaccuracy(oEnemy, nGunBank, fInaccuracy)` - Routine 664

- `664. SWMG_SetGunBankInaccuracy`
- SWMG_SetGunBankInaccuracy

- `oEnemy`: object
- `nGunBank`: int
- `fInaccuracy`: float

<a id="swmg_setgunbanklifespan"></a>

## `SWMG_SetGunBankLifespan(oFollower, nGunBank, fLifespan)` - Routine 636

- `636. SWMG_SetGunBankLifespan`
- SWMG_SetGunBankLifespan

- `oFollower`: object
- `nGunBank`: int
- `fLifespan`: float

<a id="swmg_setgunbanksensingradius"></a>

## `SWMG_SetGunBankSensingRadius(oEnemy, nGunBank, fSensingRadius)` - Routine 663

- `663. SWMG_SetGunBankSensingRadius`
- SWMG_SetGunBankSensingRadius

- `oEnemy`: object
- `nGunBank`: int
- `fSensingRadius`: float

<a id="swmg_setgunbankspeed"></a>

## `SWMG_SetGunBankSpeed(oFollower, nGunBank, fSpeed)` - Routine 637

- `637. SWMG_SetGunBankSpeed`
- SWMG_SetGunBankSpeed

- `oFollower`: object
- `nGunBank`: int
- `fSpeed`: float

<a id="swmg_setgunbanktarget"></a>

## `SWMG_SetGunBankTarget(oFollower, nGunBank, nTarget)` - Routine 638

- `638. SWMG_SetGunBankTarget`
- SWMG_SetGunBankTarget

- `oFollower`: object
- `nGunBank`: int
- `nTarget`: int

<a id="swmg_setgunbanktimebetweenshots"></a>

## `SWMG_SetGunBankTimeBetweenShots(oFollower, nGunBank, fTBS)` - Routine 635

- `635. SWMG_SetGunBankTimeBetweenShots`
- SWMG_SetGunBankTimeBetweenShots

- `oFollower`: object
- `nGunBank`: int
- `fTBS`: float

<a id="swmg_setgunbankverticalspread"></a>

## `SWMG_SetGunBankVerticalSpread(oEnemy, nGunBank, fVerticalSpread)` - Routine 662

- `662. SWMG_SetGunBankVerticalSpread`
- SWMG_SetGunBankVerticalSpread

- `oEnemy`: object
- `nGunBank`: int
- `fVerticalSpread`: float

<a id="swmg_setlateralaccelerationpersecond"></a>

## `SWMG_SetLateralAccelerationPerSecond(fLAPS)` - Routine 520

- `520. SWMG_SetLateralAccelerationPerSecond`
- Sets the minigame lateral acceleration/sec value

- `fLAPS`: float

<a id="swmg_setmaxhitpoints"></a>

## `SWMG_SetMaxHitPoints(oFollower, nMaxHP)` - Routine 618

- `618. SWMG_SetMaxHitPoints`
- SWMG_SetMaxHitPoints

- `oFollower`: object
- `nMaxHP`: int

<a id="swmg_setnumloops"></a>

## `SWMG_SetNumLoops(oFollower, nNumLoops)` - Routine 622

- `622. SWMG_SetNumLoops`
- SWMG_SetNumLoops

- `oFollower`: object
- `nNumLoops`: int

<a id="swmg_setsphereradius"></a>

## `SWMG_SetSphereRadius(oFollower, fRadius)` - Routine 620

- `620. SWMG_SetSphereRadius`
- SWMG_SetSphereRadius

- `oFollower`: object
- `fRadius`: float

<a id="takegoldfromcreature"></a>

## `TakeGoldFromCreature(nAmount, oCreatureToTakeFrom, bDestroy)` - Routine 444

- `444. TakeGoldFromCreature`
- Take nAmount of gold from oCreatureToTakeFrom.
- - nAmount
- - oCreatureToTakeFrom: If this is not a valid creature, nothing will happen.
- - bDestroy: If this is TRUE, the caller will not get the gold.  Instead, the
- gold will be destroyed and will vanish from the game.

- `nAmount`: int
- `oCreatureToTakeFrom`: object
- `bDestroy`: int (default: `0`)

<a id="talentspell"></a>

## `TalentSpell(nSpell)` - Routine 301

- `301. TalentSpell`
- Create a Spell Talent.
- - nSpell: SPELL_*

- `nSpell`: int

<a id="tan"></a>

## `tan(fValue)` - Routine 70

- `70. tan`
- Maths operation: tan of fValue

- `fValue`: float

<a id="teststringagainstpattern"></a>

## `TestStringAgainstPattern(sPattern, sStringToTest)` - Routine 177

- `177. TestStringAgainstPattern`
- - Returns TRUE if sStringToTest matches sPattern.

- `sPattern`: string
- `sStringToTest`: string

<a id="turnstoseconds"></a>

## `TurnsToSeconds(nTurns)` - Routine 123

- `123. TurnsToSeconds`
- Convert nTurns into a number of seconds
- A turn is always 60.0 seconds

- `nTurns`: int

<a id="vector"></a>

## `Vector(x, y, z)` - Routine 142

- `142. Vector`
- Create a vector with the specified values for x, y and z

- `x`: float (default: `0.0`)
- `y`: float (default: `0.0`)
- `z`: float (default: `0.0`)

<a id="vectormagnitude"></a>

## `VectorMagnitude(vVector)` - Routine 104

- `104. VectorMagnitude`
- Get the magnitude of vVector; this can be used to determine the
- distance between two points.
- - Return value on error: 0.0f

- `vVector`: vector

<a id="vectornormalize"></a>

## `VectorNormalize(vVector)` - Routine 137

- `137. VectorNormalize`
- Normalize vVector

- `vVector`: vector

<a id="vectortoangle"></a>

## `VectorToAngle(vVector)` - Routine 145

- `145. VectorToAngle`
- Convert vVector to an angle

- `vVector`: vector

<a id="willsave"></a>

## `WillSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 110

- `110. WillSave`
- Does a Will Save check for the given DC
- - oCreature
- - nDC: Difficulty check
- - nSaveType: SAVING_THROW_TYPE_*
- - oSaveVersus

- `oCreature`: object
- `nDC`: int
- `nSaveType`: int (default: `0`)
- `oSaveVersus`: object

<a id="writetimestampedlogentry"></a>

## `WriteTimestampedLogEntry(sLogEntry)` - Routine 560

- `560. WriteTimestampedLogEntry`
- Write sLogEntry as a timestamped entry into the log file

- `sLogEntry`: string

<a id="yardstometers"></a>

## `YardsToMeters(fYards)` - Routine 219

- `219. YardsToMeters`
- Convert fYards into a number of meters.

- `fYards`: float

