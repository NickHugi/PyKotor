# Sound and Music Functions

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="ambientsoundchangeday"></a>

## `AmbientSoundChangeDay(oArea, nTrack)` - Routine 435

- `435. AmbientSoundChangeDay`
- Change the ambient day track for oArea to nTrack.
- - oArea
- - nTrack

- `oArea`: object
- `nTrack`: int

<a id="ambientsoundchangenight"></a>

## `AmbientSoundChangeNight(oArea, nTrack)` - Routine 436

- `436. AmbientSoundChangeNight`
- Change the ambient night track for oArea to nTrack.
- - oArea
- - nTrack

- `oArea`: object
- `nTrack`: int

<a id="ambientsoundplay"></a>

## `AmbientSoundPlay(oArea)` - Routine 433

- `433. AmbientSoundPlay`
- Play the ambient sound for oArea.

- `oArea`: object

<a id="ambientsoundsetdayvolume"></a>

## `AmbientSoundSetDayVolume(oArea, nVolume)` - Routine 567

- `567. AmbientSoundSetDayVolume`
- Set the ambient day volume for oArea to nVolume.
- - oArea
- - nVolume: 0 - 100

- `oArea`: object
- `nVolume`: int

<a id="ambientsoundsetnightvolume"></a>

## `AmbientSoundSetNightVolume(oArea, nVolume)` - Routine 568

- `568. AmbientSoundSetNightVolume`
- Set the ambient night volume for oArea to nVolume.
- - oArea
- - nVolume: 0 - 100

- `oArea`: object
- `nVolume`: int

<a id="ambientsoundstop"></a>

## `AmbientSoundStop(oArea)` - Routine 434

- `434. AmbientSoundStop`
- Stop the ambient sound for oArea.

- `oArea`: object

<a id="displayfeedbacktext"></a>

## `DisplayFeedBackText(oCreature, nTextConstant)` - Routine 366

- `366. DisplayFeedBackText`
- displays a feed back string for the object spicified and the constant
- repersents the string to be displayed see:FeedBackText.2da

- `oCreature`: object
- `nTextConstant`: int

<a id="getisplayableracialtype"></a>

## `GetIsPlayableRacialType(oCreature)` - Routine 312

- `312. GetIsPlayableRacialType`
- - Returns TRUE if oCreature is of a playable racial type.

- `oCreature`: object

<a id="getstrrefsoundduration"></a>

## `GetStrRefSoundDuration(nStrRef)` - Routine 571

- `571. GetStrRefSoundDuration`
- Get the duration (in seconds) of the sound attached to nStrRef
- - Returns 0.0f if no duration is stored or if no sound is attached

- `nStrRef`: int

<a id="ismovieplaying"></a>

## `IsMoviePlaying()` - Routine 768

- `768. IsMoviePlaying`
- Checks if a movie is currently playing.

<a id="musicbackgroundchangeday"></a>

## `MusicBackgroundChangeDay(oArea, nTrack)` - Routine 428

- `428. MusicBackgroundChangeDay`
- Change the background day track for oArea to nTrack.
- - oArea
- - nTrack

- `oArea`: object
- `nTrack`: int

<a id="musicbackgroundchangenight"></a>

## `MusicBackgroundChangeNight(oArea, nTrack)` - Routine 429

- `429. MusicBackgroundChangeNight`
- Change the background night track for oArea to nTrack.
- - oArea
- - nTrack

- `oArea`: object
- `nTrack`: int

<a id="musicbackgroundgetbattletrack"></a>

## `MusicBackgroundGetBattleTrack(oArea)` - Routine 569

- `569. MusicBackgroundGetBattleTrack`
- Get the Battle Track for oArea.

- `oArea`: object

<a id="musicbackgroundgetdaytrack"></a>

## `MusicBackgroundGetDayTrack(oArea)` - Routine 558

- `558. MusicBackgroundGetDayTrack`
- Get the Day Track for oArea.

- `oArea`: object

<a id="musicbackgroundgetnighttrack"></a>

## `MusicBackgroundGetNightTrack(oArea)` - Routine 559

- `559. MusicBackgroundGetNightTrack`
- Get the Night Track for oArea.

- `oArea`: object

<a id="musicbackgroundplay"></a>

## `MusicBackgroundPlay(oArea)` - Routine 425

- `425. MusicBackgroundPlay`
- Play the background music for oArea.

- `oArea`: object

<a id="musicbackgroundsetdelay"></a>

## `MusicBackgroundSetDelay(oArea, nDelay)` - Routine 427

