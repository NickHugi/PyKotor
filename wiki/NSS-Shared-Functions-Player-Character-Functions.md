# Player Character Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="dosingleplayerautosave"></a>

## `DoSinglePlayerAutoSave()` - Routine 512

- `512. DoSinglePlayerAutoSave`
- Only if we are in a single player game, AutoSave the game.

<a id="exploreareaforplayer"></a>

## `ExploreAreaForPlayer(oArea, oPlayer)` - Routine 403

- `403. ExploreAreaForPlayer`
- Expose the entire map of oArea to oPlayer.

- `oArea`: object
- `oPlayer`: object

<a id="getispc"></a>

## `GetIsPC(oCreature)` - Routine 217

- `217. GetIsPC`
- - Returns TRUE if oCreature is a Player Controlled character.

- `oCreature`: object

<a id="getlastplayerdied"></a>

## `GetLastPlayerDied()` - Routine 291

- `291. GetLastPlayerDied`
- Use this in an OnPlayerDeath module script to get the last player that died.

<a id="getlastplayerdying"></a>

## `GetLastPlayerDying()` - Routine 410

- `410. GetLastPlayerDying`
- Use this in an OnPlayerDying module script to get the last player who is dying.

<a id="getpcspeaker"></a>

## `GetPCSpeaker()` - Routine 238

- `238. GetPCSpeaker`
- Get the PC that is involved in the conversation.
- - Returns OBJECT_INVALID on error.

<a id="getplayerrestrictmode"></a>

## `GetPlayerRestrictMode(oObject)` - Routine 83

- `83. GetPlayerRestrictMode`
- GetPlayerRestrictMode
- returns the current player 'restricted' mode

- `oObject`: object

<a id="setplayerrestrictmode"></a>

## `SetPlayerRestrictMode(bRestrict)` - Routine 58

- `58. SetPlayerRestrictMode`
- SetPlayerRestrictMode
- Sets whether the player is currently in 'restricted' mode

- `bRestrict`: int

<a id="swmg_getplayer"></a>

## `SWMG_GetPlayer()` - Routine 611

- `611. SWMG_GetPlayer`
- SWMG_GetPlayer

<a id="swmg_getplayeraccelerationpersecond"></a>

## `SWMG_GetPlayerAccelerationPerSecond()` - Routine 645

- `645. SWMG_GetPlayerAccelerationPerSecond`
- SWMG_GetPlayerAccelerationPerSecond

<a id="swmg_getplayerinvincibility"></a>

## `SWMG_GetPlayerInvincibility()` - Routine 642

- `642. SWMG_GetPlayerInvincibility`
- SWMG_GetPlayerInvincibility

<a id="swmg_getplayermaxspeed"></a>

## `SWMG_GetPlayerMaxSpeed()` - Routine 667

- `667. SWMG_GetPlayerMaxSpeed`
- GetPlayerMaxSpeed
- This returns the player character's max speed

<a id="swmg_getplayerminspeed"></a>

## `SWMG_GetPlayerMinSpeed()` - Routine 644

- `644. SWMG_GetPlayerMinSpeed`
- SWMG_GetPlayerMinSpeed

<a id="swmg_getplayeroffset"></a>

## `SWMG_GetPlayerOffset()` - Routine 641

- `641. SWMG_GetPlayerOffset`
- SWMG_GetPlayerOffset
- returns a vector with the player rotation for rotation minigames
- returns a vector with the player translation for translation minigames

<a id="swmg_getplayerorigin"></a>

## `SWMG_GetPlayerOrigin()` - Routine 655

- `655. SWMG_GetPlayerOrigin`
- SWMG_GetPlayerOrigin

<a id="swmg_getplayerspeed"></a>

## `SWMG_GetPlayerSpeed()` - Routine 643

- `643. SWMG_GetPlayerSpeed`
- SWMG_GetPlayerSpeed

<a id="swmg_getplayertunnelinfinite"></a>

## `SWMG_GetPlayerTunnelInfinite()` - Routine 717

- `717. SWMG_GetPlayerTunnelInfinite`
- Gets whether each of the dimensions is infinite

<a id="swmg_getplayertunnelneg"></a>

## `SWMG_GetPlayerTunnelNeg()` - Routine 653

- `653. SWMG_GetPlayerTunnelNeg`
- SWMG_GetPlayerTunnelNeg

<a id="swmg_getplayertunnelpos"></a>

## `SWMG_GetPlayerTunnelPos()` - Routine 646

- `646. SWMG_GetPlayerTunnelPos`
- SWMG_GetPlayerTunnelPos

<a id="swmg_isplayer"></a>

## `SWMG_IsPlayer(oid)` - Routine 600

- `600. SWMG_IsPlayer`
- SWMG_IsPlayer

- `oid`: object

<a id="swmg_setplayeraccelerationpersecond"></a>

## `SWMG_SetPlayerAccelerationPerSecond(fAPS)` - Routine 651

- `651. SWMG_SetPlayerAccelerationPerSecond`
- SWMG_SetPlayerAccelerationPerSecond

- `fAPS`: float

<a id="swmg_setplayerinvincibility"></a>

## `SWMG_SetPlayerInvincibility(fInvincibility)` - Routine 648

- `648. SWMG_SetPlayerInvincibility`
- SWMG_SetPlayerInvincibility

- `fInvincibility`: float

<a id="swmg_setplayermaxspeed"></a>

## `SWMG_SetPlayerMaxSpeed(fMaxSpeed)` - Routine 668

- `668. SWMG_SetPlayerMaxSpeed`
- SetPlayerMaxSpeed
- This sets the player character's max speed

- `fMaxSpeed`: float

<a id="swmg_setplayerminspeed"></a>

## `SWMG_SetPlayerMinSpeed(fMinSpeed)` - Routine 650

- `650. SWMG_SetPlayerMinSpeed`
- SWMG_SetPlayerMinSpeed

- `fMinSpeed`: float

<a id="swmg_setplayeroffset"></a>

## `SWMG_SetPlayerOffset(vOffset)` - Routine 647

- `647. SWMG_SetPlayerOffset`
- SWMG_SetPlayerOffset

- `vOffset`: vector

<a id="swmg_setplayerorigin"></a>

## `SWMG_SetPlayerOrigin(vOrigin)` - Routine 656

- `656. SWMG_SetPlayerOrigin`
- SWMG_SetPlayerOrigin

- `vOrigin`: vector

<a id="swmg_setplayerspeed"></a>

## `SWMG_SetPlayerSpeed(fSpeed)` - Routine 649

- `649. SWMG_SetPlayerSpeed`
- SWMG_SetPlayerSpeed

- `fSpeed`: float

<a id="swmg_setplayertunnelinfinite"></a>

## `SWMG_SetPlayerTunnelInfinite(vInfinite)` - Routine 718

- `718. SWMG_SetPlayerTunnelInfinite`
- Sets whether each of the dimensions is infinite

- `vInfinite`: vector

<a id="swmg_setplayertunnelneg"></a>

## `SWMG_SetPlayerTunnelNeg(vTunnel)` - Routine 654

- `654. SWMG_SetPlayerTunnelNeg`
- SWMG_SetPlayerTunnelNeg

- `vTunnel`: vector

<a id="swmg_setplayertunnelpos"></a>

## `SWMG_SetPlayerTunnelPos(vTunnel)` - Routine 652

- `652. SWMG_SetPlayerTunnelPos`
- SWMG_SetPlayerTunnelPos

- `vTunnel`: vector

