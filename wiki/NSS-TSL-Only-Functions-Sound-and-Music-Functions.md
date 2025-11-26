# Sound and Music Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** TSL-Only Functions


<a id="displaydatapad"></a>

## `DisplayDatapad(oDatapad)`

- 865
- RWT-OEI 09/28/04
- This function displays a datapad popup. Just pass it the
- object ID of a datapad.

- `oDatapad`: object

<a id="displaymessagebox"></a>

## `DisplayMessageBox(nStrRef, sIcon)`

- 864
- RWT-OEI 09/27/04
- This function displays the generic Message Box with the strref
- message in it
- sIcon is the resref for an icon you would like to display.

- `nStrRef`: int
- `sIcon`: string (default: ``)

<a id="playoverlayanimation"></a>

## `PlayOverlayAnimation(oTarget, nAnimation)`

- 854
- DJS-OEI 8/29/2004
- PlayOverlayAnimation
- This function will play an overlay animation on a character
- even if the character is moving. This does not cause an action

- `oTarget`: object
- `nAnimation`: int

<!-- TSL_ONLY_FUNCTIONS_END -->

