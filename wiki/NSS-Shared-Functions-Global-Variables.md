# Global Variables

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="getglobalboolean"></a>

## `GetGlobalBoolean(sIdentifier)` - Routine 578

- `578. GetGlobalBoolean`
- GetGlobalBoolean
- This function returns the value of a global boolean (TRUE or FALSE) scripting variable.

- `sIdentifier`: string

<a id="getgloballocation"></a>

## `GetGlobalLocation(sIdentifier)` - Routine 692

- `692. GetGlobalLocation`
- GetGlobalLocation
- This function returns the a global location scripting variable.

- `sIdentifier`: string

<a id="getglobalnumber"></a>

## `GetGlobalNumber(sIdentifier)` - Routine 580

- `580. GetGlobalNumber`
- GetGlobalNumber
- This function returns the value of a global number (-128 to +127) scripting variable.

- `sIdentifier`: string

<a id="getglobalstring"></a>

## `GetGlobalString(sIdentifier)` - Routine 194

- `194. GetGlobalString`
- Get a global string with the specified identifier
- This is an EXTREMELY restricted function.  Use only with explicit permission.
- This means if you are not Preston.  Then go see him if you're even thinking
- about using this.

- `sIdentifier`: string

<a id="setglobalboolean"></a>

## `SetGlobalBoolean(sIdentifier, nValue)` - Routine 579

- `579. SetGlobalBoolean`
- SetGlobalBoolean
- This function sets the value of a global boolean (TRUE or FALSE) scripting variable.

- `sIdentifier`: string
- `nValue`: int

<a id="setglobalfadein"></a>

## `SetGlobalFadeIn(fWait, fLength, fR, fG, fB)` - Routine 719

- `719. SetGlobalFadeIn`
- Sets a Fade In that starts after fWait seconds and fades for fLength Seconds.
- The Fade will be from a color specified by the RGB values fR, fG, and fB.
- Note that fR, fG, and fB are normalized values.
- The default values are an immediate cut in from black.

- `fWait`: float (default: `0.0`)
- `fLength`: float (default: `0.0`)
- `fR`: float (default: `0.0`)
- `fG`: float (default: `0.0`)
- `fB`: float (default: `0.0`)

<a id="setglobalfadeout"></a>

## `SetGlobalFadeOut(fWait, fLength, fR, fG, fB)` - Routine 720

- `720. SetGlobalFadeOut`
- Sets a Fade Out that starts after fWait seconds and fades for fLength Seconds.
- The Fade will be to a color specified by the RGB values fR, fG, and fB.
- Note that fR, fG, and fB are normalized values.
- The default values are an immediate cut to from black.

- `fWait`: float (default: `0.0`)
- `fLength`: float (default: `0.0`)
- `fR`: float (default: `0.0`)
- `fG`: float (default: `0.0`)
- `fB`: float (default: `0.0`)

<a id="setgloballocation"></a>

## `SetGlobalLocation(sIdentifier, lValue)` - Routine 693

- `693. SetGlobalLocation`
- SetGlobalLocation
- This function sets the a global location scripting variable.

- `sIdentifier`: string
- `lValue`: location

<a id="setglobalnumber"></a>

## `SetGlobalNumber(sIdentifier, nValue)` - Routine 581

- `581. SetGlobalNumber`
- SetGlobalNumber
- This function sets the value of a global number (-128 to +127) scripting variable.

- `sIdentifier`: string
- `nValue`: int

<a id="setglobalstring"></a>

## `SetGlobalString(sIdentifier, sValue)` - Routine 160

- `160. SetGlobalString`
- Sets a global string with the specified identifier.  This is an EXTREMELY
- restricted function - do not use without expilicit permission.
- This means if you are not Preston.  Then go see him if you're even thinking
- about using this.

- `sIdentifier`: string
- `sValue`: string