- `427. MusicBackgroundSetDelay`
- Set the delay for the background music for oArea.
- - oArea
- - nDelay: delay in milliseconds

- `oArea`: object
- `nDelay`: int

<a id="musicbackgroundstop"></a>

## `MusicBackgroundStop(oArea)` - Routine 426

- `426. MusicBackgroundStop`
- Stop the background music for oArea.

- `oArea`: object

<a id="musicbattlechange"></a>

## `MusicBattleChange(oArea, nTrack)` - Routine 432

- `432. MusicBattleChange`
- Change the battle track for oArea.
- - oArea
- - nTrack

- `oArea`: object
- `nTrack`: int

<a id="musicbattleplay"></a>

## `MusicBattlePlay(oArea)` - Routine 430

- `430. MusicBattlePlay`
- Play the battle music for oArea.

- `oArea`: object

<a id="musicbattlestop"></a>

## `MusicBattleStop(oArea)` - Routine 431

- `431. MusicBattleStop`
- Stop the battle music for oArea.

- `oArea`: object

<a id="playanimation"></a>

## `PlayAnimation(nAnimation, fSpeed, fSeconds)` - Routine 300

- `300. PlayAnimation`
- Play nAnimation immediately.
- - nAnimation: ANIMATION_*
- - fSpeed
- - fSeconds: Duration of the animation (this is not used for Fire and
- Forget animations) If a time of -1.0f is specified for a looping animation

- `nAnimation`: int
- `fSpeed`: float (default: `1.0`)
- `fSeconds`: float (default: `0.0`)

<a id="playmovie"></a>

## `PlayMovie(sMovie)` - Routine 733

- `733. PlayMovie`
- Playes a Movie.

- `sMovie`: string

<a id="playmoviequeue"></a>

## `PlayMovieQueue(bAllowSeparateSkips)` - Routine 770

- `770. PlayMovieQueue`
- Plays the movies that have been added to the queue by QueueMovie
- If bAllowSeparateSkips is TRUE, hitting escape to cancel a movie only
- cancels out of the currently playing movie rather than the entire queue
- of movies (assuming the currently playing movie is flagged as skippable).
- If bAllowSeparateSkips is FALSE, the entire movie queue will be cancelled

- `bAllowSeparateSkips`: int

<a id="playpazaak"></a>

## `PlayPazaak(nOpponentPazaakDeck, sEndScript, nMaxWager, bShowTutorial, oOpponent)` - Routine 364

- `364. PlayPazaak`
- Starts a game of pazaak.
- - nOpponentPazaakDeck: Index into PazaakDecks.2da; specifies which deck the opponent will use.
- - sEndScript: Script to be run when game finishes.
- - nMaxWager: Max player wager.  If <= 0, the player's credits won't be modified by the result of the game and the wager screen will not show up.
- - bShowTutorial: Plays in tutorial mode (nMaxWager should be 0).

- `nOpponentPazaakDeck`: int
- `sEndScript`: string
- `nMaxWager`: int
- `bShowTutorial`: int (default: `0`)
- `oOpponent`: object

<a id="playroomanimation"></a>

## `PlayRoomAnimation(sRoom, nAnimation)` - Routine 738

- `738. PlayRoomAnimation`
- PlayRoomAnimation
- Plays a looping animation on a room

- `sRoom`: string
- `nAnimation`: int

<a id="playrumblepattern"></a>

## `PlayRumblePattern(nPattern)` - Routine 370

- `370. PlayRumblePattern`
- PlayRumblePattern
- Starts a defined rumble pattern playing

- `nPattern`: int

<a id="playsound"></a>

## `PlaySound(sSoundName)` - Routine 46

- `46. PlaySound`
- Play sSoundName
- - sSoundName: TBD - SS

- `sSoundName`: string

<a id="setmusicvolume"></a>

## `SetMusicVolume(fVolume)` - Routine 765

- `765. SetMusicVolume`
- NEVER USE THIS!

- `fVolume`: float (default: `1.0`)

<a id="soundobjectfadeandstop"></a>

## `SoundObjectFadeAndStop(oSound, fSeconds)` - Routine 745

- `745. SoundObjectFadeAndStop`
- SoundObjectFadeAndStop
- Fades a sound object for 'fSeconds' and then stops it.

- `oSound`: object
- `fSeconds`: float

<a id="soundobjectgetfixedvariance"></a>

## `SoundObjectGetFixedVariance(oSound)` - Routine 188

