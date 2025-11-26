# Module and Area Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="getarea"></a>

## `GetArea(oTarget)` - Routine 24

- `24. GetArea`
- Get the area that oTarget is currently in
- - Return value on error: OBJECT_INVALID

- `oTarget`: object

<a id="getareaunescapable"></a>

## `GetAreaUnescapable()` - Routine 15

- `15. GetAreaUnescapable`
- Returns whether the current area is escapable or not
- TRUE means you can not escape the area
- FALSE means you can escape the area

<a id="getfirstobjectinarea"></a>

## `GetFirstObjectInArea(oArea, nObjectFilter)` - Routine 93

- `93. GetFirstObjectInArea`
- Get the first object in oArea.
- If no valid area is specified, it will use the caller's area.
- - oArea
- - nObjectFilter: OBJECT_TYPE_*
- - Return value on error: OBJECT_INVALID

- `oArea`: object
- `nObjectFilter`: int (default: `1`)

<a id="getmodule"></a>

## `GetModule()` - Routine 242

- `242. GetModule`
- Get the module.
- - Return value on error: OBJECT_INVALID

<a id="getmodulefilename"></a>

## `GetModuleFileName()` - Routine 210

- `210. GetModuleFileName`
- Gets the actual file name of the current module

<a id="getmodulename"></a>

## `GetModuleName()` - Routine 561

- `561. GetModuleName`
- Get the module's name in the language of the server that's running it.
- - If there is no entry for the language of the server, it will return an
- empty string

<a id="getnextobjectinarea"></a>

## `GetNextObjectInArea(oArea, nObjectFilter)` - Routine 94

- `94. GetNextObjectInArea`
- Get the next object in oArea.
- If no valid area is specified, it will use the caller's area.
- - oArea
- - nObjectFilter: OBJECT_TYPE_*
- - Return value on error: OBJECT_INVALID

- `oArea`: object
- `nObjectFilter`: int (default: `1`)

<a id="setareafogcolor"></a>

## `SetAreaFogColor(oArea, fRed, fGreen, fBlue)` - Routine 746

- `746. SetAreaFogColor`
- SetAreaFogColor
- Set the fog color for the area oArea.

- `oArea`: object
- `fRed`: float
- `fGreen`: float
- `fBlue`: float

<a id="setareatransitionbmp"></a>

## `SetAreaTransitionBMP(nPredefinedAreaTransition, sCustomAreaTransitionBMP)` - Routine 203

- `203. SetAreaTransitionBMP`
- Set the transition bitmap of a player; this should only be called in area
- transition scripts. This action should be run by the person "clicking" the
- area transition via AssignCommand.
- - nPredefinedAreaTransition:
- -> To use a predefined area transition bitmap, use one of AREA_TRANSITION_*

- `nPredefinedAreaTransition`: int
- `sCustomAreaTransitionBMP`: string (default: ``)

<a id="setareaunescapable"></a>

## `SetAreaUnescapable(bUnescapable)` - Routine 14

- `14. SetAreaUnescapable`
- Sets whether the current area is escapable or not
- TRUE means you can not escape the area
- FALSE means you can escape the area

- `bUnescapable`: int

<a id="startnewmodule"></a>

## `StartNewModule(sModuleName, sWayPoint, sMovie1, sMovie2, sMovie3, sMovie4, sMovie5, sMovie6)` - Routine 509

- `509. StartNewModule`
- Shut down the currently loaded module and start a new one (moving all
- currently-connected players to the starting point.

- `sModuleName`: string
- `sWayPoint`: string (default: ``)
- `sMovie1`: string (default: ``)
- `sMovie2`: string (default: ``)
- `sMovie3`: string (default: ``)
- `sMovie4`: string (default: ``)
- `sMovie5`: string (default: ``)
- `sMovie6`: string (default: ``)

