# Actions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="actionfollowowner"></a>

## `ActionFollowOwner(fRange)`

- 843
- RWT-OEI 07/20/04
- Similiar to ActionFollowLeader() except the creature
- follows its owner
- nRange is how close it should follow. Note that once this

- `fRange`: float (default: `2.5`)

<a id="actionswitchweapons"></a>

## `ActionSwitchWeapons()`

- 853
- ActionSwitchWeapons
- Forces the creature to switch between Config 1 and Config 2
- of their equipment. Does not work in dialogs. Works with
- AssignCommand()

