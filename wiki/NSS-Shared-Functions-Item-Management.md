# Item Management

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="changeitemcost"></a>

## `ChangeItemCost(sItem, fCostMultiplier)` - Routine 747

- `747. ChangeItemCost`
- ChangeItemCost
- Change the cost of an item

- `sItem`: string
- `fCostMultiplier`: float

<a id="createitemonfloor"></a>

## `CreateItemOnFloor(sTemplate, lLocation, bUseAppearAnimation)` - Routine 766

- `766. CreateItemOnFloor`
- Should only be used for items that have been created on the ground, and will
- be destroyed without ever being picked up or equipped.  Returns true if successful

- `sTemplate`: string
- `lLocation`: location
- `bUseAppearAnimation`: int (default: `0`)

<a id="createitemonobject"></a>

## `CreateItemOnObject(sItemTemplate, oTarget, nStackSize)` - Routine 31

- `31. CreateItemOnObject`
- Create an item with the template sItemTemplate in oTarget's inventory.
- - nStackSize: This is the stack size of the item to be created
- - Return value: The object that has been created.  On error, this returns
- OBJECT_INVALID.

- `sItemTemplate`: string
- `oTarget`: object
- `nStackSize`: int (default: `1`)

<a id="eventactivateitem"></a>

## `EventActivateItem(oItem, lTarget, oTarget)` - Routine 424

- `424. EventActivateItem`
- Activate oItem.

- `oItem`: object
- `lTarget`: location
- `oTarget`: object

<a id="getbaseitemtype"></a>

## `GetBaseItemType(oItem)` - Routine 397

- `397. GetBaseItemType`
- Get the base item type (BASE_ITEM_*) of oItem.
- - Returns BASE_ITEM_INVALID if oItem is an invalid item.

- `oItem`: object

<a id="getfirstitemininventory"></a>

## `GetFirstItemInInventory(oTarget)` - Routine 339

- `339. GetFirstItemInInventory`
- Get the first item in oTarget's inventory (start to cycle through oTarget's
- inventory).
- - Returns OBJECT_INVALID if the caller is not a creature, item, placeable or store,
- or if no item is found.

- `oTarget`: object

<a id="getinventorydisturbitem"></a>

## `GetInventoryDisturbItem()` - Routine 353

- `353. GetInventoryDisturbItem`
- get the item that caused the caller's OnInventoryDisturbed script to fire.
- - Returns OBJECT_INVALID if the caller is not a valid object.

<a id="getitemactivated"></a>

## `GetItemActivated()` - Routine 439

- `439. GetItemActivated`
- Use this in an OnItemActivated module script to get the item that was activated.

<a id="getitemactivatedtarget"></a>

## `GetItemActivatedTarget()` - Routine 442

- `442. GetItemActivatedTarget`
- Use this in an OnItemActivated module script to get the item's target.

<a id="getitemactivatedtargetlocation"></a>

## `GetItemActivatedTargetLocation()` - Routine 441

- `441. GetItemActivatedTargetLocation`
- Use this in an OnItemActivated module script to get the location of the item's
- target.

<a id="getitemactivator"></a>

## `GetItemActivator()` - Routine 440

- `440. GetItemActivator`
- Use this in an OnItemActivated module script to get the creature that
- activated the item.

<a id="getitemacvalue"></a>

## `GetItemACValue(oItem)` - Routine 401

- `401. GetItemACValue`
- Get the Armour Class of oItem.
- - Return 0 if the oItem is not a valid item, or if oItem has no armour value.

- `oItem`: object

<a id="getiteminslot"></a>

## `GetItemInSlot(nInventorySlot, oCreature)` - Routine 155

- `155. GetItemInSlot`
- Get the object which is in oCreature's specified inventory slot
- - nInventorySlot: INVENTORY_SLOT_*
- - oCreature
- - Returns OBJECT_INVALID if oCreature is not a valid creature or there is no
- item in nInventorySlot.

- `nInventorySlot`: int
- `oCreature`: object

<a id="getitempossessedby"></a>

