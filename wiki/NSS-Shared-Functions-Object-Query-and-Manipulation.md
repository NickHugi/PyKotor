# Object Query and Manipulation

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="createobject"></a>

## `CreateObject(nObjectType, sTemplate, lLocation, bUseAppearAnimation)` - Routine 243

- `243. CreateObject`
- Create an object of the specified type at lLocation.
- - nObjectType: OBJECT_TYPE_ITEM, OBJECT_TYPE_CREATURE, OBJECT_TYPE_PLACEABLE,
- OBJECT_TYPE_STORE
- - sTemplate
- - lLocation

- `nObjectType`: int
- `sTemplate`: string
- `lLocation`: location
- `bUseAppearAnimation`: int (default: `0`)

<a id="destroyobject"></a>

## `DestroyObject(oDestroy, fDelay, bNoFade, fDelayUntilFade)` - Routine 241

- `241. DestroyObject`
- Destroy oObject (irrevocably).
- This will not work on modules and areas.
- The bNoFade and fDelayUntilFade are for creatures and placeables only

- `oDestroy`: object
- `fDelay`: float (default: `0.0`)
- `bNoFade`: int (default: `0`)
- `fDelayUntilFade`: float (default: `0.0`)

<a id="getnearestcreature"></a>

## `GetNearestCreature(nFirstCriteriaType, nFirstCriteriaValue, oTarget, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 38

- `38. GetNearestCreature`
- Get the creature nearest to oTarget, subject to all the criteria specified.
- - nFirstCriteriaType: CREATURE_TYPE_*
- - nFirstCriteriaValue:
- -> CLASS_TYPE_* if nFirstCriteriaType was CREATURE_TYPE_CLASS
- -> SPELL_* if nFirstCriteriaType was CREATURE_TYPE_DOES_NOT_HAVE_SPELL_EFFECT

- `nFirstCriteriaType`: int
- `nFirstCriteriaValue`: int
- `oTarget`: object
- `nNth`: int (default: `1`)
- `nSecondCriteriaType`: int
- `nSecondCriteriaValue`: int
- `nThirdCriteriaType`: int
- `nThirdCriteriaValue`: int

<a id="getnearestcreaturetolocation"></a>

## `GetNearestCreatureToLocation(nFirstCriteriaType, nFirstCriteriaValue, lLocation, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 226

- `226. GetNearestCreatureToLocation`
- Get the creature nearest to lLocation, subject to all the criteria specified.
- - nFirstCriteriaType: CREATURE_TYPE_*
- - nFirstCriteriaValue:
- -> CLASS_TYPE_* if nFirstCriteriaType was CREATURE_TYPE_CLASS
- -> SPELL_* if nFirstCriteriaType was CREATURE_TYPE_DOES_NOT_HAVE_SPELL_EFFECT

- `nFirstCriteriaType`: int
- `nFirstCriteriaValue`: int
- `lLocation`: location
- `nNth`: int (default: `1`)
- `nSecondCriteriaType`: int
- `nSecondCriteriaValue`: int
- `nThirdCriteriaType`: int
- `nThirdCriteriaValue`: int

<a id="getnearestobject"></a>

## `GetNearestObject(nObjectType, oTarget, nNth)` - Routine 227

- `227. GetNearestObject`
- Get the Nth object nearest to oTarget that is of the specified type.
- - nObjectType: OBJECT_TYPE_*
- - oTarget
- - nNth
- - Return value on error: OBJECT_INVALID

- `nObjectType`: int (default: `32767`)
- `oTarget`: object
- `nNth`: int (default: `1`)

<a id="getnearestobjectbytag"></a>

## `GetNearestObjectByTag(sTag, oTarget, nNth)` - Routine 229

- `229. GetNearestObjectByTag`
- Get the nth Object nearest to oTarget that has sTag as its tag.
- - Return value on error: OBJECT_INVALID

- `sTag`: string
- `oTarget`: object
- `nNth`: int (default: `1`)

<a id="getnearestobjecttolocation"></a>

## `GetNearestObjectToLocation(nObjectType, lLocation, nNth)` - Routine 228

- `228. GetNearestObjectToLocation`
- Get the nNth object nearest to lLocation that is of the specified type.
- - nObjectType: OBJECT_TYPE_*
- - lLocation
- - nNth
- - Return value on error: OBJECT_INVALID

- `nObjectType`: int
- `lLocation`: location
- `nNth`: int (default: `1`)

<a id="getnearesttraptoobject"></a>

## `GetNearestTrapToObject(oTarget, nTrapDetected)` - Routine 488

- `488. GetNearestTrapToObject`
- Get the trap nearest to oTarget.
- Note : "trap objects" are actually any trigger, placeable or door that is
- trapped in oTarget's area.
- - oTarget
- - nTrapDetected: if this is TRUE, the trap returned has to have been detected

- `oTarget`: object
- `nTrapDetected`: int (default: `1`)

<a id="getobjectbytag"></a>

## `GetObjectByTag(sTag, nNth)` - Routine 200

- `200. GetObjectByTag`
- Get the nNth object with the specified tag.
- - sTag
- - nNth: the nth object with this tag may be requested
- - Returns OBJECT_INVALID if the object cannot be found.

- `sTag`: string
- `nNth`: int (default: `0`)

<a id="getobjectheard"></a>

## `GetObjectHeard(oTarget, oSource)` - Routine 290

- `290. GetObjectHeard`
- Determine whether oSource hears oTarget.

- `oTarget`: object
- `oSource`: object

<a id="getobjectseen"></a>

## `GetObjectSeen(oTarget, oSource)` - Routine 289

- `289. GetObjectSeen`
- Determine whether oSource sees oTarget.

- `oTarget`: object
- `oSource`: object

<a id="getobjecttype"></a>

## `GetObjectType(oTarget)` - Routine 106

- `106. GetObjectType`
- Get the object type (OBJECT_TYPE_*) of oTarget
- - Return value if oTarget is not a valid object: -1

- `oTarget`: object

<a id="getspelltargetobject"></a>

## `GetSpellTargetObject()` - Routine 47

- `47. GetSpellTargetObject`
- Get the object at which the caller last cast a spell
- - Return value on error: OBJECT_INVALID

<a id="swmg_getobjectbyname"></a>

## `SWMG_GetObjectByName(sName)` - Routine 585

- `585. SWMG_GetObjectByName`
- gets an object by its name (duh!)
- SWMG_GetObjectByName

- `sName`: string

<a id="swmg_getobjectname"></a>

## `SWMG_GetObjectName(oid)` - Routine 597

- `597. SWMG_GetObjectName`
- gets an objects name
- SWMG_GetObjectName

- `oid`: object

