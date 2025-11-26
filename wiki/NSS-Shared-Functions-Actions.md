# Actions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="actionattack"></a>

## `ActionAttack(oAttackee, bPassive)` - Routine 37

- `37. ActionAttack`
- Attack oAttackee.
- - bPassive: If this is TRUE, attack is in passive mode.

- `oAttackee`: object
- `bPassive`: int (default: `0`)

<a id="actionbarkstring"></a>

## `ActionBarkString(strRef)` - Routine 700

- `700. ActionBarkString`
- this will cause a creature to bark the strRef from the talk table.

- `strRef`: int

<a id="actioncastfakespellatlocation"></a>

## `ActionCastFakeSpellAtLocation(nSpell, lTarget, nProjectilePathType)` - Routine 502

- `502. ActionCastFakeSpellAtLocation`
- The action subject will fake casting a spell at lLocation; the conjure and
- cast animations and visuals will occur, nothing else.
- - nSpell
- - lTarget
- - nProjectilePathType: PROJECTILE_PATH_TYPE_*

- `nSpell`: int
- `lTarget`: location
- `nProjectilePathType`: int (default: `0`)

<a id="actioncastfakespellatobject"></a>

## `ActionCastFakeSpellAtObject(nSpell, oTarget, nProjectilePathType)` - Routine 501

- `501. ActionCastFakeSpellAtObject`
- The action subject will fake casting a spell at oTarget; the conjure and cast
- animations and visuals will occur, nothing else.
- - nSpell
- - oTarget
- - nProjectilePathType: PROJECTILE_PATH_TYPE_*

- `nSpell`: int
- `oTarget`: object
- `nProjectilePathType`: int (default: `0`)

<a id="actioncastspellatlocation"></a>

## `ActionCastSpellAtLocation(nSpell, lTargetLocation, nMetaMagic, bCheat, nProjectilePathType, bInstantSpell)` - Routine 234

- `234. ActionCastSpellAtLocation`
- Cast spell nSpell at lTargetLocation.
- - nSpell: SPELL_*
- - lTargetLocation
- - nMetaMagic: METAMAGIC_*
- - bCheat: If this is TRUE, then the executor of the action doesn't have to be

- `nSpell`: int
- `lTargetLocation`: location
- `nMetaMagic`: int (default: `0`)
- `bCheat`: int (default: `0`)
- `nProjectilePathType`: int (default: `0`)
- `bInstantSpell`: int (default: `0`)

<a id="actioncastspellatobject"></a>

## `ActionCastSpellAtObject(nSpell, oTarget, nMetaMagic, bCheat, nDomainLevel, nProjectilePathType, bInstantSpell)` - Routine 48

- `48. ActionCastSpellAtObject`
- This action casts a spell at oTarget.
- - nSpell: SPELL_*
- - oTarget: Target for the spell
- - nMetamagic: METAMAGIC_*
- - bCheat: If this is TRUE, then the executor of the action doesn't have to be

- `nSpell`: int
- `oTarget`: object
- `nMetaMagic`: int (default: `0`)
- `bCheat`: int (default: `0`)
- `nDomainLevel`: int (default: `0`)
- `nProjectilePathType`: int (default: `0`)
- `bInstantSpell`: int (default: `0`)

<a id="actionclosedoor"></a>

## `ActionCloseDoor(oDoor)` - Routine 44

- `44. ActionCloseDoor`
- Cause the action subject to close oDoor

- `oDoor`: object

<a id="actiondocommand"></a>

## `ActionDoCommand(aActionToDo)` - Routine 294

- `294. ActionDoCommand`
- Do aActionToDo.

- `aActionToDo`: action

<a id="actionequipitem"></a>

## `ActionEquipItem(oItem, nInventorySlot, bInstant)` - Routine 32

- `32. ActionEquipItem`
- Equip oItem into nInventorySlot.
- - nInventorySlot: INVENTORY_SLOT_*
- - No return value, but if an error occurs the log file will contain
- "ActionEquipItem failed."

- `oItem`: object
- `nInventorySlot`: int
- `bInstant`: int (default: `0`)

<a id="actionequipmostdamagingmelee"></a>

## `ActionEquipMostDamagingMelee(oVersus, bOffHand)` - Routine 399

