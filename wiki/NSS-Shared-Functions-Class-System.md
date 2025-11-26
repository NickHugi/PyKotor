# Class System

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="addmulticlass"></a>

## `AddMultiClass(nClassType, oSource)` - Routine 389

- `389. AddMultiClass`
- This allows you to add a new class to any creature object

- `nClassType`: int
- `oSource`: object

<a id="getclassbyposition"></a>

## `GetClassByPosition(nClassPosition, oCreature)` - Routine 341

- `341. GetClassByPosition`
- A creature can have up to three classes.  This function determines the
- creature's class (CLASS_TYPE_*) based on nClassPosition.
- - nClassPosition: 1, 2 or 3
- - oCreature
- - Returns CLASS_TYPE_INVALID if the oCreature does not have a class in

- `nClassPosition`: int
- `oCreature`: object

<a id="getfactionmostfrequentclass"></a>

## `GetFactionMostFrequentClass(oFactionMember)` - Routine 191

- `191. GetFactionMostFrequentClass`
- Get the most frequent class in the faction - this can be compared with the
- constants CLASS_TYPE_*.
- - Return value on error: -1

- `oFactionMember`: object

<a id="getlevelbyclass"></a>

## `GetLevelByClass(nClassType, oCreature)` - Routine 343

- `343. GetLevelByClass`
- Determine the levels that oCreature holds in nClassType.
- - nClassType: CLASS_TYPE_*
- - oCreature

- `nClassType`: int
- `oCreature`: object