- `188. SoundObjectGetFixedVariance`
- Gets the constant variance at which to play the sound object

- `oSound`: object

<a id="soundobjectgetpitchvariance"></a>

## `SoundObjectGetPitchVariance(oSound)` - Routine 689

- `689. SoundObjectGetPitchVariance`
- Gets the pitch variance of a placeable sound object

- `oSound`: object

<a id="soundobjectgetvolume"></a>

## `SoundObjectGetVolume(oSound)` - Routine 691

- `691. SoundObjectGetVolume`
- Gets the volume of a placeable sound object

- `oSound`: object

<a id="soundobjectplay"></a>

## `SoundObjectPlay(oSound)` - Routine 413

- `413. SoundObjectPlay`
- Play oSound.

- `oSound`: object

<a id="soundobjectsetfixedvariance"></a>

## `SoundObjectSetFixedVariance(oSound, fFixedVariance)` - Routine 124

- `124. SoundObjectSetFixedVariance`
- Sets the constant variance at which to play the sound object
- This variance is a multiplier of the original sound

- `oSound`: object
- `fFixedVariance`: float

<a id="soundobjectsetpitchvariance"></a>

## `SoundObjectSetPitchVariance(oSound, fVariance)` - Routine 690

- `690. SoundObjectSetPitchVariance`
- Sets the pitch variance of a placeable sound object

- `oSound`: object
- `fVariance`: float

<a id="soundobjectsetposition"></a>

## `SoundObjectSetPosition(oSound, vPosition)` - Routine 416

- `416. SoundObjectSetPosition`
- Set the position of oSound.

- `oSound`: object
- `vPosition`: vector

<a id="soundobjectsetvolume"></a>

## `SoundObjectSetVolume(oSound, nVolume)` - Routine 415

- `415. SoundObjectSetVolume`
- Set the volume of oSound.
- - oSound
- - nVolume: 0-127

- `oSound`: object
- `nVolume`: int

<a id="soundobjectstop"></a>

## `SoundObjectStop(oSound)` - Routine 414

- `414. SoundObjectStop`
- Stop playing oSound.

- `oSound`: object

<a id="swmg_getsoundfrequency"></a>

## `SWMG_GetSoundFrequency(oFollower, nSound)` - Routine 683

- `683. SWMG_GetSoundFrequency`
- Gets the frequency of a trackfollower sound

- `oFollower`: object
- `nSound`: int

<a id="swmg_getsoundfrequencyisrandom"></a>

## `SWMG_GetSoundFrequencyIsRandom(oFollower, nSound)` - Routine 685

- `685. SWMG_GetSoundFrequencyIsRandom`
- Gets whether the frequency of a trackfollower sound is using the random model

- `oFollower`: object
- `nSound`: int

<a id="swmg_getsoundvolume"></a>

## `SWMG_GetSoundVolume(oFollower, nSound)` - Routine 687

- `687. SWMG_GetSoundVolume`
- Gets the volume of a trackfollower sound

- `oFollower`: object
- `nSound`: int

<a id="swmg_playanimation"></a>

## `SWMG_PlayAnimation(oObject, sAnimName, bLooping, bQueue, bOverlay)` - Routine 586

- `586. SWMG_PlayAnimation`
- plays an animation on an object
- SWMG_PlayAnimation

- `oObject`: object
- `sAnimName`: string
- `bLooping`: int (default: `1`)
- `bQueue`: int (default: `0`)
- `bOverlay`: int (default: `0`)

<a id="swmg_setsoundfrequency"></a>

## `SWMG_SetSoundFrequency(oFollower, nSound, nFrequency)` - Routine 684

- `684. SWMG_SetSoundFrequency`
- Sets the frequency of a trackfollower sound

- `oFollower`: object
- `nSound`: int
- `nFrequency`: int

<a id="swmg_setsoundfrequencyisrandom"></a>

## `SWMG_SetSoundFrequencyIsRandom(oFollower, nSound, bIsRandom)` - Routine 686

- `686. SWMG_SetSoundFrequencyIsRandom`
- Sets whether the frequency of a trackfollower sound is using the random model

- `oFollower`: object
- `nSound`: int
- `bIsRandom`: int

<a id="swmg_setsoundvolume"></a>

## `SWMG_SetSoundVolume(oFollower, nSound, nVolume)` - Routine 688

- `688. SWMG_SetSoundVolume`
- Sets the volume of a trackfollower sound

- `oFollower`: object
- `nSound`: int
- `nVolume`: int

<!-- SHARED_FUNCTIONS_END -->