- `399. ActionEquipMostDamagingMelee`
- The creature will equip the melee weapon in its possession that can do the
- most damage. If no valid melee weapon is found, it will equip the most
- damaging range weapon. This function should only ever be called in the
- EndOfCombatRound scripts, because otherwise it would have to stop the combat
- round to run simulation.

- `oVersus`: object
- `bOffHand`: int (default: `0`)

<a id="actionequipmostdamagingranged"></a>

## `ActionEquipMostDamagingRanged(oVersus)` - Routine 400

- `400. ActionEquipMostDamagingRanged`
- The creature will equip the range weapon in its possession that can do the
- most damage.
- If no valid range weapon can be found, it will equip the most damaging melee
- weapon.
- - oVersus: You can try to get the most damaging weapon against oVersus

- `oVersus`: object

<a id="actionfollowleader"></a>

## `ActionFollowLeader()` - Routine 730

- `730. ActionFollowLeader`
- this action has a party member follow the leader.
- DO NOT USE ON A CREATURE THAT IS NOT IN THE PARTY!!

<a id="actionforcefollowobject"></a>

## `ActionForceFollowObject(oFollow, fFollowDistance)` - Routine 167

- `167. ActionForceFollowObject`
- The action subject will follow oFollow until a ClearAllActions() is called.
- - oFollow: this is the object to be followed
- - fFollowDistance: follow distance in metres
- - No return value

- `oFollow`: object
- `fFollowDistance`: float (default: `0.0`)

<a id="actionforcemovetolocation"></a>

## `ActionForceMoveToLocation(lDestination, bRun, fTimeout)` - Routine 382

- `382. ActionForceMoveToLocation`
- Force the action subject to move to lDestination.

- `lDestination`: location
- `bRun`: int (default: `0`)
- `fTimeout`: float (default: `30.0`)

<a id="actionforcemovetoobject"></a>

## `ActionForceMoveToObject(oMoveTo, bRun, fRange, fTimeout)` - Routine 383

- `383. ActionForceMoveToObject`
- Force the action subject to move to oMoveTo.

- `oMoveTo`: object
- `bRun`: int (default: `0`)
- `fRange`: float (default: `1.0`)
- `fTimeout`: float (default: `30.0`)

<a id="actiongiveitem"></a>

## `ActionGiveItem(oItem, oGiveTo)` - Routine 135

- `135. ActionGiveItem`
- Give oItem to oGiveTo
- If oItem is not a valid item, or oGiveTo is not a valid object, nothing will
- happen.

- `oItem`: object
- `oGiveTo`: object

<a id="actioninteractobject"></a>

## `ActionInteractObject(oPlaceable)` - Routine 329

- `329. ActionInteractObject`
- Use oPlaceable.

- `oPlaceable`: object

<a id="actionjumptolocation"></a>

## `ActionJumpToLocation(lLocation)` - Routine 214

- `214. ActionJumpToLocation`
- The subject will jump to lLocation instantly (even between areas).
- If lLocation is invalid, nothing will happen.

- `lLocation`: location

<a id="actionjumptoobject"></a>

## `ActionJumpToObject(oToJumpTo, bWalkStraightLineToPoint)` - Routine 196

- `196. ActionJumpToObject`
- Jump to an object ID, or as near to it as possible.

- `oToJumpTo`: object
- `bWalkStraightLineToPoint`: int (default: `1`)

<a id="actionlockobject"></a>

## `ActionLockObject(oTarget)` - Routine 484

- `484. ActionLockObject`
- The action subject will lock oTarget, which can be a door or a placeable
- object.

- `oTarget`: object

<a id="actionmoveawayfromlocation"></a>

## `ActionMoveAwayFromLocation(lMoveAwayFrom, bRun, fMoveAwayRange)` - Routine 360

- `360. ActionMoveAwayFromLocation`
- Causes the action subject to move away from lMoveAwayFrom.

- `lMoveAwayFrom`: location
- `bRun`: int (default: `0`)
- `fMoveAwayRange`: float (default: `40.0`)

<a id="actionmoveawayfromobject"></a>

## `ActionMoveAwayFromObject(oFleeFrom, bRun, fMoveAwayRange)` - Routine 23

