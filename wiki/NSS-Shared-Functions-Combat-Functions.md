# Combat Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="cancelcombat"></a>

## `CancelCombat(oidCreature)` - Routine 54

- `54. CancelCombat`
- Cancels combat for the specified creature.

- `oidCreature`: object

<a id="cutsceneattack"></a>

## `CutsceneAttack(oTarget, nAnimation, nAttackResult, nDamage)` - Routine 503

- `503. CutsceneAttack`
- CutsceneAttack
- This function allows the designer to specify exactly what's going to happen in a combat round
- There are no guarentees made that the animation specified here will be correct - only that it will be played,
- so it is up to the designer to ensure that they have selected the right animation
- It relies upon constants specified above for the attack result

- `oTarget`: object
- `nAnimation`: int
- `nAttackResult`: int
- `nDamage`: int

<a id="getattacktarget"></a>

## `GetAttackTarget(oCreature)` - Routine 316

- `316. GetAttackTarget`
- Get the attack target of oCreature.
- This only works when oCreature is in combat.

- `oCreature`: object

<a id="getattemptedattacktarget"></a>

## `GetAttemptedAttackTarget()` - Routine 361

- `361. GetAttemptedAttackTarget`
- Get the target that the caller attempted to attack - this should be used in
- conjunction with GetAttackTarget(). This value is set every time an attack is
- made, and is reset at the end of combat.
- - Returns OBJECT_INVALID if the caller is not a valid creature.

<a id="getfirstattacker"></a>

## `GetFirstAttacker(oCreature)` - Routine 727

- `727. GetFirstAttacker`
- Returns the first object in the area that is attacking oCreature

- `oCreature`: object

<a id="getgoingtobeattackedby"></a>

## `GetGoingToBeAttackedBy(oTarget)` - Routine 211

- `211. GetGoingToBeAttackedBy`
- Get the creature that is going to attack oTarget.
- Note: This value is cleared out at the end of every combat round and should
- not be used in any case except when getting a "going to be attacked" shout
- from the master creature (and this creature is a henchman)
- - Returns OBJECT_INVALID if oTarget is not a valid creature.

- `oTarget`: object

<a id="getisincombat"></a>

## `GetIsInCombat(oCreature)` - Routine 320

- `320. GetIsInCombat`
- - Returns TRUE if oCreature is in combat.

- `oCreature`: object

<a id="getlastattackaction"></a>

## `GetLastAttackAction(oAttacker)` - Routine 722

- `722. GetLastAttackAction`
- Returns the last attack action for a given object

- `oAttacker`: object

<a id="getlastattacker"></a>

## `GetLastAttacker(oAttackee)` - Routine 36

- `36. GetLastAttacker`
- Get the last attacker of oAttackee.  This should only be used ONLY in the
- OnAttacked events for creatures, placeables and doors.
- - Return value on error: OBJECT_INVALID

- `oAttackee`: object

<a id="getlastattackmode"></a>

## `GetLastAttackMode(oCreature)` - Routine 318

- `318. GetLastAttackMode`
- Get the attack mode (COMBAT_MODE_*) of oCreature's last attack.
- This only works when oCreature is in combat.

- `oCreature`: object

<a id="getlastattackresult"></a>

## `GetLastAttackResult(oAttacker)` - Routine 725

- `725. GetLastAttackResult`
- Returns the result of the last attack

- `oAttacker`: object

<a id="getlastattacktype"></a>

## `GetLastAttackType(oCreature)` - Routine 317

- `317. GetLastAttackType`
- Get the attack type (SPECIAL_ATTACK_*) of oCreature's last attack.
- This only works when oCreature is in combat.

- `oCreature`: object

<a id="getlastkiller"></a>

## `GetLastKiller()` - Routine 437

- `437. GetLastKiller`
- Get the object that killed the caller.

<a id="getnextattacker"></a>

## `GetNextAttacker(oCreature)` - Routine 728

- `728. GetNextAttacker`
- Returns the next object in the area that is attacking oCreature

- `oCreature`: object

<a id="touchattackmelee"></a>

## `TouchAttackMelee(oTarget, bDisplayFeedback)` - Routine 146

- `146. TouchAttackMelee`
- The caller will perform a Melee Touch Attack on oTarget
- This is not an action, and it assumes the caller is already within range of
- oTarget
- - Returns 0 on a miss, 1 on a hit and 2 on a critical hit

- `oTarget`: object
- `bDisplayFeedback`: int (default: `1`)

<a id="touchattackranged"></a>

## `TouchAttackRanged(oTarget, bDisplayFeedback)` - Routine 147

- `147. TouchAttackRanged`
- The caller will perform a Ranged Touch Attack on oTarget
- - Returns 0 on a miss, 1 on a hit and 2 on a critical hit

- `oTarget`: object
- `bDisplayFeedback`: int (default: `1`)

