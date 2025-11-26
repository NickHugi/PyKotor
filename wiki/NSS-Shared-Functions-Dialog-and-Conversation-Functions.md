# Dialog and Conversation Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="barkstring"></a>

## `BarkString(oCreature, strRef)` - Routine 671

- `671. BarkString`
- BarkString
- this will cause a creature to bark the strRef from the talk table
- If creature is specefied as OBJECT_INVALID a general bark is made.

- `oCreature`: object
- `strRef`: int

<a id="beginconversation"></a>

## `BeginConversation(sResRef, oObjectToDialog)` - Routine 255

- `255. BeginConversation`
- Use this in an OnDialog script to start up the dialog tree.
- - sResRef: if this is not specified, the default dialog file will be used
- - oObjectToDialog: if this is not specified the person that triggered the
- event will be used

- `sResRef`: string (default: ``)
- `oObjectToDialog`: object

<a id="cancelpostdialogcharacterswitch"></a>

## `CancelPostDialogCharacterSwitch()` - Routine 757

- `757. CancelPostDialogCharacterSwitch`
- CancelPostDialogCharacterSwitch()

<a id="eventconversation"></a>

## `EventConversation()` - Routine 295

- `295. EventConversation`
- Conversation event.

<a id="getisconversationactive"></a>

## `GetIsConversationActive()` - Routine 701

- `701. GetIsConversationActive`
- Checks to see if any conversations are currently taking place

<a id="getisinconversation"></a>

## `GetIsInConversation(oObject)` - Routine 445

- `445. GetIsInConversation`
- Determine whether oObject is in conversation.

- `oObject`: object

<a id="getlastconversation"></a>

## `GetLastConversation()` - Routine 711

- `711. GetLastConversation`
- GetLastConversation
- Gets the last conversation string.

<a id="getlastspeaker"></a>

## `GetLastSpeaker()` - Routine 254

- `254. GetLastSpeaker`
- Use this in a conversation script to get the person with whom you are conversing.
- - Returns OBJECT_INVALID if the caller is not a valid creature.

<a id="holdworldfadeinfordialog"></a>

## `HoldWorldFadeInForDialog()` - Routine 760

- `760. HoldWorldFadeInForDialog`
- HoldWorldFadeInForDialog()

<a id="resetdialogstate"></a>

## `ResetDialogState()` - Routine 749

- `749. ResetDialogState`
- ResetDialogState
- Resets the GlobalDialogState for the engine.
- NOTE: NEVER USE THIS UNLESS YOU KNOW WHAT ITS FOR!
- only to be used for a failing OnDialog script

<a id="setdialogplaceablecamera"></a>

## `SetDialogPlaceableCamera(nCameraId)` - Routine 461

- `461. SetDialogPlaceableCamera`
- Cut immediately to placeable camera 'nCameraId' during dialog.  nCameraId must be
- an existing Placeable Camera ID.  Function only works during Dialog.

- `nCameraId`: int

<a id="setlockheadfollowindialog"></a>

## `SetLockHeadFollowInDialog(oObject, nValue)` - Routine 506

- `506. SetLockHeadFollowInDialog`
- SetLockHeadFollowInDialog
- Allows the locking and undlocking of head following for an object in dialog
- - oObject - Object
- - nValue - TRUE or FALSE

- `oObject`: object
- `nValue`: int

<a id="setlockorientationindialog"></a>

## `SetLockOrientationInDialog(oObject, nValue)` - Routine 505

- `505. SetLockOrientationInDialog`
- SetLockOrientationInDialog
- Allows the locking and unlocking of orientation changes for an object in dialog
- - oObject - Object
- - nValue - TRUE or FALSE

- `oObject`: object
- `nValue`: int

<a id="speakonelinerconversation"></a>

## `SpeakOneLinerConversation(sDialogResRef, oTokenTarget)` - Routine 417

- `417. SpeakOneLinerConversation`
- Immediately speak a conversation one-liner.
- - sDialogResRef
- - oTokenTarget: This must be specified if there are creature-specific tokens
- in the string.

- `sDialogResRef`: string (default: ``)
- `oTokenTarget`: object (default: `32767`)

<a id="speakstring"></a>

## `SpeakString(sStringToSpeak, nTalkVolume)` - Routine 221

- `221. SpeakString`
- The caller will immediately speak sStringToSpeak (this is different from
- ActionSpeakString)
- - sStringToSpeak
- - nTalkVolume: TALKVOLUME_*

- `sStringToSpeak`: string
- `nTalkVolume`: int (default: `0`)