- `23. ActionMoveAwayFromObject`
- Cause the action subject to move to a certain distance away from oFleeFrom.
- - oFleeFrom: This is the object we wish the action subject to move away from.
- If oFleeFrom is not in the same area as the action subject, nothing will
- happen.
- - bRun: If this is TRUE, the action subject will run rather than walk

- `oFleeFrom`: object
- `bRun`: int (default: `0`)
- `fMoveAwayRange`: float (default: `40.0`)

<a id="actionmovetolocation"></a>

## `ActionMoveToLocation(lDestination, bRun)` - Routine 21

- `21. ActionMoveToLocation`
- The action subject will move to lDestination.
- - lDestination: The object will move to this location.  If the location is
- invalid or a path cannot be found to it, the command does nothing.
- - bRun: If this is TRUE, the action subject will run rather than walk
- - No return value, but if an error occurs the log file will contain

- `lDestination`: location
- `bRun`: int (default: `0`)

<a id="actionmovetoobject"></a>

## `ActionMoveToObject(oMoveTo, bRun, fRange)` - Routine 22

- `22. ActionMoveToObject`
- Cause the action subject to move to a certain distance from oMoveTo.
- If there is no path to oMoveTo, this command will do nothing.
- - oMoveTo: This is the object we wish the action subject to move to
- - bRun: If this is TRUE, the action subject will run rather than walk
- - fRange: This is the desired distance between the action subject and oMoveTo

- `oMoveTo`: object
- `bRun`: int (default: `0`)
- `fRange`: float (default: `1.0`)

<a id="actionopendoor"></a>

## `ActionOpenDoor(oDoor)` - Routine 43

- `43. ActionOpenDoor`
- Cause the action subject to open oDoor

- `oDoor`: object

<a id="actionpauseconversation"></a>

## `ActionPauseConversation()` - Routine 205

- `205. ActionPauseConversation`
- Pause the current conversation.

<a id="actionpickupitem"></a>

## `ActionPickUpItem(oItem)` - Routine 34

- `34. ActionPickUpItem`
- Pick up oItem from the ground.
- - No return value, but if an error occurs the log file will contain
- "ActionPickUpItem failed."

- `oItem`: object

<a id="actionplayanimation"></a>

## `ActionPlayAnimation(nAnimation, fSpeed, fDurationSeconds)` - Routine 40

- `40. ActionPlayAnimation`
- Cause the action subject to play an animation
- - nAnimation: ANIMATION_*
- - fSpeed: Speed of the animation
- - fDurationSeconds: Duration of the animation (this is not used for Fire and
- Forget animations) If a time of -1.0f is specified for a looping animation

- `nAnimation`: int
- `fSpeed`: float (default: `1.0`)
- `fDurationSeconds`: float (default: `0.0`)

<a id="actionputdownitem"></a>

## `ActionPutDownItem(oItem)` - Routine 35

- `35. ActionPutDownItem`
- Put down oItem on the ground.
- - No return value, but if an error occurs the log file will contain
- "ActionPutDownItem failed."

- `oItem`: object

<a id="actionrandomwalk"></a>

## `ActionRandomWalk()` - Routine 20

- `20. ActionRandomWalk`
- The action subject will generate a random location near its current location
- and pathfind to it.  All commands will remove a RandomWalk() from the action
- queue if there is one in place.
- - No return value, but if an error occurs the log file will contain
- "ActionRandomWalk failed."

<a id="actionresumeconversation"></a>

## `ActionResumeConversation()` - Routine 206

- `206. ActionResumeConversation`
- Resume a conversation after it has been paused.

<a id="actionspeakstring"></a>

## `ActionSpeakString(sStringToSpeak, nTalkVolume)` - Routine 39

- `39. ActionSpeakString`
- Add a speak action to the action subject.
- - sStringToSpeak: String to be spoken
- - nTalkVolume: TALKVOLUME_*

- `sStringToSpeak`: string
- `nTalkVolume`: int (default: `0`)

<a id="actionspeakstringbystrref"></a>

## `ActionSpeakStringByStrRef(nStrRef, nTalkVolume)` - Routine 240