## `GetItemPossessedBy(oCreature, sItemTag)` - Routine 30

- `30. GetItemPossessedBy`
- Get the object possessed by oCreature with the tag sItemTag
- - Return value on error: OBJECT_INVALID

- `oCreature`: object
- `sItemTag`: string

<a id="getitempossessor"></a>

## `GetItemPossessor(oItem)` - Routine 29

- `29. GetItemPossessor`
- Get the possessor of oItem
- - Return value on error: OBJECT_INVALID

- `oItem`: object

<a id="getitemstacksize"></a>

## `GetItemStackSize(oItem)` - Routine 138

- `138. GetItemStackSize`
- Gets the stack size of an item.

- `oItem`: object

<a id="getlastitemequipped"></a>

## `GetLastItemEquipped()` - Routine 52

- `52. GetLastItemEquipped`
- Returns the last item that was equipped by a creature.

<a id="getmoduleitemacquired"></a>

## `GetModuleItemAcquired()` - Routine 282

- `282. GetModuleItemAcquired`
- Use this in an OnItemAcquired script to get the item that was acquired.
- - Returns OBJECT_INVALID if the module is not valid.

<a id="getmoduleitemacquiredfrom"></a>

## `GetModuleItemAcquiredFrom()` - Routine 283

- `283. GetModuleItemAcquiredFrom`
- Use this in an OnItemAcquired script to get the creatre that previously
- possessed the item.
- - Returns OBJECT_INVALID if the item was picked up from the ground.

<a id="getmoduleitemlost"></a>

## `GetModuleItemLost()` - Routine 292

- `292. GetModuleItemLost`
- Use this in an OnItemLost script to get the item that was lost/dropped.
- - Returns OBJECT_INVALID if the module is not valid.

<a id="getmoduleitemlostby"></a>

## `GetModuleItemLostBy()` - Routine 293

- `293. GetModuleItemLostBy`
- Use this in an OnItemLost script to get the creature that lost the item.
- - Returns OBJECT_INVALID if the module is not valid.

<a id="getnextitemininventory"></a>

## `GetNextItemInInventory(oTarget)` - Routine 340

- `340. GetNextItemInInventory`
- Get the next item in oTarget's inventory (continue to cycle through oTarget's
- inventory).
- - Returns OBJECT_INVALID if the caller is not a creature, item, placeable or store,
- or if no item is found.

- `oTarget`: object

<a id="getnumstackeditems"></a>

## `GetNumStackedItems(oItem)` - Routine 475

- `475. GetNumStackedItems`
- Get the number of stacked items that oItem comprises.

- `oItem`: object

<a id="getspellcastitem"></a>

## `GetSpellCastItem()` - Routine 438

- `438. GetSpellCastItem`
- Use this in a spell script to get the item used to cast the spell.

<a id="giveitem"></a>

## `GiveItem(oItem, oGiveTo)` - Routine 271

- `271. GiveItem`
- Give oItem to oGiveTo (instant; for similar Action use ActionGiveItem)
- If oItem is not a valid item, or oGiveTo is not a valid object, nothing will
- happen.

- `oItem`: object
- `oGiveTo`: object

<a id="setitemnonequippable"></a>

## `SetItemNonEquippable(oItem, bNonEquippable)` - Routine 266

- `266. SetItemNonEquippable`
- Flag the specified item as being non-equippable or not.  Set bNonEquippable
- to TRUE to prevent this item from being equipped, and FALSE to allow
- the normal equipping checks to determine if the item can be equipped.
- NOTE: This will do nothing if the object passed in is not an item.  Items that
- are already equipped when this is called will not automatically be

- `oItem`: object
- `bNonEquippable`: int

<a id="setitemstacksize"></a>

## `SetItemStackSize(oItem, nStackSize)` - Routine 150

- `150. SetItemStackSize`
- Set the stack size of an item.
- NOTE: The stack size will be clamped to between 1 and the max stack size (as
- specified in the base item).

- `oItem`: object
- `nStackSize`: int