- `240. ActionSpeakStringByStrRef`
- Causes the creature to speak a translated string.
- - nStrRef: Reference of the string in the talk table
- - nTalkVolume: TALKVOLUME_*

- `nStrRef`: int
- `nTalkVolume`: int (default: `0`)

<a id="actionstartconversation"></a>

## `ActionStartConversation(oObjectToConverse, sDialogResRef, bPrivateConversation, nConversationType, bIgnoreStartRange, sNameObjectToIgnore1, sNameObjectToIgnore2, sNameObjectToIgnore3, sNameObjectToIgnore4, sNameObjectToIgnore5, sNameObjectToIgnore6, bUseLeader)` - Routine 204

- `204. ActionStartConversation`
- AMF: APRIL 28, 2003 - I HAVE CHANGED THIS FUNCTION AS PER DAN'S REQUEST
- Starts a conversation with oObjectToConverseWith - this will cause their
- OnDialog event to fire.
- - oObjectToConverseWith
- - sDialogResRef: If this is blank, the creature's own dialogue file will be used

- `oObjectToConverse`: object
- `sDialogResRef`: string (default: ``)
- `bPrivateConversation`: int (default: `0`)
- `nConversationType`: int (default: `0`)
- `bIgnoreStartRange`: int (default: `0`)
- `sNameObjectToIgnore1`: string (default: ``)
- `sNameObjectToIgnore2`: string (default: ``)
- `sNameObjectToIgnore3`: string (default: ``)
- `sNameObjectToIgnore4`: string (default: ``)
- `sNameObjectToIgnore5`: string (default: ``)
- `sNameObjectToIgnore6`: string (default: ``)
- `bUseLeader`: int (default: `0`)

<a id="actionsurrendertoenemies"></a>

## `ActionSurrenderToEnemies()` - Routine 379

- `379. ActionSurrenderToEnemies`

<a id="actiontakeitem"></a>

## `ActionTakeItem(oItem, oTakeFrom)` - Routine 136

- `136. ActionTakeItem`
- Take oItem from oTakeFrom
- If oItem is not a valid item, or oTakeFrom is not a valid object, nothing
- will happen.

- `oItem`: object
- `oTakeFrom`: object

<a id="actionunequipitem"></a>

## `ActionUnequipItem(oItem, bInstant)` - Routine 33

- `33. ActionUnequipItem`
- Unequip oItem from whatever slot it is currently in.

- `oItem`: object
- `bInstant`: int (default: `0`)

<a id="actionunlockobject"></a>

## `ActionUnlockObject(oTarget)` - Routine 483

- `483. ActionUnlockObject`
- The action subject will unlock oTarget, which can be a door or a placeable
- object.

- `oTarget`: object

<a id="actionusefeat"></a>

## `ActionUseFeat(nFeat, oTarget)` - Routine 287

- `287. ActionUseFeat`
- Use nFeat on oTarget.
- - nFeat: FEAT_*
- - oTarget

- `nFeat`: int
- `oTarget`: object

<a id="actionuseskill"></a>

## `ActionUseSkill(nSkill, oTarget, nSubSkill, oItemUsed)` - Routine 288

- `288. ActionUseSkill`
- Runs the action "UseSkill" on the current creature
- Use nSkill on oTarget.
- - nSkill: SKILL_*
- - oTarget
- - nSubSkill: SUBSKILL_*

- `nSkill`: int
- `oTarget`: object
- `nSubSkill`: int (default: `0`)
- `oItemUsed`: object

<a id="actionusetalentatlocation"></a>

## `ActionUseTalentAtLocation(tChosenTalent, lTargetLocation)` - Routine 310

- `310. ActionUseTalentAtLocation`
- Use tChosenTalent at lTargetLocation.

- `tChosenTalent`: talent
- `lTargetLocation`: location

<a id="actionusetalentonobject"></a>

## `ActionUseTalentOnObject(tChosenTalent, oTarget)` - Routine 309

- `309. ActionUseTalentOnObject`
- Use tChosenTalent on oTarget.

- `tChosenTalent`: talent
- `oTarget`: object

<a id="actionwait"></a>

## `ActionWait(fSeconds)` - Routine 202

- `202. ActionWait`
- Do nothing for fSeconds seconds.

- `fSeconds`: float

