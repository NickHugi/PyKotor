# KotOR NSS File Format Documentation

NSS (NWScript Source) files contain human-readable NWScript source code that compiles to [NCS bytecode](NCS-File-Format). The `nwscript.nss` file defines all engine-exposed functions and constants available to scripts. KotOR 1 and KotOR 2 each have their own `nwscript.nss` with game-specific functions and constants.

## Table of Contents

<!-- TOC_START -->
- [KotOR NSS File Format Documentation](#kotor-nss-file-format-documentation)
  - [Table of Contents](#table-of-contents)
  - [PyKotor Implementation](#pykotor-implementation)
    - [Compilation Integration](#compilation-integration)
    - [Data Structures](#data-structures)
  - [Shared Functions (K1 \& TSL)](#shared-functions-k1--tsl)
    - [Abilities and Stats](#abilities-and-stats)
      - [`GetAbilityModifier(nAbility, oCreature)` - Routine 331](#getabilitymodifiernability-ocreature---routine-331)
      - [`GetAbilityScore(oCreature, nAbilityType)` - Routine 139](#getabilityscoreocreature-nabilitytype---routine-139)
      - [`GetNPCSelectability(nNPC)` - Routine 709](#getnpcselectabilitynnpc---routine-709)
      - [`SetNPCSelectability(nNPC, nSelectability)` - Routine 708](#setnpcselectabilitynnpc-nselectability---routine-708)
      - [`SWMG_StartInvulnerability(oFollower)` - Routine 666](#swmg_startinvulnerabilityofollower---routine-666)
    - [Actions](#actions)
      - [`ActionAttack(oAttackee, bPassive)` - Routine 37](#actionattackoattackee-bpassive---routine-37)
      - [`ActionBarkString(strRef)` - Routine 700](#actionbarkstringstrref---routine-700)
      - [`ActionCastFakeSpellAtLocation(nSpell, lTarget, nProjectilePathType)` - Routine 502](#actioncastfakespellatlocationnspell-ltarget-nprojectilepathtype---routine-502)
      - [`ActionCastFakeSpellAtObject(nSpell, oTarget, nProjectilePathType)` - Routine 501](#actioncastfakespellatobjectnspell-otarget-nprojectilepathtype---routine-501)
      - [`ActionCastSpellAtLocation(nSpell, lTargetLocation, nMetaMagic, bCheat, nProjectilePathType, bInstantSpell)` - Routine 234](#actioncastspellatlocationnspell-ltargetlocation-nmetamagic-bcheat-nprojectilepathtype-binstantspell---routine-234)
      - [`ActionCastSpellAtObject(nSpell, oTarget, nMetaMagic, bCheat, nDomainLevel, nProjectilePathType, bInstantSpell)` - Routine 48](#actioncastspellatobjectnspell-otarget-nmetamagic-bcheat-ndomainlevel-nprojectilepathtype-binstantspell---routine-48)
      - [`ActionCloseDoor(oDoor)` - Routine 44](#actionclosedoorodoor---routine-44)
      - [`ActionDoCommand(aActionToDo)` - Routine 294](#actiondocommandaactiontodo---routine-294)
      - [`ActionEquipItem(oItem, nInventorySlot, bInstant)` - Routine 32](#actionequipitemoitem-ninventoryslot-binstant---routine-32)
      - [`ActionEquipMostDamagingMelee(oVersus, bOffHand)` - Routine 399](#actionequipmostdamagingmeleeoversus-boffhand---routine-399)
      - [`ActionEquipMostDamagingRanged(oVersus)` - Routine 400](#actionequipmostdamagingrangedoversus---routine-400)
      - [`ActionFollowLeader()` - Routine 730](#actionfollowleader---routine-730)
      - [`ActionForceFollowObject(oFollow, fFollowDistance)` - Routine 167](#actionforcefollowobjectofollow-ffollowdistance---routine-167)
      - [`ActionForceMoveToLocation(lDestination, bRun, fTimeout)` - Routine 382](#actionforcemovetolocationldestination-brun-ftimeout---routine-382)
      - [`ActionForceMoveToObject(oMoveTo, bRun, fRange, fTimeout)` - Routine 383](#actionforcemovetoobjectomoveto-brun-frange-ftimeout---routine-383)
      - [`ActionGiveItem(oItem, oGiveTo)` - Routine 135](#actiongiveitemoitem-ogiveto---routine-135)
      - [`ActionInteractObject(oPlaceable)` - Routine 329](#actioninteractobjectoplaceable---routine-329)
      - [`ActionJumpToLocation(lLocation)` - Routine 214](#actionjumptolocationllocation---routine-214)
      - [`ActionJumpToObject(oToJumpTo, bWalkStraightLineToPoint)` - Routine 196](#actionjumptoobjectotojumpto-bwalkstraightlinetopoint---routine-196)
      - [`ActionLockObject(oTarget)` - Routine 484](#actionlockobjectotarget---routine-484)
      - [`ActionMoveAwayFromLocation(lMoveAwayFrom, bRun, fMoveAwayRange)` - Routine 360](#actionmoveawayfromlocationlmoveawayfrom-brun-fmoveawayrange---routine-360)
      - [`ActionMoveAwayFromObject(oFleeFrom, bRun, fMoveAwayRange)` - Routine 23](#actionmoveawayfromobjectofleefrom-brun-fmoveawayrange---routine-23)
      - [`ActionMoveToLocation(lDestination, bRun)` - Routine 21](#actionmovetolocationldestination-brun---routine-21)
      - [`ActionMoveToObject(oMoveTo, bRun, fRange)` - Routine 22](#actionmovetoobjectomoveto-brun-frange---routine-22)
      - [`ActionOpenDoor(oDoor)` - Routine 43](#actionopendoorodoor---routine-43)
      - [`ActionPauseConversation()` - Routine 205](#actionpauseconversation---routine-205)
      - [`ActionPickUpItem(oItem)` - Routine 34](#actionpickupitemoitem---routine-34)
      - [`ActionPlayAnimation(nAnimation, fSpeed, fDurationSeconds)` - Routine 40](#actionplayanimationnanimation-fspeed-fdurationseconds---routine-40)
      - [`ActionPutDownItem(oItem)` - Routine 35](#actionputdownitemoitem---routine-35)
      - [`ActionRandomWalk()` - Routine 20](#actionrandomwalk---routine-20)
      - [`ActionResumeConversation()` - Routine 206](#actionresumeconversation---routine-206)
      - [`ActionSpeakString(sStringToSpeak, nTalkVolume)` - Routine 39](#actionspeakstringsstringtospeak-ntalkvolume---routine-39)
      - [`ActionSpeakStringByStrRef(nStrRef, nTalkVolume)` - Routine 240](#actionspeakstringbystrrefnstrref-ntalkvolume---routine-240)
      - [`ActionStartConversation(oObjectToConverse, sDialogResRef, bPrivateConversation, nConversationType, bIgnoreStartRange, sNameObjectToIgnore1, sNameObjectToIgnore2, sNameObjectToIgnore3, sNameObjectToIgnore4, sNameObjectToIgnore5, sNameObjectToIgnore6, bUseLeader)` - Routine 204](#actionstartconversationoobjecttoconverse-sdialogresref-bprivateconversation-nconversationtype-bignorestartrange-snameobjecttoignore1-snameobjecttoignore2-snameobjecttoignore3-snameobjecttoignore4-snameobjecttoignore5-snameobjecttoignore6-buseleader---routine-204)
      - [`ActionSurrenderToEnemies()` - Routine 379](#actionsurrendertoenemies---routine-379)
      - [`ActionTakeItem(oItem, oTakeFrom)` - Routine 136](#actiontakeitemoitem-otakefrom---routine-136)
      - [`ActionUnequipItem(oItem, bInstant)` - Routine 33](#actionunequipitemoitem-binstant---routine-33)
      - [`ActionUnlockObject(oTarget)` - Routine 483](#actionunlockobjectotarget---routine-483)
      - [`ActionUseFeat(nFeat, oTarget)` - Routine 287](#actionusefeatnfeat-otarget---routine-287)
      - [`ActionUseSkill(nSkill, oTarget, nSubSkill, oItemUsed)` - Routine 288](#actionuseskillnskill-otarget-nsubskill-oitemused---routine-288)
      - [`ActionUseTalentAtLocation(tChosenTalent, lTargetLocation)` - Routine 310](#actionusetalentatlocationtchosentalent-ltargetlocation---routine-310)
      - [`ActionUseTalentOnObject(tChosenTalent, oTarget)` - Routine 309](#actionusetalentonobjecttchosentalent-otarget---routine-309)
      - [`ActionWait(fSeconds)` - Routine 202](#actionwaitfseconds---routine-202)
    - [Alignment System](#alignment-system)
      - [`AdjustAlignment(oSubject, nAlignment, nShift)` - Routine 201](#adjustalignmentosubject-nalignment-nshift---routine-201)
      - [`GetAlignmentGoodEvil(oCreature)` - Routine 127](#getalignmentgoodevilocreature---routine-127)
      - [`GetFactionAverageGoodEvilAlignment(oFactionMember)` - Routine 187](#getfactionaveragegoodevilalignmentofactionmember---routine-187)
      - [`VersusAlignmentEffect(eEffect, nLawChaos, nGoodEvil)` - Routine 355](#versusalignmenteffecteeffect-nlawchaos-ngoodevil---routine-355)
    - [Class System](#class-system)
      - [`AddMultiClass(nClassType, oSource)` - Routine 389](#addmulticlassnclasstype-osource---routine-389)
      - [`GetClassByPosition(nClassPosition, oCreature)` - Routine 341](#getclassbypositionnclassposition-ocreature---routine-341)
      - [`GetFactionMostFrequentClass(oFactionMember)` - Routine 191](#getfactionmostfrequentclassofactionmember---routine-191)
      - [`GetLevelByClass(nClassType, oCreature)` - Routine 343](#getlevelbyclassnclasstype-ocreature---routine-343)
    - [Combat Functions](#combat-functions)
      - [`CancelCombat(oidCreature)` - Routine 54](#cancelcombatoidcreature---routine-54)
      - [`CutsceneAttack(oTarget, nAnimation, nAttackResult, nDamage)` - Routine 503](#cutsceneattackotarget-nanimation-nattackresult-ndamage---routine-503)
      - [`GetAttackTarget(oCreature)` - Routine 316](#getattacktargetocreature---routine-316)
      - [`GetAttemptedAttackTarget()` - Routine 361](#getattemptedattacktarget---routine-361)
      - [`GetFirstAttacker(oCreature)` - Routine 727](#getfirstattackerocreature---routine-727)
      - [`GetGoingToBeAttackedBy(oTarget)` - Routine 211](#getgoingtobeattackedbyotarget---routine-211)
      - [`GetIsInCombat(oCreature)` - Routine 320](#getisincombatocreature---routine-320)
      - [`GetLastAttackAction(oAttacker)` - Routine 722](#getlastattackactionoattacker---routine-722)
      - [`GetLastAttacker(oAttackee)` - Routine 36](#getlastattackeroattackee---routine-36)
      - [`GetLastAttackMode(oCreature)` - Routine 318](#getlastattackmodeocreature---routine-318)
      - [`GetLastAttackResult(oAttacker)` - Routine 725](#getlastattackresultoattacker---routine-725)
      - [`GetLastAttackType(oCreature)` - Routine 317](#getlastattacktypeocreature---routine-317)
      - [`GetLastKiller()` - Routine 437](#getlastkiller---routine-437)
      - [`GetNextAttacker(oCreature)` - Routine 728](#getnextattackerocreature---routine-728)
      - [`TouchAttackMelee(oTarget, bDisplayFeedback)` - Routine 146](#touchattackmeleeotarget-bdisplayfeedback---routine-146)
      - [`TouchAttackRanged(oTarget, bDisplayFeedback)` - Routine 147](#touchattackrangedotarget-bdisplayfeedback---routine-147)
    - [Dialog and Conversation Functions](#dialog-and-conversation-functions)
      - [`BarkString(oCreature, strRef)` - Routine 671](#barkstringocreature-strref---routine-671)
      - [`BeginConversation(sResRef, oObjectToDialog)` - Routine 255](#beginconversationsresref-oobjecttodialog---routine-255)
      - [`CancelPostDialogCharacterSwitch()` - Routine 757](#cancelpostdialogcharacterswitch---routine-757)
      - [`EventConversation()` - Routine 295](#eventconversation---routine-295)
      - [`GetIsConversationActive()` - Routine 701](#getisconversationactive---routine-701)
      - [`GetIsInConversation(oObject)` - Routine 445](#getisinconversationoobject---routine-445)
      - [`GetLastConversation()` - Routine 711](#getlastconversation---routine-711)
      - [`GetLastSpeaker()` - Routine 254](#getlastspeaker---routine-254)
      - [`HoldWorldFadeInForDialog()` - Routine 760](#holdworldfadeinfordialog---routine-760)
      - [`ResetDialogState()` - Routine 749](#resetdialogstate---routine-749)
      - [`SetDialogPlaceableCamera(nCameraId)` - Routine 461](#setdialogplaceablecamerancameraid---routine-461)
      - [`SetLockHeadFollowInDialog(oObject, nValue)` - Routine 506](#setlockheadfollowindialogoobject-nvalue---routine-506)
      - [`SetLockOrientationInDialog(oObject, nValue)` - Routine 505](#setlockorientationindialogoobject-nvalue---routine-505)
      - [`SpeakOneLinerConversation(sDialogResRef, oTokenTarget)` - Routine 417](#speakonelinerconversationsdialogresref-otokentarget---routine-417)
      - [`SpeakString(sStringToSpeak, nTalkVolume)` - Routine 221](#speakstringsstringtospeak-ntalkvolume---routine-221)
    - [Effects System](#effects-system)
      - [`ActionEquipMostEffectiveArmor()` - Routine 404](#actionequipmosteffectivearmor---routine-404)
      - [`ApplyEffectAtLocation(nDurationType, eEffect, lLocation, fDuration)` - Routine 216](#applyeffectatlocationndurationtype-eeffect-llocation-fduration---routine-216)
      - [`ApplyEffectToObject(nDurationType, eEffect, oTarget, fDuration)` - Routine 220](#applyeffecttoobjectndurationtype-eeffect-otarget-fduration---routine-220)
      - [`ClearAllEffects()` - Routine 710](#clearalleffects---routine-710)
      - [`DisableVideoEffect()` - Routine 508](#disablevideoeffect---routine-508)
      - [`EffectAbilityDecrease(nAbility, nModifyBy)` - Routine 446](#effectabilitydecreasenability-nmodifyby---routine-446)
      - [`EffectAbilityIncrease(nAbilityToIncrease, nModifyBy)` - Routine 80](#effectabilityincreasenabilitytoincrease-nmodifyby---routine-80)
      - [`EffectACDecrease(nValue, nModifyType, nDamageType)` - Routine 450](#effectacdecreasenvalue-nmodifytype-ndamagetype---routine-450)
      - [`EffectACIncrease(nValue, nModifyType, nDamageType)` - Routine 115](#effectacincreasenvalue-nmodifytype-ndamagetype---routine-115)
      - [`EffectAreaOfEffect(nAreaEffectId, sOnEnterScript, sHeartbeatScript, sOnExitScript)` - Routine 171](#effectareaofeffectnareaeffectid-sonenterscript-sheartbeatscript-sonexitscript---routine-171)
      - [`EffectAssuredDeflection(nReturn)` - Routine 252](#effectassureddeflectionnreturn---routine-252)
      - [`EffectAssuredHit()` - Routine 51](#effectassuredhit---routine-51)
      - [`EffectAttackDecrease(nPenalty, nModifierType)` - Routine 447](#effectattackdecreasenpenalty-nmodifiertype---routine-447)
      - [`EffectAttackIncrease(nBonus, nModifierType)` - Routine 118](#effectattackincreasenbonus-nmodifiertype---routine-118)
      - [`EffectBeam(nBeamVisualEffect, oEffector, nBodyPart, bMissEffect)` - Routine 207](#effectbeamnbeamvisualeffect-oeffector-nbodypart-bmisseffect---routine-207)
      - [`EffectBlasterDeflectionDecrease(nChange)` - Routine 470](#effectblasterdeflectiondecreasenchange---routine-470)
      - [`EffectBlasterDeflectionIncrease(nChange)` - Routine 469](#effectblasterdeflectionincreasenchange---routine-469)
      - [`EffectBodyFuel()` - Routine 224](#effectbodyfuel---routine-224)
      - [`EffectChoke()` - Routine 159](#effectchoke---routine-159)
      - [`EffectConcealment(nPercentage)` - Routine 458](#effectconcealmentnpercentage---routine-458)
      - [`EffectConfused()` - Routine 157](#effectconfused---routine-157)
      - [`EffectCutSceneHorrified()` - Routine 754](#effectcutscenehorrified---routine-754)
      - [`EffectCutSceneParalyze()` - Routine 755](#effectcutsceneparalyze---routine-755)
      - [`EffectCutSceneStunned()` - Routine 756](#effectcutscenestunned---routine-756)
      - [`EffectDamage(nDamageAmount, nDamageType, nDamagePower)` - Routine 79](#effectdamagendamageamount-ndamagetype-ndamagepower---routine-79)
      - [`EffectDamageDecrease(nPenalty, nDamageType)` - Routine 448](#effectdamagedecreasenpenalty-ndamagetype---routine-448)
      - [`EffectDamageForcePoints(nDamage)` - Routine 372](#effectdamageforcepointsndamage---routine-372)
      - [`EffectDamageImmunityDecrease(nDamageType, nPercentImmunity)` - Routine 449](#effectdamageimmunitydecreasendamagetype-npercentimmunity---routine-449)
      - [`EffectDamageImmunityIncrease(nDamageType, nPercentImmunity)` - Routine 275](#effectdamageimmunityincreasendamagetype-npercentimmunity---routine-275)
      - [`EffectDamageIncrease(nBonus, nDamageType)` - Routine 120](#effectdamageincreasenbonus-ndamagetype---routine-120)
      - [`EffectDamageReduction(nAmount, nDamagePower, nLimit)` - Routine 119](#effectdamagereductionnamount-ndamagepower-nlimit---routine-119)
      - [`EffectDamageResistance(nDamageType, nAmount, nLimit)` - Routine 81](#effectdamageresistancendamagetype-namount-nlimit---routine-81)
      - [`EffectDamageShield(nDamageAmount, nRandomAmount, nDamageType)` - Routine 487](#effectdamageshieldndamageamount-nrandomamount-ndamagetype---routine-487)
      - [`EffectDeath(nSpectacularDeath, nDisplayFeedback)` - Routine 133](#effectdeathnspectaculardeath-ndisplayfeedback---routine-133)
      - [`EffectDisguise(nDisguiseAppearance)` - Routine 463](#effectdisguisendisguiseappearance---routine-463)
      - [`EffectDispelMagicAll(nCasterLevel)` - Routine 460](#effectdispelmagicallncasterlevel---routine-460)
      - [`EffectDispelMagicBest(nCasterLevel)` - Routine 473](#effectdispelmagicbestncasterlevel---routine-473)
      - [`EffectDroidStun()` - Routine 391](#effectdroidstun---routine-391)
      - [`EffectEntangle()` - Routine 130](#effectentangle---routine-130)
      - [`EffectForceDrain(nDamage)` - Routine 675](#effectforcedrainndamage---routine-675)
      - [`EffectForceFizzle()` - Routine 420](#effectforcefizzle---routine-420)
      - [`EffectForceJump(oTarget, nAdvanced)` - Routine 153](#effectforcejumpotarget-nadvanced---routine-153)
      - [`EffectForcePushed()` - Routine 392](#effectforcepushed---routine-392)
      - [`EffectForcePushTargeted(lCentre, nIgnoreTestDirectLine)` - Routine 269](#effectforcepushtargetedlcentre-nignoretestdirectline---routine-269)
      - [`EffectForceResistanceDecrease(nValue)` - Routine 454](#effectforceresistancedecreasenvalue---routine-454)
      - [`EffectForceResistanceIncrease(nValue)` - Routine 212](#effectforceresistanceincreasenvalue---routine-212)
      - [`EffectForceResisted(oSource)` - Routine 402](#effectforceresistedosource---routine-402)
      - [`EffectForceShield(nShield)` - Routine 459](#effectforceshieldnshield---routine-459)
      - [`EffectFrightened()` - Routine 158](#effectfrightened---routine-158)
      - [`EffectHaste()` - Routine 270](#effecthaste---routine-270)
      - [`EffectHeal(nDamageToHeal)` - Routine 78](#effecthealndamagetoheal---routine-78)
      - [`EffectHealForcePoints(nHeal)` - Routine 373](#effecthealforcepointsnheal---routine-373)
      - [`EffectHitPointChangeWhenDying(fHitPointChangePerRound)` - Routine 387](#effecthitpointchangewhendyingfhitpointchangeperround---routine-387)
      - [`EffectHorrified()` - Routine 471](#effecthorrified---routine-471)
      - [`EffectImmunity(nImmunityType)` - Routine 273](#effectimmunitynimmunitytype---routine-273)
      - [`EffectInvisibility(nInvisibilityType)` - Routine 457](#effectinvisibilityninvisibilitytype---routine-457)
      - [`EffectKnockdown()` - Routine 134](#effectknockdown---routine-134)
      - [`EffectLightsaberThrow(oTarget1, oTarget2, oTarget3, nAdvancedDamage)` - Routine 702](#effectlightsaberthrowotarget1-otarget2-otarget3-nadvanceddamage---routine-702)
      - [`EffectLinkEffects(eChildEffect, eParentEffect)` - Routine 199](#effectlinkeffectsechildeffect-eparenteffect---routine-199)
      - [`EffectMissChance(nPercentage)` - Routine 477](#effectmisschancenpercentage---routine-477)
      - [`EffectModifyAttacks(nAttacks)` - Routine 485](#effectmodifyattacksnattacks---routine-485)
      - [`EffectMovementSpeedDecrease(nPercentChange)` - Routine 451](#effectmovementspeeddecreasenpercentchange---routine-451)
      - [`EffectMovementSpeedIncrease(nNewSpeedPercent)` - Routine 165](#effectmovementspeedincreasennewspeedpercent---routine-165)
      - [`EffectParalyze()` - Routine 148](#effectparalyze---routine-148)
      - [`EffectPoison(nPoisonType)` - Routine 250](#effectpoisonnpoisontype---routine-250)
      - [`EffectPsychicStatic()` - Routine 676](#effectpsychicstatic---routine-676)
      - [`EffectRegenerate(nAmount, fIntervalSeconds)` - Routine 164](#effectregeneratenamount-fintervalseconds---routine-164)
      - [`EffectResurrection()` - Routine 82](#effectresurrection---routine-82)
      - [`EffectSavingThrowDecrease(nSave, nValue, nSaveType)` - Routine 452](#effectsavingthrowdecreasensave-nvalue-nsavetype---routine-452)
      - [`EffectSavingThrowIncrease(nSave, nValue, nSaveType)` - Routine 117](#effectsavingthrowincreasensave-nvalue-nsavetype---routine-117)
      - [`EffectSeeInvisible()` - Routine 466](#effectseeinvisible---routine-466)
      - [`EffectSkillDecrease(nSkill, nValue)` - Routine 453](#effectskilldecreasenskill-nvalue---routine-453)
      - [`EffectSkillIncrease(nSkill, nValue)` - Routine 351](#effectskillincreasenskill-nvalue---routine-351)
      - [`EffectSleep()` - Routine 154](#effectsleep---routine-154)
      - [`EffectSpellImmunity(nImmunityToSpell)` - Routine 149](#effectspellimmunitynimmunitytospell---routine-149)
      - [`EffectSpellLevelAbsorption(nMaxSpellLevelAbsorbed, nTotalSpellLevelsAbsorbed, nSpellSchool)` - Routine 472](#effectspelllevelabsorptionnmaxspelllevelabsorbed-ntotalspelllevelsabsorbed-nspellschool---routine-472)
      - [`EffectStunned()` - Routine 161](#effectstunned---routine-161)
      - [`EffectTemporaryForcePoints(nTempForce)` - Routine 156](#effecttemporaryforcepointsntempforce---routine-156)
      - [`EffectTemporaryHitpoints(nHitPoints)` - Routine 314](#effecttemporaryhitpointsnhitpoints---routine-314)
      - [`EffectTimeStop()` - Routine 467](#effecttimestop---routine-467)
      - [`EffectTrueSeeing()` - Routine 465](#effecttrueseeing---routine-465)
      - [`EffectVisualEffect(nVisualEffectId, nMissEffect)` - Routine 180](#effectvisualeffectnvisualeffectid-nmisseffect---routine-180)
      - [`EffectWhirlWind()` - Routine 703](#effectwhirlwind---routine-703)
      - [`EnableVideoEffect(nEffectType)` - Routine 508](#enablevideoeffectneffecttype---routine-508)
      - [`ExtraordinaryEffect(eEffect)` - Routine 114](#extraordinaryeffecteeffect---routine-114)
      - [`GetAreaOfEffectCreator(oAreaOfEffectObject)` - Routine 264](#getareaofeffectcreatoroareaofeffectobject---routine-264)
      - [`GetEffectCreator(eEffect)` - Routine 91](#geteffectcreatoreeffect---routine-91)
      - [`GetEffectDurationType(eEffect)` - Routine 89](#geteffectdurationtypeeeffect---routine-89)
      - [`GetEffectSpellId(eSpellEffect)` - Routine 305](#geteffectspellidespelleffect---routine-305)
      - [`GetEffectSubType(eEffect)` - Routine 90](#geteffectsubtypeeeffect---routine-90)
      - [`GetEffectType(eEffect)` - Routine 170](#geteffecttypeeeffect---routine-170)
      - [`GetFirstEffect(oCreature)` - Routine 85](#getfirsteffectocreature---routine-85)
      - [`GetHasFeatEffect(nFeat, oObject)` - Routine 543](#gethasfeateffectnfeat-oobject---routine-543)
      - [`GetHasSpellEffect(nSpell, oObject)` - Routine 304](#gethasspelleffectnspell-oobject---routine-304)
      - [`GetIsEffectValid(eEffect)` - Routine 88](#getiseffectvalideeffect---routine-88)
      - [`GetIsWeaponEffective(oVersus, bOffHand)` - Routine 422](#getisweaponeffectiveoversus-boffhand---routine-422)
      - [`GetNextEffect(oCreature)` - Routine 86](#getnexteffectocreature---routine-86)
      - [`MagicalEffect(eEffect)` - Routine 112](#magicaleffecteeffect---routine-112)
      - [`PlayVisualAreaEffect(nEffectID, lTarget)` - Routine 677](#playvisualareaeffectneffectid-ltarget---routine-677)
      - [`RemoveEffect(oCreature, eEffect)` - Routine 87](#removeeffectocreature-eeffect---routine-87)
      - [`SetEffectIcon(eEffect, nIcon)` - Routine 552](#seteffecticoneeffect-nicon---routine-552)
      - [`SupernaturalEffect(eEffect)` - Routine 113](#supernaturaleffecteeffect---routine-113)
      - [`SWMG_SetSpeedBlurEffect(bEnabled, fRatio)` - Routine 563](#swmg_setspeedblureffectbenabled-fratio---routine-563)
      - [`VersusRacialTypeEffect(eEffect, nRacialType)` - Routine 356](#versusracialtypeeffecteeffect-nracialtype---routine-356)
      - [`VersusTrapEffect(eEffect)` - Routine 357](#versustrapeffecteeffect---routine-357)
    - [Global Variables](#global-variables)
      - [`GetGlobalBoolean(sIdentifier)` - Routine 578](#getglobalbooleansidentifier---routine-578)
      - [`GetGlobalLocation(sIdentifier)` - Routine 692](#getgloballocationsidentifier---routine-692)
      - [`GetGlobalNumber(sIdentifier)` - Routine 580](#getglobalnumbersidentifier---routine-580)
      - [`GetGlobalString(sIdentifier)` - Routine 194](#getglobalstringsidentifier---routine-194)
      - [`SetGlobalBoolean(sIdentifier, nValue)` - Routine 579](#setglobalbooleansidentifier-nvalue---routine-579)
      - [`SetGlobalFadeIn(fWait, fLength, fR, fG, fB)` - Routine 719](#setglobalfadeinfwait-flength-fr-fg-fb---routine-719)
      - [`SetGlobalFadeOut(fWait, fLength, fR, fG, fB)` - Routine 720](#setglobalfadeoutfwait-flength-fr-fg-fb---routine-720)
      - [`SetGlobalLocation(sIdentifier, lValue)` - Routine 693](#setgloballocationsidentifier-lvalue---routine-693)
      - [`SetGlobalNumber(sIdentifier, nValue)` - Routine 581](#setglobalnumbersidentifier-nvalue---routine-581)
      - [`SetGlobalString(sIdentifier, sValue)` - Routine 160](#setglobalstringsidentifier-svalue---routine-160)
    - [Item Management](#item-management)
      - [`ChangeItemCost(sItem, fCostMultiplier)` - Routine 747](#changeitemcostsitem-fcostmultiplier---routine-747)
      - [`CreateItemOnFloor(sTemplate, lLocation, bUseAppearAnimation)` - Routine 766](#createitemonfloorstemplate-llocation-buseappearanimation---routine-766)
      - [`CreateItemOnObject(sItemTemplate, oTarget, nStackSize)` - Routine 31](#createitemonobjectsitemtemplate-otarget-nstacksize---routine-31)
      - [`EventActivateItem(oItem, lTarget, oTarget)` - Routine 424](#eventactivateitemoitem-ltarget-otarget---routine-424)
      - [`GetBaseItemType(oItem)` - Routine 397](#getbaseitemtypeoitem---routine-397)
      - [`GetFirstItemInInventory(oTarget)` - Routine 339](#getfirstitemininventoryotarget---routine-339)
      - [`GetInventoryDisturbItem()` - Routine 353](#getinventorydisturbitem---routine-353)
      - [`GetItemActivated()` - Routine 439](#getitemactivated---routine-439)
      - [`GetItemActivatedTarget()` - Routine 442](#getitemactivatedtarget---routine-442)
      - [`GetItemActivatedTargetLocation()` - Routine 441](#getitemactivatedtargetlocation---routine-441)
      - [`GetItemActivator()` - Routine 440](#getitemactivator---routine-440)
      - [`GetItemACValue(oItem)` - Routine 401](#getitemacvalueoitem---routine-401)
      - [`GetItemInSlot(nInventorySlot, oCreature)` - Routine 155](#getiteminslotninventoryslot-ocreature---routine-155)
      - [`GetItemPossessedBy(oCreature, sItemTag)` - Routine 30](#getitempossessedbyocreature-sitemtag---routine-30)
      - [`GetItemPossessor(oItem)` - Routine 29](#getitempossessoroitem---routine-29)
      - [`GetItemStackSize(oItem)` - Routine 138](#getitemstacksizeoitem---routine-138)
      - [`GetLastItemEquipped()` - Routine 52](#getlastitemequipped---routine-52)
      - [`GetModuleItemAcquired()` - Routine 282](#getmoduleitemacquired---routine-282)
      - [`GetModuleItemAcquiredFrom()` - Routine 283](#getmoduleitemacquiredfrom---routine-283)
      - [`GetModuleItemLost()` - Routine 292](#getmoduleitemlost---routine-292)
      - [`GetModuleItemLostBy()` - Routine 293](#getmoduleitemlostby---routine-293)
      - [`GetNextItemInInventory(oTarget)` - Routine 340](#getnextitemininventoryotarget---routine-340)
      - [`GetNumStackedItems(oItem)` - Routine 475](#getnumstackeditemsoitem---routine-475)
      - [`GetSpellCastItem()` - Routine 438](#getspellcastitem---routine-438)
      - [`GiveItem(oItem, oGiveTo)` - Routine 271](#giveitemoitem-ogiveto---routine-271)
      - [`SetItemNonEquippable(oItem, bNonEquippable)` - Routine 266](#setitemnonequippableoitem-bnonequippable---routine-266)
      - [`SetItemStackSize(oItem, nStackSize)` - Routine 150](#setitemstacksizeoitem-nstacksize---routine-150)
    - [Item Properties](#item-properties)
      - [`GetItemHasItemProperty(oItem, nProperty)` - Routine 398](#getitemhasitempropertyoitem-nproperty---routine-398)
    - [Local Variables](#local-variables)
      - [`GetLocalBoolean(oObject, nIndex)` - Routine 679](#getlocalbooleanoobject-nindex---routine-679)
      - [`GetLocalNumber(oObject, nIndex)` - Routine 681](#getlocalnumberoobject-nindex---routine-681)
      - [`SetLocalBoolean(oObject, nIndex, nValue)` - Routine 680](#setlocalbooleanoobject-nindex-nvalue---routine-680)
      - [`SetLocalNumber(oObject, nIndex, nValue)` - Routine 682](#setlocalnumberoobject-nindex-nvalue---routine-682)
    - [Module and Area Functions](#module-and-area-functions)
      - [`GetArea(oTarget)` - Routine 24](#getareaotarget---routine-24)
      - [`GetAreaUnescapable()` - Routine 15](#getareaunescapable---routine-15)
      - [`GetFirstObjectInArea(oArea, nObjectFilter)` - Routine 93](#getfirstobjectinareaoarea-nobjectfilter---routine-93)
      - [`GetModule()` - Routine 242](#getmodule---routine-242)
      - [`GetModuleFileName()` - Routine 210](#getmodulefilename---routine-210)
      - [`GetModuleName()` - Routine 561](#getmodulename---routine-561)
      - [`GetNextObjectInArea(oArea, nObjectFilter)` - Routine 94](#getnextobjectinareaoarea-nobjectfilter---routine-94)
      - [`SetAreaFogColor(oArea, fRed, fGreen, fBlue)` - Routine 746](#setareafogcoloroarea-fred-fgreen-fblue---routine-746)
      - [`SetAreaTransitionBMP(nPredefinedAreaTransition, sCustomAreaTransitionBMP)` - Routine 203](#setareatransitionbmpnpredefinedareatransition-scustomareatransitionbmp---routine-203)
      - [`SetAreaUnescapable(bUnescapable)` - Routine 14](#setareaunescapablebunescapable---routine-14)
      - [`StartNewModule(sModuleName, sWayPoint, sMovie1, sMovie2, sMovie3, sMovie4, sMovie5, sMovie6)` - Routine 509](#startnewmodulesmodulename-swaypoint-smovie1-smovie2-smovie3-smovie4-smovie5-smovie6---routine-509)
    - [Object Query and Manipulation](#object-query-and-manipulation)
      - [`CreateObject(nObjectType, sTemplate, lLocation, bUseAppearAnimation)` - Routine 243](#createobjectnobjecttype-stemplate-llocation-buseappearanimation---routine-243)
      - [`DestroyObject(oDestroy, fDelay, bNoFade, fDelayUntilFade)` - Routine 241](#destroyobjectodestroy-fdelay-bnofade-fdelayuntilfade---routine-241)
      - [`GetNearestCreature(nFirstCriteriaType, nFirstCriteriaValue, oTarget, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 38](#getnearestcreaturenfirstcriteriatype-nfirstcriteriavalue-otarget-nnth-nsecondcriteriatype-nsecondcriteriavalue-nthirdcriteriatype-nthirdcriteriavalue---routine-38)
      - [`GetNearestCreatureToLocation(nFirstCriteriaType, nFirstCriteriaValue, lLocation, nNth, nSecondCriteriaType, nSecondCriteriaValue, nThirdCriteriaType, nThirdCriteriaValue)` - Routine 226](#getnearestcreaturetolocationnfirstcriteriatype-nfirstcriteriavalue-llocation-nnth-nsecondcriteriatype-nsecondcriteriavalue-nthirdcriteriatype-nthirdcriteriavalue---routine-226)
      - [`GetNearestObject(nObjectType, oTarget, nNth)` - Routine 227](#getnearestobjectnobjecttype-otarget-nnth---routine-227)
      - [`GetNearestObjectByTag(sTag, oTarget, nNth)` - Routine 229](#getnearestobjectbytagstag-otarget-nnth---routine-229)
      - [`GetNearestObjectToLocation(nObjectType, lLocation, nNth)` - Routine 228](#getnearestobjecttolocationnobjecttype-llocation-nnth---routine-228)
      - [`GetNearestTrapToObject(oTarget, nTrapDetected)` - Routine 488](#getnearesttraptoobjectotarget-ntrapdetected---routine-488)
      - [`GetObjectByTag(sTag, nNth)` - Routine 200](#getobjectbytagstag-nnth---routine-200)
      - [`GetObjectHeard(oTarget, oSource)` - Routine 290](#getobjectheardotarget-osource---routine-290)
      - [`GetObjectSeen(oTarget, oSource)` - Routine 289](#getobjectseenotarget-osource---routine-289)
      - [`GetObjectType(oTarget)` - Routine 106](#getobjecttypeotarget---routine-106)
      - [`GetSpellTargetObject()` - Routine 47](#getspelltargetobject---routine-47)
      - [`SWMG_GetObjectByName(sName)` - Routine 585](#swmg_getobjectbynamesname---routine-585)
      - [`SWMG_GetObjectName(oid)` - Routine 597](#swmg_getobjectnameoid---routine-597)
    - [Other Functions](#other-functions)
      - [`abs(nValue)` - Routine 77](#absnvalue---routine-77)
      - [`acos(fValue)` - Routine 71](#acosfvalue---routine-71)
      - [`AddJournalQuestEntry(szPlotID, nState, bAllowOverrideHigher)` - Routine 367](#addjournalquestentryszplotid-nstate-ballowoverridehigher---routine-367)
      - [`AddJournalWorldEntry(nIndex, szEntry, szTitle)` - Routine 669](#addjournalworldentrynindex-szentry-sztitle---routine-669)
      - [`AddJournalWorldEntryStrref(strref, strrefTitle)` - Routine 670](#addjournalworldentrystrrefstrref-strreftitle---routine-670)
      - [`AdjustReputation(oTarget, oSourceFactionMember, nAdjustment)` - Routine 209](#adjustreputationotarget-osourcefactionmember-nadjustment---routine-209)
      - [`AngleToVector(fAngle)` - Routine 144](#angletovectorfangle---routine-144)
      - [`asin(fValue)` - Routine 72](#asinfvalue---routine-72)
      - [`AssignCommand(oActionSubject, aActionToAssign)` - Routine 6](#assigncommandoactionsubject-aactiontoassign---routine-6)
      - [`atan(fValue)` - Routine 73](#atanfvalue---routine-73)
      - [`AurPostString(sString, nX, nY, fLife)` - Routine 582](#aurpoststringsstring-nx-ny-flife---routine-582)
      - [`AwardStealthXP(oTarget)` - Routine 480](#awardstealthxpotarget---routine-480)
      - [`ChangeFaction(oObjectToChangeFaction, oMemberOfFactionToJoin)` - Routine 173](#changefactionoobjecttochangefaction-omemberoffactiontojoin---routine-173)
      - [`ChangeFactionByFaction(nFactionFrom, nFactionTo)` - Routine 737](#changefactionbyfactionnfactionfrom-nfactionto---routine-737)
      - [`ChangeToStandardFaction(oCreatureToChange, nStandardFaction)` - Routine 412](#changetostandardfactionocreaturetochange-nstandardfaction---routine-412)
      - [`ClearAllActions()` - Routine 9](#clearallactions---routine-9)
      - [`cos(fValue)` - Routine 68](#cosfvalue---routine-68)
      - [`CutsceneMove(oObject, vPosition, nRun)` - Routine 507](#cutscenemoveoobject-vposition-nrun---routine-507)
      - [`d10(nNumDice)` - Routine 100](#d10nnumdice---routine-100)
      - [`d100(nNumDice)` - Routine 103](#d100nnumdice---routine-103)
      - [`d12(nNumDice)` - Routine 101](#d12nnumdice---routine-101)
      - [`d2(nNumDice)` - Routine 95](#d2nnumdice---routine-95)
      - [`d20(nNumDice)` - Routine 102](#d20nnumdice---routine-102)
      - [`d3(nNumDice)` - Routine 96](#d3nnumdice---routine-96)
      - [`d4(nNumDice)` - Routine 97](#d4nnumdice---routine-97)
      - [`d6(nNumDice)` - Routine 98](#d6nnumdice---routine-98)
      - [`d8(nNumDice)` - Routine 99](#d8nnumdice---routine-99)
      - [`DelayCommand(fSeconds, aActionToDelay)` - Routine 7](#delaycommandfseconds-aactiontodelay---routine-7)
      - [`DeleteJournalWorldAllEntries()` - Routine 672](#deletejournalworldallentries---routine-672)
      - [`DeleteJournalWorldEntry(nIndex)` - Routine 673](#deletejournalworldentrynindex---routine-673)
      - [`DeleteJournalWorldEntryStrref(strref)` - Routine 674](#deletejournalworldentrystrrefstrref---routine-674)
      - [`DoDoorAction(oTargetDoor, nDoorAction)` - Routine 338](#dodooractionotargetdoor-ndooraction---routine-338)
      - [`DoPlaceableObjectAction(oPlaceable, nPlaceableAction)` - Routine 547](#doplaceableobjectactionoplaceable-nplaceableaction---routine-547)
      - [`DuplicateHeadAppearance(oidCreatureToChange, oidCreatureToMatch)` - Routine 500](#duplicateheadappearanceoidcreaturetochange-oidcreaturetomatch---routine-500)
      - [`EndGame(nShowEndGameGui)` - Routine 564](#endgamenshowendgamegui---routine-564)
      - [`EventSpellCastAt(oCaster, nSpell, bHarmful)` - Routine 244](#eventspellcastatocaster-nspell-bharmful---routine-244)
      - [`EventUserDefined(nUserDefinedEventNumber)` - Routine 132](#eventuserdefinednuserdefinedeventnumber---routine-132)
      - [`ExecuteScript(sScript, oTarget, nScriptVar)` - Routine 8](#executescriptsscript-otarget-nscriptvar---routine-8)
      - [`ExportAllCharacters()` - Routine 557](#exportallcharacters---routine-557)
      - [`fabs(fValue)` - Routine 67](#fabsfvalue---routine-67)
      - [`FaceObjectAwayFromObject(oFacer, oObjectToFaceAwayFrom)` - Routine 553](#faceobjectawayfromobjectofacer-oobjecttofaceawayfrom---routine-553)
      - [`FeetToMeters(fFeet)` - Routine 218](#feettometersffeet---routine-218)
      - [`FindSubString(sString, sSubString)` - Routine 66](#findsubstringsstring-ssubstring---routine-66)
      - [`FloatingTextStringOnCreature(sStringToDisplay, oCreatureToFloatAbove, bBroadcastToFaction)` - Routine 526](#floatingtextstringoncreaturesstringtodisplay-ocreaturetofloatabove-bbroadcasttofaction---routine-526)
      - [`FloatingTextStrRefOnCreature(nStrRefToDisplay, oCreatureToFloatAbove, bBroadcastToFaction)` - Routine 525](#floatingtextstrrefoncreaturenstrreftodisplay-ocreaturetofloatabove-bbroadcasttofaction---routine-525)
      - [`FloatToInt(fFloat)` - Routine 231](#floattointffloat---routine-231)
      - [`FloatToString(fFloat, nWidth, nDecimals)` - Routine 3](#floattostringffloat-nwidth-ndecimals---routine-3)
      - [`FortitudeSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 108](#fortitudesaveocreature-ndc-nsavetype-osaveversus---routine-108)
      - [`GetAC(oObject, nForFutureUse)` - Routine 116](#getacoobject-nforfutureuse---routine-116)
      - [`GetAppearanceType(oCreature)` - Routine 524](#getappearancetypeocreature---routine-524)
      - [`GetAttemptedMovementTarget()` - Routine 489](#getattemptedmovementtarget---routine-489)
      - [`GetAttemptedSpellTarget()` - Routine 375](#getattemptedspelltarget---routine-375)
      - [`GetBlockingCreature(oTarget)` - Routine 490](#getblockingcreatureotarget---routine-490)
      - [`GetBlockingDoor()` - Routine 336](#getblockingdoor---routine-336)
      - [`GetButtonMashCheck()` - Routine 267](#getbuttonmashcheck---routine-267)
      - [`GetCasterLevel(oCreature)` - Routine 84](#getcasterlevelocreature---routine-84)
      - [`GetCategoryFromTalent(tTalent)` - Routine 735](#getcategoryfromtalentttalent---routine-735)
      - [`GetChallengeRating(oCreature)` - Routine 494](#getchallengeratingocreature---routine-494)
      - [`GetCheatCode(nCode)` - Routine 764](#getcheatcodencode---routine-764)
      - [`GetClickingObject()` - Routine 326](#getclickingobject---routine-326)
      - [`GetCommandable(oTarget)` - Routine 163](#getcommandableotarget---routine-163)
      - [`GetCreatureHasTalent(tTalent, oCreature)` - Routine 306](#getcreaturehastalentttalent-ocreature---routine-306)
      - [`GetCreatureMovmentType(oidCreature)` - Routine 566](#getcreaturemovmenttypeoidcreature---routine-566)
      - [`GetCreatureSize(oCreature)` - Routine 479](#getcreaturesizeocreature---routine-479)
      - [`GetCreatureTalentBest(nCategory, nCRMax, oCreature, nInclusion, nExcludeType, nExcludeId)` - Routine 308](#getcreaturetalentbestncategory-ncrmax-ocreature-ninclusion-nexcludetype-nexcludeid---routine-308)
      - [`GetCreatureTalentRandom(nCategory, oCreature, nInclusion)` - Routine 307](#getcreaturetalentrandomncategory-ocreature-ninclusion---routine-307)
      - [`GetCurrentAction(oObject)` - Routine 522](#getcurrentactionoobject---routine-522)
      - [`GetCurrentForcePoints(oObject)` - Routine 55](#getcurrentforcepointsoobject---routine-55)
      - [`GetCurrentHitPoints(oObject)` - Routine 49](#getcurrenthitpointsoobject---routine-49)
      - [`GetCurrentStealthXP()` - Routine 474](#getcurrentstealthxp---routine-474)
      - [`GetDamageDealtByType(nDamageType)` - Routine 344](#getdamagedealtbytypendamagetype---routine-344)
      - [`GetDifficultyModifier()` - Routine 523](#getdifficultymodifier---routine-523)
      - [`GetDistanceBetween(oObjectA, oObjectB)` - Routine 151](#getdistancebetweenoobjecta-oobjectb---routine-151)
      - [`GetDistanceBetween2D(oObjectA, oObjectB)` - Routine 319](#getdistancebetween2doobjecta-oobjectb---routine-319)
      - [`GetDistanceBetweenLocations(lLocationA, lLocationB)` - Routine 298](#getdistancebetweenlocationsllocationa-llocationb---routine-298)
      - [`GetDistanceBetweenLocations2D(lLocationA, lLocationB)` - Routine 334](#getdistancebetweenlocations2dllocationa-llocationb---routine-334)
      - [`GetDistanceToObject(oObject)` - Routine 41](#getdistancetoobjectoobject---routine-41)
      - [`GetDistanceToObject2D(oObject)` - Routine 335](#getdistancetoobject2doobject---routine-335)
      - [`GetEncounterActive(oEncounter)` - Routine 276](#getencounteractiveoencounter---routine-276)
      - [`GetEncounterDifficulty(oEncounter)` - Routine 297](#getencounterdifficultyoencounter---routine-297)
      - [`GetEncounterSpawnsCurrent(oEncounter)` - Routine 280](#getencounterspawnscurrentoencounter---routine-280)
      - [`GetEncounterSpawnsMax(oEncounter)` - Routine 278](#getencounterspawnsmaxoencounter---routine-278)
      - [`GetEnteringObject()` - Routine 25](#getenteringobject---routine-25)
      - [`GetExitingObject()` - Routine 26](#getexitingobject---routine-26)
      - [`GetFacing(oTarget)` - Routine 28](#getfacingotarget---routine-28)
      - [`GetFacingFromLocation(lLocation)` - Routine 225](#getfacingfromlocationllocation---routine-225)
      - [`GetFactionAverageLevel(oFactionMember)` - Routine 189](#getfactionaveragelevelofactionmember---routine-189)
      - [`GetFactionAverageReputation(oSourceFactionMember, oTarget)` - Routine 186](#getfactionaveragereputationosourcefactionmember-otarget---routine-186)
      - [`GetFactionAverageXP(oFactionMember)` - Routine 190](#getfactionaveragexpofactionmember---routine-190)
      - [`GetFactionBestAC(oFactionMember, bMustBeVisible)` - Routine 193](#getfactionbestacofactionmember-bmustbevisible---routine-193)
      - [`GetFactionEqual(oFirstObject, oSecondObject)` - Routine 172](#getfactionequalofirstobject-osecondobject---routine-172)
      - [`GetFactionGold(oFactionMember)` - Routine 185](#getfactiongoldofactionmember---routine-185)
      - [`GetFactionLeader(oMemberOfFaction)` - Routine 562](#getfactionleaderomemberoffaction---routine-562)
      - [`GetFactionLeastDamagedMember(oFactionMember, bMustBeVisible)` - Routine 184](#getfactionleastdamagedmemberofactionmember-bmustbevisible---routine-184)
      - [`GetFactionMostDamagedMember(oFactionMember, bMustBeVisible)` - Routine 183](#getfactionmostdamagedmemberofactionmember-bmustbevisible---routine-183)
      - [`GetFactionStrongestMember(oFactionMember, bMustBeVisible)` - Routine 182](#getfactionstrongestmemberofactionmember-bmustbevisible---routine-182)
      - [`GetFactionWeakestMember(oFactionMember, bMustBeVisible)` - Routine 181](#getfactionweakestmemberofactionmember-bmustbevisible---routine-181)
      - [`GetFactionWorstAC(oFactionMember, bMustBeVisible)` - Routine 192](#getfactionworstacofactionmember-bmustbevisible---routine-192)
      - [`GetFirstFactionMember(oMemberOfFaction, bPCOnly)` - Routine 380](#getfirstfactionmemberomemberoffaction-bpconly---routine-380)
      - [`GetFirstInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`](#getfirstinpersistentobjectopersistentobject-nresidentobjecttype-npersistentzone)
      - [`GetFirstObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 128](#getfirstobjectinshapenshape-fsize-ltarget-blineofsight-nobjectfilter-vorigin---routine-128)
      - [`GetFirstPC()` - Routine 548](#getfirstpc---routine-548)
      - [`GetFortitudeSavingThrow(oTarget)` - Routine 491](#getfortitudesavingthrowotarget---routine-491)
      - [`GetFoundEnemyCreature(oTarget)` - Routine 495](#getfoundenemycreatureotarget---routine-495)
      - [`GetGameDifficulty()` - Routine 513](#getgamedifficulty---routine-513)
      - [`GetGender(oCreature)` - Routine 358](#getgenderocreature---routine-358)
      - [`GetGold(oTarget)` - Routine 418](#getgoldotarget---routine-418)
      - [`GetGoldPieceValue(oItem)` - Routine 311](#getgoldpiecevalueoitem---routine-311)
      - [`GetGoodEvilValue(oCreature)` - Routine 125](#getgoodevilvalueocreature---routine-125)
      - [`GetHasInventory(oObject)` - Routine 570](#gethasinventoryoobject---routine-570)
      - [`GetHasSpell(nSpell, oCreature)` - Routine 377](#gethasspellnspell-ocreature---routine-377)
      - [`GetHitDice(oCreature)` - Routine 166](#gethitdiceocreature---routine-166)
      - [`GetIdentified(oItem)` - Routine 332](#getidentifiedoitem---routine-332)
      - [`GetIdFromTalent(tTalent)` - Routine 363](#getidfromtalentttalent---routine-363)
      - [`GetInventoryDisturbType()` - Routine 352](#getinventorydisturbtype---routine-352)
      - [`GetIsDawn()` - Routine 407](#getisdawn---routine-407)
      - [`GetIsDay()` - Routine 405](#getisday---routine-405)
      - [`GetIsDead(oCreature)` - Routine 140](#getisdeadocreature---routine-140)
      - [`GetIsDebilitated(oCreature)` - Routine 732](#getisdebilitatedocreature---routine-732)
      - [`GetIsDoorActionPossible(oTargetDoor, nDoorAction)` - Routine 337](#getisdooractionpossibleotargetdoor-ndooraction---routine-337)
      - [`GetIsDusk()` - Routine 408](#getisdusk---routine-408)
      - [`GetIsEncounterCreature(oCreature)` - Routine 409](#getisencountercreatureocreature---routine-409)
      - [`GetIsEnemy(oTarget, oSource)` - Routine 235](#getisenemyotarget-osource---routine-235)
      - [`GetIsFriend(oTarget, oSource)` - Routine 236](#getisfriendotarget-osource---routine-236)
      - [`GetIsImmune(oCreature, nImmunityType, oVersus)` - Routine 274](#getisimmuneocreature-nimmunitytype-oversus---routine-274)
      - [`GetIsLinkImmune(oTarget, eEffect)` - Routine 390](#getislinkimmuneotarget-eeffect---routine-390)
      - [`GetIsListening(oObject)` - Routine 174](#getislisteningoobject---routine-174)
      - [`GetIsLiveContentAvailable(nPkg)` - Routine 748](#getislivecontentavailablenpkg---routine-748)
      - [`GetIsNeutral(oTarget, oSource)` - Routine 237](#getisneutralotarget-osource---routine-237)
      - [`GetIsNight()` - Routine 406](#getisnight---routine-406)
      - [`GetIsObjectValid(oObject)` - Routine 42](#getisobjectvalidoobject---routine-42)
      - [`GetIsOpen(oObject)` - Routine 443](#getisopenoobject---routine-443)
      - [`GetIsPlaceableObjectActionPossible(oPlaceable, nPlaceableAction)` - Routine 546](#getisplaceableobjectactionpossibleoplaceable-nplaceableaction---routine-546)
      - [`GetIsPoisoned(oObject)` - Routine 751](#getispoisonedoobject---routine-751)
      - [`GetIsTalentValid(tTalent)` - Routine 359](#getistalentvalidttalent---routine-359)
      - [`GetIsTrapped(oObject)` - Routine 551](#getistrappedoobject---routine-551)
      - [`GetJournalEntry(szPlotID)` - Routine 369](#getjournalentryszplotid---routine-369)
      - [`GetJournalQuestExperience(szPlotID)` - Routine 384](#getjournalquestexperienceszplotid---routine-384)
      - [`GetLastAssociateCommand(oAssociate)` - Routine 321](#getlastassociatecommandoassociate---routine-321)
      - [`GetLastClosedBy()` - Routine 260](#getlastclosedby---routine-260)
      - [`GetLastDamager()` - Routine 346](#getlastdamager---routine-346)
      - [`GetLastDisarmed()` - Routine 347](#getlastdisarmed---routine-347)
      - [`GetLastDisturbed()` - Routine 348](#getlastdisturbed---routine-348)
      - [`GetLastForcePowerUsed(oAttacker)` - Routine 723](#getlastforcepowerusedoattacker---routine-723)
      - [`GetLastHostileActor(oVictim)` - Routine 556](#getlasthostileactorovictim---routine-556)
      - [`GetLastHostileTarget(oAttacker)` - Routine 721](#getlasthostiletargetoattacker---routine-721)
      - [`GetLastLocked()` - Routine 349](#getlastlocked---routine-349)
      - [`GetLastOpenedBy()` - Routine 376](#getlastopenedby---routine-376)
      - [`GetLastPazaakResult()` - Routine 365](#getlastpazaakresult---routine-365)
      - [`GetLastPerceived()` - Routine 256](#getlastperceived---routine-256)
      - [`GetLastPerceptionHeard()` - Routine 257](#getlastperceptionheard---routine-257)
      - [`GetLastPerceptionInaudible()` - Routine 258](#getlastperceptioninaudible---routine-258)
      - [`GetLastPerceptionSeen()` - Routine 259](#getlastperceptionseen---routine-259)
      - [`GetLastPerceptionVanished()` - Routine 261](#getlastperceptionvanished---routine-261)
      - [`GetLastRespawnButtonPresser()` - Routine 419](#getlastrespawnbuttonpresser---routine-419)
      - [`GetLastSpell()` - Routine 246](#getlastspell---routine-246)
      - [`GetLastSpellCaster()` - Routine 245](#getlastspellcaster---routine-245)
      - [`GetLastSpellHarmful()` - Routine 423](#getlastspellharmful---routine-423)
      - [`GetLastTrapDetected(oTarget)` - Routine 486](#getlasttrapdetectedotarget---routine-486)
      - [`GetLastUnlocked()` - Routine 350](#getlastunlocked---routine-350)
      - [`GetLastUsedBy()` - Routine 330](#getlastusedby---routine-330)
      - [`GetLastWeaponUsed(oCreature)` - Routine 328](#getlastweaponusedocreature---routine-328)
      - [`GetLevelByPosition(nClassPosition, oCreature)` - Routine 342](#getlevelbypositionnclassposition-ocreature---routine-342)
      - [`GetListenPatternNumber()` - Routine 195](#getlistenpatternnumber---routine-195)
      - [`GetLoadFromSaveGame()` - Routine 251](#getloadfromsavegame---routine-251)
      - [`GetLocation(oObject)` - Routine 213](#getlocationoobject---routine-213)
      - [`GetLocked(oTarget)` - Routine 325](#getlockedotarget---routine-325)
      - [`GetLockKeyRequired(oObject)` - Routine 537](#getlockkeyrequiredoobject---routine-537)
      - [`GetLockKeyTag(oObject)` - Routine 538](#getlockkeytagoobject---routine-538)
      - [`GetLockLockable(oObject)` - Routine 539](#getlocklockableoobject---routine-539)
      - [`GetLockLockDC(oObject)` - Routine 541](#getlocklockdcoobject---routine-541)
      - [`GetLockUnlockDC(oObject)` - Routine 540](#getlockunlockdcoobject---routine-540)
      - [`GetMatchedSubstring(nString)` - Routine 178](#getmatchedsubstringnstring---routine-178)
      - [`GetMatchedSubstringsCount()` - Routine 179](#getmatchedsubstringscount---routine-179)
      - [`GetMaxForcePoints(oObject)` - Routine 56](#getmaxforcepointsoobject---routine-56)
      - [`GetMaxHitPoints(oObject)` - Routine 50](#getmaxhitpointsoobject---routine-50)
      - [`GetMaxStealthXP()` - Routine 464](#getmaxstealthxp---routine-464)
      - [`GetMinOneHP(oObject)` - Routine 715](#getminonehpoobject---routine-715)
      - [`GetMovementRate(oCreature)` - Routine 496](#getmovementrateocreature---routine-496)
      - [`GetName(oObject)` - Routine 253](#getnameoobject---routine-253)
      - [`GetNextFactionMember(oMemberOfFaction, bPCOnly)` - Routine 381](#getnextfactionmemberomemberoffaction-bpconly---routine-381)
      - [`GetNextInPersistentObject(oPersistentObject, nResidentObjectType, nPersistentZone)`](#getnextinpersistentobjectopersistentobject-nresidentobjecttype-npersistentzone)
      - [`GetNextObjectInShape(nShape, fSize, lTarget, bLineOfSight, nObjectFilter, vOrigin)` - Routine 129](#getnextobjectinshapenshape-fsize-ltarget-blineofsight-nobjectfilter-vorigin---routine-129)
      - [`GetNextPC()` - Routine 548](#getnextpc---routine-548)
      - [`GetNPCAIStyle(oCreature)` - Routine 705](#getnpcaistyleocreature---routine-705)
      - [`GetPCLevellingUp()` - Routine 542](#getpclevellingup---routine-542)
      - [`GetPlaceableIllumination(oPlaceable)` - Routine 545](#getplaceableilluminationoplaceable---routine-545)
      - [`GetPlanetAvailable(nPlanet)` - Routine 743](#getplanetavailablenplanet---routine-743)
      - [`GetPlanetSelectable(nPlanet)` - Routine 741](#getplanetselectablenplanet---routine-741)
      - [`GetPlotFlag(oTarget)` - Routine 455](#getplotflagotarget---routine-455)
      - [`GetPosition(oTarget)` - Routine 27](#getpositionotarget---routine-27)
      - [`GetPositionFromLocation(lLocation)` - Routine 223](#getpositionfromlocationllocation---routine-223)
      - [`GetRacialType(oCreature)` - Routine 107](#getracialtypeocreature---routine-107)
      - [`GetReflexAdjustedDamage(nDamage, oTarget, nDC, nSaveType, oSaveVersus)` - Routine 299](#getreflexadjusteddamagendamage-otarget-ndc-nsavetype-osaveversus---routine-299)
      - [`GetReflexSavingThrow(oTarget)` - Routine 493](#getreflexsavingthrowotarget---routine-493)
      - [`GetReputation(oSource, oTarget)` - Routine 208](#getreputationosource-otarget---routine-208)
      - [`GetRunScriptVar()` - Routine 565](#getrunscriptvar---routine-565)
      - [`GetSelectedPlanet()` - Routine 744](#getselectedplanet---routine-744)
      - [`GetSoloMode()` - Routine 462](#getsolomode---routine-462)
      - [`GetSpellId()` - Routine 248](#getspellid---routine-248)
      - [`GetSpellSaveDC()` - Routine 111](#getspellsavedc---routine-111)
      - [`GetSpellTarget(oCreature)` - Routine 752](#getspelltargetocreature---routine-752)
      - [`GetSpellTargetLocation()` - Routine 222](#getspelltargetlocation---routine-222)
      - [`GetStandardFaction(oObject)` - Routine 713](#getstandardfactionoobject---routine-713)
      - [`GetStartingLocation()` - Routine 411](#getstartinglocation---routine-411)
      - [`GetStealthXPDecrement()` - Routine 498](#getstealthxpdecrement---routine-498)
      - [`GetStealthXPEnabled()` - Routine 481](#getstealthxpenabled---routine-481)
      - [`GetStringByStrRef(nStrRef)` - Routine 239](#getstringbystrrefnstrref---routine-239)
      - [`GetStringLeft(sString, nCount)` - Routine 63](#getstringleftsstring-ncount---routine-63)
      - [`GetStringLength(sString)` - Routine 59](#getstringlengthsstring---routine-59)
      - [`GetStringLowerCase(sString)` - Routine 61](#getstringlowercasesstring---routine-61)
      - [`GetStringRight(sString, nCount)` - Routine 62](#getstringrightsstring-ncount---routine-62)
      - [`GetStringUpperCase(sString)` - Routine 60](#getstringuppercasesstring---routine-60)
      - [`GetSubRace(oCreature)` - Routine 497](#getsubraceocreature---routine-497)
      - [`GetSubScreenID()` - Routine 53](#getsubscreenid---routine-53)
      - [`GetSubString(sString, nStart, nCount)` - Routine 65](#getsubstringsstring-nstart-ncount---routine-65)
      - [`GetTag(oObject)` - Routine 168](#gettagoobject---routine-168)
      - [`GetTimeHour()` - Routine 16](#gettimehour---routine-16)
      - [`GetTimeMillisecond()` - Routine 19](#gettimemillisecond---routine-19)
      - [`GetTimeMinute()` - Routine 17](#gettimeminute---routine-17)
      - [`GetTimeSecond()` - Routine 18](#gettimesecond---routine-18)
      - [`GetTotalDamageDealt()` - Routine 345](#gettotaldamagedealt---routine-345)
      - [`GetTransitionTarget(oTransition)` - Routine 198](#gettransitiontargetotransition---routine-198)
      - [`GetTrapBaseType(oTrapObject)` - Routine 531](#gettrapbasetypeotrapobject---routine-531)
      - [`GetTrapCreator(oTrapObject)` - Routine 533](#gettrapcreatorotrapobject---routine-533)
      - [`GetTrapDetectable(oTrapObject)` - Routine 528](#gettrapdetectableotrapobject---routine-528)
      - [`GetTrapDetectDC(oTrapObject)` - Routine 536](#gettrapdetectdcotrapobject---routine-536)
      - [`GetTrapDetectedBy(oTrapObject, oCreature)` - Routine 529](#gettrapdetectedbyotrapobject-ocreature---routine-529)
      - [`GetTrapDisarmable(oTrapObject)` - Routine 527](#gettrapdisarmableotrapobject---routine-527)
      - [`GetTrapDisarmDC(oTrapObject)` - Routine 535](#gettrapdisarmdcotrapobject---routine-535)
      - [`GetTrapFlagged(oTrapObject)` - Routine 530](#gettrapflaggedotrapobject---routine-530)
      - [`GetTrapKeyTag(oTrapObject)` - Routine 534](#gettrapkeytagotrapobject---routine-534)
      - [`GetTrapOneShot(oTrapObject)` - Routine 532](#gettraponeshototrapobject---routine-532)
      - [`GetTypeFromTalent(tTalent)` - Routine 362](#gettypefromtalentttalent---routine-362)
      - [`GetUserActionsPending()` - Routine 514](#getuseractionspending---routine-514)
      - [`GetUserDefinedEventNumber()` - Routine 247](#getuserdefinedeventnumber---routine-247)
      - [`GetWasForcePowerSuccessful(oAttacker)` - Routine 726](#getwasforcepowersuccessfuloattacker---routine-726)
      - [`GetWaypointByTag(sWaypointTag)` - Routine 197](#getwaypointbytagswaypointtag---routine-197)
      - [`GetWeaponRanged(oItem)` - Routine 511](#getweaponrangedoitem---routine-511)
      - [`GetWillSavingThrow(oTarget)` - Routine 492](#getwillsavingthrowotarget---routine-492)
      - [`GetXP(oCreature)` - Routine 395](#getxpocreature---routine-395)
      - [`GiveGoldToCreature(oCreature, nGP)` - Routine 322](#givegoldtocreatureocreature-ngp---routine-322)
      - [`GivePlotXP(sPlotName, nPercentage)` - Routine 714](#giveplotxpsplotname-npercentage---routine-714)
      - [`GiveXPToCreature(oCreature, nXpAmount)` - Routine 393](#givexptocreatureocreature-nxpamount---routine-393)
      - [`HoursToSeconds(nHours)` - Routine 122](#hourstosecondsnhours---routine-122)
      - [`InsertString(sDestination, sString, nPosition)` - Routine 64](#insertstringsdestination-sstring-nposition---routine-64)
      - [`IntToFloat(nInteger)` - Routine 230](#inttofloatninteger---routine-230)
      - [`IntToHexString(nInteger)` - Routine 396](#inttohexstringninteger---routine-396)
      - [`IntToString(nInteger)` - Routine 92](#inttostringninteger---routine-92)
      - [`IsAvailableCreature(nNPC)` - Routine 696](#isavailablecreaturennpc---routine-696)
      - [`IsCreditSequenceInProgress()` - Routine 519](#iscreditsequenceinprogress---routine-519)
      - [`JumpToLocation(lDestination)` - Routine 313](#jumptolocationldestination---routine-313)
      - [`JumpToObject(oToJumpTo, nWalkStraightLineToPoint)` - Routine 385](#jumptoobjectotojumpto-nwalkstraightlinetopoint---routine-385)
      - [`Location(vPosition, fOrientation)` - Routine 215](#locationvposition-forientation---routine-215)
      - [`log(fValue)` - Routine 74](#logfvalue---routine-74)
      - [`NoClicksFor(fDuration)` - Routine 759](#noclicksforfduration---routine-759)
      - [`ObjectToString(oObject)` - Routine 272](#objecttostringoobject---routine-272)
      - [`OpenStore(oStore, oPC, nBonusMarkUp, nBonusMarkDown)` - Routine 378](#openstoreostore-opc-nbonusmarkup-nbonusmarkdown---routine-378)
      - [`PauseGame(bPause)` - Routine 57](#pausegamebpause---routine-57)
      - [`PopUpDeathGUIPanel(oPC, bRespawnButtonEnabled, bWaitForHelpButtonEnabled, nHelpStringReference, sHelpString)` - Routine 554](#popupdeathguipanelopc-brespawnbuttonenabled-bwaitforhelpbuttonenabled-nhelpstringreference-shelpstring---routine-554)
      - [`PopUpGUIPanel(oPC, nGUIPanel)` - Routine 388](#popupguipanelopc-nguipanel---routine-388)
      - [`pow(fValue, fExponent)` - Routine 75](#powfvalue-fexponent---routine-75)
      - [`PrintFloat(fFloat, nWidth, nDecimals)` - Routine 2](#printfloatffloat-nwidth-ndecimals---routine-2)
      - [`PrintInteger(nInteger)` - Routine 4](#printintegerninteger---routine-4)
      - [`PrintObject(oObject)` - Routine 5](#printobjectoobject---routine-5)
      - [`PrintString(sString)` - Routine 1](#printstringsstring---routine-1)
      - [`PrintVector(vVector, bPrepend)` - Routine 141](#printvectorvvector-bprepend---routine-141)
      - [`QueueMovie(sMovie, bSkippable)` - Routine 769](#queuemoviesmovie-bskippable---routine-769)
      - [`Random(nMaxInteger)`](#randomnmaxinteger)
      - [`RandomName()` - Routine 249](#randomname---routine-249)
      - [`ReflexSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 109](#reflexsaveocreature-ndc-nsavetype-osaveversus---routine-109)
      - [`RemoveAvailableNPC(nNPC)` - Routine 695](#removeavailablenpcnnpc---routine-695)
      - [`RemoveJournalQuestEntry(szPlotID)` - Routine 368](#removejournalquestentryszplotid---routine-368)
      - [`ResistForce(oSource, oTarget)` - Routine 169](#resistforceosource-otarget---routine-169)
      - [`RevealMap(vPoint, nRadius)` - Routine 515](#revealmapvpoint-nradius---routine-515)
      - [`RoundsToSeconds(nRounds)` - Routine 121](#roundstosecondsnrounds---routine-121)
      - [`SaveNPCState(nNPC)` - Routine 734](#savenpcstatennpc---routine-734)
      - [`SendMessageToPC(oPlayer, szMessage)` - Routine 374](#sendmessagetopcoplayer-szmessage---routine-374)
      - [`SetAssociateListenPatterns(oTarget)` - Routine 327](#setassociatelistenpatternsotarget---routine-327)
      - [`SetAvailableNPCId()` - Routine 767](#setavailablenpcid---routine-767)
      - [`SetButtonMashCheck(nCheck)` - Routine 268](#setbuttonmashcheckncheck---routine-268)
      - [`SetCameraFacing(fDirection)` - Routine 45](#setcamerafacingfdirection---routine-45)
      - [`SetCameraMode(oPlayer, nCameraMode)` - Routine 504](#setcameramodeoplayer-ncameramode---routine-504)
      - [`SetCommandable(bCommandable, oTarget)` - Routine 162](#setcommandablebcommandable-otarget---routine-162)
      - [`SetCurrentStealthXP(nCurrent)` - Routine 478](#setcurrentstealthxpncurrent---routine-478)
      - [`SetCustomToken(nCustomTokenNumber, sTokenValue)` - Routine 284](#setcustomtokenncustomtokennumber-stokenvalue---routine-284)
      - [`SetEncounterActive(nNewValue, oEncounter)` - Routine 277](#setencounteractivennewvalue-oencounter---routine-277)
      - [`SetEncounterDifficulty(nEncounterDifficulty, oEncounter)` - Routine 296](#setencounterdifficultynencounterdifficulty-oencounter---routine-296)
      - [`SetEncounterSpawnsCurrent(nNewValue, oEncounter)` - Routine 281](#setencounterspawnscurrentnnewvalue-oencounter---routine-281)
      - [`SetEncounterSpawnsMax(nNewValue, oEncounter)` - Routine 279](#setencounterspawnsmaxnnewvalue-oencounter---routine-279)
      - [`SetFacing(fDirection)` - Routine 10](#setfacingfdirection---routine-10)
      - [`SetFacingPoint(vTarget)` - Routine 143](#setfacingpointvtarget---routine-143)
      - [`SetForcePowerUnsuccessful(nResult, oCreature)` - Routine 731](#setforcepowerunsuccessfulnresult-ocreature---routine-731)
      - [`SetFormation(oAnchor, oCreature, nFormationPattern, nPosition)` - Routine 729](#setformationoanchor-ocreature-nformationpattern-nposition---routine-729)
      - [`SetGoodEvilValue(oCreature, nAlignment)` - Routine 750](#setgoodevilvalueocreature-nalignment---routine-750)
      - [`SetIdentified(oItem, bIdentified)` - Routine 333](#setidentifiedoitem-bidentified---routine-333)
      - [`SetIsDestroyable(bDestroyable, bRaiseable, bSelectableWhenDead)` - Routine 323](#setisdestroyablebdestroyable-braiseable-bselectablewhendead---routine-323)
      - [`SetJournalQuestEntryPicture(szPlotID, oObject, nPictureIndex, bAllPartyMemebers, bAllPlayers)` - Routine 678](#setjournalquestentrypictureszplotid-oobject-npictureindex-ballpartymemebers-ballplayers---routine-678)
      - [`SetLightsaberPowered(oCreature, bOverride, bPowered, bShowTransition)` - Routine 421](#setlightsaberpoweredocreature-boverride-bpowered-bshowtransition---routine-421)
      - [`SetListening(oObject, bValue)` - Routine 175](#setlisteningoobject-bvalue---routine-175)
      - [`SetListenPattern(oObject, sPattern, nNumber)` - Routine 176](#setlistenpatternoobject-spattern-nnumber---routine-176)
      - [`SetLocked(oTarget, bLocked)` - Routine 324](#setlockedotarget-blocked---routine-324)
      - [`SetMapPinEnabled(oMapPin, nEnabled)` - Routine 386](#setmappinenabledomappin-nenabled---routine-386)
      - [`SetMaxHitPoints(oObject, nMaxHP)` - Routine 758](#setmaxhitpointsoobject-nmaxhp---routine-758)
      - [`SetMaxStealthXP(nMax)` - Routine 468](#setmaxstealthxpnmax---routine-468)
      - [`SetMinOneHP(oObject, nMinOneHP)` - Routine 716](#setminonehpoobject-nminonehp---routine-716)
      - [`SetNPCAIStyle(oCreature, nStyle)` - Routine 707](#setnpcaistyleocreature-nstyle---routine-707)
      - [`SetPlaceableIllumination(oPlaceable, bIlluminate)` - Routine 544](#setplaceableilluminationoplaceable-billuminate---routine-544)
      - [`SetPlanetAvailable(nPlanet, bAvailable)` - Routine 742](#setplanetavailablenplanet-bavailable---routine-742)
      - [`SetPlanetSelectable(nPlanet, bSelectable)` - Routine 740](#setplanetselectablenplanet-bselectable---routine-740)
      - [`SetPlotFlag(oTarget, nPlotFlag)` - Routine 456](#setplotflagotarget-nplotflag---routine-456)
      - [`SetReturnStrref(bShow, srStringRef, srReturnQueryStrRef)` - Routine 152](#setreturnstrrefbshow-srstringref-srreturnquerystrref---routine-152)
      - [`SetSoloMode(bActivate)` - Routine 753](#setsolomodebactivate---routine-753)
      - [`SetStealthXPDecrement(nDecrement)` - Routine 499](#setstealthxpdecrementndecrement---routine-499)
      - [`SetStealthXPEnabled(bEnabled)` - Routine 482](#setstealthxpenabledbenabled---routine-482)
      - [`SetTime(nHour, nMinute, nSecond, nMillisecond)` - Routine 12](#settimenhour-nminute-nsecond-nmillisecond---routine-12)
      - [`SetTrapDetectedBy(oTrap, oDetector)` - Routine 550](#settrapdetectedbyotrap-odetector---routine-550)
      - [`SetTrapDisabled(oTrap)` - Routine 555](#settrapdisabledotrap---routine-555)
      - [`SetTutorialWindowsEnabled(bEnabled)` - Routine 516](#settutorialwindowsenabledbenabled---routine-516)
      - [`SetXP(oCreature, nXpAmount)` - Routine 394](#setxpocreature-nxpamount---routine-394)
      - [`ShipBuild()` - Routine 761](#shipbuild---routine-761)
      - [`ShowGalaxyMap(nPlanet)` - Routine 739](#showgalaxymapnplanet---routine-739)
      - [`ShowLevelUpGUI()` - Routine 265](#showlevelupgui---routine-265)
      - [`ShowTutorialWindow(nWindow)` - Routine 517](#showtutorialwindownwindow---routine-517)
      - [`ShowUpgradeScreen(oItem)` - Routine 354](#showupgradescreenoitem---routine-354)
      - [`SignalEvent(oObject, evToRun)` - Routine 131](#signaleventoobject-evtorun---routine-131)
      - [`sin(fValue)` - Routine 69](#sinfvalue---routine-69)
      - [`SpawnAvailableNPC(nNPC, lPosition)` - Routine 698](#spawnavailablenpcnnpc-lposition---routine-698)
      - [`sqrt(fValue)` - Routine 76](#sqrtfvalue---routine-76)
      - [`StartCreditSequence(bTransparentBackground)` - Routine 518](#startcreditsequencebtransparentbackground---routine-518)
      - [`StopRumblePattern(nPattern)` - Routine 371](#stoprumblepatternnpattern---routine-371)
      - [`StringToFloat(sNumber)` - Routine 233](#stringtofloatsnumber---routine-233)
      - [`StringToInt(sNumber)` - Routine 232](#stringtointsnumber---routine-232)
      - [`SuppressStatusSummaryEntry(nNumEntries)` - Routine 763](#suppressstatussummaryentrynnumentries---routine-763)
      - [`SurrenderByFaction(nFactionFrom, nFactionTo)` - Routine 736](#surrenderbyfactionnfactionfrom-nfactionto---routine-736)
      - [`SurrenderRetainBuffs()` - Routine 762](#surrenderretainbuffs---routine-762)
      - [`SurrenderToEnemies()` - Routine 476](#surrendertoenemies---routine-476)
      - [`SWMG_AdjustFollowerHitPoints(oFollower, nHP, nAbsolute)` - Routine 590](#swmg_adjustfollowerhitpointsofollower-nhp-nabsolute---routine-590)
      - [`SWMG_GetCameraFarClip()` - Routine 609](#swmg_getcamerafarclip---routine-609)
      - [`SWMG_GetCameraNearClip()` - Routine 608](#swmg_getcameranearclip---routine-608)
      - [`SWMG_GetEnemy(nEntry)` - Routine 613](#swmg_getenemynentry---routine-613)
      - [`SWMG_GetEnemyCount()` - Routine 612](#swmg_getenemycount---routine-612)
      - [`SWMG_GetGunBankBulletModel(oFollower, nGunBank)` - Routine 625](#swmg_getgunbankbulletmodelofollower-ngunbank---routine-625)
      - [`SWMG_GetGunBankCount(oFollower)` - Routine 624](#swmg_getgunbankcountofollower---routine-624)
      - [`SWMG_GetGunBankDamage(oFollower, nGunBank)` - Routine 627](#swmg_getgunbankdamageofollower-ngunbank---routine-627)
      - [`SWMG_GetGunBankGunModel(oFollower, nGunBank)` - Routine 626](#swmg_getgunbankgunmodelofollower-ngunbank---routine-626)
      - [`SWMG_GetGunBankHorizontalSpread(oEnemy, nGunBank)` - Routine 657](#swmg_getgunbankhorizontalspreadoenemy-ngunbank---routine-657)
      - [`SWMG_GetGunBankInaccuracy(oEnemy, nGunBank)` - Routine 660](#swmg_getgunbankinaccuracyoenemy-ngunbank---routine-660)
      - [`SWMG_GetGunBankLifespan(oFollower, nGunBank)` - Routine 629](#swmg_getgunbanklifespanofollower-ngunbank---routine-629)
      - [`SWMG_GetGunBankSensingRadius(oEnemy, nGunBank)` - Routine 659](#swmg_getgunbanksensingradiusoenemy-ngunbank---routine-659)
      - [`SWMG_GetGunBankSpeed(oFollower, nGunBank)` - Routine 630](#swmg_getgunbankspeedofollower-ngunbank---routine-630)
      - [`SWMG_GetGunBankTarget(oFollower, nGunBank)` - Routine 631](#swmg_getgunbanktargetofollower-ngunbank---routine-631)
      - [`SWMG_GetGunBankTimeBetweenShots(oFollower, nGunBank)` - Routine 628](#swmg_getgunbanktimebetweenshotsofollower-ngunbank---routine-628)
      - [`SWMG_GetGunBankVerticalSpread(oEnemy, nGunBank)` - Routine 658](#swmg_getgunbankverticalspreadoenemy-ngunbank---routine-658)
      - [`SWMG_GetHitPoints(oFollower)` - Routine 616](#swmg_gethitpointsofollower---routine-616)
      - [`SWMG_GetIsInvulnerable(oFollower)` - Routine 665](#swmg_getisinvulnerableofollower---routine-665)
      - [`SWMG_GetLastBulletFiredDamage()` - Routine 595](#swmg_getlastbulletfireddamage---routine-595)
      - [`SWMG_GetLastBulletFiredTarget()` - Routine 596](#swmg_getlastbulletfiredtarget---routine-596)
      - [`SWMG_GetLastBulletHitDamage()` - Routine 587](#swmg_getlastbullethitdamage---routine-587)
      - [`SWMG_GetLastBulletHitPart()` - Routine 639](#swmg_getlastbullethitpart---routine-639)
      - [`SWMG_GetLastBulletHitShooter()` - Routine 589](#swmg_getlastbullethitshooter---routine-589)
      - [`SWMG_GetLastBulletHitTarget()` - Routine 588](#swmg_getlastbullethittarget---routine-588)
      - [`SWMG_GetLastEvent()` - Routine 583](#swmg_getlastevent---routine-583)
      - [`SWMG_GetLastEventModelName()` - Routine 584](#swmg_getlasteventmodelname---routine-584)
      - [`SWMG_GetLastFollowerHit()` - Routine 593](#swmg_getlastfollowerhit---routine-593)
      - [`SWMG_GetLastHPChange()` - Routine 606](#swmg_getlasthpchange---routine-606)
      - [`SWMG_GetLastObstacleHit()` - Routine 594](#swmg_getlastobstaclehit---routine-594)
      - [`SWMG_GetLateralAccelerationPerSecond()` - Routine 521](#swmg_getlateralaccelerationpersecond---routine-521)
      - [`SWMG_GetMaxHitPoints(oFollower)` - Routine 617](#swmg_getmaxhitpointsofollower---routine-617)
      - [`SWMG_GetNumLoops(oFollower)` - Routine 621](#swmg_getnumloopsofollower---routine-621)
      - [`SWMG_GetObstacle(nEntry)` - Routine 615](#swmg_getobstaclenentry---routine-615)
      - [`SWMG_GetObstacleCount()` - Routine 614](#swmg_getobstaclecount---routine-614)
      - [`SWMG_GetPosition(oFollower)` - Routine 623](#swmg_getpositionofollower---routine-623)
      - [`SWMG_GetSphereRadius(oFollower)` - Routine 619](#swmg_getsphereradiusofollower---routine-619)
      - [`SWMG_IsEnemy(oid)` - Routine 601](#swmg_isenemyoid---routine-601)
      - [`SWMG_IsFollower(oid)` - Routine 599](#swmg_isfolloweroid---routine-599)
      - [`SWMG_IsGunBankTargetting(oFollower, nGunBank)` - Routine 640](#swmg_isgunbanktargettingofollower-ngunbank---routine-640)
      - [`SWMG_IsObstacle(oid)` - Routine 603](#swmg_isobstacleoid---routine-603)
      - [`SWMG_IsTrigger(oid)` - Routine 602](#swmg_istriggeroid---routine-602)
      - [`SWMG_OnBulletHit()` - Routine 591](#swmg_onbullethit---routine-591)
      - [`SWMG_OnDamage()` - Routine 605](#swmg_ondamage---routine-605)
      - [`SWMG_OnDeath()` - Routine 598](#swmg_ondeath---routine-598)
      - [`SWMG_OnObstacleHit()` - Routine 592](#swmg_onobstaclehit---routine-592)
      - [`SWMG_RemoveAnimation(oObject, sAnimName)` - Routine 607](#swmg_removeanimationoobject-sanimname---routine-607)
      - [`SWMG_SetCameraClip(fNear, fFar)` - Routine 610](#swmg_setcameraclipfnear-ffar---routine-610)
      - [`SWMG_SetFollowerHitPoints(oFollower, nHP)` - Routine 604](#swmg_setfollowerhitpointsofollower-nhp---routine-604)
      - [`SWMG_SetGunBankBulletModel(oFollower, nGunBank, sBulletModel)` - Routine 632](#swmg_setgunbankbulletmodelofollower-ngunbank-sbulletmodel---routine-632)
      - [`SWMG_SetGunBankDamage(oFollower, nGunBank, nDamage)` - Routine 634](#swmg_setgunbankdamageofollower-ngunbank-ndamage---routine-634)
      - [`SWMG_SetGunBankGunModel(oFollower, nGunBank, sGunModel)` - Routine 633](#swmg_setgunbankgunmodelofollower-ngunbank-sgunmodel---routine-633)
      - [`SWMG_SetGunBankHorizontalSpread(oEnemy, nGunBank, fHorizontalSpread)` - Routine 661](#swmg_setgunbankhorizontalspreadoenemy-ngunbank-fhorizontalspread---routine-661)
      - [`SWMG_SetGunBankInaccuracy(oEnemy, nGunBank, fInaccuracy)` - Routine 664](#swmg_setgunbankinaccuracyoenemy-ngunbank-finaccuracy---routine-664)
      - [`SWMG_SetGunBankLifespan(oFollower, nGunBank, fLifespan)` - Routine 636](#swmg_setgunbanklifespanofollower-ngunbank-flifespan---routine-636)
      - [`SWMG_SetGunBankSensingRadius(oEnemy, nGunBank, fSensingRadius)` - Routine 663](#swmg_setgunbanksensingradiusoenemy-ngunbank-fsensingradius---routine-663)
      - [`SWMG_SetGunBankSpeed(oFollower, nGunBank, fSpeed)` - Routine 637](#swmg_setgunbankspeedofollower-ngunbank-fspeed---routine-637)
      - [`SWMG_SetGunBankTarget(oFollower, nGunBank, nTarget)` - Routine 638](#swmg_setgunbanktargetofollower-ngunbank-ntarget---routine-638)
      - [`SWMG_SetGunBankTimeBetweenShots(oFollower, nGunBank, fTBS)` - Routine 635](#swmg_setgunbanktimebetweenshotsofollower-ngunbank-ftbs---routine-635)
      - [`SWMG_SetGunBankVerticalSpread(oEnemy, nGunBank, fVerticalSpread)` - Routine 662](#swmg_setgunbankverticalspreadoenemy-ngunbank-fverticalspread---routine-662)
      - [`SWMG_SetLateralAccelerationPerSecond(fLAPS)` - Routine 520](#swmg_setlateralaccelerationpersecondflaps---routine-520)
      - [`SWMG_SetMaxHitPoints(oFollower, nMaxHP)` - Routine 618](#swmg_setmaxhitpointsofollower-nmaxhp---routine-618)
      - [`SWMG_SetNumLoops(oFollower, nNumLoops)` - Routine 622](#swmg_setnumloopsofollower-nnumloops---routine-622)
      - [`SWMG_SetSphereRadius(oFollower, fRadius)` - Routine 620](#swmg_setsphereradiusofollower-fradius---routine-620)
      - [`TakeGoldFromCreature(nAmount, oCreatureToTakeFrom, bDestroy)` - Routine 444](#takegoldfromcreaturenamount-ocreaturetotakefrom-bdestroy---routine-444)
      - [`TalentSpell(nSpell)` - Routine 301](#talentspellnspell---routine-301)
      - [`tan(fValue)` - Routine 70](#tanfvalue---routine-70)
      - [`TestStringAgainstPattern(sPattern, sStringToTest)` - Routine 177](#teststringagainstpatternspattern-sstringtotest---routine-177)
      - [`TurnsToSeconds(nTurns)` - Routine 123](#turnstosecondsnturns---routine-123)
      - [`Vector(x, y, z)` - Routine 142](#vectorx-y-z---routine-142)
      - [`VectorMagnitude(vVector)` - Routine 104](#vectormagnitudevvector---routine-104)
      - [`VectorNormalize(vVector)` - Routine 137](#vectornormalizevvector---routine-137)
      - [`VectorToAngle(vVector)` - Routine 145](#vectortoanglevvector---routine-145)
      - [`WillSave(oCreature, nDC, nSaveType, oSaveVersus)` - Routine 110](#willsaveocreature-ndc-nsavetype-osaveversus---routine-110)
      - [`WriteTimestampedLogEntry(sLogEntry)` - Routine 560](#writetimestampedlogentryslogentry---routine-560)
      - [`YardsToMeters(fYards)` - Routine 219](#yardstometersfyards---routine-219)
    - [Party Management](#party-management)
      - [`AddAvailableNPCByObject(nNPC, oCreature)` - Routine 694](#addavailablenpcbyobjectnnpc-ocreature---routine-694)
      - [`AddAvailableNPCByTemplate(nNPC, sTemplate)` - Routine 697](#addavailablenpcbytemplatennpc-stemplate---routine-697)
      - [`AddPartyMember(nNPC, oCreature)` - Routine 574](#addpartymembernnpc-ocreature---routine-574)
      - [`AddToParty(oPC, oPartyLeader)` - Routine 572](#addtopartyopc-opartyleader---routine-572)
      - [`GetPartyAIStyle()` - Routine 704](#getpartyaistyle---routine-704)
      - [`GetPartyMemberByIndex(nIndex)` - Routine 577](#getpartymemberbyindexnindex---routine-577)
      - [`GetPartyMemberCount()` - Routine 126](#getpartymembercount---routine-126)
      - [`IsNPCPartyMember(nNPC)` - Routine 699](#isnpcpartymembernnpc---routine-699)
      - [`IsObjectPartyMember(oCreature)` - Routine 576](#isobjectpartymemberocreature---routine-576)
      - [`RemoveFromParty(oPC)` - Routine 573](#removefrompartyopc---routine-573)
      - [`RemovePartyMember(nNPC)` - Routine 575](#removepartymembernnpc---routine-575)
      - [`SetPartyAIStyle(nStyle)` - Routine 706](#setpartyaistylenstyle---routine-706)
      - [`SetPartyLeader(nNPC)` - Routine 13](#setpartyleadernnpc---routine-13)
      - [`ShowPartySelectionGUI(sExitScript, nForceNPC1, nForceNPC2)` - Routine 712](#showpartyselectionguisexitscript-nforcenpc1-nforcenpc2---routine-712)
      - [`SwitchPlayerCharacter(nNPC)` - Routine 11](#switchplayercharacternnpc---routine-11)
    - [Player Character Functions](#player-character-functions)
      - [`DoSinglePlayerAutoSave()` - Routine 512](#dosingleplayerautosave---routine-512)
      - [`ExploreAreaForPlayer(oArea, oPlayer)` - Routine 403](#exploreareaforplayeroarea-oplayer---routine-403)
      - [`GetIsPC(oCreature)` - Routine 217](#getispcocreature---routine-217)
      - [`GetLastPlayerDied()` - Routine 291](#getlastplayerdied---routine-291)
      - [`GetLastPlayerDying()` - Routine 410](#getlastplayerdying---routine-410)
      - [`GetPCSpeaker()` - Routine 238](#getpcspeaker---routine-238)
      - [`GetPlayerRestrictMode(oObject)` - Routine 83](#getplayerrestrictmodeoobject---routine-83)
      - [`SetPlayerRestrictMode(bRestrict)` - Routine 58](#setplayerrestrictmodebrestrict---routine-58)
      - [`SWMG_GetPlayer()` - Routine 611](#swmg_getplayer---routine-611)
      - [`SWMG_GetPlayerAccelerationPerSecond()` - Routine 645](#swmg_getplayeraccelerationpersecond---routine-645)
      - [`SWMG_GetPlayerInvincibility()` - Routine 642](#swmg_getplayerinvincibility---routine-642)
      - [`SWMG_GetPlayerMaxSpeed()` - Routine 667](#swmg_getplayermaxspeed---routine-667)
      - [`SWMG_GetPlayerMinSpeed()` - Routine 644](#swmg_getplayerminspeed---routine-644)
      - [`SWMG_GetPlayerOffset()` - Routine 641](#swmg_getplayeroffset---routine-641)
      - [`SWMG_GetPlayerOrigin()` - Routine 655](#swmg_getplayerorigin---routine-655)
      - [`SWMG_GetPlayerSpeed()` - Routine 643](#swmg_getplayerspeed---routine-643)
      - [`SWMG_GetPlayerTunnelInfinite()` - Routine 717](#swmg_getplayertunnelinfinite---routine-717)
      - [`SWMG_GetPlayerTunnelNeg()` - Routine 653](#swmg_getplayertunnelneg---routine-653)
      - [`SWMG_GetPlayerTunnelPos()` - Routine 646](#swmg_getplayertunnelpos---routine-646)
      - [`SWMG_IsPlayer(oid)` - Routine 600](#swmg_isplayeroid---routine-600)
      - [`SWMG_SetPlayerAccelerationPerSecond(fAPS)` - Routine 651](#swmg_setplayeraccelerationpersecondfaps---routine-651)
      - [`SWMG_SetPlayerInvincibility(fInvincibility)` - Routine 648](#swmg_setplayerinvincibilityfinvincibility---routine-648)
      - [`SWMG_SetPlayerMaxSpeed(fMaxSpeed)` - Routine 668](#swmg_setplayermaxspeedfmaxspeed---routine-668)
      - [`SWMG_SetPlayerMinSpeed(fMinSpeed)` - Routine 650](#swmg_setplayerminspeedfminspeed---routine-650)
      - [`SWMG_SetPlayerOffset(vOffset)` - Routine 647](#swmg_setplayeroffsetvoffset---routine-647)
      - [`SWMG_SetPlayerOrigin(vOrigin)` - Routine 656](#swmg_setplayeroriginvorigin---routine-656)
      - [`SWMG_SetPlayerSpeed(fSpeed)` - Routine 649](#swmg_setplayerspeedfspeed---routine-649)
      - [`SWMG_SetPlayerTunnelInfinite(vInfinite)` - Routine 718](#swmg_setplayertunnelinfinitevinfinite---routine-718)
      - [`SWMG_SetPlayerTunnelNeg(vTunnel)` - Routine 654](#swmg_setplayertunnelnegvtunnel---routine-654)
      - [`SWMG_SetPlayerTunnelPos(vTunnel)` - Routine 652](#swmg_setplayertunnelposvtunnel---routine-652)
    - [Skills and Feats](#skills-and-feats)
      - [`GetHasFeat(nFeat, oCreature)` - Routine 285](#gethasfeatnfeat-ocreature---routine-285)
      - [`GetHasSkill(nSkill, oCreature)` - Routine 286](#gethasskillnskill-ocreature---routine-286)
      - [`GetLastCombatFeatUsed(oAttacker)` - Routine 724](#getlastcombatfeatusedoattacker---routine-724)
      - [`GetMetaMagicFeat()` - Routine 105](#getmetamagicfeat---routine-105)
      - [`GetSkillRank(nSkill, oTarget)` - Routine 315](#getskillranknskill-otarget---routine-315)
      - [`TalentFeat(nFeat)` - Routine 302](#talentfeatnfeat---routine-302)
      - [`TalentSkill(nSkill)` - Routine 303](#talentskillnskill---routine-303)
    - [Sound and Music Functions](#sound-and-music-functions)
      - [`AmbientSoundChangeDay(oArea, nTrack)` - Routine 435](#ambientsoundchangedayoarea-ntrack---routine-435)
      - [`AmbientSoundChangeNight(oArea, nTrack)` - Routine 436](#ambientsoundchangenightoarea-ntrack---routine-436)
      - [`AmbientSoundPlay(oArea)` - Routine 433](#ambientsoundplayoarea---routine-433)
      - [`AmbientSoundSetDayVolume(oArea, nVolume)` - Routine 567](#ambientsoundsetdayvolumeoarea-nvolume---routine-567)
      - [`AmbientSoundSetNightVolume(oArea, nVolume)` - Routine 568](#ambientsoundsetnightvolumeoarea-nvolume---routine-568)
      - [`AmbientSoundStop(oArea)` - Routine 434](#ambientsoundstopoarea---routine-434)
      - [`DisplayFeedBackText(oCreature, nTextConstant)` - Routine 366](#displayfeedbacktextocreature-ntextconstant---routine-366)
      - [`GetIsPlayableRacialType(oCreature)` - Routine 312](#getisplayableracialtypeocreature---routine-312)
      - [`GetStrRefSoundDuration(nStrRef)` - Routine 571](#getstrrefsounddurationnstrref---routine-571)
      - [`IsMoviePlaying()` - Routine 768](#ismovieplaying---routine-768)
      - [`MusicBackgroundChangeDay(oArea, nTrack)` - Routine 428](#musicbackgroundchangedayoarea-ntrack---routine-428)
      - [`MusicBackgroundChangeNight(oArea, nTrack)` - Routine 429](#musicbackgroundchangenightoarea-ntrack---routine-429)
      - [`MusicBackgroundGetBattleTrack(oArea)` - Routine 569](#musicbackgroundgetbattletrackoarea---routine-569)
      - [`MusicBackgroundGetDayTrack(oArea)` - Routine 558](#musicbackgroundgetdaytrackoarea---routine-558)
      - [`MusicBackgroundGetNightTrack(oArea)` - Routine 559](#musicbackgroundgetnighttrackoarea---routine-559)
      - [`MusicBackgroundPlay(oArea)` - Routine 425](#musicbackgroundplayoarea---routine-425)
      - [`MusicBackgroundSetDelay(oArea, nDelay)` - Routine 427](#musicbackgroundsetdelayoarea-ndelay---routine-427)
      - [`MusicBackgroundStop(oArea)` - Routine 426](#musicbackgroundstopoarea---routine-426)
      - [`MusicBattleChange(oArea, nTrack)` - Routine 432](#musicbattlechangeoarea-ntrack---routine-432)
      - [`MusicBattlePlay(oArea)` - Routine 430](#musicbattleplayoarea---routine-430)
      - [`MusicBattleStop(oArea)` - Routine 431](#musicbattlestopoarea---routine-431)
      - [`PlayAnimation(nAnimation, fSpeed, fSeconds)` - Routine 300](#playanimationnanimation-fspeed-fseconds---routine-300)
      - [`PlayMovie(sMovie)` - Routine 733](#playmoviesmovie---routine-733)
      - [`PlayMovieQueue(bAllowSeparateSkips)` - Routine 770](#playmoviequeueballowseparateskips---routine-770)
      - [`PlayPazaak(nOpponentPazaakDeck, sEndScript, nMaxWager, bShowTutorial, oOpponent)` - Routine 364](#playpazaaknopponentpazaakdeck-sendscript-nmaxwager-bshowtutorial-oopponent---routine-364)
      - [`PlayRoomAnimation(sRoom, nAnimation)` - Routine 738](#playroomanimationsroom-nanimation---routine-738)
      - [`PlayRumblePattern(nPattern)` - Routine 370](#playrumblepatternnpattern---routine-370)
      - [`PlaySound(sSoundName)` - Routine 46](#playsoundssoundname---routine-46)
      - [`SetMusicVolume(fVolume)` - Routine 765](#setmusicvolumefvolume---routine-765)
      - [`SoundObjectFadeAndStop(oSound, fSeconds)` - Routine 745](#soundobjectfadeandstoposound-fseconds---routine-745)
      - [`SoundObjectGetFixedVariance(oSound)` - Routine 188](#soundobjectgetfixedvarianceosound---routine-188)
      - [`SoundObjectGetPitchVariance(oSound)` - Routine 689](#soundobjectgetpitchvarianceosound---routine-689)
      - [`SoundObjectGetVolume(oSound)` - Routine 691](#soundobjectgetvolumeosound---routine-691)
      - [`SoundObjectPlay(oSound)` - Routine 413](#soundobjectplayosound---routine-413)
      - [`SoundObjectSetFixedVariance(oSound, fFixedVariance)` - Routine 124](#soundobjectsetfixedvarianceosound-ffixedvariance---routine-124)
      - [`SoundObjectSetPitchVariance(oSound, fVariance)` - Routine 690](#soundobjectsetpitchvarianceosound-fvariance---routine-690)
      - [`SoundObjectSetPosition(oSound, vPosition)` - Routine 416](#soundobjectsetpositionosound-vposition---routine-416)
      - [`SoundObjectSetVolume(oSound, nVolume)` - Routine 415](#soundobjectsetvolumeosound-nvolume---routine-415)
      - [`SoundObjectStop(oSound)` - Routine 414](#soundobjectstoposound---routine-414)
      - [`SWMG_GetSoundFrequency(oFollower, nSound)` - Routine 683](#swmg_getsoundfrequencyofollower-nsound---routine-683)
      - [`SWMG_GetSoundFrequencyIsRandom(oFollower, nSound)` - Routine 685](#swmg_getsoundfrequencyisrandomofollower-nsound---routine-685)
      - [`SWMG_GetSoundVolume(oFollower, nSound)` - Routine 687](#swmg_getsoundvolumeofollower-nsound---routine-687)
      - [`SWMG_PlayAnimation(oObject, sAnimName, bLooping, bQueue, bOverlay)` - Routine 586](#swmg_playanimationoobject-sanimname-blooping-bqueue-boverlay---routine-586)
      - [`SWMG_SetSoundFrequency(oFollower, nSound, nFrequency)` - Routine 684](#swmg_setsoundfrequencyofollower-nsound-nfrequency---routine-684)
      - [`SWMG_SetSoundFrequencyIsRandom(oFollower, nSound, bIsRandom)` - Routine 686](#swmg_setsoundfrequencyisrandomofollower-nsound-bisrandom---routine-686)
      - [`SWMG_SetSoundVolume(oFollower, nSound, nVolume)` - Routine 688](#swmg_setsoundvolumeofollower-nsound-nvolume---routine-688)
  - [K1-Only Functions](#k1-only-functions)
    - [Other Functions](#other-functions-1)
      - [`YavinHackCloseDoor(oidDoor)` - Routine 771](#yavinhackclosedooroiddoor---routine-771)
  - [TSL-Only Functions](#tsl-only-functions)
    - [Actions](#actions-1)
      - [`ActionFollowOwner(fRange)`](#actionfollowownerfrange)
      - [`ActionSwitchWeapons()`](#actionswitchweapons)
    - [Class System](#class-system-1)
      - [`SetInputClass(nClass)`](#setinputclassnclass)
    - [Combat Functions](#combat-functions-1)
      - [`GetCombatActionsPending(oCreature)`](#getcombatactionspendingocreature)
      - [`SetFakeCombatState(oObject, nEnable)` - Routine 791](#setfakecombatstateoobject-nenable---routine-791)
    - [Dialog and Conversation Functions](#dialog-and-conversation-functions-1)
      - [`SetKeepStealthInDialog(nStealthState)`](#setkeepstealthindialognstealthstate)
    - [Effects System](#effects-system-1)
      - [`EffectBlind()` - Routine 778](#effectblind---routine-778)
      - [`EffectCrush()` - Routine 781](#effectcrush---routine-781)
      - [`EffectDroidConfused()`](#effectdroidconfused)
      - [`EffectDroidScramble()`](#effectdroidscramble)
      - [`EffectFactionModifier(nNewFaction)`](#effectfactionmodifiernnewfaction)
      - [`EffectForceBody(nLevel)` - Routine 770](#effectforcebodynlevel---routine-770)
      - [`EffectForceSight()`](#effectforcesight)
      - [`EffectFPRegenModifier(nPercent)` - Routine 779](#effectfpregenmodifiernpercent---routine-779)
      - [`EffectFury()` - Routine 777](#effectfury---routine-777)
      - [`EffectMindTrick()`](#effectmindtrick)
      - [`EffectVPRegenModifier(nPercent)` - Routine 780](#effectvpregenmodifiernpercent---routine-780)
      - [`RemoveEffectByExactMatch(oCreature, eEffect)`](#removeeffectbyexactmatchocreature-eeffect)
      - [`RemoveEffectByID(oCreature, nEffectID)`](#removeeffectbyidocreature-neffectid)
    - [Global Variables](#global-variables-1)
      - [`DecrementGlobalNumber(sIdentifier, nAmount)` - Routine 800](#decrementglobalnumbersidentifier-namount---routine-800)
      - [`IncrementGlobalNumber(sIdentifier, nAmount)` - Routine 799](#incrementglobalnumbersidentifier-namount---routine-799)
    - [Item Management](#item-management-1)
      - [`GetItemComponent()` - Routine 771](#getitemcomponent---routine-771)
      - [`GetItemComponentPieceValue()` - Routine 771](#getitemcomponentpiecevalue---routine-771)
    - [Object Query and Manipulation](#object-query-and-manipulation-1)
      - [`GetObjectPersonalSpace(aObject)`](#getobjectpersonalspaceaobject)
    - [Other Functions](#other-functions-2)
      - [`AddBonusForcePoints(oCreature, nBonusFP)` - Routine 802](#addbonusforcepointsocreature-nbonusfp---routine-802)
      - [`AdjustCreatureAttributes(oObject, nAttribute, nAmount)`](#adjustcreatureattributesoobject-nattribute-namount)
      - [`AssignPUP(nPUP, nNPC)`](#assignpupnpup-nnpc)
      - [`ChangeObjectAppearance(oObjectToChange, nAppearance)`](#changeobjectappearanceoobjecttochange-nappearance)
      - [`CreatureFlourishWeapon(oObject)`](#creatureflourishweaponoobject)
      - [`DetonateMine(oMine)`](#detonatemineomine)
      - [`DisableHealthRegen(nFlag)`](#disablehealthregennflag)
      - [`DisableMap(nFlag)`](#disablemapnflag)
      - [`EnableRain(nFlag)`](#enablerainnflag)
      - [`EnableRendering(oObject, bEnable)`](#enablerenderingoobject-benable)
      - [`ForceHeartbeat(oCreature)`](#forceheartbeatocreature)
      - [`GetBonusForcePoints(oCreature)` - Routine 803](#getbonusforcepointsocreature---routine-803)
      - [`GetChemicalPieceValue()` - Routine 775](#getchemicalpiecevalue---routine-775)
      - [`GetChemicals()` - Routine 774](#getchemicals---routine-774)
      - [`GetHealTarget(oidHealer)`](#gethealtargetoidhealer)
      - [`GetInfluence(nNPC)` - Routine 795](#getinfluencennpc---routine-795)
      - [`GetIsPuppet(oPUP)`](#getispuppetopup)
      - [`GetIsXBox()`](#getisxbox)
      - [`GetLastForfeitViolation()`](#getlastforfeitviolation)
      - [`GetPUPOwner(oPUP)`](#getpupowneropup)
      - [`GetRacialSubType(oTarget)` - Routine 798](#getracialsubtypeotarget---routine-798)
      - [`GetRandomDestination(oCreature, rangeLimit)`](#getrandomdestinationocreature-rangelimit)
      - [`GetScriptParameter(nIndex)` - Routine 768](#getscriptparameternindex---routine-768)
      - [`GetScriptStringParameter()`](#getscriptstringparameter)
      - [`GetSpellAcquired(nSpell, oCreature)` - Routine 377](#getspellacquirednspell-ocreature---routine-377)
      - [`GetSpellBaseForcePointCost(nSpellID)`](#getspellbaseforcepointcostnspellid)
      - [`GetSpellForcePointCost()` - Routine 776](#getspellforcepointcost---routine-776)
      - [`GetSpellFormMask(nSpellID)`](#getspellformmasknspellid)
      - [`GrantSpell(nSpell, oCreature)` - Routine 787](#grantspellnspell-ocreature---routine-787)
      - [`HasLineOfSight(vSource, vTarget, oSource, oTarget)`](#haslineofsightvsource-vtarget-osource-otarget)
      - [`IsFormActive(oCreature, nFormID)`](#isformactiveocreature-nformid)
      - [`IsInTotalDefense(oCreature)`](#isintotaldefenseocreature)
      - [`IsMeditating(oCreature)`](#ismeditatingocreature)
      - [`IsRunning(oCreature)`](#isrunningocreature)
      - [`IsStealthed(oCreature)`](#isstealthedocreature)
      - [`ModifyFortitudeSavingThrowBase(aObject, aModValue)`](#modifyfortitudesavingthrowbaseaobject-amodvalue)
      - [`ModifyInfluence(nNPC, nModifier)` - Routine 797](#modifyinfluencennpc-nmodifier---routine-797)
      - [`ModifyReflexSavingThrowBase(aObject, aModValue)`](#modifyreflexsavingthrowbaseaobject-amodvalue)
      - [`ModifyWillSavingThrowBase(aObject, aModValue)`](#modifywillsavingthrowbaseaobject-amodvalue)
      - [`RemoveHeartbeat(oPlaceable)`](#removeheartbeatoplaceable)
      - [`ResetCreatureAILevel(oObject)`](#resetcreatureaileveloobject)
      - [`SaveNPCByObject(nNPC, oidCharacter)`](#savenpcbyobjectnnpc-oidcharacter)
      - [`SavePUPByObject(nPUP, oidPuppet)`](#savepupbyobjectnpup-oidpuppet)
      - [`SetBonusForcePoints(oCreature, nBonusFP)` - Routine 801](#setbonusforcepointsocreature-nbonusfp---routine-801)
      - [`SetCreatureAILevel(oObject, nPriority)`](#setcreatureaileveloobject-npriority)
      - [`SetCurrentForm(oCreature, nFormID)`](#setcurrentformocreature-nformid)
      - [`SetDisableTransit(nFlag)`](#setdisabletransitnflag)
      - [`SetFadeUntilScript()` - Routine 769](#setfadeuntilscript---routine-769)
      - [`SetForceAlwaysUpdate(oObject, nFlag)`](#setforcealwaysupdateoobject-nflag)
      - [`SetForfeitConditions(nForfeitFlags)`](#setforfeitconditionsnforfeitflags)
      - [`SetHealTarget(oidHealer, oidTarget)`](#sethealtargetoidhealer-oidtarget)
      - [`SetInfluence(nNPC, nInfluence)` - Routine 796](#setinfluencennpc-ninfluence---routine-796)
      - [`SetOrientOnClick(oCreature, nState)` - Routine 794](#setorientonclickocreature-nstate---routine-794)
      - [`ShowChemicalUpgradeScreen(oCharacter)` - Routine 773](#showchemicalupgradescreenocharacter---routine-773)
      - [`ShowDemoScreen(sTexture, nTimeout, nDisplayString, nDisplayX, nDisplayY)`](#showdemoscreenstexture-ntimeout-ndisplaystring-ndisplayx-ndisplayy)
      - [`ShowSwoopUpgradeScreen()` - Routine 785](#showswoopupgradescreen---routine-785)
      - [`SpawnAvailablePUP(nPUP, lLocation)`](#spawnavailablepupnpup-llocation)
      - [`SpawnMine(nMineType, lPoint, nDetectDCBase, nDisarmDCBase, oCreator)` - Routine 788](#spawnminenminetype-lpoint-ndetectdcbase-ndisarmdcbase-ocreator---routine-788)
      - [`SWMG_DestroyMiniGameObject(oObject)` - Routine 792](#swmg_destroyminigameobjectoobject---routine-792)
      - [`SWMG_GetSwoopUpgrade(nSlot)` - Routine 782](#swmg_getswoopupgradenslot---routine-782)
      - [`SWMG_GetTrackPosition(oFollower)` - Routine 789](#swmg_gettrackpositionofollower---routine-789)
      - [`SWMG_SetFollowerPosition(vPos)` - Routine 790](#swmg_setfollowerpositionvpos---routine-790)
      - [`SWMG_SetJumpSpeed(fSpeed)` - Routine 804](#swmg_setjumpspeedfspeed---routine-804)
      - [`UnlockAllSongs()`](#unlockallsongs)
      - [`YavinHackDoorClose(oCreature)`](#yavinhackdoorcloseocreature)
    - [Party Management](#party-management-1)
      - [`AddAvailablePUPByObject(nPUP, oPuppet)`](#addavailablepupbyobjectnpup-opuppet)
      - [`AddAvailablePUPByTemplate(nPUP, sTemplate)`](#addavailablepupbytemplatenpup-stemplate)
      - [`AddPartyPuppet(nPUP, oidCreature)`](#addpartypuppetnpup-oidcreature)
      - [`GetIsPartyLeader(oCharacter)`](#getispartyleaderocharacter)
      - [`GetPartyLeader()`](#getpartyleader)
      - [`RemoveNPCFromPartyToBase(nNPC)`](#removenpcfrompartytobasennpc)
    - [Player Character Functions](#player-character-functions-1)
      - [`GetIsPlayerMadeCharacter(oidCharacter)`](#getisplayermadecharacteroidcharacter)
      - [`SWMG_PlayerApplyForce(vForce)`](#swmg_playerapplyforcevforce)
    - [Skills and Feats](#skills-and-feats-1)
      - [`AdjustCreatureSkills(oObject, nSkill, nAmount)`](#adjustcreatureskillsoobject-nskill-namount)
      - [`GetFeatAcquired(nFeat, oCreature)` - Routine 285](#getfeatacquirednfeat-ocreature---routine-285)
      - [`GetOwnerDemolitionsSkill(oObject)` - Routine 793](#getownerdemolitionsskilloobject---routine-793)
      - [`GetSkillRankBase(nSkill, oObject)`](#getskillrankbasenskill-oobject)
      - [`GrantFeat(nFeat, oCreature)` - Routine 786](#grantfeatnfeat-ocreature---routine-786)
    - [Sound and Music Functions](#sound-and-music-functions-1)
      - [`DisplayDatapad(oDatapad)`](#displaydatapadodatapad)
      - [`DisplayMessageBox(nStrRef, sIcon)`](#displaymessageboxnstrref-sicon)
      - [`PlayOverlayAnimation(oTarget, nAnimation)`](#playoverlayanimationotarget-nanimation)
  - [Shared Constants (K1 \& TSL)](#shared-constants-k1--tsl)
    - [Ability Constants](#ability-constants)
      - [`ABILITY_CHARISMA`](#ability_charisma)
      - [`ABILITY_CONSTITUTION`](#ability_constitution)
      - [`ABILITY_DEXTERITY`](#ability_dexterity)
      - [`ABILITY_INTELLIGENCE`](#ability_intelligence)
      - [`ABILITY_STRENGTH`](#ability_strength)
      - [`ABILITY_WISDOM`](#ability_wisdom)
    - [Alignment Constants](#alignment-constants)
      - [`ALIGNMENT_ALL`](#alignment_all)
      - [`ALIGNMENT_DARK_SIDE`](#alignment_dark_side)
      - [`ALIGNMENT_LIGHT_SIDE`](#alignment_light_side)
      - [`ALIGNMENT_NEUTRAL`](#alignment_neutral)
      - [`ITEM_PROPERTY_AC_BONUS_VS_ALIGNMENT_GROUP`](#item_property_ac_bonus_vs_alignment_group)
      - [`ITEM_PROPERTY_ATTACK_BONUS_VS_ALIGNMENT_GROUP`](#item_property_attack_bonus_vs_alignment_group)
      - [`ITEM_PROPERTY_DAMAGE_BONUS_VS_ALIGNMENT_GROUP`](#item_property_damage_bonus_vs_alignment_group)
      - [`ITEM_PROPERTY_ENHANCEMENT_BONUS_VS_ALIGNMENT_GROUP`](#item_property_enhancement_bonus_vs_alignment_group)
      - [`ITEM_PROPERTY_USE_LIMITATION_ALIGNMENT_GROUP`](#item_property_use_limitation_alignment_group)
    - [Class Type Constants](#class-type-constants)
      - [`CLASS_TYPE_COMBATDROID`](#class_type_combatdroid)
      - [`CLASS_TYPE_EXPERTDROID`](#class_type_expertdroid)
      - [`CLASS_TYPE_INVALID`](#class_type_invalid)
      - [`CLASS_TYPE_JEDICONSULAR`](#class_type_jediconsular)
      - [`CLASS_TYPE_JEDIGUARDIAN`](#class_type_jediguardian)
      - [`CLASS_TYPE_JEDISENTINEL`](#class_type_jedisentinel)
      - [`CLASS_TYPE_MINION`](#class_type_minion)
      - [`CLASS_TYPE_SCOUNDREL`](#class_type_scoundrel)
      - [`CLASS_TYPE_SCOUT`](#class_type_scout)
      - [`CLASS_TYPE_SOLDIER`](#class_type_soldier)
    - [Inventory Constants](#inventory-constants)
      - [`INVENTORY_DISTURB_TYPE_ADDED`](#inventory_disturb_type_added)
      - [`INVENTORY_DISTURB_TYPE_REMOVED`](#inventory_disturb_type_removed)
      - [`INVENTORY_DISTURB_TYPE_STOLEN`](#inventory_disturb_type_stolen)
      - [`INVENTORY_SLOT_BELT`](#inventory_slot_belt)
      - [`INVENTORY_SLOT_BODY`](#inventory_slot_body)
      - [`INVENTORY_SLOT_CARMOUR`](#inventory_slot_carmour)
      - [`INVENTORY_SLOT_CWEAPON_B`](#inventory_slot_cweapon_b)
      - [`INVENTORY_SLOT_CWEAPON_L`](#inventory_slot_cweapon_l)
      - [`INVENTORY_SLOT_CWEAPON_R`](#inventory_slot_cweapon_r)
      - [`INVENTORY_SLOT_HANDS`](#inventory_slot_hands)
      - [`INVENTORY_SLOT_HEAD`](#inventory_slot_head)
      - [`INVENTORY_SLOT_IMPLANT`](#inventory_slot_implant)
      - [`INVENTORY_SLOT_LEFTARM`](#inventory_slot_leftarm)
      - [`INVENTORY_SLOT_LEFTWEAPON`](#inventory_slot_leftweapon)
      - [`INVENTORY_SLOT_RIGHTARM`](#inventory_slot_rightarm)
      - [`INVENTORY_SLOT_RIGHTWEAPON`](#inventory_slot_rightweapon)
      - [`NUM_INVENTORY_SLOTS`](#num_inventory_slots)
    - [NPC Constants](#npc-constants)
      - [`NPC_AISTYLE_AID`](#npc_aistyle_aid)
      - [`NPC_AISTYLE_DEFAULT_ATTACK`](#npc_aistyle_default_attack)
      - [`NPC_AISTYLE_GRENADE_THROWER`](#npc_aistyle_grenade_thrower)
      - [`NPC_AISTYLE_JEDI_SUPPORT`](#npc_aistyle_jedi_support)
      - [`NPC_AISTYLE_MELEE_ATTACK`](#npc_aistyle_melee_attack)
      - [`NPC_AISTYLE_RANGED_ATTACK`](#npc_aistyle_ranged_attack)
      - [`NPC_CANDEROUS`](#npc_canderous)
      - [`NPC_HK_47`](#npc_hk_47)
      - [`NPC_PLAYER`](#npc_player)
      - [`NPC_T3_M4`](#npc_t3_m4)
    - [Object Type Constants](#object-type-constants)
      - [`OBJECT_TYPE_ALL`](#object_type_all)
      - [`OBJECT_TYPE_AREA_OF_EFFECT`](#object_type_area_of_effect)
      - [`OBJECT_TYPE_CREATURE`](#object_type_creature)
      - [`OBJECT_TYPE_DOOR`](#object_type_door)
      - [`OBJECT_TYPE_ENCOUNTER`](#object_type_encounter)
      - [`OBJECT_TYPE_INVALID`](#object_type_invalid)
      - [`OBJECT_TYPE_ITEM`](#object_type_item)
      - [`OBJECT_TYPE_PLACEABLE`](#object_type_placeable)
      - [`OBJECT_TYPE_SOUND`](#object_type_sound)
      - [`OBJECT_TYPE_STORE`](#object_type_store)
      - [`OBJECT_TYPE_TRIGGER`](#object_type_trigger)
      - [`OBJECT_TYPE_WAYPOINT`](#object_type_waypoint)
    - [Other Constants](#other-constants)
      - [`AC_ARMOUR_ENCHANTMENT_BONUS`](#ac_armour_enchantment_bonus)
      - [`AC_DEFLECTION_BONUS`](#ac_deflection_bonus)
      - [`AC_DODGE_BONUS`](#ac_dodge_bonus)
      - [`AC_NATURAL_BONUS`](#ac_natural_bonus)
      - [`AC_SHIELD_ENCHANTMENT_BONUS`](#ac_shield_enchantment_bonus)
      - [`AC_VS_DAMAGE_TYPE_ALL`](#ac_vs_damage_type_all)
      - [`ACTION_ANIMALEMPATHY`](#action_animalempathy)
      - [`ACTION_ATTACKOBJECT`](#action_attackobject)
      - [`ACTION_CASTSPELL`](#action_castspell)
      - [`ACTION_CLOSEDOOR`](#action_closedoor)
      - [`ACTION_COUNTERSPELL`](#action_counterspell)
      - [`ACTION_DIALOGOBJECT`](#action_dialogobject)
      - [`ACTION_DISABLETRAP`](#action_disabletrap)
      - [`ACTION_DROPITEM`](#action_dropitem)
      - [`ACTION_EXAMINETRAP`](#action_examinetrap)
      - [`ACTION_FLAGTRAP`](#action_flagtrap)
      - [`ACTION_FOLLOW`](#action_follow)
      - [`ACTION_FOLLOWLEADER`](#action_followleader)
      - [`ACTION_HEAL`](#action_heal)
      - [`ACTION_INVALID`](#action_invalid)
      - [`ACTION_ITEMCASTSPELL`](#action_itemcastspell)
      - [`ACTION_LOCK`](#action_lock)
      - [`ACTION_MOVETOPOINT`](#action_movetopoint)
      - [`ACTION_OPENDOOR`](#action_opendoor)
      - [`ACTION_OPENLOCK`](#action_openlock)
      - [`ACTION_PICKPOCKET`](#action_pickpocket)
      - [`ACTION_PICKUPITEM`](#action_pickupitem)
      - [`ACTION_QUEUEEMPTY`](#action_queueempty)
      - [`ACTION_RECOVERTRAP`](#action_recovertrap)
      - [`ACTION_REST`](#action_rest)
      - [`ACTION_SETTRAP`](#action_settrap)
      - [`ACTION_SIT`](#action_sit)
      - [`ACTION_TAUNT`](#action_taunt)
      - [`ACTION_USEOBJECT`](#action_useobject)
      - [`ACTION_WAIT`](#action_wait)
      - [`ANIMATION_FIREFORGET_ACTIVATE`](#animation_fireforget_activate)
      - [`ANIMATION_FIREFORGET_BOW`](#animation_fireforget_bow)
      - [`ANIMATION_FIREFORGET_CHOKE`](#animation_fireforget_choke)
      - [`ANIMATION_FIREFORGET_CUSTOM01`](#animation_fireforget_custom01)
      - [`ANIMATION_FIREFORGET_GREETING`](#animation_fireforget_greeting)
      - [`ANIMATION_FIREFORGET_HEAD_TURN_LEFT`](#animation_fireforget_head_turn_left)
      - [`ANIMATION_FIREFORGET_HEAD_TURN_RIGHT`](#animation_fireforget_head_turn_right)
      - [`ANIMATION_FIREFORGET_INJECT`](#animation_fireforget_inject)
      - [`ANIMATION_FIREFORGET_PAUSE_BORED`](#animation_fireforget_pause_bored)
      - [`ANIMATION_FIREFORGET_PAUSE_SCRATCH_HEAD`](#animation_fireforget_pause_scratch_head)
      - [`ANIMATION_FIREFORGET_PERSUADE`](#animation_fireforget_persuade)
      - [`ANIMATION_FIREFORGET_SALUTE`](#animation_fireforget_salute)
      - [`ANIMATION_FIREFORGET_TAUNT`](#animation_fireforget_taunt)
      - [`ANIMATION_FIREFORGET_THROW_HIGH`](#animation_fireforget_throw_high)
      - [`ANIMATION_FIREFORGET_THROW_LOW`](#animation_fireforget_throw_low)
      - [`ANIMATION_FIREFORGET_TREAT_INJURED`](#animation_fireforget_treat_injured)
      - [`ANIMATION_FIREFORGET_USE_COMPUTER`](#animation_fireforget_use_computer)
      - [`ANIMATION_FIREFORGET_VICTORY1`](#animation_fireforget_victory1)
      - [`ANIMATION_FIREFORGET_VICTORY2`](#animation_fireforget_victory2)
      - [`ANIMATION_FIREFORGET_VICTORY3`](#animation_fireforget_victory3)
      - [`ANIMATION_LOOPING_CHOKE`](#animation_looping_choke)
      - [`ANIMATION_LOOPING_DANCE`](#animation_looping_dance)
      - [`ANIMATION_LOOPING_DANCE1`](#animation_looping_dance1)
      - [`ANIMATION_LOOPING_DEACTIVATE`](#animation_looping_deactivate)
      - [`ANIMATION_LOOPING_DEAD`](#animation_looping_dead)
      - [`ANIMATION_LOOPING_DEAD_PRONE`](#animation_looping_dead_prone)
      - [`ANIMATION_LOOPING_FLIRT`](#animation_looping_flirt)
      - [`ANIMATION_LOOPING_GET_LOW`](#animation_looping_get_low)
      - [`ANIMATION_LOOPING_GET_MID`](#animation_looping_get_mid)
      - [`ANIMATION_LOOPING_HORROR`](#animation_looping_horror)
      - [`ANIMATION_LOOPING_KNEEL_TALK_ANGRY`](#animation_looping_kneel_talk_angry)
      - [`ANIMATION_LOOPING_KNEEL_TALK_SAD`](#animation_looping_kneel_talk_sad)
      - [`ANIMATION_LOOPING_LISTEN`](#animation_looping_listen)
      - [`ANIMATION_LOOPING_LISTEN_INJURED`](#animation_looping_listen_injured)
      - [`ANIMATION_LOOPING_MEDITATE`](#animation_looping_meditate)
      - [`ANIMATION_LOOPING_PAUSE`](#animation_looping_pause)
      - [`ANIMATION_LOOPING_PAUSE2`](#animation_looping_pause2)
      - [`ANIMATION_LOOPING_PAUSE3`](#animation_looping_pause3)
      - [`ANIMATION_LOOPING_PAUSE_DRUNK`](#animation_looping_pause_drunk)
      - [`ANIMATION_LOOPING_PAUSE_TIRED`](#animation_looping_pause_tired)
      - [`ANIMATION_LOOPING_PRONE`](#animation_looping_prone)
      - [`ANIMATION_LOOPING_READY`](#animation_looping_ready)
      - [`ANIMATION_LOOPING_SLEEP`](#animation_looping_sleep)
      - [`ANIMATION_LOOPING_SPASM`](#animation_looping_spasm)
      - [`ANIMATION_LOOPING_TALK_FORCEFUL`](#animation_looping_talk_forceful)
      - [`ANIMATION_LOOPING_TALK_INJURED`](#animation_looping_talk_injured)
      - [`ANIMATION_LOOPING_TALK_LAUGHING`](#animation_looping_talk_laughing)
      - [`ANIMATION_LOOPING_TALK_NORMAL`](#animation_looping_talk_normal)
      - [`ANIMATION_LOOPING_TALK_PLEADING`](#animation_looping_talk_pleading)
      - [`ANIMATION_LOOPING_TALK_SAD`](#animation_looping_talk_sad)
      - [`ANIMATION_LOOPING_TREAT_INJURED`](#animation_looping_treat_injured)
      - [`ANIMATION_LOOPING_USE_COMPUTER`](#animation_looping_use_computer)
      - [`ANIMATION_LOOPING_WELD`](#animation_looping_weld)
      - [`ANIMATION_LOOPING_WORSHIP`](#animation_looping_worship)
      - [`ANIMATION_PLACEABLE_ACTIVATE`](#animation_placeable_activate)
      - [`ANIMATION_PLACEABLE_ANIMLOOP01`](#animation_placeable_animloop01)
      - [`ANIMATION_PLACEABLE_ANIMLOOP02`](#animation_placeable_animloop02)
      - [`ANIMATION_PLACEABLE_ANIMLOOP03`](#animation_placeable_animloop03)
      - [`ANIMATION_PLACEABLE_ANIMLOOP04`](#animation_placeable_animloop04)
      - [`ANIMATION_PLACEABLE_ANIMLOOP05`](#animation_placeable_animloop05)
      - [`ANIMATION_PLACEABLE_ANIMLOOP06`](#animation_placeable_animloop06)
      - [`ANIMATION_PLACEABLE_ANIMLOOP07`](#animation_placeable_animloop07)
      - [`ANIMATION_PLACEABLE_ANIMLOOP08`](#animation_placeable_animloop08)
      - [`ANIMATION_PLACEABLE_ANIMLOOP09`](#animation_placeable_animloop09)
      - [`ANIMATION_PLACEABLE_ANIMLOOP10`](#animation_placeable_animloop10)
      - [`ANIMATION_PLACEABLE_CLOSE`](#animation_placeable_close)
      - [`ANIMATION_PLACEABLE_DEACTIVATE`](#animation_placeable_deactivate)
      - [`ANIMATION_PLACEABLE_OPEN`](#animation_placeable_open)
      - [`ANIMATION_ROOM_SCRIPTLOOP01`](#animation_room_scriptloop01)
      - [`ANIMATION_ROOM_SCRIPTLOOP02`](#animation_room_scriptloop02)
      - [`ANIMATION_ROOM_SCRIPTLOOP03`](#animation_room_scriptloop03)
      - [`ANIMATION_ROOM_SCRIPTLOOP04`](#animation_room_scriptloop04)
      - [`ANIMATION_ROOM_SCRIPTLOOP05`](#animation_room_scriptloop05)
      - [`ANIMATION_ROOM_SCRIPTLOOP06`](#animation_room_scriptloop06)
      - [`ANIMATION_ROOM_SCRIPTLOOP07`](#animation_room_scriptloop07)
      - [`ANIMATION_ROOM_SCRIPTLOOP08`](#animation_room_scriptloop08)
      - [`ANIMATION_ROOM_SCRIPTLOOP09`](#animation_room_scriptloop09)
      - [`ANIMATION_ROOM_SCRIPTLOOP10`](#animation_room_scriptloop10)
      - [`ANIMATION_ROOM_SCRIPTLOOP11`](#animation_room_scriptloop11)
      - [`ANIMATION_ROOM_SCRIPTLOOP12`](#animation_room_scriptloop12)
      - [`ANIMATION_ROOM_SCRIPTLOOP13`](#animation_room_scriptloop13)
      - [`ANIMATION_ROOM_SCRIPTLOOP14`](#animation_room_scriptloop14)
      - [`ANIMATION_ROOM_SCRIPTLOOP15`](#animation_room_scriptloop15)
      - [`ANIMATION_ROOM_SCRIPTLOOP16`](#animation_room_scriptloop16)
      - [`ANIMATION_ROOM_SCRIPTLOOP17`](#animation_room_scriptloop17)
      - [`ANIMATION_ROOM_SCRIPTLOOP18`](#animation_room_scriptloop18)
      - [`ANIMATION_ROOM_SCRIPTLOOP19`](#animation_room_scriptloop19)
      - [`ANIMATION_ROOM_SCRIPTLOOP20`](#animation_room_scriptloop20)
      - [`AOE_MOB_BLINDING`](#aoe_mob_blinding)
      - [`AOE_MOB_CIRCCHAOS`](#aoe_mob_circchaos)
      - [`AOE_MOB_CIRCEVIL`](#aoe_mob_circevil)
      - [`AOE_MOB_CIRCGOOD`](#aoe_mob_circgood)
      - [`AOE_MOB_CIRCLAW`](#aoe_mob_circlaw)
      - [`AOE_MOB_DRAGON_FEAR`](#aoe_mob_dragon_fear)
      - [`AOE_MOB_ELECTRICAL`](#aoe_mob_electrical)
      - [`AOE_MOB_FEAR`](#aoe_mob_fear)
      - [`AOE_MOB_FIRE`](#aoe_mob_fire)
      - [`AOE_MOB_FROST`](#aoe_mob_frost)
      - [`AOE_MOB_INVISIBILITY_PURGE`](#aoe_mob_invisibility_purge)
      - [`AOE_MOB_MENACE`](#aoe_mob_menace)
      - [`AOE_MOB_PROTECTION`](#aoe_mob_protection)
      - [`AOE_MOB_SILENCE`](#aoe_mob_silence)
      - [`AOE_MOB_STUN`](#aoe_mob_stun)
      - [`AOE_MOB_TYRANT_FOG`](#aoe_mob_tyrant_fog)
      - [`AOE_MOB_UNEARTHLY`](#aoe_mob_unearthly)
      - [`AOE_MOB_UNNATURAL`](#aoe_mob_unnatural)
      - [`AOE_PER_CREEPING_DOOM`](#aoe_per_creeping_doom)
      - [`AOE_PER_DARKNESS`](#aoe_per_darkness)
      - [`AOE_PER_DELAY_BLAST_FIREBALL`](#aoe_per_delay_blast_fireball)
      - [`AOE_PER_ENTANGLE`](#aoe_per_entangle)
      - [`AOE_PER_EVARDS_BLACK_TENTACLES`](#aoe_per_evards_black_tentacles)
      - [`AOE_PER_FOGACID`](#aoe_per_fogacid)
      - [`AOE_PER_FOGFIRE`](#aoe_per_fogfire)
      - [`AOE_PER_FOGGHOUL`](#aoe_per_fogghoul)
      - [`AOE_PER_FOGKILL`](#aoe_per_fogkill)
      - [`AOE_PER_FOGMIND`](#aoe_per_fogmind)
      - [`AOE_PER_FOGSTINK`](#aoe_per_fogstink)
      - [`AOE_PER_GREASE`](#aoe_per_grease)
      - [`AOE_PER_INVIS_SPHERE`](#aoe_per_invis_sphere)
      - [`AOE_PER_STORM`](#aoe_per_storm)
      - [`AOE_PER_WALLBLADE`](#aoe_per_wallblade)
      - [`AOE_PER_WALLFIRE`](#aoe_per_wallfire)
      - [`AOE_PER_WALLWIND`](#aoe_per_wallwind)
      - [`AOE_PER_WEB`](#aoe_per_web)
      - [`AREA_TRANSITION_CASTLE_01`](#area_transition_castle_01)
      - [`AREA_TRANSITION_CASTLE_02`](#area_transition_castle_02)
      - [`AREA_TRANSITION_CASTLE_03`](#area_transition_castle_03)
      - [`AREA_TRANSITION_CASTLE_04`](#area_transition_castle_04)
      - [`AREA_TRANSITION_CASTLE_05`](#area_transition_castle_05)
      - [`AREA_TRANSITION_CASTLE_06`](#area_transition_castle_06)
      - [`AREA_TRANSITION_CASTLE_07`](#area_transition_castle_07)
      - [`AREA_TRANSITION_CASTLE_08`](#area_transition_castle_08)
      - [`AREA_TRANSITION_CITY`](#area_transition_city)
      - [`AREA_TRANSITION_CITY_01`](#area_transition_city_01)
      - [`AREA_TRANSITION_CITY_02`](#area_transition_city_02)
      - [`AREA_TRANSITION_CITY_03`](#area_transition_city_03)
      - [`AREA_TRANSITION_CITY_04`](#area_transition_city_04)
      - [`AREA_TRANSITION_CITY_05`](#area_transition_city_05)
      - [`AREA_TRANSITION_CRYPT`](#area_transition_crypt)
      - [`AREA_TRANSITION_CRYPT_01`](#area_transition_crypt_01)
      - [`AREA_TRANSITION_CRYPT_02`](#area_transition_crypt_02)
      - [`AREA_TRANSITION_CRYPT_03`](#area_transition_crypt_03)
      - [`AREA_TRANSITION_CRYPT_04`](#area_transition_crypt_04)
      - [`AREA_TRANSITION_CRYPT_05`](#area_transition_crypt_05)
      - [`AREA_TRANSITION_DUNGEON_01`](#area_transition_dungeon_01)
      - [`AREA_TRANSITION_DUNGEON_02`](#area_transition_dungeon_02)
      - [`AREA_TRANSITION_DUNGEON_03`](#area_transition_dungeon_03)
      - [`AREA_TRANSITION_DUNGEON_04`](#area_transition_dungeon_04)
      - [`AREA_TRANSITION_DUNGEON_05`](#area_transition_dungeon_05)
      - [`AREA_TRANSITION_DUNGEON_06`](#area_transition_dungeon_06)
      - [`AREA_TRANSITION_DUNGEON_07`](#area_transition_dungeon_07)
      - [`AREA_TRANSITION_DUNGEON_08`](#area_transition_dungeon_08)
      - [`AREA_TRANSITION_FOREST`](#area_transition_forest)
      - [`AREA_TRANSITION_FOREST_01`](#area_transition_forest_01)
      - [`AREA_TRANSITION_FOREST_02`](#area_transition_forest_02)
      - [`AREA_TRANSITION_FOREST_03`](#area_transition_forest_03)
      - [`AREA_TRANSITION_FOREST_04`](#area_transition_forest_04)
      - [`AREA_TRANSITION_FOREST_05`](#area_transition_forest_05)
      - [`AREA_TRANSITION_INTERIOR_01`](#area_transition_interior_01)
      - [`AREA_TRANSITION_INTERIOR_02`](#area_transition_interior_02)
      - [`AREA_TRANSITION_INTERIOR_03`](#area_transition_interior_03)
      - [`AREA_TRANSITION_INTERIOR_04`](#area_transition_interior_04)
      - [`AREA_TRANSITION_INTERIOR_05`](#area_transition_interior_05)
      - [`AREA_TRANSITION_INTERIOR_06`](#area_transition_interior_06)
      - [`AREA_TRANSITION_INTERIOR_07`](#area_transition_interior_07)
      - [`AREA_TRANSITION_INTERIOR_08`](#area_transition_interior_08)
      - [`AREA_TRANSITION_INTERIOR_09`](#area_transition_interior_09)
      - [`AREA_TRANSITION_INTERIOR_10`](#area_transition_interior_10)
      - [`AREA_TRANSITION_INTERIOR_11`](#area_transition_interior_11)
      - [`AREA_TRANSITION_INTERIOR_12`](#area_transition_interior_12)
      - [`AREA_TRANSITION_INTERIOR_13`](#area_transition_interior_13)
      - [`AREA_TRANSITION_INTERIOR_14`](#area_transition_interior_14)
      - [`AREA_TRANSITION_INTERIOR_15`](#area_transition_interior_15)
      - [`AREA_TRANSITION_INTERIOR_16`](#area_transition_interior_16)
      - [`AREA_TRANSITION_MINES_01`](#area_transition_mines_01)
      - [`AREA_TRANSITION_MINES_02`](#area_transition_mines_02)
      - [`AREA_TRANSITION_MINES_03`](#area_transition_mines_03)
      - [`AREA_TRANSITION_MINES_04`](#area_transition_mines_04)
      - [`AREA_TRANSITION_MINES_05`](#area_transition_mines_05)
      - [`AREA_TRANSITION_MINES_06`](#area_transition_mines_06)
      - [`AREA_TRANSITION_MINES_07`](#area_transition_mines_07)
      - [`AREA_TRANSITION_MINES_08`](#area_transition_mines_08)
      - [`AREA_TRANSITION_MINES_09`](#area_transition_mines_09)
      - [`AREA_TRANSITION_RANDOM`](#area_transition_random)
      - [`AREA_TRANSITION_RURAL`](#area_transition_rural)
      - [`AREA_TRANSITION_RURAL_01`](#area_transition_rural_01)
      - [`AREA_TRANSITION_RURAL_02`](#area_transition_rural_02)
      - [`AREA_TRANSITION_RURAL_03`](#area_transition_rural_03)
      - [`AREA_TRANSITION_RURAL_04`](#area_transition_rural_04)
      - [`AREA_TRANSITION_RURAL_05`](#area_transition_rural_05)
      - [`AREA_TRANSITION_SEWER_01`](#area_transition_sewer_01)
      - [`AREA_TRANSITION_SEWER_02`](#area_transition_sewer_02)
      - [`AREA_TRANSITION_SEWER_03`](#area_transition_sewer_03)
      - [`AREA_TRANSITION_SEWER_04`](#area_transition_sewer_04)
      - [`AREA_TRANSITION_SEWER_05`](#area_transition_sewer_05)
      - [`AREA_TRANSITION_USER_DEFINED`](#area_transition_user_defined)
      - [`ATTACK_BONUS_MISC`](#attack_bonus_misc)
      - [`ATTACK_BONUS_OFFHAND`](#attack_bonus_offhand)
      - [`ATTACK_BONUS_ONHAND`](#attack_bonus_onhand)
      - [`ATTACK_RESULT_ATTACK_FAILED`](#attack_result_attack_failed)
      - [`ATTACK_RESULT_ATTACK_RESISTED`](#attack_result_attack_resisted)
      - [`ATTACK_RESULT_AUTOMATIC_HIT`](#attack_result_automatic_hit)
      - [`ATTACK_RESULT_CRITICAL_HIT`](#attack_result_critical_hit)
      - [`ATTACK_RESULT_DEFLECTED`](#attack_result_deflected)
      - [`ATTACK_RESULT_HIT_SUCCESSFUL`](#attack_result_hit_successful)
      - [`ATTACK_RESULT_INVALID`](#attack_result_invalid)
      - [`ATTACK_RESULT_MISS`](#attack_result_miss)
      - [`ATTACK_RESULT_PARRIED`](#attack_result_parried)
      - [`ATTITUDE_AGGRESSIVE`](#attitude_aggressive)
      - [`ATTITUDE_DEFENSIVE`](#attitude_defensive)
      - [`ATTITUDE_NEUTRAL`](#attitude_neutral)
      - [`ATTITUDE_SPECIAL`](#attitude_special)
      - [`BASE_ITEM_ADHESIVE_GRENADE`](#base_item_adhesive_grenade)
      - [`BASE_ITEM_ADRENALINE`](#base_item_adrenaline)
      - [`BASE_ITEM_AESTHETIC_ITEM`](#base_item_aesthetic_item)
      - [`BASE_ITEM_ARMOR_CLASS_4`](#base_item_armor_class_4)
      - [`BASE_ITEM_ARMOR_CLASS_5`](#base_item_armor_class_5)
      - [`BASE_ITEM_ARMOR_CLASS_6`](#base_item_armor_class_6)
      - [`BASE_ITEM_ARMOR_CLASS_7`](#base_item_armor_class_7)
      - [`BASE_ITEM_ARMOR_CLASS_8`](#base_item_armor_class_8)
      - [`BASE_ITEM_ARMOR_CLASS_9`](#base_item_armor_class_9)
      - [`BASE_ITEM_BASIC_CLOTHING`](#base_item_basic_clothing)
      - [`BASE_ITEM_BELT`](#base_item_belt)
      - [`BASE_ITEM_BLASTER_CARBINE`](#base_item_blaster_carbine)
      - [`BASE_ITEM_BLASTER_PISTOL`](#base_item_blaster_pistol)
      - [`BASE_ITEM_BLASTER_RIFLE`](#base_item_blaster_rifle)
      - [`BASE_ITEM_BOWCASTER`](#base_item_bowcaster)
      - [`BASE_ITEM_COLLAR_LIGHT`](#base_item_collar_light)
      - [`BASE_ITEM_COMBAT_SHOTS`](#base_item_combat_shots)
      - [`BASE_ITEM_CREATURE_HIDE_ITEM`](#base_item_creature_hide_item)
      - [`BASE_ITEM_CREATURE_ITEM_PIERCE`](#base_item_creature_item_pierce)
      - [`BASE_ITEM_CREATURE_ITEM_SLASH`](#base_item_creature_item_slash)
      - [`BASE_ITEM_CREATURE_WEAPON_SL_PRC`](#base_item_creature_weapon_sl_prc)
      - [`BASE_ITEM_CREDITS`](#base_item_credits)
      - [`BASE_ITEM_CRYOBAN_GRENADE`](#base_item_cryoban_grenade)
      - [`BASE_ITEM_DATA_PAD`](#base_item_data_pad)
      - [`BASE_ITEM_DISRUPTER_PISTOL`](#base_item_disrupter_pistol)
      - [`BASE_ITEM_DISRUPTER_RIFLE`](#base_item_disrupter_rifle)
      - [`BASE_ITEM_DOUBLE_BLADED_LIGHTSABER`](#base_item_double_bladed_lightsaber)
      - [`BASE_ITEM_DOUBLE_BLADED_SWORD`](#base_item_double_bladed_sword)
      - [`BASE_ITEM_DROID_COMPUTER_SPIKE_MOUNT`](#base_item_droid_computer_spike_mount)
      - [`BASE_ITEM_DROID_HEAVY_PLATING`](#base_item_droid_heavy_plating)
      - [`BASE_ITEM_DROID_LIGHT_PLATING`](#base_item_droid_light_plating)
      - [`BASE_ITEM_DROID_MEDIUM_PLATING`](#base_item_droid_medium_plating)
      - [`BASE_ITEM_DROID_MOTION_SENSORS`](#base_item_droid_motion_sensors)
      - [`BASE_ITEM_DROID_REPAIR_EQUIPMENT`](#base_item_droid_repair_equipment)
      - [`BASE_ITEM_DROID_SEARCH_SCOPE`](#base_item_droid_search_scope)
      - [`BASE_ITEM_DROID_SECURITY_SPIKE_MOUNT`](#base_item_droid_security_spike_mount)
      - [`BASE_ITEM_DROID_SHIELD`](#base_item_droid_shield)
      - [`BASE_ITEM_DROID_SONIC_SENSORS`](#base_item_droid_sonic_sensors)
      - [`BASE_ITEM_DROID_TARGETING_COMPUTERS`](#base_item_droid_targeting_computers)
      - [`BASE_ITEM_DROID_UTILITY_DEVICE`](#base_item_droid_utility_device)
      - [`BASE_ITEM_FIRE_GRENADE`](#base_item_fire_grenade)
      - [`BASE_ITEM_FLASH_GRENADE`](#base_item_flash_grenade)
      - [`BASE_ITEM_FOREARM_BANDS`](#base_item_forearm_bands)
      - [`BASE_ITEM_FRAGMENTATION_GRENADES`](#base_item_fragmentation_grenades)
      - [`BASE_ITEM_GAMMOREAN_BATTLEAXE`](#base_item_gammorean_battleaxe)
      - [`BASE_ITEM_GAUNTLETS`](#base_item_gauntlets)
      - [`BASE_ITEM_GHAFFI_STICK`](#base_item_ghaffi_stick)
      - [`BASE_ITEM_GLOW_ROD`](#base_item_glow_rod)
      - [`BASE_ITEM_HEAVY_BLASTER`](#base_item_heavy_blaster)
      - [`BASE_ITEM_HEAVY_REPEATING_BLASTER`](#base_item_heavy_repeating_blaster)
      - [`BASE_ITEM_HOLD_OUT_BLASTER`](#base_item_hold_out_blaster)
      - [`BASE_ITEM_IMPLANT_1`](#base_item_implant_1)
      - [`BASE_ITEM_IMPLANT_2`](#base_item_implant_2)
      - [`BASE_ITEM_IMPLANT_3`](#base_item_implant_3)
      - [`BASE_ITEM_INVALID`](#base_item_invalid)
      - [`BASE_ITEM_ION_BLASTER`](#base_item_ion_blaster)
      - [`BASE_ITEM_ION_GRENADE`](#base_item_ion_grenade)
      - [`BASE_ITEM_ION_RIFLE`](#base_item_ion_rifle)
      - [`BASE_ITEM_JEDI_KNIGHT_ROBE`](#base_item_jedi_knight_robe)
      - [`BASE_ITEM_JEDI_MASTER_ROBE`](#base_item_jedi_master_robe)
      - [`BASE_ITEM_JEDI_ROBE`](#base_item_jedi_robe)
      - [`BASE_ITEM_LIGHTSABER`](#base_item_lightsaber)
      - [`BASE_ITEM_LIGHTSABER_CRYSTALS`](#base_item_lightsaber_crystals)
      - [`BASE_ITEM_LONG_SWORD`](#base_item_long_sword)
      - [`BASE_ITEM_MASK`](#base_item_mask)
      - [`BASE_ITEM_MEDICAL_EQUIPMENT`](#base_item_medical_equipment)
      - [`BASE_ITEM_PLOT_USEABLE_ITEMS`](#base_item_plot_useable_items)
      - [`BASE_ITEM_POISON_GRENADE`](#base_item_poison_grenade)
      - [`BASE_ITEM_PROGRAMMING_SPIKES`](#base_item_programming_spikes)
      - [`BASE_ITEM_QUARTER_STAFF`](#base_item_quarter_staff)
      - [`BASE_ITEM_REPEATING_BLASTER`](#base_item_repeating_blaster)
      - [`BASE_ITEM_SECURITY_SPIKES`](#base_item_security_spikes)
      - [`BASE_ITEM_SHORT_LIGHTSABER`](#base_item_short_lightsaber)
      - [`BASE_ITEM_SHORT_SWORD`](#base_item_short_sword)
      - [`BASE_ITEM_SONIC_GRENADE`](#base_item_sonic_grenade)
      - [`BASE_ITEM_SONIC_PISTOL`](#base_item_sonic_pistol)
      - [`BASE_ITEM_SONIC_RIFLE`](#base_item_sonic_rifle)
      - [`BASE_ITEM_STUN_BATON`](#base_item_stun_baton)
      - [`BASE_ITEM_STUN_GRENADES`](#base_item_stun_grenades)
      - [`BASE_ITEM_THERMAL_DETONATOR`](#base_item_thermal_detonator)
      - [`BASE_ITEM_TORCH`](#base_item_torch)
      - [`BASE_ITEM_TRAP_KIT`](#base_item_trap_kit)
      - [`BASE_ITEM_VIBRO_BLADE`](#base_item_vibro_blade)
      - [`BASE_ITEM_VIBRO_DOUBLE_BLADE`](#base_item_vibro_double_blade)
      - [`BASE_ITEM_VIBRO_SWORD`](#base_item_vibro_sword)
      - [`BASE_ITEM_WOOKIE_WARBLADE`](#base_item_wookie_warblade)
      - [`BODY_NODE_CHEST`](#body_node_chest)
      - [`BODY_NODE_HAND`](#body_node_hand)
      - [`BODY_NODE_HAND_LEFT`](#body_node_hand_left)
      - [`BODY_NODE_HAND_RIGHT`](#body_node_hand_right)
      - [`BODY_NODE_HEAD`](#body_node_head)
      - [`CAMERA_MODE_CHASE_CAMERA`](#camera_mode_chase_camera)
      - [`CAMERA_MODE_STIFF_CHASE_CAMERA`](#camera_mode_stiff_chase_camera)
      - [`CAMERA_MODE_TOP_DOWN`](#camera_mode_top_down)
      - [`COMBAT_MODE_FLURRY_OF_BLOWS`](#combat_mode_flurry_of_blows)
      - [`COMBAT_MODE_IMPROVED_POWER_ATTACK`](#combat_mode_improved_power_attack)
      - [`COMBAT_MODE_INVALID`](#combat_mode_invalid)
      - [`COMBAT_MODE_PARRY`](#combat_mode_parry)
      - [`COMBAT_MODE_POWER_ATTACK`](#combat_mode_power_attack)
      - [`COMBAT_MODE_RAPID_SHOT`](#combat_mode_rapid_shot)
      - [`CONVERSATION_TYPE_CINEMATIC`](#conversation_type_cinematic)
      - [`CONVERSATION_TYPE_COMPUTER`](#conversation_type_computer)
      - [`CREATURE_SIZE_HUGE`](#creature_size_huge)
      - [`CREATURE_SIZE_INVALID`](#creature_size_invalid)
      - [`CREATURE_SIZE_LARGE`](#creature_size_large)
      - [`CREATURE_SIZE_MEDIUM`](#creature_size_medium)
      - [`CREATURE_SIZE_SMALL`](#creature_size_small)
      - [`CREATURE_SIZE_TINY`](#creature_size_tiny)
      - [`CREATURE_TYPE_CLASS`](#creature_type_class)
      - [`CREATURE_TYPE_DOES_NOT_HAVE_SPELL_EFFECT`](#creature_type_does_not_have_spell_effect)
      - [`CREATURE_TYPE_HAS_SPELL_EFFECT`](#creature_type_has_spell_effect)
      - [`CREATURE_TYPE_IS_ALIVE`](#creature_type_is_alive)
      - [`CREATURE_TYPE_PERCEPTION`](#creature_type_perception)
      - [`CREATURE_TYPE_PLAYER_CHAR`](#creature_type_player_char)
      - [`CREATURE_TYPE_RACIAL_TYPE`](#creature_type_racial_type)
      - [`CREATURE_TYPE_REPUTATION`](#creature_type_reputation)
      - [`DAMAGE_BONUS_1`](#damage_bonus_1)
      - [`DAMAGE_BONUS_1d10`](#damage_bonus_1d10)
      - [`DAMAGE_BONUS_1d4`](#damage_bonus_1d4)
      - [`DAMAGE_BONUS_1d6`](#damage_bonus_1d6)
      - [`DAMAGE_BONUS_1d8`](#damage_bonus_1d8)
      - [`DAMAGE_BONUS_2`](#damage_bonus_2)
      - [`DAMAGE_BONUS_2d6`](#damage_bonus_2d6)
      - [`DAMAGE_BONUS_3`](#damage_bonus_3)
      - [`DAMAGE_BONUS_4`](#damage_bonus_4)
      - [`DAMAGE_BONUS_5`](#damage_bonus_5)
      - [`DAMAGE_POWER_ENERGY`](#damage_power_energy)
      - [`DAMAGE_POWER_NORMAL`](#damage_power_normal)
      - [`DAMAGE_POWER_PLUS_FIVE`](#damage_power_plus_five)
      - [`DAMAGE_POWER_PLUS_FOUR`](#damage_power_plus_four)
      - [`DAMAGE_POWER_PLUS_ONE`](#damage_power_plus_one)
      - [`DAMAGE_POWER_PLUS_THREE`](#damage_power_plus_three)
      - [`DAMAGE_POWER_PLUS_TWO`](#damage_power_plus_two)
      - [`DAMAGE_TYPE_ACID`](#damage_type_acid)
      - [`DAMAGE_TYPE_BLASTER`](#damage_type_blaster)
      - [`DAMAGE_TYPE_BLUDGEONING`](#damage_type_bludgeoning)
      - [`DAMAGE_TYPE_COLD`](#damage_type_cold)
      - [`DAMAGE_TYPE_DARK_SIDE`](#damage_type_dark_side)
      - [`DAMAGE_TYPE_ELECTRICAL`](#damage_type_electrical)
      - [`DAMAGE_TYPE_FIRE`](#damage_type_fire)
      - [`DAMAGE_TYPE_ION`](#damage_type_ion)
      - [`DAMAGE_TYPE_LIGHT_SIDE`](#damage_type_light_side)
      - [`DAMAGE_TYPE_PIERCING`](#damage_type_piercing)
      - [`DAMAGE_TYPE_SLASHING`](#damage_type_slashing)
      - [`DAMAGE_TYPE_SONIC`](#damage_type_sonic)
      - [`DAMAGE_TYPE_UNIVERSAL`](#damage_type_universal)
      - [`DIRECTION_EAST`](#direction_east)
      - [`DIRECTION_NORTH`](#direction_north)
      - [`DIRECTION_SOUTH`](#direction_south)
      - [`DIRECTION_WEST`](#direction_west)
      - [`DISGUISE_TYPE_C_BANTHA`](#disguise_type_c_bantha)
      - [`DISGUISE_TYPE_C_BRITH`](#disguise_type_c_brith)
      - [`DISGUISE_TYPE_C_DEWBACK`](#disguise_type_c_dewback)
      - [`DISGUISE_TYPE_C_DRDASSASSIN`](#disguise_type_c_drdassassin)
      - [`DISGUISE_TYPE_C_DRDASTRO`](#disguise_type_c_drdastro)
      - [`DISGUISE_TYPE_C_DRDG`](#disguise_type_c_drdg)
      - [`DISGUISE_TYPE_C_DRDMKFOUR`](#disguise_type_c_drdmkfour)
      - [`DISGUISE_TYPE_C_DRDMKONE`](#disguise_type_c_drdmkone)
      - [`DISGUISE_TYPE_C_DRDMKTWO`](#disguise_type_c_drdmktwo)
      - [`DISGUISE_TYPE_C_DRDPROBE`](#disguise_type_c_drdprobe)
      - [`DISGUISE_TYPE_C_DRDPROT`](#disguise_type_c_drdprot)
      - [`DISGUISE_TYPE_C_DRDSENTRY`](#disguise_type_c_drdsentry)
      - [`DISGUISE_TYPE_C_DRDSPYDER`](#disguise_type_c_drdspyder)
      - [`DISGUISE_TYPE_C_DRDWAR`](#disguise_type_c_drdwar)
      - [`DISGUISE_TYPE_C_FIRIXA`](#disguise_type_c_firixa)
      - [`DISGUISE_TYPE_C_GAMMOREAN`](#disguise_type_c_gammorean)
      - [`DISGUISE_TYPE_C_GIZKA`](#disguise_type_c_gizka)
      - [`DISGUISE_TYPE_C_HUTT`](#disguise_type_c_hutt)
      - [`DISGUISE_TYPE_C_IRIAZ`](#disguise_type_c_iriaz)
      - [`DISGUISE_TYPE_C_ITHORIAN`](#disguise_type_c_ithorian)
      - [`DISGUISE_TYPE_C_JAWA`](#disguise_type_c_jawa)
      - [`DISGUISE_TYPE_C_KATAARN`](#disguise_type_c_kataarn)
      - [`DISGUISE_TYPE_C_KHOUNDA`](#disguise_type_c_khounda)
      - [`DISGUISE_TYPE_C_KHOUNDB`](#disguise_type_c_khoundb)
      - [`DISGUISE_TYPE_C_KINRATH`](#disguise_type_c_kinrath)
      - [`DISGUISE_TYPE_C_KRAYTDRAGON`](#disguise_type_c_kraytdragon)
      - [`DISGUISE_TYPE_C_MYKAL`](#disguise_type_c_mykal)
      - [`DISGUISE_TYPE_C_RAKGHOUL`](#disguise_type_c_rakghoul)
      - [`DISGUISE_TYPE_C_RANCOR`](#disguise_type_c_rancor)
      - [`DISGUISE_TYPE_C_RONTO`](#disguise_type_c_ronto)
      - [`DISGUISE_TYPE_C_SEABEAST`](#disguise_type_c_seabeast)
      - [`DISGUISE_TYPE_C_SELKATH`](#disguise_type_c_selkath)
      - [`DISGUISE_TYPE_C_TACH`](#disguise_type_c_tach)
      - [`DISGUISE_TYPE_C_TUKATA`](#disguise_type_c_tukata)
      - [`DISGUISE_TYPE_C_TWOHEAD`](#disguise_type_c_twohead)
      - [`DISGUISE_TYPE_C_VERKAAL`](#disguise_type_c_verkaal)
      - [`DISGUISE_TYPE_C_WRAID`](#disguise_type_c_wraid)
      - [`DISGUISE_TYPE_COMMONER_FEM_BLACK`](#disguise_type_commoner_fem_black)
      - [`DISGUISE_TYPE_COMMONER_FEM_OLD_ASIAN`](#disguise_type_commoner_fem_old_asian)
      - [`DISGUISE_TYPE_COMMONER_FEM_OLD_BLACK`](#disguise_type_commoner_fem_old_black)
      - [`DISGUISE_TYPE_COMMONER_FEM_OLD_WHITE`](#disguise_type_commoner_fem_old_white)
      - [`DISGUISE_TYPE_COMMONER_FEM_WHITE`](#disguise_type_commoner_fem_white)
      - [`DISGUISE_TYPE_COMMONER_MAL_BLACK`](#disguise_type_commoner_mal_black)
      - [`DISGUISE_TYPE_COMMONER_MAL_OLD_ASIAN`](#disguise_type_commoner_mal_old_asian)
      - [`DISGUISE_TYPE_COMMONER_MAL_OLD_BLACK`](#disguise_type_commoner_mal_old_black)
      - [`DISGUISE_TYPE_COMMONER_MAL_OLD_WHITE`](#disguise_type_commoner_mal_old_white)
      - [`DISGUISE_TYPE_COMMONER_MAL_WHITE`](#disguise_type_commoner_mal_white)
      - [`DISGUISE_TYPE_CZERKA_OFFICER_BLACK`](#disguise_type_czerka_officer_black)
      - [`DISGUISE_TYPE_CZERKA_OFFICER_OLD_ASIAN`](#disguise_type_czerka_officer_old_asian)
      - [`DISGUISE_TYPE_CZERKA_OFFICER_OLD_BLACK`](#disguise_type_czerka_officer_old_black)
      - [`DISGUISE_TYPE_CZERKA_OFFICER_OLD_WHITE`](#disguise_type_czerka_officer_old_white)
      - [`DISGUISE_TYPE_CZERKA_OFFICER_WHITE`](#disguise_type_czerka_officer_white)
      - [`DISGUISE_TYPE_DROID_ASTRO_02`](#disguise_type_droid_astro_02)
      - [`DISGUISE_TYPE_DROID_ASTRO_03`](#disguise_type_droid_astro_03)
      - [`DISGUISE_TYPE_DROID_PROTOCOL_02`](#disguise_type_droid_protocol_02)
      - [`DISGUISE_TYPE_DROID_PROTOCOL_03`](#disguise_type_droid_protocol_03)
      - [`DISGUISE_TYPE_DROID_PROTOCOL_04`](#disguise_type_droid_protocol_04)
      - [`DISGUISE_TYPE_DROID_WAR_02`](#disguise_type_droid_war_02)
      - [`DISGUISE_TYPE_DROID_WAR_03`](#disguise_type_droid_war_03)
      - [`DISGUISE_TYPE_DROID_WAR_04`](#disguise_type_droid_war_04)
      - [`DISGUISE_TYPE_DROID_WAR_05`](#disguise_type_droid_war_05)
      - [`DISGUISE_TYPE_ENVIRONMENTSUIT`](#disguise_type_environmentsuit)
      - [`DISGUISE_TYPE_ENVIRONMENTSUIT_02`](#disguise_type_environmentsuit_02)
      - [`DISGUISE_TYPE_GAMMOREAN_02`](#disguise_type_gammorean_02)
      - [`DISGUISE_TYPE_GAMMOREAN_03`](#disguise_type_gammorean_03)
      - [`DISGUISE_TYPE_GAMMOREAN_04`](#disguise_type_gammorean_04)
      - [`DISGUISE_TYPE_HUTT_02`](#disguise_type_hutt_02)
      - [`DISGUISE_TYPE_HUTT_03`](#disguise_type_hutt_03)
      - [`DISGUISE_TYPE_HUTT_04`](#disguise_type_hutt_04)
      - [`DISGUISE_TYPE_ITHORIAN_02`](#disguise_type_ithorian_02)
      - [`DISGUISE_TYPE_ITHORIAN_03`](#disguise_type_ithorian_03)
      - [`DISGUISE_TYPE_JEDI_ASIAN_FEMALE_01`](#disguise_type_jedi_asian_female_01)
      - [`DISGUISE_TYPE_JEDI_ASIAN_FEMALE_02`](#disguise_type_jedi_asian_female_02)
      - [`DISGUISE_TYPE_JEDI_ASIAN_FEMALE_03`](#disguise_type_jedi_asian_female_03)
      - [`DISGUISE_TYPE_JEDI_ASIAN_FEMALE_04`](#disguise_type_jedi_asian_female_04)
      - [`DISGUISE_TYPE_JEDI_ASIAN_FEMALE_05`](#disguise_type_jedi_asian_female_05)
      - [`DISGUISE_TYPE_JEDI_ASIAN_MALE_01`](#disguise_type_jedi_asian_male_01)
      - [`DISGUISE_TYPE_JEDI_ASIAN_MALE_02`](#disguise_type_jedi_asian_male_02)
      - [`DISGUISE_TYPE_JEDI_ASIAN_MALE_03`](#disguise_type_jedi_asian_male_03)
      - [`DISGUISE_TYPE_JEDI_ASIAN_MALE_04`](#disguise_type_jedi_asian_male_04)
      - [`DISGUISE_TYPE_JEDI_ASIAN_MALE_05`](#disguise_type_jedi_asian_male_05)
      - [`DISGUISE_TYPE_JEDI_ASIAN_OLD_FEM`](#disguise_type_jedi_asian_old_fem)
      - [`DISGUISE_TYPE_JEDI_ASIAN_OLD_MALE`](#disguise_type_jedi_asian_old_male)
      - [`DISGUISE_TYPE_JEDI_BLACK_FEMALE_01`](#disguise_type_jedi_black_female_01)
      - [`DISGUISE_TYPE_JEDI_BLACK_FEMALE_02`](#disguise_type_jedi_black_female_02)
      - [`DISGUISE_TYPE_JEDI_BLACK_FEMALE_03`](#disguise_type_jedi_black_female_03)
      - [`DISGUISE_TYPE_JEDI_BLACK_FEMALE_04`](#disguise_type_jedi_black_female_04)
      - [`DISGUISE_TYPE_JEDI_BLACK_FEMALE_05`](#disguise_type_jedi_black_female_05)
      - [`DISGUISE_TYPE_JEDI_BLACK_MALE_01`](#disguise_type_jedi_black_male_01)
      - [`DISGUISE_TYPE_JEDI_BLACK_MALE_02`](#disguise_type_jedi_black_male_02)
      - [`DISGUISE_TYPE_JEDI_BLACK_MALE_03`](#disguise_type_jedi_black_male_03)
      - [`DISGUISE_TYPE_JEDI_BLACK_MALE_04`](#disguise_type_jedi_black_male_04)
      - [`DISGUISE_TYPE_JEDI_BLACK_MALE_05`](#disguise_type_jedi_black_male_05)
      - [`DISGUISE_TYPE_JEDI_BLACK_OLD_FEM`](#disguise_type_jedi_black_old_fem)
      - [`DISGUISE_TYPE_JEDI_BLACK_OLD_MALE`](#disguise_type_jedi_black_old_male)
      - [`DISGUISE_TYPE_JEDI_WHITE_FEMALE_02`](#disguise_type_jedi_white_female_02)
      - [`DISGUISE_TYPE_JEDI_WHITE_FEMALE_03`](#disguise_type_jedi_white_female_03)
      - [`DISGUISE_TYPE_JEDI_WHITE_FEMALE_04`](#disguise_type_jedi_white_female_04)
      - [`DISGUISE_TYPE_JEDI_WHITE_FEMALE_05`](#disguise_type_jedi_white_female_05)
      - [`DISGUISE_TYPE_JEDI_WHITE_MALE_02`](#disguise_type_jedi_white_male_02)
      - [`DISGUISE_TYPE_JEDI_WHITE_MALE_03`](#disguise_type_jedi_white_male_03)
      - [`DISGUISE_TYPE_JEDI_WHITE_MALE_04`](#disguise_type_jedi_white_male_04)
      - [`DISGUISE_TYPE_JEDI_WHITE_MALE_05`](#disguise_type_jedi_white_male_05)
      - [`DISGUISE_TYPE_JEDI_WHITE_OLD_FEM`](#disguise_type_jedi_white_old_fem)
      - [`DISGUISE_TYPE_JEDI_WHITE_OLD_MALE`](#disguise_type_jedi_white_old_male)
      - [`DISGUISE_TYPE_KATH_HOUND_A02`](#disguise_type_kath_hound_a02)
      - [`DISGUISE_TYPE_KATH_HOUND_A03`](#disguise_type_kath_hound_a03)
      - [`DISGUISE_TYPE_KATH_HOUND_A04`](#disguise_type_kath_hound_a04)
      - [`DISGUISE_TYPE_KATH_HOUND_B02`](#disguise_type_kath_hound_b02)
      - [`DISGUISE_TYPE_KATH_HOUND_B03`](#disguise_type_kath_hound_b03)
      - [`DISGUISE_TYPE_KATH_HOUND_B04`](#disguise_type_kath_hound_b04)
      - [`DISGUISE_TYPE_N_ADMRLSAULKAR`](#disguise_type_n_admrlsaulkar)
      - [`DISGUISE_TYPE_N_BITH`](#disguise_type_n_bith)
      - [`DISGUISE_TYPE_N_CALONORD`](#disguise_type_n_calonord)
      - [`DISGUISE_TYPE_N_COMMF`](#disguise_type_n_commf)
      - [`DISGUISE_TYPE_N_COMMKIDF`](#disguise_type_n_commkidf)
      - [`DISGUISE_TYPE_N_COMMKIDM`](#disguise_type_n_commkidm)
      - [`DISGUISE_TYPE_N_COMMM`](#disguise_type_n_commm)
      - [`DISGUISE_TYPE_N_CZERLAOFF`](#disguise_type_n_czerlaoff)
      - [`DISGUISE_TYPE_N_DARKJEDIF`](#disguise_type_n_darkjedif)
      - [`DISGUISE_TYPE_N_DARKJEDIM`](#disguise_type_n_darkjedim)
      - [`DISGUISE_TYPE_N_DARTHBAND`](#disguise_type_n_darthband)
      - [`DISGUISE_TYPE_N_DARTHMALAK`](#disguise_type_n_darthmalak)
      - [`DISGUISE_TYPE_N_DARTHREVAN`](#disguise_type_n_darthrevan)
      - [`DISGUISE_TYPE_N_DODONNA`](#disguise_type_n_dodonna)
      - [`DISGUISE_TYPE_N_DUROS`](#disguise_type_n_duros)
      - [`DISGUISE_TYPE_N_FATCOMF`](#disguise_type_n_fatcomf)
      - [`DISGUISE_TYPE_N_FATCOMM`](#disguise_type_n_fatcomm)
      - [`DISGUISE_TYPE_N_JEDICOUNTF`](#disguise_type_n_jedicountf)
      - [`DISGUISE_TYPE_N_JEDICOUNTM`](#disguise_type_n_jedicountm)
      - [`DISGUISE_TYPE_N_JEDIMALEK`](#disguise_type_n_jedimalek)
      - [`DISGUISE_TYPE_N_JEDIMEMF`](#disguise_type_n_jedimemf)
      - [`DISGUISE_TYPE_N_JEDIMEMM`](#disguise_type_n_jedimemm)
      - [`DISGUISE_TYPE_N_MANDALORIAN`](#disguise_type_n_mandalorian)
      - [`DISGUISE_TYPE_N_RAKATA`](#disguise_type_n_rakata)
      - [`DISGUISE_TYPE_N_REPOFF`](#disguise_type_n_repoff)
      - [`DISGUISE_TYPE_N_REPSOLD`](#disguise_type_n_repsold)
      - [`DISGUISE_TYPE_N_RODIAN`](#disguise_type_n_rodian)
      - [`DISGUISE_TYPE_N_SITHAPPREN`](#disguise_type_n_sithappren)
      - [`DISGUISE_TYPE_N_SITHCOMF`](#disguise_type_n_sithcomf)
      - [`DISGUISE_TYPE_N_SITHCOMM`](#disguise_type_n_sithcomm)
      - [`DISGUISE_TYPE_N_SITHSOLDIER`](#disguise_type_n_sithsoldier)
      - [`DISGUISE_TYPE_N_SMUGGLER`](#disguise_type_n_smuggler)
      - [`DISGUISE_TYPE_N_SWOOPGANG`](#disguise_type_n_swoopgang)
      - [`DISGUISE_TYPE_N_TUSKEN`](#disguise_type_n_tusken)
      - [`DISGUISE_TYPE_N_TUSKENF`](#disguise_type_n_tuskenf)
      - [`DISGUISE_TYPE_N_TWILEKF`](#disguise_type_n_twilekf)
      - [`DISGUISE_TYPE_N_TWILEKM`](#disguise_type_n_twilekm)
      - [`DISGUISE_TYPE_N_WALRUSMAN`](#disguise_type_n_walrusman)
      - [`DISGUISE_TYPE_N_WOOKIEF`](#disguise_type_n_wookief)
      - [`DISGUISE_TYPE_N_WOOKIEM`](#disguise_type_n_wookiem)
      - [`DISGUISE_TYPE_N_YODA`](#disguise_type_n_yoda)
      - [`DISGUISE_TYPE_P_BASTILLA`](#disguise_type_p_bastilla)
      - [`DISGUISE_TYPE_P_CAND`](#disguise_type_p_cand)
      - [`DISGUISE_TYPE_P_CARTH`](#disguise_type_p_carth)
      - [`DISGUISE_TYPE_P_FEM_A_LRG_01`](#disguise_type_p_fem_a_lrg_01)
      - [`DISGUISE_TYPE_P_FEM_A_LRG_02`](#disguise_type_p_fem_a_lrg_02)
      - [`DISGUISE_TYPE_P_FEM_A_LRG_03`](#disguise_type_p_fem_a_lrg_03)
      - [`DISGUISE_TYPE_P_FEM_A_LRG_04`](#disguise_type_p_fem_a_lrg_04)
      - [`DISGUISE_TYPE_P_FEM_A_LRG_05`](#disguise_type_p_fem_a_lrg_05)
      - [`DISGUISE_TYPE_P_FEM_A_MED_01`](#disguise_type_p_fem_a_med_01)
      - [`DISGUISE_TYPE_P_FEM_A_MED_02`](#disguise_type_p_fem_a_med_02)
      - [`DISGUISE_TYPE_P_FEM_A_MED_03`](#disguise_type_p_fem_a_med_03)
      - [`DISGUISE_TYPE_P_FEM_A_MED_04`](#disguise_type_p_fem_a_med_04)
      - [`DISGUISE_TYPE_P_FEM_A_MED_05`](#disguise_type_p_fem_a_med_05)
      - [`DISGUISE_TYPE_P_FEM_A_SML_01`](#disguise_type_p_fem_a_sml_01)
      - [`DISGUISE_TYPE_P_FEM_A_SML_02`](#disguise_type_p_fem_a_sml_02)
      - [`DISGUISE_TYPE_P_FEM_A_SML_03`](#disguise_type_p_fem_a_sml_03)
      - [`DISGUISE_TYPE_P_FEM_A_SML_04`](#disguise_type_p_fem_a_sml_04)
      - [`DISGUISE_TYPE_P_FEM_A_SML_05`](#disguise_type_p_fem_a_sml_05)
      - [`DISGUISE_TYPE_P_FEM_B_LRG_01`](#disguise_type_p_fem_b_lrg_01)
      - [`DISGUISE_TYPE_P_FEM_B_LRG_02`](#disguise_type_p_fem_b_lrg_02)
      - [`DISGUISE_TYPE_P_FEM_B_LRG_03`](#disguise_type_p_fem_b_lrg_03)
      - [`DISGUISE_TYPE_P_FEM_B_LRG_04`](#disguise_type_p_fem_b_lrg_04)
      - [`DISGUISE_TYPE_P_FEM_B_LRG_05`](#disguise_type_p_fem_b_lrg_05)
      - [`DISGUISE_TYPE_P_FEM_B_MED_01`](#disguise_type_p_fem_b_med_01)
      - [`DISGUISE_TYPE_P_FEM_B_MED_02`](#disguise_type_p_fem_b_med_02)
      - [`DISGUISE_TYPE_P_FEM_B_MED_03`](#disguise_type_p_fem_b_med_03)
      - [`DISGUISE_TYPE_P_FEM_B_MED_04`](#disguise_type_p_fem_b_med_04)
      - [`DISGUISE_TYPE_P_FEM_B_MED_05`](#disguise_type_p_fem_b_med_05)
      - [`DISGUISE_TYPE_P_FEM_B_SML_01`](#disguise_type_p_fem_b_sml_01)
      - [`DISGUISE_TYPE_P_FEM_B_SML_02`](#disguise_type_p_fem_b_sml_02)
      - [`DISGUISE_TYPE_P_FEM_B_SML_03`](#disguise_type_p_fem_b_sml_03)
      - [`DISGUISE_TYPE_P_FEM_B_SML_04`](#disguise_type_p_fem_b_sml_04)
      - [`DISGUISE_TYPE_P_FEM_B_SML_05`](#disguise_type_p_fem_b_sml_05)
      - [`DISGUISE_TYPE_P_FEM_C_LRG_01`](#disguise_type_p_fem_c_lrg_01)
      - [`DISGUISE_TYPE_P_FEM_C_LRG_02`](#disguise_type_p_fem_c_lrg_02)
      - [`DISGUISE_TYPE_P_FEM_C_LRG_03`](#disguise_type_p_fem_c_lrg_03)
      - [`DISGUISE_TYPE_P_FEM_C_LRG_04`](#disguise_type_p_fem_c_lrg_04)
      - [`DISGUISE_TYPE_P_FEM_C_LRG_05`](#disguise_type_p_fem_c_lrg_05)
      - [`DISGUISE_TYPE_P_FEM_C_MED_01`](#disguise_type_p_fem_c_med_01)
      - [`DISGUISE_TYPE_P_FEM_C_MED_02`](#disguise_type_p_fem_c_med_02)
      - [`DISGUISE_TYPE_P_FEM_C_MED_03`](#disguise_type_p_fem_c_med_03)
      - [`DISGUISE_TYPE_P_FEM_C_MED_04`](#disguise_type_p_fem_c_med_04)
      - [`DISGUISE_TYPE_P_FEM_C_MED_05`](#disguise_type_p_fem_c_med_05)
      - [`DISGUISE_TYPE_P_FEM_C_SML_01`](#disguise_type_p_fem_c_sml_01)
      - [`DISGUISE_TYPE_P_FEM_C_SML_02`](#disguise_type_p_fem_c_sml_02)
      - [`DISGUISE_TYPE_P_FEM_C_SML_03`](#disguise_type_p_fem_c_sml_03)
      - [`DISGUISE_TYPE_P_FEM_C_SML_04`](#disguise_type_p_fem_c_sml_04)
      - [`DISGUISE_TYPE_P_FEM_C_SML_05`](#disguise_type_p_fem_c_sml_05)
      - [`DISGUISE_TYPE_P_HK47`](#disguise_type_p_hk47)
      - [`DISGUISE_TYPE_P_JOLEE`](#disguise_type_p_jolee)
      - [`DISGUISE_TYPE_P_JUHANI`](#disguise_type_p_juhani)
      - [`DISGUISE_TYPE_P_MAL_A_LRG_01`](#disguise_type_p_mal_a_lrg_01)
      - [`DISGUISE_TYPE_P_MAL_A_LRG_02`](#disguise_type_p_mal_a_lrg_02)
      - [`DISGUISE_TYPE_P_MAL_A_LRG_03`](#disguise_type_p_mal_a_lrg_03)
      - [`DISGUISE_TYPE_P_MAL_A_LRG_04`](#disguise_type_p_mal_a_lrg_04)
      - [`DISGUISE_TYPE_P_MAL_A_LRG_05`](#disguise_type_p_mal_a_lrg_05)
      - [`DISGUISE_TYPE_P_MAL_A_MED_01`](#disguise_type_p_mal_a_med_01)
      - [`DISGUISE_TYPE_P_MAL_A_MED_02`](#disguise_type_p_mal_a_med_02)
      - [`DISGUISE_TYPE_P_MAL_A_MED_03`](#disguise_type_p_mal_a_med_03)
      - [`DISGUISE_TYPE_P_MAL_A_MED_04`](#disguise_type_p_mal_a_med_04)
      - [`DISGUISE_TYPE_P_MAL_A_MED_05`](#disguise_type_p_mal_a_med_05)
      - [`DISGUISE_TYPE_P_MAL_A_SML_01`](#disguise_type_p_mal_a_sml_01)
      - [`DISGUISE_TYPE_P_MAL_A_SML_02`](#disguise_type_p_mal_a_sml_02)
      - [`DISGUISE_TYPE_P_MAL_A_SML_03`](#disguise_type_p_mal_a_sml_03)
      - [`DISGUISE_TYPE_P_MAL_A_SML_04`](#disguise_type_p_mal_a_sml_04)
      - [`DISGUISE_TYPE_P_MAL_A_SML_05`](#disguise_type_p_mal_a_sml_05)
      - [`DISGUISE_TYPE_P_MAL_B_LRG_01`](#disguise_type_p_mal_b_lrg_01)
      - [`DISGUISE_TYPE_P_MAL_B_LRG_02`](#disguise_type_p_mal_b_lrg_02)
      - [`DISGUISE_TYPE_P_MAL_B_LRG_03`](#disguise_type_p_mal_b_lrg_03)
      - [`DISGUISE_TYPE_P_MAL_B_LRG_04`](#disguise_type_p_mal_b_lrg_04)
      - [`DISGUISE_TYPE_P_MAL_B_LRG_05`](#disguise_type_p_mal_b_lrg_05)
      - [`DISGUISE_TYPE_P_MAL_B_MED_01`](#disguise_type_p_mal_b_med_01)
      - [`DISGUISE_TYPE_P_MAL_B_MED_02`](#disguise_type_p_mal_b_med_02)
      - [`DISGUISE_TYPE_P_MAL_B_MED_03`](#disguise_type_p_mal_b_med_03)
      - [`DISGUISE_TYPE_P_MAL_B_MED_04`](#disguise_type_p_mal_b_med_04)
      - [`DISGUISE_TYPE_P_MAL_B_MED_05`](#disguise_type_p_mal_b_med_05)
      - [`DISGUISE_TYPE_P_MAL_B_SML_01`](#disguise_type_p_mal_b_sml_01)
      - [`DISGUISE_TYPE_P_MAL_B_SML_02`](#disguise_type_p_mal_b_sml_02)
      - [`DISGUISE_TYPE_P_MAL_B_SML_03`](#disguise_type_p_mal_b_sml_03)
      - [`DISGUISE_TYPE_P_MAL_B_SML_04`](#disguise_type_p_mal_b_sml_04)
      - [`DISGUISE_TYPE_P_MAL_B_SML_05`](#disguise_type_p_mal_b_sml_05)
      - [`DISGUISE_TYPE_P_MAL_C_LRG_01`](#disguise_type_p_mal_c_lrg_01)
      - [`DISGUISE_TYPE_P_MAL_C_LRG_02`](#disguise_type_p_mal_c_lrg_02)
      - [`DISGUISE_TYPE_P_MAL_C_LRG_03`](#disguise_type_p_mal_c_lrg_03)
      - [`DISGUISE_TYPE_P_MAL_C_LRG_04`](#disguise_type_p_mal_c_lrg_04)
      - [`DISGUISE_TYPE_P_MAL_C_LRG_05`](#disguise_type_p_mal_c_lrg_05)
      - [`DISGUISE_TYPE_P_MAL_C_MED_01`](#disguise_type_p_mal_c_med_01)
      - [`DISGUISE_TYPE_P_MAL_C_MED_02`](#disguise_type_p_mal_c_med_02)
      - [`DISGUISE_TYPE_P_MAL_C_MED_03`](#disguise_type_p_mal_c_med_03)
      - [`DISGUISE_TYPE_P_MAL_C_MED_04`](#disguise_type_p_mal_c_med_04)
      - [`DISGUISE_TYPE_P_MAL_C_MED_05`](#disguise_type_p_mal_c_med_05)
      - [`DISGUISE_TYPE_P_MAL_C_SML_01`](#disguise_type_p_mal_c_sml_01)
      - [`DISGUISE_TYPE_P_MAL_C_SML_02`](#disguise_type_p_mal_c_sml_02)
      - [`DISGUISE_TYPE_P_MAL_C_SML_03`](#disguise_type_p_mal_c_sml_03)
      - [`DISGUISE_TYPE_P_MAL_C_SML_04`](#disguise_type_p_mal_c_sml_04)
      - [`DISGUISE_TYPE_P_MAL_C_SML_05`](#disguise_type_p_mal_c_sml_05)
      - [`DISGUISE_TYPE_P_MISSION`](#disguise_type_p_mission)
      - [`DISGUISE_TYPE_P_T3M3`](#disguise_type_p_t3m3)
      - [`DISGUISE_TYPE_P_ZAALBAR`](#disguise_type_p_zaalbar)
      - [`DISGUISE_TYPE_RAKATA_02`](#disguise_type_rakata_02)
      - [`DISGUISE_TYPE_RAKATA_03`](#disguise_type_rakata_03)
      - [`DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_BLACK`](#disguise_type_republic_officer_mal_black)
      - [`DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_ASIAN`](#disguise_type_republic_officer_mal_old_asian)
      - [`DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_BLACK`](#disguise_type_republic_officer_mal_old_black)
      - [`DISGUISE_TYPE_REPUBLIC_OFFICER_MAL_OLD_WHITE`](#disguise_type_republic_officer_mal_old_white)
      - [`DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_BLACK`](#disguise_type_republic_soldier_mal_black)
      - [`DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_ASIAN`](#disguise_type_republic_soldier_mal_old_asian)
      - [`DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_BLACK`](#disguise_type_republic_soldier_mal_old_black)
      - [`DISGUISE_TYPE_REPUBLIC_SOLDIER_MAL_OLD_WHITE`](#disguise_type_republic_soldier_mal_old_white)
      - [`DISGUISE_TYPE_RODIAN_02`](#disguise_type_rodian_02)
      - [`DISGUISE_TYPE_RODIAN_03`](#disguise_type_rodian_03)
      - [`DISGUISE_TYPE_RODIAN_04`](#disguise_type_rodian_04)
      - [`DISGUISE_TYPE_SELKATH_02`](#disguise_type_selkath_02)
      - [`DISGUISE_TYPE_SELKATH_03`](#disguise_type_selkath_03)
      - [`DISGUISE_TYPE_SHYRACK_01`](#disguise_type_shyrack_01)
      - [`DISGUISE_TYPE_SHYRACK_02`](#disguise_type_shyrack_02)
      - [`DISGUISE_TYPE_SITH_FEM_ASIAN`](#disguise_type_sith_fem_asian)
      - [`DISGUISE_TYPE_SITH_FEM_BLACK`](#disguise_type_sith_fem_black)
      - [`DISGUISE_TYPE_SITH_FEM_OLD_ASIAN`](#disguise_type_sith_fem_old_asian)
      - [`DISGUISE_TYPE_SITH_FEM_OLD_BLACK`](#disguise_type_sith_fem_old_black)
      - [`DISGUISE_TYPE_SITH_FEM_OLD_WHITE`](#disguise_type_sith_fem_old_white)
      - [`DISGUISE_TYPE_SITH_FEM_WHITE`](#disguise_type_sith_fem_white)
      - [`DISGUISE_TYPE_SITH_MAL_ASIAN`](#disguise_type_sith_mal_asian)
      - [`DISGUISE_TYPE_SITH_MAL_BLACK`](#disguise_type_sith_mal_black)
      - [`DISGUISE_TYPE_SITH_MAL_OLD_ASIAN`](#disguise_type_sith_mal_old_asian)
      - [`DISGUISE_TYPE_SITH_MAL_OLD_BLACK`](#disguise_type_sith_mal_old_black)
      - [`DISGUISE_TYPE_SITH_MAL_OLD_WHITE`](#disguise_type_sith_mal_old_white)
      - [`DISGUISE_TYPE_SITH_MAL_WHITE`](#disguise_type_sith_mal_white)
      - [`DISGUISE_TYPE_SITH_SOLDIER_03`](#disguise_type_sith_soldier_03)
      - [`DISGUISE_TYPE_SWOOP_GANG_02`](#disguise_type_swoop_gang_02)
      - [`DISGUISE_TYPE_SWOOP_GANG_03`](#disguise_type_swoop_gang_03)
      - [`DISGUISE_TYPE_SWOOP_GANG_04`](#disguise_type_swoop_gang_04)
      - [`DISGUISE_TYPE_SWOOP_GANG_05`](#disguise_type_swoop_gang_05)
      - [`DISGUISE_TYPE_TEST`](#disguise_type_test)
      - [`DISGUISE_TYPE_TURRET`](#disguise_type_turret)
      - [`DISGUISE_TYPE_TURRET2`](#disguise_type_turret2)
      - [`DISGUISE_TYPE_TUSKAN_RAIDER_02`](#disguise_type_tuskan_raider_02)
      - [`DISGUISE_TYPE_TUSKAN_RAIDER_03`](#disguise_type_tuskan_raider_03)
      - [`DISGUISE_TYPE_TUSKAN_RAIDER_04`](#disguise_type_tuskan_raider_04)
      - [`DISGUISE_TYPE_TWILEK_FEMALE_02`](#disguise_type_twilek_female_02)
      - [`DISGUISE_TYPE_TWILEK_MALE_02`](#disguise_type_twilek_male_02)
      - [`DISGUISE_TYPE_WOOKIE_FEMALE_02`](#disguise_type_wookie_female_02)
      - [`DISGUISE_TYPE_WOOKIE_FEMALE_03`](#disguise_type_wookie_female_03)
      - [`DISGUISE_TYPE_WOOKIE_FEMALE_04`](#disguise_type_wookie_female_04)
      - [`DISGUISE_TYPE_WOOKIE_FEMALE_05`](#disguise_type_wookie_female_05)
      - [`DISGUISE_TYPE_WOOKIE_MALE_02`](#disguise_type_wookie_male_02)
      - [`DISGUISE_TYPE_WOOKIE_MALE_03`](#disguise_type_wookie_male_03)
      - [`DISGUISE_TYPE_WOOKIE_MALE_04`](#disguise_type_wookie_male_04)
      - [`DISGUISE_TYPE_WOOKIE_MALE_05`](#disguise_type_wookie_male_05)
      - [`DISGUISE_TYPE_WRAID_02`](#disguise_type_wraid_02)
      - [`DISGUISE_TYPE_WRAID_03`](#disguise_type_wraid_03)
      - [`DISGUISE_TYPE_WRAID_04`](#disguise_type_wraid_04)
      - [`DISGUISE_TYPE_YUTHURA_BAN`](#disguise_type_yuthura_ban)
      - [`DOOR_ACTION_BASH`](#door_action_bash)
      - [`DOOR_ACTION_IGNORE`](#door_action_ignore)
      - [`DOOR_ACTION_KNOCK`](#door_action_knock)
      - [`DOOR_ACTION_OPEN`](#door_action_open)
      - [`DOOR_ACTION_UNLOCK`](#door_action_unlock)
      - [`DURATION_TYPE_INSTANT`](#duration_type_instant)
      - [`DURATION_TYPE_PERMANENT`](#duration_type_permanent)
      - [`DURATION_TYPE_TEMPORARY`](#duration_type_temporary)
      - [`EFFECT_TYPE_ABILITY_DECREASE`](#effect_type_ability_decrease)
      - [`EFFECT_TYPE_ABILITY_INCREASE`](#effect_type_ability_increase)
      - [`EFFECT_TYPE_AC_DECREASE`](#effect_type_ac_decrease)
      - [`EFFECT_TYPE_AC_INCREASE`](#effect_type_ac_increase)
      - [`EFFECT_TYPE_ARCANE_SPELL_FAILURE`](#effect_type_arcane_spell_failure)
      - [`EFFECT_TYPE_AREA_OF_EFFECT`](#effect_type_area_of_effect)
      - [`EFFECT_TYPE_ASSUREDDEFLECTION`](#effect_type_assureddeflection)
      - [`EFFECT_TYPE_ASSUREDHIT`](#effect_type_assuredhit)
      - [`EFFECT_TYPE_ATTACK_DECREASE`](#effect_type_attack_decrease)
      - [`EFFECT_TYPE_ATTACK_INCREASE`](#effect_type_attack_increase)
      - [`EFFECT_TYPE_BEAM`](#effect_type_beam)
      - [`EFFECT_TYPE_BLINDNESS`](#effect_type_blindness)
      - [`EFFECT_TYPE_CHARMED`](#effect_type_charmed)
      - [`EFFECT_TYPE_CONCEALMENT`](#effect_type_concealment)
      - [`EFFECT_TYPE_CONFUSED`](#effect_type_confused)
      - [`EFFECT_TYPE_CURSE`](#effect_type_curse)
      - [`EFFECT_TYPE_DAMAGE_DECREASE`](#effect_type_damage_decrease)
      - [`EFFECT_TYPE_DAMAGE_IMMUNITY_DECREASE`](#effect_type_damage_immunity_decrease)
      - [`EFFECT_TYPE_DAMAGE_IMMUNITY_INCREASE`](#effect_type_damage_immunity_increase)
      - [`EFFECT_TYPE_DAMAGE_INCREASE`](#effect_type_damage_increase)
      - [`EFFECT_TYPE_DAMAGE_REDUCTION`](#effect_type_damage_reduction)
      - [`EFFECT_TYPE_DAMAGE_RESISTANCE`](#effect_type_damage_resistance)
      - [`EFFECT_TYPE_DARKNESS`](#effect_type_darkness)
      - [`EFFECT_TYPE_DAZED`](#effect_type_dazed)
      - [`EFFECT_TYPE_DEAF`](#effect_type_deaf)
      - [`EFFECT_TYPE_DISEASE`](#effect_type_disease)
      - [`EFFECT_TYPE_DISGUISE`](#effect_type_disguise)
      - [`EFFECT_TYPE_DISPELMAGICALL`](#effect_type_dispelmagicall)
      - [`EFFECT_TYPE_DISPELMAGICBEST`](#effect_type_dispelmagicbest)
      - [`EFFECT_TYPE_DOMINATED`](#effect_type_dominated)
      - [`EFFECT_TYPE_ELEMENTALSHIELD`](#effect_type_elementalshield)
      - [`EFFECT_TYPE_ENEMY_ATTACK_BONUS`](#effect_type_enemy_attack_bonus)
      - [`EFFECT_TYPE_ENTANGLE`](#effect_type_entangle)
      - [`EFFECT_TYPE_FORCE_RESISTANCE_DECREASE`](#effect_type_force_resistance_decrease)
      - [`EFFECT_TYPE_FORCE_RESISTANCE_INCREASE`](#effect_type_force_resistance_increase)
      - [`EFFECT_TYPE_FORCEJUMP`](#effect_type_forcejump)
      - [`EFFECT_TYPE_FRIGHTENED`](#effect_type_frightened)
      - [`EFFECT_TYPE_HASTE`](#effect_type_haste)
      - [`EFFECT_TYPE_IMMUNITY`](#effect_type_immunity)
      - [`EFFECT_TYPE_IMPROVEDINVISIBILITY`](#effect_type_improvedinvisibility)
      - [`EFFECT_TYPE_INVALIDEFFECT`](#effect_type_invalideffect)
      - [`EFFECT_TYPE_INVISIBILITY`](#effect_type_invisibility)
      - [`EFFECT_TYPE_INVULNERABLE`](#effect_type_invulnerable)
      - [`EFFECT_TYPE_LIGHTSABERTHROW`](#effect_type_lightsaberthrow)
      - [`EFFECT_TYPE_MISS_CHANCE`](#effect_type_miss_chance)
      - [`EFFECT_TYPE_MOVEMENT_SPEED_DECREASE`](#effect_type_movement_speed_decrease)
      - [`EFFECT_TYPE_MOVEMENT_SPEED_INCREASE`](#effect_type_movement_speed_increase)
      - [`EFFECT_TYPE_NEGATIVELEVEL`](#effect_type_negativelevel)
      - [`EFFECT_TYPE_PARALYZE`](#effect_type_paralyze)
      - [`EFFECT_TYPE_POISON`](#effect_type_poison)
      - [`EFFECT_TYPE_REGENERATE`](#effect_type_regenerate)
      - [`EFFECT_TYPE_RESURRECTION`](#effect_type_resurrection)
      - [`EFFECT_TYPE_SANCTUARY`](#effect_type_sanctuary)
      - [`EFFECT_TYPE_SAVING_THROW_DECREASE`](#effect_type_saving_throw_decrease)
      - [`EFFECT_TYPE_SAVING_THROW_INCREASE`](#effect_type_saving_throw_increase)
      - [`EFFECT_TYPE_SEEINVISIBLE`](#effect_type_seeinvisible)
      - [`EFFECT_TYPE_SILENCE`](#effect_type_silence)
      - [`EFFECT_TYPE_SKILL_DECREASE`](#effect_type_skill_decrease)
      - [`EFFECT_TYPE_SKILL_INCREASE`](#effect_type_skill_increase)
      - [`EFFECT_TYPE_SLEEP`](#effect_type_sleep)
      - [`EFFECT_TYPE_SLOW`](#effect_type_slow)
      - [`EFFECT_TYPE_SPELL_IMMUNITY`](#effect_type_spell_immunity)
      - [`EFFECT_TYPE_SPELLLEVELABSORPTION`](#effect_type_spelllevelabsorption)
      - [`EFFECT_TYPE_STUNNED`](#effect_type_stunned)
      - [`EFFECT_TYPE_TEMPORARY_HITPOINTS`](#effect_type_temporary_hitpoints)
      - [`EFFECT_TYPE_TIMESTOP`](#effect_type_timestop)
      - [`EFFECT_TYPE_TRUESEEING`](#effect_type_trueseeing)
      - [`EFFECT_TYPE_TURNED`](#effect_type_turned)
      - [`EFFECT_TYPE_ULTRAVISION`](#effect_type_ultravision)
      - [`EFFECT_TYPE_VISUAL`](#effect_type_visual)
      - [`ENCOUNTER_DIFFICULTY_EASY`](#encounter_difficulty_easy)
      - [`ENCOUNTER_DIFFICULTY_HARD`](#encounter_difficulty_hard)
      - [`ENCOUNTER_DIFFICULTY_IMPOSSIBLE`](#encounter_difficulty_impossible)
      - [`ENCOUNTER_DIFFICULTY_NORMAL`](#encounter_difficulty_normal)
      - [`ENCOUNTER_DIFFICULTY_VERY_EASY`](#encounter_difficulty_very_easy)
      - [`FALSE`](#false)
      - [`FEAT_ADVANCED_DOUBLE_WEAPON_FIGHTING`](#feat_advanced_double_weapon_fighting)
      - [`FEAT_ADVANCED_GUARD_STANCE`](#feat_advanced_guard_stance)
      - [`FEAT_ADVANCED_JEDI_DEFENSE`](#feat_advanced_jedi_defense)
      - [`FEAT_AMBIDEXTERITY`](#feat_ambidexterity)
      - [`FEAT_ARMOUR_PROF_HEAVY`](#feat_armour_prof_heavy)
      - [`FEAT_ARMOUR_PROF_LIGHT`](#feat_armour_prof_light)
      - [`FEAT_ARMOUR_PROF_MEDIUM`](#feat_armour_prof_medium)
      - [`FEAT_BATTLE_MEDITATION`](#feat_battle_meditation)
      - [`FEAT_CAUTIOUS`](#feat_cautious)
      - [`FEAT_CRITICAL_STRIKE`](#feat_critical_strike)
      - [`FEAT_DOUBLE_WEAPON_FIGHTING`](#feat_double_weapon_fighting)
      - [`FEAT_DROID_UPGRADE_1`](#feat_droid_upgrade_1)
      - [`FEAT_DROID_UPGRADE_2`](#feat_droid_upgrade_2)
      - [`FEAT_DROID_UPGRADE_3`](#feat_droid_upgrade_3)
      - [`FEAT_EMPATHY`](#feat_empathy)
      - [`FEAT_FLURRY`](#feat_flurry)
      - [`FEAT_FORCE_FOCUS_ADVANCED`](#feat_force_focus_advanced)
      - [`FEAT_FORCE_FOCUS_ALTER`](#feat_force_focus_alter)
      - [`FEAT_FORCE_FOCUS_CONTROL`](#feat_force_focus_control)
      - [`FEAT_FORCE_FOCUS_MASTERY`](#feat_force_focus_mastery)
      - [`FEAT_FORCE_FOCUS_SENSE`](#feat_force_focus_sense)
      - [`FEAT_GEAR_HEAD`](#feat_gear_head)
      - [`FEAT_GREAT_FORTITUDE`](#feat_great_fortitude)
      - [`FEAT_GUARD_STANCE`](#feat_guard_stance)
      - [`FEAT_IMPLANT_LEVEL_1`](#feat_implant_level_1)
      - [`FEAT_IMPLANT_LEVEL_2`](#feat_implant_level_2)
      - [`FEAT_IMPLANT_LEVEL_3`](#feat_implant_level_3)
      - [`FEAT_IMPROVED_CRITICAL_STRIKE`](#feat_improved_critical_strike)
      - [`FEAT_IMPROVED_FLURRY`](#feat_improved_flurry)
      - [`FEAT_IMPROVED_POWER_ATTACK`](#feat_improved_power_attack)
      - [`FEAT_IMPROVED_POWER_BLAST`](#feat_improved_power_blast)
      - [`FEAT_IMPROVED_RAPID_SHOT`](#feat_improved_rapid_shot)
      - [`FEAT_IMPROVED_SNIPER_SHOT`](#feat_improved_sniper_shot)
      - [`FEAT_IRON_WILL`](#feat_iron_will)
      - [`FEAT_JEDI_DEFENSE`](#feat_jedi_defense)
      - [`FEAT_LIGHTNING_REFLEXES`](#feat_lightning_reflexes)
      - [`FEAT_MASTER_CRITICAL_STRIKE`](#feat_master_critical_strike)
      - [`FEAT_MASTER_GUARD_STANCE`](#feat_master_guard_stance)
      - [`FEAT_MASTER_JEDI_DEFENSE`](#feat_master_jedi_defense)
      - [`FEAT_MASTER_POWER_ATTACK`](#feat_master_power_attack)
      - [`FEAT_MASTER_POWER_BLAST`](#feat_master_power_blast)
      - [`FEAT_MASTER_SNIPER_SHOT`](#feat_master_sniper_shot)
      - [`FEAT_MULTI_SHOT`](#feat_multi_shot)
      - [`FEAT_PERCEPTIVE`](#feat_perceptive)
      - [`FEAT_POWER_ATTACK`](#feat_power_attack)
      - [`FEAT_POWER_BLAST`](#feat_power_blast)
      - [`FEAT_PROFICIENCY_ALL`](#feat_proficiency_all)
      - [`FEAT_RAPID_SHOT`](#feat_rapid_shot)
      - [`FEAT_SKILL_FOCUS_AWARENESS`](#feat_skill_focus_awareness)
      - [`FEAT_SKILL_FOCUS_COMPUTER_USE`](#feat_skill_focus_computer_use)
      - [`FEAT_SKILL_FOCUS_DEMOLITIONS`](#feat_skill_focus_demolitions)
      - [`FEAT_SKILL_FOCUS_PERSUADE`](#feat_skill_focus_persuade)
      - [`FEAT_SKILL_FOCUS_REPAIR`](#feat_skill_focus_repair)
      - [`FEAT_SKILL_FOCUS_SECURITY`](#feat_skill_focus_security)
      - [`FEAT_SKILL_FOCUS_STEALTH`](#feat_skill_focus_stealth)
      - [`FEAT_SKILL_FOCUS_TREAT_INJUURY`](#feat_skill_focus_treat_injuury)
      - [`FEAT_SNEAK_ATTACK_10D6`](#feat_sneak_attack_10d6)
      - [`FEAT_SNEAK_ATTACK_1D6`](#feat_sneak_attack_1d6)
      - [`FEAT_SNEAK_ATTACK_2D6`](#feat_sneak_attack_2d6)
      - [`FEAT_SNEAK_ATTACK_3D6`](#feat_sneak_attack_3d6)
      - [`FEAT_SNEAK_ATTACK_4D6`](#feat_sneak_attack_4d6)
      - [`FEAT_SNEAK_ATTACK_5D6`](#feat_sneak_attack_5d6)
      - [`FEAT_SNEAK_ATTACK_6D6`](#feat_sneak_attack_6d6)
      - [`FEAT_SNEAK_ATTACK_7D6`](#feat_sneak_attack_7d6)
      - [`FEAT_SNEAK_ATTACK_8D6`](#feat_sneak_attack_8d6)
      - [`FEAT_SNEAK_ATTACK_9D6`](#feat_sneak_attack_9d6)
      - [`FEAT_SNIPER_SHOT`](#feat_sniper_shot)
      - [`FEAT_TOUGHNESS`](#feat_toughness)
      - [`FEAT_UNCANNY_DODGE_1`](#feat_uncanny_dodge_1)
      - [`FEAT_UNCANNY_DODGE_2`](#feat_uncanny_dodge_2)
      - [`FEAT_WEAPON_FOCUS_BLASTER`](#feat_weapon_focus_blaster)
      - [`FEAT_WEAPON_FOCUS_BLASTER_RIFLE`](#feat_weapon_focus_blaster_rifle)
      - [`FEAT_WEAPON_FOCUS_GRENADE`](#feat_weapon_focus_grenade)
      - [`FEAT_WEAPON_FOCUS_HEAVY_WEAPONS`](#feat_weapon_focus_heavy_weapons)
      - [`FEAT_WEAPON_FOCUS_LIGHTSABER`](#feat_weapon_focus_lightsaber)
      - [`FEAT_WEAPON_FOCUS_MELEE_WEAPONS`](#feat_weapon_focus_melee_weapons)
      - [`FEAT_WEAPON_FOCUS_SIMPLE_WEAPONS`](#feat_weapon_focus_simple_weapons)
      - [`FEAT_WEAPON_PROFICIENCY_BLASTER`](#feat_weapon_proficiency_blaster)
      - [`FEAT_WEAPON_PROFICIENCY_BLASTER_RIFLE`](#feat_weapon_proficiency_blaster_rifle)
      - [`FEAT_WEAPON_PROFICIENCY_GRENADE`](#feat_weapon_proficiency_grenade)
      - [`FEAT_WEAPON_PROFICIENCY_HEAVY_WEAPONS`](#feat_weapon_proficiency_heavy_weapons)
      - [`FEAT_WEAPON_PROFICIENCY_LIGHTSABER`](#feat_weapon_proficiency_lightsaber)
      - [`FEAT_WEAPON_PROFICIENCY_MELEE_WEAPONS`](#feat_weapon_proficiency_melee_weapons)
      - [`FEAT_WEAPON_PROFICIENCY_SIMPLE_WEAPONS`](#feat_weapon_proficiency_simple_weapons)
      - [`FEAT_WEAPON_SPECIALIZATION_BLASTER`](#feat_weapon_specialization_blaster)
      - [`FEAT_WEAPON_SPECIALIZATION_BLASTER_RIFLE`](#feat_weapon_specialization_blaster_rifle)
      - [`FEAT_WEAPON_SPECIALIZATION_GRENADE`](#feat_weapon_specialization_grenade)
      - [`FEAT_WEAPON_SPECIALIZATION_HEAVY_WEAPONS`](#feat_weapon_specialization_heavy_weapons)
      - [`FEAT_WEAPON_SPECIALIZATION_LIGHTSABER`](#feat_weapon_specialization_lightsaber)
      - [`FEAT_WEAPON_SPECIALIZATION_MELEE_WEAPONS`](#feat_weapon_specialization_melee_weapons)
      - [`FEAT_WEAPON_SPECIALIZATION_SIMPLE_WEAPONS`](#feat_weapon_specialization_simple_weapons)
      - [`FEAT_WHIRLWIND_ATTACK`](#feat_whirlwind_attack)
      - [`FORCE_POWER_AFFECT_MIND`](#force_power_affect_mind)
      - [`FORCE_POWER_AFFLICTION`](#force_power_affliction)
      - [`FORCE_POWER_ALL_FORCE_POWERS`](#force_power_all_force_powers)
      - [`FORCE_POWER_CHOKE`](#force_power_choke)
      - [`FORCE_POWER_CURE`](#force_power_cure)
      - [`FORCE_POWER_DEATH_FIELD`](#force_power_death_field)
      - [`FORCE_POWER_DOMINATE`](#force_power_dominate)
      - [`FORCE_POWER_DRAIN_LIFE`](#force_power_drain_life)
      - [`FORCE_POWER_DROID_DESTROY`](#force_power_droid_destroy)
      - [`FORCE_POWER_DROID_DISABLE`](#force_power_droid_disable)
      - [`FORCE_POWER_DROID_STUN`](#force_power_droid_stun)
      - [`FORCE_POWER_FEAR`](#force_power_fear)
      - [`FORCE_POWER_FORCE_ARMOR`](#force_power_force_armor)
      - [`FORCE_POWER_FORCE_AURA`](#force_power_force_aura)
      - [`FORCE_POWER_FORCE_BREACH`](#force_power_force_breach)
      - [`FORCE_POWER_FORCE_IMMUNITY`](#force_power_force_immunity)
      - [`FORCE_POWER_FORCE_JUMP`](#force_power_force_jump)
      - [`FORCE_POWER_FORCE_JUMP_ADVANCED`](#force_power_force_jump_advanced)
      - [`FORCE_POWER_FORCE_MIND`](#force_power_force_mind)
      - [`FORCE_POWER_FORCE_PUSH`](#force_power_force_push)
      - [`FORCE_POWER_FORCE_SHIELD`](#force_power_force_shield)
      - [`FORCE_POWER_FORCE_STORM`](#force_power_force_storm)
      - [`FORCE_POWER_FORCE_WAVE`](#force_power_force_wave)
      - [`FORCE_POWER_FORCE_WHIRLWIND`](#force_power_force_whirlwind)
      - [`FORCE_POWER_HEAL`](#force_power_heal)
      - [`FORCE_POWER_HOLD`](#force_power_hold)
      - [`FORCE_POWER_HORROR`](#force_power_horror)
      - [`FORCE_POWER_INSANITY`](#force_power_insanity)
      - [`FORCE_POWER_KILL`](#force_power_kill)
      - [`FORCE_POWER_KNIGHT_MIND`](#force_power_knight_mind)
      - [`FORCE_POWER_KNIGHT_SPEED`](#force_power_knight_speed)
      - [`FORCE_POWER_LIGHT_SABER_THROW`](#force_power_light_saber_throw)
      - [`FORCE_POWER_LIGHT_SABER_THROW_ADVANCED`](#force_power_light_saber_throw_advanced)
      - [`FORCE_POWER_LIGHTNING`](#force_power_lightning)
      - [`FORCE_POWER_MASTER_ALTER`](#force_power_master_alter)
      - [`FORCE_POWER_MASTER_CONTROL`](#force_power_master_control)
      - [`FORCE_POWER_MASTER_SENSE`](#force_power_master_sense)
      - [`FORCE_POWER_MIND_MASTERY`](#force_power_mind_mastery)
      - [`FORCE_POWER_PLAGUE`](#force_power_plague)
      - [`FORCE_POWER_REGENERATION`](#force_power_regeneration)
      - [`FORCE_POWER_REGNERATION_ADVANCED`](#force_power_regneration_advanced)
      - [`FORCE_POWER_RESIST_COLD_HEAT_ENERGY`](#force_power_resist_cold_heat_energy)
      - [`FORCE_POWER_RESIST_FORCE`](#force_power_resist_force)
      - [`FORCE_POWER_RESIST_POISON_DISEASE_SONIC`](#force_power_resist_poison_disease_sonic)
      - [`FORCE_POWER_SHOCK`](#force_power_shock)
      - [`FORCE_POWER_SLEEP`](#force_power_sleep)
      - [`FORCE_POWER_SLOW`](#force_power_slow)
      - [`FORCE_POWER_SPEED_BURST`](#force_power_speed_burst)
      - [`FORCE_POWER_SPEED_MASTERY`](#force_power_speed_mastery)
      - [`FORCE_POWER_STUN`](#force_power_stun)
      - [`FORCE_POWER_SUPRESS_FORCE`](#force_power_supress_force)
      - [`FORCE_POWER_WOUND`](#force_power_wound)
      - [`FORMATION_LINE`](#formation_line)
      - [`FORMATION_WEDGE`](#formation_wedge)
      - [`GAME_DIFFICULTY_CORE_RULES`](#game_difficulty_core_rules)
      - [`GAME_DIFFICULTY_DIFFICULT`](#game_difficulty_difficult)
      - [`GAME_DIFFICULTY_EASY`](#game_difficulty_easy)
      - [`GAME_DIFFICULTY_NORMAL`](#game_difficulty_normal)
      - [`GAME_DIFFICULTY_VERY_EASY`](#game_difficulty_very_easy)
      - [`GENDER_BOTH`](#gender_both)
      - [`GENDER_FEMALE`](#gender_female)
      - [`GENDER_MALE`](#gender_male)
      - [`GENDER_NONE`](#gender_none)
      - [`GENDER_OTHER`](#gender_other)
      - [`GUI_PANEL_PLAYER_DEATH`](#gui_panel_player_death)
      - [`IMMUNITY_TYPE_ABILITY_DECREASE`](#immunity_type_ability_decrease)
      - [`IMMUNITY_TYPE_AC_DECREASE`](#immunity_type_ac_decrease)
      - [`IMMUNITY_TYPE_ATTACK_DECREASE`](#immunity_type_attack_decrease)
      - [`IMMUNITY_TYPE_BLINDNESS`](#immunity_type_blindness)
      - [`IMMUNITY_TYPE_CHARM`](#immunity_type_charm)
      - [`IMMUNITY_TYPE_CONFUSED`](#immunity_type_confused)
      - [`IMMUNITY_TYPE_CRITICAL_HIT`](#immunity_type_critical_hit)
      - [`IMMUNITY_TYPE_CURSED`](#immunity_type_cursed)
      - [`IMMUNITY_TYPE_DAMAGE_DECREASE`](#immunity_type_damage_decrease)
      - [`IMMUNITY_TYPE_DAMAGE_IMMUNITY_DECREASE`](#immunity_type_damage_immunity_decrease)
      - [`IMMUNITY_TYPE_DAZED`](#immunity_type_dazed)
      - [`IMMUNITY_TYPE_DEAFNESS`](#immunity_type_deafness)
      - [`IMMUNITY_TYPE_DEATH`](#immunity_type_death)
      - [`IMMUNITY_TYPE_DISEASE`](#immunity_type_disease)
      - [`IMMUNITY_TYPE_DOMINATE`](#immunity_type_dominate)
      - [`IMMUNITY_TYPE_ENTANGLE`](#immunity_type_entangle)
      - [`IMMUNITY_TYPE_FEAR`](#immunity_type_fear)
      - [`IMMUNITY_TYPE_FORCE_RESISTANCE_DECREASE`](#immunity_type_force_resistance_decrease)
      - [`IMMUNITY_TYPE_KNOCKDOWN`](#immunity_type_knockdown)
      - [`IMMUNITY_TYPE_MIND_SPELLS`](#immunity_type_mind_spells)
      - [`IMMUNITY_TYPE_MOVEMENT_SPEED_DECREASE`](#immunity_type_movement_speed_decrease)
      - [`IMMUNITY_TYPE_NEGATIVE_LEVEL`](#immunity_type_negative_level)
      - [`IMMUNITY_TYPE_NONE`](#immunity_type_none)
      - [`IMMUNITY_TYPE_PARALYSIS`](#immunity_type_paralysis)
      - [`IMMUNITY_TYPE_POISON`](#immunity_type_poison)
      - [`IMMUNITY_TYPE_SAVING_THROW_DECREASE`](#immunity_type_saving_throw_decrease)
      - [`IMMUNITY_TYPE_SILENCE`](#immunity_type_silence)
      - [`IMMUNITY_TYPE_SKILL_DECREASE`](#immunity_type_skill_decrease)
      - [`IMMUNITY_TYPE_SLEEP`](#immunity_type_sleep)
      - [`IMMUNITY_TYPE_SLOW`](#immunity_type_slow)
      - [`IMMUNITY_TYPE_SNEAK_ATTACK`](#immunity_type_sneak_attack)
      - [`IMMUNITY_TYPE_STUN`](#immunity_type_stun)
      - [`IMMUNITY_TYPE_TRAP`](#immunity_type_trap)
      - [`INVALID_STANDARD_FACTION`](#invalid_standard_faction)
      - [`INVISIBILITY_TYPE_DARKNESS`](#invisibility_type_darkness)
      - [`INVISIBILITY_TYPE_IMPROVED`](#invisibility_type_improved)
      - [`INVISIBILITY_TYPE_NORMAL`](#invisibility_type_normal)
      - [`ITEM_PROPERTY_ABILITY_BONUS`](#item_property_ability_bonus)
      - [`ITEM_PROPERTY_AC_BONUS`](#item_property_ac_bonus)
      - [`ITEM_PROPERTY_AC_BONUS_VS_DAMAGE_TYPE`](#item_property_ac_bonus_vs_damage_type)
      - [`ITEM_PROPERTY_AC_BONUS_VS_RACIAL_GROUP`](#item_property_ac_bonus_vs_racial_group)
      - [`ITEM_PROPERTY_ACTIVATE_ITEM`](#item_property_activate_item)
      - [`ITEM_PROPERTY_ATTACK_BONUS`](#item_property_attack_bonus)
      - [`ITEM_PROPERTY_ATTACK_BONUS_VS_RACIAL_GROUP`](#item_property_attack_bonus_vs_racial_group)
      - [`ITEM_PROPERTY_ATTACK_PENALTY`](#item_property_attack_penalty)
      - [`ITEM_PROPERTY_BLASTER_BOLT_DEFLECT_DECREASE`](#item_property_blaster_bolt_deflect_decrease)
      - [`ITEM_PROPERTY_BLASTER_BOLT_DEFLECT_INCREASE`](#item_property_blaster_bolt_deflect_increase)
      - [`ITEM_PROPERTY_BONUS_FEAT`](#item_property_bonus_feat)
      - [`ITEM_PROPERTY_COMPUTER_SPIKE`](#item_property_computer_spike)
      - [`ITEM_PROPERTY_DAMAGE_BONUS`](#item_property_damage_bonus)
      - [`ITEM_PROPERTY_DAMAGE_BONUS_VS_RACIAL_GROUP`](#item_property_damage_bonus_vs_racial_group)
      - [`ITEM_PROPERTY_DAMAGE_REDUCTION`](#item_property_damage_reduction)
      - [`ITEM_PROPERTY_DAMAGE_RESISTANCE`](#item_property_damage_resistance)
      - [`ITEM_PROPERTY_DAMAGE_VULNERABILITY`](#item_property_damage_vulnerability)
      - [`ITEM_PROPERTY_DECREASED_ABILITY_SCORE`](#item_property_decreased_ability_score)
      - [`ITEM_PROPERTY_DECREASED_AC`](#item_property_decreased_ac)
      - [`ITEM_PROPERTY_DECREASED_ATTACK_MODIFIER`](#item_property_decreased_attack_modifier)
      - [`ITEM_PROPERTY_DECREASED_DAMAGE`](#item_property_decreased_damage)
      - [`ITEM_PROPERTY_DECREASED_SAVING_THROWS`](#item_property_decreased_saving_throws)
      - [`ITEM_PROPERTY_DECREASED_SAVING_THROWS_SPECIFIC`](#item_property_decreased_saving_throws_specific)
      - [`ITEM_PROPERTY_DECREASED_SKILL_MODIFIER`](#item_property_decreased_skill_modifier)
      - [`ITEM_PROPERTY_DROID_REPAIR_KIT`](#item_property_droid_repair_kit)
      - [`ITEM_PROPERTY_ENHANCEMENT_BONUS`](#item_property_enhancement_bonus)
      - [`ITEM_PROPERTY_ENHANCEMENT_BONUS_VS_RACIAL_GROUP`](#item_property_enhancement_bonus_vs_racial_group)
      - [`ITEM_PROPERTY_EXTRA_MELEE_DAMAGE_TYPE`](#item_property_extra_melee_damage_type)
      - [`ITEM_PROPERTY_EXTRA_RANGED_DAMAGE_TYPE`](#item_property_extra_ranged_damage_type)
      - [`ITEM_PROPERTY_FREEDOM_OF_MOVEMENT`](#item_property_freedom_of_movement)
      - [`ITEM_PROPERTY_IMMUNITY`](#item_property_immunity)
      - [`ITEM_PROPERTY_IMMUNITY_DAMAGE_TYPE`](#item_property_immunity_damage_type)
      - [`ITEM_PROPERTY_IMPROVED_FORCE_RESISTANCE`](#item_property_improved_force_resistance)
      - [`ITEM_PROPERTY_IMPROVED_SAVING_THROW`](#item_property_improved_saving_throw)
      - [`ITEM_PROPERTY_IMPROVED_SAVING_THROW_SPECIFIC`](#item_property_improved_saving_throw_specific)
      - [`ITEM_PROPERTY_KEEN`](#item_property_keen)
      - [`ITEM_PROPERTY_LIGHT`](#item_property_light)
      - [`ITEM_PROPERTY_MASSIVE_CRITICALS`](#item_property_massive_criticals)
      - [`ITEM_PROPERTY_MIGHTY`](#item_property_mighty)
      - [`ITEM_PROPERTY_MONSTER_DAMAGE`](#item_property_monster_damage)
      - [`ITEM_PROPERTY_NO_DAMAGE`](#item_property_no_damage)
      - [`ITEM_PROPERTY_ON_HIT_PROPERTIES`](#item_property_on_hit_properties)
      - [`ITEM_PROPERTY_ON_MONSTER_HIT`](#item_property_on_monster_hit)
      - [`ITEM_PROPERTY_REGENERATION`](#item_property_regeneration)
      - [`ITEM_PROPERTY_REGENERATION_FORCE_POINTS`](#item_property_regeneration_force_points)
      - [`ITEM_PROPERTY_SECURITY_SPIKE`](#item_property_security_spike)
      - [`ITEM_PROPERTY_SKILL_BONUS`](#item_property_skill_bonus)
      - [`ITEM_PROPERTY_SPECIAL_WALK`](#item_property_special_walk)
      - [`ITEM_PROPERTY_TRAP`](#item_property_trap)
      - [`ITEM_PROPERTY_TRUE_SEEING`](#item_property_true_seeing)
      - [`ITEM_PROPERTY_UNLIMITED_AMMUNITION`](#item_property_unlimited_ammunition)
      - [`ITEM_PROPERTY_USE_LIMITATION_CLASS`](#item_property_use_limitation_class)
      - [`ITEM_PROPERTY_USE_LIMITATION_FEAT`](#item_property_use_limitation_feat)
      - [`ITEM_PROPERTY_USE_LIMITATION_RACIAL_TYPE`](#item_property_use_limitation_racial_type)
      - [`LIVE_CONTENT_PKG1`](#live_content_pkg1)
      - [`LIVE_CONTENT_PKG2`](#live_content_pkg2)
      - [`LIVE_CONTENT_PKG3`](#live_content_pkg3)
      - [`LIVE_CONTENT_PKG4`](#live_content_pkg4)
      - [`LIVE_CONTENT_PKG5`](#live_content_pkg5)
      - [`LIVE_CONTENT_PKG6`](#live_content_pkg6)
      - [`MOVEMENT_SPEED_DEFAULT`](#movement_speed_default)
      - [`MOVEMENT_SPEED_DMFAST`](#movement_speed_dmfast)
      - [`MOVEMENT_SPEED_FAST`](#movement_speed_fast)
      - [`MOVEMENT_SPEED_IMMOBILE`](#movement_speed_immobile)
      - [`MOVEMENT_SPEED_NORMAL`](#movement_speed_normal)
      - [`MOVEMENT_SPEED_PC`](#movement_speed_pc)
      - [`MOVEMENT_SPEED_SLOW`](#movement_speed_slow)
      - [`MOVEMENT_SPEED_VERYFAST`](#movement_speed_veryfast)
      - [`MOVEMENT_SPEED_VERYSLOW`](#movement_speed_veryslow)
      - [`PARTY_AISTYLE_AGGRESSIVE`](#party_aistyle_aggressive)
      - [`PARTY_AISTYLE_DEFENSIVE`](#party_aistyle_defensive)
      - [`PARTY_AISTYLE_PASSIVE`](#party_aistyle_passive)
      - [`PERCEPTION_HEARD`](#perception_heard)
      - [`PERCEPTION_HEARD_AND_NOT_SEEN`](#perception_heard_and_not_seen)
      - [`PERCEPTION_NOT_HEARD`](#perception_not_heard)
      - [`PERCEPTION_NOT_SEEN`](#perception_not_seen)
      - [`PERCEPTION_NOT_SEEN_AND_NOT_HEARD`](#perception_not_seen_and_not_heard)
      - [`PERCEPTION_SEEN`](#perception_seen)
      - [`PERCEPTION_SEEN_AND_HEARD`](#perception_seen_and_heard)
      - [`PERCEPTION_SEEN_AND_NOT_HEARD`](#perception_seen_and_not_heard)
      - [`PERSISTENT_ZONE_ACTIVE`](#persistent_zone_active)
      - [`PERSISTENT_ZONE_FOLLOW`](#persistent_zone_follow)
      - [`PI`](#pi)
      - [`PLACEABLE_ACTION_BASH`](#placeable_action_bash)
      - [`PLACEABLE_ACTION_KNOCK`](#placeable_action_knock)
      - [`PLACEABLE_ACTION_UNLOCK`](#placeable_action_unlock)
      - [`PLACEABLE_ACTION_USE`](#placeable_action_use)
      - [`PLAYER_CHAR_IS_PC`](#player_char_is_pc)
      - [`PLAYER_CHAR_NOT_PC`](#player_char_not_pc)
      - [`PLOT_O_BIG_MONSTERS`](#plot_o_big_monsters)
      - [`PLOT_O_DOOM`](#plot_o_doom)
      - [`PLOT_O_SCARY_STUFF`](#plot_o_scary_stuff)
      - [`POISON_ABILITY_SCORE_AVERAGE`](#poison_ability_score_average)
      - [`POISON_ABILITY_SCORE_MILD`](#poison_ability_score_mild)
      - [`POISON_ABILITY_SCORE_VIRULENT`](#poison_ability_score_virulent)
      - [`POISON_DAMAGE_AVERAGE`](#poison_damage_average)
      - [`POISON_DAMAGE_MILD`](#poison_damage_mild)
      - [`POISON_DAMAGE_VIRULENT`](#poison_damage_virulent)
      - [`POLYMORPH_TYPE_BADGER`](#polymorph_type_badger)
      - [`POLYMORPH_TYPE_BALOR`](#polymorph_type_balor)
      - [`POLYMORPH_TYPE_BOAR`](#polymorph_type_boar)
      - [`POLYMORPH_TYPE_BROWN_BEAR`](#polymorph_type_brown_bear)
      - [`POLYMORPH_TYPE_COW`](#polymorph_type_cow)
      - [`POLYMORPH_TYPE_DEATH_SLAAD`](#polymorph_type_death_slaad)
      - [`POLYMORPH_TYPE_DIRE_BADGER`](#polymorph_type_dire_badger)
      - [`POLYMORPH_TYPE_DIRE_BOAR`](#polymorph_type_dire_boar)
      - [`POLYMORPH_TYPE_DIRE_BROWN_BEAR`](#polymorph_type_dire_brown_bear)
      - [`POLYMORPH_TYPE_DIRE_PANTHER`](#polymorph_type_dire_panther)
      - [`POLYMORPH_TYPE_DIRE_WOLF`](#polymorph_type_dire_wolf)
      - [`POLYMORPH_TYPE_DOOM_KNIGHT`](#polymorph_type_doom_knight)
      - [`POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL`](#polymorph_type_elder_air_elemental)
      - [`POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL`](#polymorph_type_elder_earth_elemental)
      - [`POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL`](#polymorph_type_elder_fire_elemental)
      - [`POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL`](#polymorph_type_elder_water_elemental)
      - [`POLYMORPH_TYPE_FIRE_GIANT`](#polymorph_type_fire_giant)
      - [`POLYMORPH_TYPE_GIANT_SPIDER`](#polymorph_type_giant_spider)
      - [`POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL`](#polymorph_type_huge_air_elemental)
      - [`POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL`](#polymorph_type_huge_earth_elemental)
      - [`POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL`](#polymorph_type_huge_fire_elemental)
      - [`POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL`](#polymorph_type_huge_water_elemental)
      - [`POLYMORPH_TYPE_IMP`](#polymorph_type_imp)
      - [`POLYMORPH_TYPE_IRON_GOLEM`](#polymorph_type_iron_golem)
      - [`POLYMORPH_TYPE_PANTHER`](#polymorph_type_panther)
      - [`POLYMORPH_TYPE_PENGUIN`](#polymorph_type_penguin)
      - [`POLYMORPH_TYPE_PIXIE`](#polymorph_type_pixie)
      - [`POLYMORPH_TYPE_QUASIT`](#polymorph_type_quasit)
      - [`POLYMORPH_TYPE_RED_DRAGON`](#polymorph_type_red_dragon)
      - [`POLYMORPH_TYPE_SUCCUBUS`](#polymorph_type_succubus)
      - [`POLYMORPH_TYPE_TROLL`](#polymorph_type_troll)
      - [`POLYMORPH_TYPE_UMBER_HULK`](#polymorph_type_umber_hulk)
      - [`POLYMORPH_TYPE_WERECAT`](#polymorph_type_werecat)
      - [`POLYMORPH_TYPE_WERERAT`](#polymorph_type_wererat)
      - [`POLYMORPH_TYPE_WEREWOLF`](#polymorph_type_werewolf)
      - [`POLYMORPH_TYPE_WOLF`](#polymorph_type_wolf)
      - [`POLYMORPH_TYPE_YUANTI`](#polymorph_type_yuanti)
      - [`POLYMORPH_TYPE_ZOMBIE`](#polymorph_type_zombie)
      - [`PROJECTILE_PATH_TYPE_ACCELERATING`](#projectile_path_type_accelerating)
      - [`PROJECTILE_PATH_TYPE_BALLISTIC`](#projectile_path_type_ballistic)
      - [`PROJECTILE_PATH_TYPE_DEFAULT`](#projectile_path_type_default)
      - [`PROJECTILE_PATH_TYPE_HIGH_BALLISTIC`](#projectile_path_type_high_ballistic)
      - [`PROJECTILE_PATH_TYPE_HOMING`](#projectile_path_type_homing)
      - [`RACIAL_TYPE_ALL`](#racial_type_all)
      - [`RACIAL_TYPE_DROID`](#racial_type_droid)
      - [`RACIAL_TYPE_ELF`](#racial_type_elf)
      - [`RACIAL_TYPE_GNOME`](#racial_type_gnome)
      - [`RACIAL_TYPE_HALFELF`](#racial_type_halfelf)
      - [`RACIAL_TYPE_HALFLING`](#racial_type_halfling)
      - [`RACIAL_TYPE_HUMAN`](#racial_type_human)
      - [`RACIAL_TYPE_INVALID`](#racial_type_invalid)
      - [`RACIAL_TYPE_UNKNOWN`](#racial_type_unknown)
      - [`RADIUS_SIZE_COLOSSAL`](#radius_size_colossal)
      - [`RADIUS_SIZE_GARGANTUAN`](#radius_size_gargantuan)
      - [`RADIUS_SIZE_HUGE`](#radius_size_huge)
      - [`RADIUS_SIZE_LARGE`](#radius_size_large)
      - [`RADIUS_SIZE_MEDIUM`](#radius_size_medium)
      - [`RADIUS_SIZE_SMALL`](#radius_size_small)
      - [`REPUTATION_TYPE_ENEMY`](#reputation_type_enemy)
      - [`REPUTATION_TYPE_FRIEND`](#reputation_type_friend)
      - [`REPUTATION_TYPE_NEUTRAL`](#reputation_type_neutral)
      - [`SAVING_THROW_ALL`](#saving_throw_all)
      - [`SAVING_THROW_FORT`](#saving_throw_fort)
      - [`SAVING_THROW_REFLEX`](#saving_throw_reflex)
      - [`SAVING_THROW_TYPE_ACID`](#saving_throw_type_acid)
      - [`SAVING_THROW_TYPE_ALL`](#saving_throw_type_all)
      - [`SAVING_THROW_TYPE_BLASTER`](#saving_throw_type_blaster)
      - [`SAVING_THROW_TYPE_COLD`](#saving_throw_type_cold)
      - [`SAVING_THROW_TYPE_DARK_SIDE`](#saving_throw_type_dark_side)
      - [`SAVING_THROW_TYPE_DEATH`](#saving_throw_type_death)
      - [`SAVING_THROW_TYPE_DISEASE`](#saving_throw_type_disease)
      - [`SAVING_THROW_TYPE_ELECTRICAL`](#saving_throw_type_electrical)
      - [`SAVING_THROW_TYPE_FEAR`](#saving_throw_type_fear)
      - [`SAVING_THROW_TYPE_FIRE`](#saving_throw_type_fire)
      - [`SAVING_THROW_TYPE_FORCE_POWER`](#saving_throw_type_force_power)
      - [`SAVING_THROW_TYPE_ION`](#saving_throw_type_ion)
      - [`SAVING_THROW_TYPE_LIGHT_SIDE`](#saving_throw_type_light_side)
      - [`SAVING_THROW_TYPE_MIND_AFFECTING`](#saving_throw_type_mind_affecting)
      - [`SAVING_THROW_TYPE_NONE`](#saving_throw_type_none)
      - [`SAVING_THROW_TYPE_PARALYSIS`](#saving_throw_type_paralysis)
      - [`SAVING_THROW_TYPE_POISON`](#saving_throw_type_poison)
      - [`SAVING_THROW_TYPE_SNEAK_ATTACK`](#saving_throw_type_sneak_attack)
      - [`SAVING_THROW_TYPE_SONIC`](#saving_throw_type_sonic)
      - [`SAVING_THROW_TYPE_TRAP`](#saving_throw_type_trap)
      - [`SAVING_THROW_WILL`](#saving_throw_will)
      - [`SHAPE_CONE`](#shape_cone)
      - [`SHAPE_CUBE`](#shape_cube)
      - [`SHAPE_SPELLCONE`](#shape_spellcone)
      - [`SHAPE_SPELLCYLINDER`](#shape_spellcylinder)
      - [`SHAPE_SPHERE`](#shape_sphere)
      - [`SHIELD_ANTIQUE_DROID`](#shield_antique_droid)
      - [`SHIELD_DROID_ENERGY_1`](#shield_droid_energy_1)
      - [`SHIELD_DROID_ENERGY_2`](#shield_droid_energy_2)
      - [`SHIELD_DROID_ENERGY_3`](#shield_droid_energy_3)
      - [`SHIELD_DROID_ENVIRO_1`](#shield_droid_enviro_1)
      - [`SHIELD_DROID_ENVIRO_2`](#shield_droid_enviro_2)
      - [`SHIELD_DROID_ENVIRO_3`](#shield_droid_enviro_3)
      - [`SHIELD_DUELING_ECHANI`](#shield_dueling_echani)
      - [`SHIELD_DUELING_YUSANIS`](#shield_dueling_yusanis)
      - [`SHIELD_ECHANI`](#shield_echani)
      - [`SHIELD_ENERGY`](#shield_energy)
      - [`SHIELD_ENERGY_ARKANIAN`](#shield_energy_arkanian)
      - [`SHIELD_ENERGY_SITH`](#shield_energy_sith)
      - [`SHIELD_MANDALORIAN_MELEE`](#shield_mandalorian_melee)
      - [`SHIELD_MANDALORIAN_POWER`](#shield_mandalorian_power)
      - [`SHIELD_PLOT_TAR_M09AA`](#shield_plot_tar_m09aa)
      - [`SHIELD_PLOT_UNK_M44AA`](#shield_plot_unk_m44aa)
      - [`SHIELD_VERPINE_PROTOTYPE`](#shield_verpine_prototype)
      - [`SKILL_AWARENESS`](#skill_awareness)
      - [`SKILL_COMPUTER_USE`](#skill_computer_use)
      - [`SKILL_DEMOLITIONS`](#skill_demolitions)
      - [`SKILL_MAX_SKILLS`](#skill_max_skills)
      - [`SKILL_PERSUADE`](#skill_persuade)
      - [`SKILL_REPAIR`](#skill_repair)
      - [`SKILL_SECURITY`](#skill_security)
      - [`SKILL_STEALTH`](#skill_stealth)
      - [`SKILL_TREAT_INJURY`](#skill_treat_injury)
      - [`sLanguage`](#slanguage)
      - [`SPECIAL_ABILITY_BATTLE_MEDITATION`](#special_ability_battle_meditation)
      - [`SPECIAL_ABILITY_BODY_FUEL`](#special_ability_body_fuel)
      - [`SPECIAL_ABILITY_CAMOFLAGE`](#special_ability_camoflage)
      - [`SPECIAL_ABILITY_CATHAR_REFLEXES`](#special_ability_cathar_reflexes)
      - [`SPECIAL_ABILITY_COMBAT_REGENERATION`](#special_ability_combat_regeneration)
      - [`SPECIAL_ABILITY_DOMINATE_MIND`](#special_ability_dominate_mind)
      - [`SPECIAL_ABILITY_ENHANCED_SENSES`](#special_ability_enhanced_senses)
      - [`SPECIAL_ABILITY_PSYCHIC_STANCE`](#special_ability_psychic_stance)
      - [`SPECIAL_ABILITY_RAGE`](#special_ability_rage)
      - [`SPECIAL_ABILITY_SENTINEL_STANCE`](#special_ability_sentinel_stance)
      - [`SPECIAL_ABILITY_TAUNT`](#special_ability_taunt)
      - [`SPECIAL_ABILITY_WARRIOR_STANCE`](#special_ability_warrior_stance)
      - [`SPECIAL_ABILITY_WHIRLING_DERVISH`](#special_ability_whirling_dervish)
      - [`SPECIAL_ATTACK_CALLED_SHOT_ARM`](#special_attack_called_shot_arm)
      - [`SPECIAL_ATTACK_CALLED_SHOT_LEG`](#special_attack_called_shot_leg)
      - [`SPECIAL_ATTACK_DISARM`](#special_attack_disarm)
      - [`SPECIAL_ATTACK_FLURRY_OF_BLOWS`](#special_attack_flurry_of_blows)
      - [`SPECIAL_ATTACK_IMPROVED_DISARM`](#special_attack_improved_disarm)
      - [`SPECIAL_ATTACK_IMPROVED_KNOCKDOWN`](#special_attack_improved_knockdown)
      - [`SPECIAL_ATTACK_INVALID`](#special_attack_invalid)
      - [`SPECIAL_ATTACK_KNOCKDOWN`](#special_attack_knockdown)
      - [`SPECIAL_ATTACK_RAPID_SHOT`](#special_attack_rapid_shot)
      - [`SPECIAL_ATTACK_SAP`](#special_attack_sap)
      - [`SPECIAL_ATTACK_STUNNING_FIST`](#special_attack_stunning_fist)
      - [`STANDARD_FACTION_ENDAR_SPIRE`](#standard_faction_endar_spire)
      - [`STANDARD_FACTION_FRIENDLY_1`](#standard_faction_friendly_1)
      - [`STANDARD_FACTION_FRIENDLY_2`](#standard_faction_friendly_2)
      - [`STANDARD_FACTION_GIZKA_1`](#standard_faction_gizka_1)
      - [`STANDARD_FACTION_GIZKA_2`](#standard_faction_gizka_2)
      - [`STANDARD_FACTION_GLB_XOR`](#standard_faction_glb_xor)
      - [`STANDARD_FACTION_HOSTILE_1`](#standard_faction_hostile_1)
      - [`STANDARD_FACTION_HOSTILE_2`](#standard_faction_hostile_2)
      - [`STANDARD_FACTION_INSANE`](#standard_faction_insane)
      - [`STANDARD_FACTION_NEUTRAL`](#standard_faction_neutral)
      - [`STANDARD_FACTION_PREDATOR`](#standard_faction_predator)
      - [`STANDARD_FACTION_PREY`](#standard_faction_prey)
      - [`STANDARD_FACTION_PTAT_TUSKAN`](#standard_faction_ptat_tuskan)
      - [`STANDARD_FACTION_RANCOR`](#standard_faction_rancor)
      - [`STANDARD_FACTION_SURRENDER_1`](#standard_faction_surrender_1)
      - [`STANDARD_FACTION_SURRENDER_2`](#standard_faction_surrender_2)
      - [`STANDARD_FACTION_TRAP`](#standard_faction_trap)
      - [`SUBRACE_NONE`](#subrace_none)
      - [`SUBRACE_WOOKIE`](#subrace_wookie)
      - [`SUBSCREEN_ID_ABILITY`](#subscreen_id_ability)
      - [`SUBSCREEN_ID_CHARACTER_RECORD`](#subscreen_id_character_record)
      - [`SUBSCREEN_ID_EQUIP`](#subscreen_id_equip)
      - [`SUBSCREEN_ID_ITEM`](#subscreen_id_item)
      - [`SUBSCREEN_ID_MAP`](#subscreen_id_map)
      - [`SUBSCREEN_ID_MESSAGES`](#subscreen_id_messages)
      - [`SUBSCREEN_ID_NONE`](#subscreen_id_none)
      - [`SUBSCREEN_ID_OPTIONS`](#subscreen_id_options)
      - [`SUBSCREEN_ID_QUEST`](#subscreen_id_quest)
      - [`SUBSKILL_EXAMINETRAP`](#subskill_examinetrap)
      - [`SUBSKILL_FLAGTRAP`](#subskill_flagtrap)
      - [`SUBSKILL_RECOVERTRAP`](#subskill_recovertrap)
      - [`SUBTYPE_EXTRAORDINARY`](#subtype_extraordinary)
      - [`SUBTYPE_MAGICAL`](#subtype_magical)
      - [`SUBTYPE_SUPERNATURAL`](#subtype_supernatural)
      - [`SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH`](#swminigame_trackfollower_sound_death)
      - [`SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE`](#swminigame_trackfollower_sound_engine)
      - [`TALENT_EXCLUDE_ALL_OF_TYPE`](#talent_exclude_all_of_type)
      - [`TALENT_TYPE_FEAT`](#talent_type_feat)
      - [`TALENT_TYPE_FORCE`](#talent_type_force)
      - [`TALENT_TYPE_SKILL`](#talent_type_skill)
      - [`TALENT_TYPE_SPELL`](#talent_type_spell)
      - [`TALKVOLUME_SHOUT`](#talkvolume_shout)
      - [`TALKVOLUME_SILENT_SHOUT`](#talkvolume_silent_shout)
      - [`TALKVOLUME_SILENT_TALK`](#talkvolume_silent_talk)
      - [`TALKVOLUME_TALK`](#talkvolume_talk)
      - [`TALKVOLUME_WHISPER`](#talkvolume_whisper)
      - [`TRAP_BASE_TYPE_FLASH_STUN_AVERAGE`](#trap_base_type_flash_stun_average)
      - [`TRAP_BASE_TYPE_FLASH_STUN_DEADLY`](#trap_base_type_flash_stun_deadly)
      - [`TRAP_BASE_TYPE_FLASH_STUN_MINOR`](#trap_base_type_flash_stun_minor)
      - [`TRAP_BASE_TYPE_FRAGMENTATION_MINE_AVERAGE`](#trap_base_type_fragmentation_mine_average)
      - [`TRAP_BASE_TYPE_FRAGMENTATION_MINE_DEADLY`](#trap_base_type_fragmentation_mine_deadly)
      - [`TRAP_BASE_TYPE_FRAGMENTATION_MINE_MINOR`](#trap_base_type_fragmentation_mine_minor)
      - [`TRAP_BASE_TYPE_LASER_SLICING_AVERAGE`](#trap_base_type_laser_slicing_average)
      - [`TRAP_BASE_TYPE_LASER_SLICING_DEADLY`](#trap_base_type_laser_slicing_deadly)
      - [`TRAP_BASE_TYPE_LASER_SLICING_MINOR`](#trap_base_type_laser_slicing_minor)
      - [`TRAP_BASE_TYPE_POISON_GAS_AVERAGE`](#trap_base_type_poison_gas_average)
      - [`TRAP_BASE_TYPE_POISON_GAS_DEADLY`](#trap_base_type_poison_gas_deadly)
      - [`TRAP_BASE_TYPE_POISON_GAS_MINOR`](#trap_base_type_poison_gas_minor)
      - [`TRUE`](#true)
      - [`TUTORIAL_WINDOW_RETURN_TO_BASE`](#tutorial_window_return_to_base)
      - [`TUTORIAL_WINDOW_START_SWOOP_RACE`](#tutorial_window_start_swoop_race)
      - [`VIDEO_EFFECT_FREELOOK_HK47`](#video_effect_freelook_hk47)
      - [`VIDEO_EFFECT_FREELOOK_T3M4`](#video_effect_freelook_t3m4)
      - [`VIDEO_EFFECT_NONE`](#video_effect_none)
      - [`VIDEO_EFFECT_SECURITY_CAMERA`](#video_effect_security_camera)
    - [Planet Constants](#planet-constants)
      - [`PLANET_DANTOOINE`](#planet_dantooine)
      - [`PLANET_EBON_HAWK`](#planet_ebon_hawk)
      - [`PLANET_KORRIBAN`](#planet_korriban)
      - [`PLANET_LIVE_01`](#planet_live_01)
      - [`PLANET_LIVE_02`](#planet_live_02)
      - [`PLANET_LIVE_03`](#planet_live_03)
      - [`PLANET_LIVE_04`](#planet_live_04)
      - [`PLANET_LIVE_05`](#planet_live_05)
    - [Visual Effects (VFX)](#visual-effects-vfx)
      - [`VFX_ARD_HEAT_SHIMMER`](#vfx_ard_heat_shimmer)
      - [`VFX_ARD_LIGHT_BLIND`](#vfx_ard_light_blind)
      - [`VFX_ARD_LIGHT_YELLOW_10`](#vfx_ard_light_yellow_10)
      - [`VFX_ARD_LIGHT_YELLOW_20`](#vfx_ard_light_yellow_20)
      - [`VFX_BEAM_COLD_RAY`](#vfx_beam_cold_ray)
      - [`VFX_BEAM_DEATH_FIELD_TENTACLE`](#vfx_beam_death_field_tentacle)
      - [`VFX_BEAM_DRAIN_LIFE`](#vfx_beam_drain_life)
      - [`VFX_BEAM_DROID_DESTROY`](#vfx_beam_droid_destroy)
      - [`VFX_BEAM_DROID_DISABLE`](#vfx_beam_droid_disable)
      - [`VFX_BEAM_FLAME_SPRAY`](#vfx_beam_flame_spray)
      - [`VFX_BEAM_ION_RAY_01`](#vfx_beam_ion_ray_01)
      - [`VFX_BEAM_ION_RAY_02`](#vfx_beam_ion_ray_02)
      - [`VFX_BEAM_LIGHTNING_DARK_L`](#vfx_beam_lightning_dark_l)
      - [`VFX_BEAM_LIGHTNING_DARK_S`](#vfx_beam_lightning_dark_s)
      - [`VFX_BEAM_STUN_RAY`](#vfx_beam_stun_ray)
      - [`VFX_COM_BLASTER_DEFLECTION`](#vfx_com_blaster_deflection)
      - [`VFX_COM_BLASTER_IMPACT`](#vfx_com_blaster_impact)
      - [`VFX_COM_BLASTER_IMPACT_GROUND`](#vfx_com_blaster_impact_ground)
      - [`VFX_COM_CRITICAL_STRIKE_IMPROVED_SABER`](#vfx_com_critical_strike_improved_saber)
      - [`VFX_COM_CRITICAL_STRIKE_IMPROVED_STAFF`](#vfx_com_critical_strike_improved_staff)
      - [`VFX_COM_CRITICAL_STRIKE_MASTERY_SABER`](#vfx_com_critical_strike_mastery_saber)
      - [`VFX_COM_CRITICAL_STRIKE_MASTERY_STAFF`](#vfx_com_critical_strike_mastery_staff)
      - [`VFX_COM_DROID_EXPLOSION_1`](#vfx_com_droid_explosion_1)
      - [`VFX_COM_DROID_EXPLOSION_2`](#vfx_com_droid_explosion_2)
      - [`VFX_COM_FLURRY_IMPROVED_SABER`](#vfx_com_flurry_improved_saber)
      - [`VFX_COM_FLURRY_IMPROVED_STAFF`](#vfx_com_flurry_improved_staff)
      - [`VFX_COM_FORCE_RESISTED`](#vfx_com_force_resisted)
      - [`VFX_COM_JEDI_FORCE_FIZZLE`](#vfx_com_jedi_force_fizzle)
      - [`VFX_COM_MULTI_SHOT`](#vfx_com_multi_shot)
      - [`VFX_COM_POWER_ATTACK_IMPROVED_SABER`](#vfx_com_power_attack_improved_saber)
      - [`VFX_COM_POWER_ATTACK_IMPROVED_STAFF`](#vfx_com_power_attack_improved_staff)
      - [`VFX_COM_POWER_ATTACK_MASTERY_SABER`](#vfx_com_power_attack_mastery_saber)
      - [`VFX_COM_POWER_ATTACK_MASTERY_STAFF`](#vfx_com_power_attack_mastery_staff)
      - [`VFX_COM_POWER_BLAST_IMPROVED`](#vfx_com_power_blast_improved)
      - [`VFX_COM_POWER_BLAST_MASTERY`](#vfx_com_power_blast_mastery)
      - [`VFX_COM_RAPID_SHOT_IMPROVED`](#vfx_com_rapid_shot_improved)
      - [`VFX_COM_SNIPER_SHOT_IMPROVED`](#vfx_com_sniper_shot_improved)
      - [`VFX_COM_SNIPER_SHOT_MASTERY`](#vfx_com_sniper_shot_mastery)
      - [`VFX_COM_SPARKS_BLASTER`](#vfx_com_sparks_blaster)
      - [`VFX_COM_SPARKS_LARGE`](#vfx_com_sparks_large)
      - [`VFX_COM_SPARKS_LIGHTSABER`](#vfx_com_sparks_lightsaber)
      - [`VFX_COM_SPARKS_PARRY_METAL`](#vfx_com_sparks_parry_metal)
      - [`VFX_COM_WHIRLWIND_STRIKE_SABER`](#vfx_com_whirlwind_strike_saber)
      - [`VFX_COM_WHIRLWIND_STRIKE_STAFF`](#vfx_com_whirlwind_strike_staff)
      - [`VFX_DUR_BODY_FUAL`](#vfx_dur_body_fual)
      - [`VFX_DUR_CARBONITE_CHUNKS`](#vfx_dur_carbonite_chunks)
      - [`VFX_DUR_CARBONITE_ENCASING`](#vfx_dur_carbonite_encasing)
      - [`VFX_DUR_FORCE_WHIRLWIND`](#vfx_dur_force_whirlwind)
      - [`VFX_DUR_HOLD`](#vfx_dur_hold)
      - [`VFX_DUR_INVISIBILITY`](#vfx_dur_invisibility)
      - [`VFX_DUR_KNIGHTS_SPEED`](#vfx_dur_knights_speed)
      - [`VFX_DUR_PSYCHIC_STATIC`](#vfx_dur_psychic_static)
      - [`VFX_DUR_SHIELD_BLUE_01`](#vfx_dur_shield_blue_01)
      - [`VFX_DUR_SHIELD_BLUE_02`](#vfx_dur_shield_blue_02)
      - [`VFX_DUR_SHIELD_BLUE_03`](#vfx_dur_shield_blue_03)
      - [`VFX_DUR_SHIELD_BLUE_04`](#vfx_dur_shield_blue_04)
      - [`VFX_DUR_SHIELD_BLUE_MARK_I`](#vfx_dur_shield_blue_mark_i)
      - [`VFX_DUR_SHIELD_BLUE_MARK_II`](#vfx_dur_shield_blue_mark_ii)
      - [`VFX_DUR_SHIELD_BLUE_MARK_IV`](#vfx_dur_shield_blue_mark_iv)
      - [`VFX_DUR_SHIELD_CHROME_01`](#vfx_dur_shield_chrome_01)
      - [`VFX_DUR_SHIELD_CHROME_02`](#vfx_dur_shield_chrome_02)
      - [`VFX_DUR_SHIELD_GREEN_01`](#vfx_dur_shield_green_01)
      - [`VFX_DUR_SHIELD_RED_01`](#vfx_dur_shield_red_01)
      - [`VFX_DUR_SHIELD_RED_02`](#vfx_dur_shield_red_02)
      - [`VFX_DUR_SHIELD_RED_MARK_I`](#vfx_dur_shield_red_mark_i)
      - [`VFX_DUR_SHIELD_RED_MARK_II`](#vfx_dur_shield_red_mark_ii)
      - [`VFX_DUR_SHIELD_RED_MARK_IV`](#vfx_dur_shield_red_mark_iv)
      - [`VFX_DUR_SPEED`](#vfx_dur_speed)
      - [`VFX_DUR_STEALTH_PULSE`](#vfx_dur_stealth_pulse)
      - [`VFX_FNF_FORCE_WAVE`](#vfx_fnf_force_wave)
      - [`VFX_FNF_GRAVITY_GENERATOR`](#vfx_fnf_gravity_generator)
      - [`VFX_FNF_GRENADE_ADHESIVE`](#vfx_fnf_grenade_adhesive)
      - [`VFX_FNF_GRENADE_CRYOBAN`](#vfx_fnf_grenade_cryoban)
      - [`VFX_FNF_GRENADE_FRAGMENTATION`](#vfx_fnf_grenade_fragmentation)
      - [`VFX_FNF_GRENADE_ION`](#vfx_fnf_grenade_ion)
      - [`VFX_FNF_GRENADE_PLASMA`](#vfx_fnf_grenade_plasma)
      - [`VFX_FNF_GRENADE_POISON`](#vfx_fnf_grenade_poison)
      - [`VFX_FNF_GRENADE_SONIC`](#vfx_fnf_grenade_sonic)
      - [`VFX_FNF_GRENADE_STUN`](#vfx_fnf_grenade_stun)
      - [`VFX_FNF_GRENADE_THERMAL_DETONATOR`](#vfx_fnf_grenade_thermal_detonator)
      - [`VFX_FNF_PLOT_MAN_SONIC_WAVE`](#vfx_fnf_plot_man_sonic_wave)
      - [`VFX_IMP_CHOKE`](#vfx_imp_choke)
      - [`VFX_IMP_CURE`](#vfx_imp_cure)
      - [`VFX_IMP_FLAME`](#vfx_imp_flame)
      - [`VFX_IMP_FORCE_BREACH`](#vfx_imp_force_breach)
      - [`VFX_IMP_FORCE_JUMP_ADVANCED`](#vfx_imp_force_jump_advanced)
      - [`VFX_IMP_FORCE_PUSH`](#vfx_imp_force_push)
      - [`VFX_IMP_FORCE_WAVE`](#vfx_imp_force_wave)
      - [`VFX_IMP_FORCE_WHIRLWIND`](#vfx_imp_force_whirlwind)
      - [`VFX_IMP_GRENADE_ADHESIVE_PERSONAL`](#vfx_imp_grenade_adhesive_personal)
      - [`VFX_IMP_HEAL`](#vfx_imp_heal)
      - [`VFX_IMP_HEALING_SMALL`](#vfx_imp_healing_small)
      - [`VFX_IMP_MIND_FORCE`](#vfx_imp_mind_force)
      - [`VFX_IMP_MIND_KINIGHT`](#vfx_imp_mind_kinight)
      - [`VFX_IMP_MIND_MASTERY`](#vfx_imp_mind_mastery)
      - [`VFX_IMP_MIRV`](#vfx_imp_mirv)
      - [`VFX_IMP_MIRV_IMPACT`](#vfx_imp_mirv_impact)
      - [`VFX_IMP_SCREEN_SHAKE`](#vfx_imp_screen_shake)
      - [`VFX_IMP_SPEED_KNIGHT`](#vfx_imp_speed_knight)
      - [`VFX_IMP_SPEED_MASTERY`](#vfx_imp_speed_mastery)
      - [`VFX_IMP_STUN`](#vfx_imp_stun)
      - [`VFX_IMP_SUPPRESS_FORCE`](#vfx_imp_suppress_force)
      - [`VFX_NONE`](#vfx_none)
      - [`VFX_PRO_AFFLICT`](#vfx_pro_afflict)
      - [`VFX_PRO_DEATH_FIELD`](#vfx_pro_death_field)
      - [`VFX_PRO_DRAIN`](#vfx_pro_drain)
      - [`VFX_PRO_DROID_DISABLE`](#vfx_pro_droid_disable)
      - [`VFX_PRO_DROID_KILL`](#vfx_pro_droid_kill)
      - [`VFX_PRO_FORCE_ARMOR`](#vfx_pro_force_armor)
      - [`VFX_PRO_FORCE_AURA`](#vfx_pro_force_aura)
      - [`VFX_PRO_FORCE_SHIELD`](#vfx_pro_force_shield)
      - [`VFX_PRO_LIGHTNING_JEDI`](#vfx_pro_lightning_jedi)
      - [`VFX_PRO_LIGHTNING_L`](#vfx_pro_lightning_l)
      - [`VFX_PRO_LIGHTNING_L_SOUND`](#vfx_pro_lightning_l_sound)
      - [`VFX_PRO_LIGHTNING_S`](#vfx_pro_lightning_s)
      - [`VFX_PRO_RESIST_ELEMENTS`](#vfx_pro_resist_elements)
      - [`VFX_PRO_RESIST_FORCE`](#vfx_pro_resist_force)
      - [`VFX_PRO_RESIST_POISON`](#vfx_pro_resist_poison)
  - [K1-Only Constants](#k1-only-constants)
    - [NPC Constants](#npc-constants-1)
      - [`NPC_BASTILA`](#npc_bastila)
      - [`NPC_CARTH`](#npc_carth)
      - [`NPC_JOLEE`](#npc_jolee)
      - [`NPC_JUHANI`](#npc_juhani)
      - [`NPC_MISSION`](#npc_mission)
      - [`NPC_ZAALBAR`](#npc_zaalbar)
    - [Other Constants](#other-constants-1)
      - [`TUTORIAL_WINDOW_MOVEMENT_KEYS`](#tutorial_window_movement_keys)
    - [Planet Constants](#planet-constants-1)
      - [`PLANET_ENDAR_SPIRE`](#planet_endar_spire)
      - [`PLANET_KASHYYYK`](#planet_kashyyyk)
      - [`PLANET_LEVIATHAN`](#planet_leviathan)
      - [`PLANET_MANAAN`](#planet_manaan)
      - [`PLANET_STAR_FORGE`](#planet_star_forge)
      - [`PLANET_TARIS`](#planet_taris)
      - [`PLANET_TATOOINE`](#planet_tatooine)
      - [`PLANET_UNKNOWN_WORLD`](#planet_unknown_world)
  - [TSL-Only Constants](#tsl-only-constants)
    - [Class Type Constants](#class-type-constants-1)
      - [`CLASS_TYPE_BOUNTYHUNTER`](#class_type_bountyhunter)
      - [`CLASS_TYPE_JEDIMASTER`](#class_type_jedimaster)
      - [`CLASS_TYPE_JEDIWATCHMAN`](#class_type_jediwatchman)
      - [`CLASS_TYPE_JEDIWEAPONMASTER`](#class_type_jediweaponmaster)
      - [`CLASS_TYPE_SITHASSASSIN`](#class_type_sithassassin)
      - [`CLASS_TYPE_SITHLORD`](#class_type_sithlord)
      - [`CLASS_TYPE_SITHMARAUDER`](#class_type_sithmarauder)
      - [`CLASS_TYPE_TECHSPECIALIST`](#class_type_techspecialist)
    - [Inventory Constants](#inventory-constants-1)
      - [`INVENTORY_SLOT_LEFTWEAPON2`](#inventory_slot_leftweapon2)
      - [`INVENTORY_SLOT_RIGHTWEAPON2`](#inventory_slot_rightweapon2)
    - [NPC Constants](#npc-constants-2)
      - [`NPC_AISTYLE_HEALER`](#npc_aistyle_healer)
      - [`NPC_AISTYLE_MONSTER_POWERS`](#npc_aistyle_monster_powers)
      - [`NPC_AISTYLE_PARTY_AGGRO`](#npc_aistyle_party_aggro)
      - [`NPC_AISTYLE_PARTY_DEFENSE`](#npc_aistyle_party_defense)
      - [`NPC_AISTYLE_PARTY_RANGED`](#npc_aistyle_party_ranged)
      - [`NPC_AISTYLE_PARTY_REMOTE`](#npc_aistyle_party_remote)
      - [`NPC_AISTYLE_PARTY_STATIONARY`](#npc_aistyle_party_stationary)
      - [`NPC_AISTYLE_PARTY_SUPPORT`](#npc_aistyle_party_support)
      - [`NPC_AISTYLE_SKIRMISH`](#npc_aistyle_skirmish)
      - [`NPC_AISTYLE_TURTLE`](#npc_aistyle_turtle)
      - [`NPC_ATTON`](#npc_atton)
      - [`NPC_BAO_DUR`](#npc_bao_dur)
      - [`NPC_DISCIPLE`](#npc_disciple)
      - [`NPC_G0T0`](#npc_g0t0)
      - [`NPC_HANDMAIDEN`](#npc_handmaiden)
      - [`NPC_HANHARR`](#npc_hanharr)
      - [`NPC_KREIA`](#npc_kreia)
      - [`NPC_MIRA`](#npc_mira)
      - [`NPC_VISAS`](#npc_visas)
    - [Other Constants](#other-constants-2)
      - [`ACTION_FOLLOWOWNER`](#action_followowner)
      - [`AI_LEVEL_HIGH`](#ai_level_high)
      - [`AI_LEVEL_LOW`](#ai_level_low)
      - [`AI_LEVEL_NORMAL`](#ai_level_normal)
      - [`AI_LEVEL_VERY_HIGH`](#ai_level_very_high)
      - [`AI_LEVEL_VERY_LOW`](#ai_level_very_low)
      - [`ANIMATION_FIREFORGET_DIVE_ROLL`](#animation_fireforget_dive_roll)
      - [`ANIMATION_FIREFORGET_FORCE_CAST`](#animation_fireforget_force_cast)
      - [`ANIMATION_FIREFORGET_OPEN`](#animation_fireforget_open)
      - [`ANIMATION_FIREFORGET_SCREAM`](#animation_fireforget_scream)
      - [`ANIMATION_LOOPING_CHECK_BODY`](#animation_looping_check_body)
      - [`ANIMATION_LOOPING_CHOKE_WORKING`](#animation_looping_choke_working)
      - [`ANIMATION_LOOPING_CLOSED`](#animation_looping_closed)
      - [`ANIMATION_LOOPING_MEDITATE_STAND`](#animation_looping_meditate_stand)
      - [`ANIMATION_LOOPING_RAGE`](#animation_looping_rage)
      - [`ANIMATION_LOOPING_SIT_AND_MEDITATE`](#animation_looping_sit_and_meditate)
      - [`ANIMATION_LOOPING_SIT_CHAIR`](#animation_looping_sit_chair)
      - [`ANIMATION_LOOPING_SIT_CHAIR_COMP1`](#animation_looping_sit_chair_comp1)
      - [`ANIMATION_LOOPING_SIT_CHAIR_COMP2`](#animation_looping_sit_chair_comp2)
      - [`ANIMATION_LOOPING_SIT_CHAIR_DRINK`](#animation_looping_sit_chair_drink)
      - [`ANIMATION_LOOPING_SIT_CHAIR_PAZAK`](#animation_looping_sit_chair_pazak)
      - [`ANIMATION_LOOPING_STEALTH`](#animation_looping_stealth)
      - [`ANIMATION_LOOPING_UNLOCK_DOOR`](#animation_looping_unlock_door)
      - [`BASE_ITEM_FORCE_PIKE`](#base_item_force_pike)
      - [`BASE_ITEM_WRIST_LAUNCHER`](#base_item_wrist_launcher)
      - [`EFFECT_TYPE_DROID_CONFUSED`](#effect_type_droid_confused)
      - [`EFFECT_TYPE_DROIDSCRAMBLE`](#effect_type_droidscramble)
      - [`EFFECT_TYPE_MINDTRICK`](#effect_type_mindtrick)
      - [`FEAT_CLASS_SKILL_AWARENESS`](#feat_class_skill_awareness)
      - [`FEAT_CLASS_SKILL_COMPUTER_USE`](#feat_class_skill_computer_use)
      - [`FEAT_CLASS_SKILL_DEMOLITIONS`](#feat_class_skill_demolitions)
      - [`FEAT_CLASS_SKILL_REPAIR`](#feat_class_skill_repair)
      - [`FEAT_CLASS_SKILL_SECURITY`](#feat_class_skill_security)
      - [`FEAT_CLASS_SKILL_STEALTH`](#feat_class_skill_stealth)
      - [`FEAT_CLASS_SKILL_TREAT_INJURY`](#feat_class_skill_treat_injury)
      - [`FEAT_CLOSE_COMBAT`](#feat_close_combat)
      - [`FEAT_CRAFT`](#feat_craft)
      - [`FEAT_DARK_SIDE_CORRUPTION`](#feat_dark_side_corruption)
      - [`FEAT_DEFLECT`](#feat_deflect)
      - [`FEAT_DROID_INTERFACE`](#feat_droid_interface)
      - [`FEAT_DUAL_STRIKE`](#feat_dual_strike)
      - [`FEAT_EVASION`](#feat_evasion)
      - [`FEAT_FIGHTING_SPIRIT`](#feat_fighting_spirit)
      - [`FEAT_FINESSE_LIGHTSABERS`](#feat_finesse_lightsabers)
      - [`FEAT_FINESSE_MELEE_WEAPONS`](#feat_finesse_melee_weapons)
      - [`FEAT_FORCE_CHAIN`](#feat_force_chain)
      - [`FEAT_HEROIC_RESOLVE`](#feat_heroic_resolve)
      - [`FEAT_IGNORE_PAIN_1`](#feat_ignore_pain_1)
      - [`FEAT_IGNORE_PAIN_2`](#feat_ignore_pain_2)
      - [`FEAT_IGNORE_PAIN_3`](#feat_ignore_pain_3)
      - [`FEAT_IMPLANT_SWITCHING`](#feat_implant_switching)
      - [`FEAT_IMPROVED_CLOSE_COMBAT`](#feat_improved_close_combat)
      - [`FEAT_IMPROVED_DUAL_STRIKE`](#feat_improved_dual_strike)
      - [`FEAT_IMPROVED_FORCE_CAMOUFLAGE`](#feat_improved_force_camouflage)
      - [`FEAT_IMPROVED_PRECISE_SHOT`](#feat_improved_precise_shot)
      - [`FEAT_INCREASE_COMBAT_DAMAGE_1`](#feat_increase_combat_damage_1)
      - [`FEAT_INCREASE_COMBAT_DAMAGE_2`](#feat_increase_combat_damage_2)
      - [`FEAT_INCREASE_COMBAT_DAMAGE_3`](#feat_increase_combat_damage_3)
      - [`FEAT_INCREASE_MELEE_DAMAGE_1`](#feat_increase_melee_damage_1)
      - [`FEAT_INCREASE_MELEE_DAMAGE_2`](#feat_increase_melee_damage_2)
      - [`FEAT_INCREASE_MELEE_DAMAGE_3`](#feat_increase_melee_damage_3)
      - [`FEAT_INNER_STRENGTH_1`](#feat_inner_strength_1)
      - [`FEAT_INNER_STRENGTH_2`](#feat_inner_strength_2)
      - [`FEAT_INNER_STRENGTH_3`](#feat_inner_strength_3)
      - [`FEAT_KINETIC_COMBAT`](#feat_kinetic_combat)
      - [`FEAT_LIGHT_SIDE_ENLIGHTENMENT`](#feat_light_side_enlightenment)
      - [`FEAT_MANDALORIAN_COURAGE`](#feat_mandalorian_courage)
      - [`FEAT_MASTER_DUAL_STRIKE`](#feat_master_dual_strike)
      - [`FEAT_MASTER_FORCE_CAMOUFLAGE`](#feat_master_force_camouflage)
      - [`FEAT_MASTER_PRECISE_SHOT`](#feat_master_precise_shot)
      - [`FEAT_MASTERCRAFT_ARMOR_1`](#feat_mastercraft_armor_1)
      - [`FEAT_MASTERCRAFT_ARMOR_2`](#feat_mastercraft_armor_2)
      - [`FEAT_MASTERCRAFT_ARMOR_3`](#feat_mastercraft_armor_3)
      - [`FEAT_MASTERCRAFT_WEAPONS_1`](#feat_mastercraft_weapons_1)
      - [`FEAT_MASTERCRAFT_WEAPONS_2`](#feat_mastercraft_weapons_2)
      - [`FEAT_MASTERCRAFT_WEAPONS_3`](#feat_mastercraft_weapons_3)
      - [`FEAT_MENTOR`](#feat_mentor)
      - [`FEAT_MOBILITY`](#feat_mobility)
      - [`FEAT_PERSONAL_CLOAKING_SHIELD`](#feat_personal_cloaking_shield)
      - [`FEAT_PRECISE_SHOT`](#feat_precise_shot)
      - [`FEAT_PRECISE_SHOT_IV`](#feat_precise_shot_iv)
      - [`FEAT_PRECISE_SHOT_V`](#feat_precise_shot_v)
      - [`FEAT_REGENERATE_FORCE_POINTS`](#feat_regenerate_force_points)
      - [`FEAT_REGENERATE_VITALITY_POINTS`](#feat_regenerate_vitality_points)
      - [`FEAT_SPIRIT`](#feat_spirit)
      - [`FEAT_STEALTH_RUN`](#feat_stealth_run)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_1`](#feat_superior_weapon_focus_lightsaber_1)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_2`](#feat_superior_weapon_focus_lightsaber_2)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_LIGHTSABER_3`](#feat_superior_weapon_focus_lightsaber_3)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_1`](#feat_superior_weapon_focus_two_weapon_1)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_2`](#feat_superior_weapon_focus_two_weapon_2)
      - [`FEAT_SUPERIOR_WEAPON_FOCUS_TWO_WEAPON_3`](#feat_superior_weapon_focus_two_weapon_3)
      - [`FEAT_SURVIVAL`](#feat_survival)
      - [`FEAT_TARGETING_1`](#feat_targeting_1)
      - [`FEAT_TARGETING_10`](#feat_targeting_10)
      - [`FEAT_TARGETING_2`](#feat_targeting_2)
      - [`FEAT_TARGETING_3`](#feat_targeting_3)
      - [`FEAT_TARGETING_4`](#feat_targeting_4)
      - [`FEAT_TARGETING_5`](#feat_targeting_5)
      - [`FEAT_TARGETING_6`](#feat_targeting_6)
      - [`FEAT_TARGETING_7`](#feat_targeting_7)
      - [`FEAT_TARGETING_8`](#feat_targeting_8)
      - [`FEAT_TARGETING_9`](#feat_targeting_9)
      - [`FEAT_WAR_VETERAN`](#feat_war_veteran)
      - [`FORCE_POWER_BAT_MED_ENEMY`](#force_power_bat_med_enemy)
      - [`FORCE_POWER_BATTLE_MEDITATION_PC`](#force_power_battle_meditation_pc)
      - [`FORCE_POWER_BATTLE_PRECOGNITION`](#force_power_battle_precognition)
      - [`FORCE_POWER_BEAST_CONFUSION`](#force_power_beast_confusion)
      - [`FORCE_POWER_BEAST_TRICK`](#force_power_beast_trick)
      - [`FORCE_POWER_BREATH_CONTROL`](#force_power_breath_control)
      - [`FORCE_POWER_CONFUSION`](#force_power_confusion)
      - [`FORCE_POWER_CRUSH_OPPOSITION_I`](#force_power_crush_opposition_i)
      - [`FORCE_POWER_CRUSH_OPPOSITION_II`](#force_power_crush_opposition_ii)
      - [`FORCE_POWER_CRUSH_OPPOSITION_III`](#force_power_crush_opposition_iii)
      - [`FORCE_POWER_CRUSH_OPPOSITION_IV`](#force_power_crush_opposition_iv)
      - [`FORCE_POWER_CRUSH_OPPOSITION_V`](#force_power_crush_opposition_v)
      - [`FORCE_POWER_CRUSH_OPPOSITION_VI`](#force_power_crush_opposition_vi)
      - [`FORCE_POWER_DRAIN_FORCE`](#force_power_drain_force)
      - [`FORCE_POWER_DROID_CONFUSION`](#force_power_droid_confusion)
      - [`FORCE_POWER_DROID_TRICK`](#force_power_droid_trick)
      - [`FORCE_POWER_FORCE_BARRIER`](#force_power_force_barrier)
      - [`FORCE_POWER_FORCE_BODY`](#force_power_force_body)
      - [`FORCE_POWER_FORCE_CAMOUFLAGE`](#force_power_force_camouflage)
      - [`FORCE_POWER_FORCE_CRUSH`](#force_power_force_crush)
      - [`FORCE_POWER_FORCE_ENLIGHTENMENT`](#force_power_force_enlightenment)
      - [`FORCE_POWER_FORCE_REDIRECTION`](#force_power_force_redirection)
      - [`FORCE_POWER_FORCE_REPULSION`](#force_power_force_repulsion)
      - [`FORCE_POWER_FORCE_SCREAM`](#force_power_force_scream)
      - [`FORCE_POWER_FORCE_SIGHT`](#force_power_force_sight)
      - [`FORCE_POWER_FURY`](#force_power_fury)
      - [`FORCE_POWER_IMP_BAT_MED_ENEMY`](#force_power_imp_bat_med_enemy)
      - [`FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC`](#force_power_improved_battle_meditation_pc)
      - [`FORCE_POWER_IMPROVED_DRAIN_FORCE`](#force_power_improved_drain_force)
      - [`FORCE_POWER_IMPROVED_FORCE_BARRIER`](#force_power_improved_force_barrier)
      - [`FORCE_POWER_IMPROVED_FORCE_BODY`](#force_power_improved_force_body)
      - [`FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE`](#force_power_improved_force_camouflage)
      - [`FORCE_POWER_IMPROVED_FORCE_SCREAM`](#force_power_improved_force_scream)
      - [`FORCE_POWER_IMPROVED_FURY`](#force_power_improved_fury)
      - [`FORCE_POWER_IMPROVED_REVITALIZE`](#force_power_improved_revitalize)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_I`](#force_power_inspire_followers_i)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_II`](#force_power_inspire_followers_ii)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_III`](#force_power_inspire_followers_iii)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_IV`](#force_power_inspire_followers_iv)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_V`](#force_power_inspire_followers_v)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_VI`](#force_power_inspire_followers_vi)
      - [`FORCE_POWER_MAS_BAT_MED_ENEMY`](#force_power_mas_bat_med_enemy)
      - [`FORCE_POWER_MASTER_BATTLE_MEDITATION_PC`](#force_power_master_battle_meditation_pc)
      - [`FORCE_POWER_MASTER_DRAIN_FORCE`](#force_power_master_drain_force)
      - [`FORCE_POWER_MASTER_ENERGY_RESISTANCE`](#force_power_master_energy_resistance)
      - [`FORCE_POWER_MASTER_FORCE_BARRIER`](#force_power_master_force_barrier)
      - [`FORCE_POWER_MASTER_FORCE_BODY`](#force_power_master_force_body)
      - [`FORCE_POWER_MASTER_FORCE_CAMOUFLAGE`](#force_power_master_force_camouflage)
      - [`FORCE_POWER_MASTER_FORCE_SCREAM`](#force_power_master_force_scream)
      - [`FORCE_POWER_MASTER_FURY`](#force_power_master_fury)
      - [`FORCE_POWER_MASTER_HEAL`](#force_power_master_heal)
      - [`FORCE_POWER_MASTER_REVITALIZE`](#force_power_master_revitalize)
      - [`FORCE_POWER_MIND_TRICK`](#force_power_mind_trick)
      - [`FORCE_POWER_PRECOGNITION`](#force_power_precognition)
      - [`FORCE_POWER_REVITALIZE`](#force_power_revitalize)
      - [`FORCE_POWER_WOOKIEE_RAGE_I`](#force_power_wookiee_rage_i)
      - [`FORCE_POWER_WOOKIEE_RAGE_II`](#force_power_wookiee_rage_ii)
      - [`FORCE_POWER_WOOKIEE_RAGE_III`](#force_power_wookiee_rage_iii)
      - [`FORFEIT_DXUN_SWORD_ONLY`](#forfeit_dxun_sword_only)
      - [`FORFEIT_NO_ARMOR`](#forfeit_no_armor)
      - [`FORFEIT_NO_FORCE_POWERS`](#forfeit_no_force_powers)
      - [`FORFEIT_NO_ITEM_BUT_SHIELD`](#forfeit_no_item_but_shield)
      - [`FORFEIT_NO_ITEMS`](#forfeit_no_items)
      - [`FORFEIT_NO_LIGHTSABER`](#forfeit_no_lightsaber)
      - [`FORFEIT_NO_RANGED`](#forfeit_no_ranged)
      - [`FORFEIT_NO_WEAPONS`](#forfeit_no_weapons)
      - [`FORM_FORCE_I_FOCUS`](#form_force_i_focus)
      - [`FORM_FORCE_II_POTENCY`](#form_force_ii_potency)
      - [`FORM_FORCE_III_AFFINITY`](#form_force_iii_affinity)
      - [`FORM_FORCE_IV_MASTERY`](#form_force_iv_mastery)
      - [`FORM_SABER_I_SHII_CHO`](#form_saber_i_shii_cho)
      - [`FORM_SABER_II_MAKASHI`](#form_saber_ii_makashi)
      - [`FORM_SABER_III_SORESU`](#form_saber_iii_soresu)
      - [`FORM_SABER_IV_ATARU`](#form_saber_iv_ataru)
      - [`FORM_SABER_V_SHIEN`](#form_saber_v_shien)
      - [`FORM_SABER_VI_NIMAN`](#form_saber_vi_niman)
      - [`FORM_SABER_VII_JUYO`](#form_saber_vii_juyo)
      - [`IMMUNITY_TYPE_DROID_CONFUSED`](#immunity_type_droid_confused)
      - [`IMPLANT_AGI`](#implant_agi)
      - [`IMPLANT_END`](#implant_end)
      - [`IMPLANT_NONE`](#implant_none)
      - [`IMPLANT_REGEN`](#implant_regen)
      - [`IMPLANT_STR`](#implant_str)
      - [`ITEM_PROPERTY_DAMPEN_SOUND`](#item_property_dampen_sound)
      - [`ITEM_PROPERTY_DISGUISE`](#item_property_disguise)
      - [`ITEM_PROPERTY_DOORCUTTING`](#item_property_doorcutting)
      - [`ITEM_PROPERTY_DOORSABERING`](#item_property_doorsabering)
      - [`ITEM_PROPERTY_LIMIT_USE_BY_GENDER`](#item_property_limit_use_by_gender)
      - [`ITEM_PROPERTY_LIMIT_USE_BY_PC`](#item_property_limit_use_by_pc)
      - [`ITEM_PROPERTY_LIMIT_USE_BY_SUBRACE`](#item_property_limit_use_by_subrace)
      - [`POISON_ABILITY_AND_DAMAGE_AVERAGE`](#poison_ability_and_damage_average)
      - [`POISON_ABILITY_AND_DAMAGE_VIRULENT`](#poison_ability_and_damage_virulent)
      - [`POISON_DAMAGE_KYBER_DART`](#poison_damage_kyber_dart)
      - [`POISON_DAMAGE_KYBER_DART_HALF`](#poison_damage_kyber_dart_half)
      - [`POISON_DAMAGE_NORMAL_DART`](#poison_damage_normal_dart)
      - [`POISON_DAMAGE_ROCKET`](#poison_damage_rocket)
      - [`PUP_OTHER1`](#pup_other1)
      - [`PUP_OTHER2`](#pup_other2)
      - [`PUP_SENSORBALL`](#pup_sensorball)
      - [`SHIELD_DREXL`](#shield_drexl)
      - [`SHIELD_HEAT`](#shield_heat)
      - [`SHIELD_PLOT_MAN_M28AA`](#shield_plot_man_m28aa)
      - [`STANDARD_FACTION_ONE_ON_ONE`](#standard_faction_one_on_one)
      - [`STANDARD_FACTION_PARTYPUPPET`](#standard_faction_partypuppet)
      - [`STANDARD_FACTION_SELF_LOATHING`](#standard_faction_self_loathing)
      - [`TRAP_BASE_TYPE_FLASH_STUN_DEVASTATING`](#trap_base_type_flash_stun_devastating)
      - [`TRAP_BASE_TYPE_FLASH_STUN_STRONG`](#trap_base_type_flash_stun_strong)
      - [`TRAP_BASE_TYPE_FRAGMENTATION_MINE_DEVASTATING`](#trap_base_type_fragmentation_mine_devastating)
      - [`TRAP_BASE_TYPE_FRAGMENTATION_MINE_STRONG`](#trap_base_type_fragmentation_mine_strong)
      - [`TRAP_BASE_TYPE_LASER_SLICING_DEVASTATING`](#trap_base_type_laser_slicing_devastating)
      - [`TRAP_BASE_TYPE_LASER_SLICING_STRONG`](#trap_base_type_laser_slicing_strong)
      - [`TRAP_BASE_TYPE_POISON_GAS_DEVASTATING`](#trap_base_type_poison_gas_devastating)
      - [`TRAP_BASE_TYPE_POISON_GAS_STRONG`](#trap_base_type_poison_gas_strong)
      - [`TRAP_BASE_TYPE_SONIC_CHARGE_AVERAGE`](#trap_base_type_sonic_charge_average)
      - [`TRAP_BASE_TYPE_SONIC_CHARGE_DEADLY`](#trap_base_type_sonic_charge_deadly)
      - [`TRAP_BASE_TYPE_SONIC_CHARGE_DEVASTATING`](#trap_base_type_sonic_charge_devastating)
      - [`TRAP_BASE_TYPE_SONIC_CHARGE_MINOR`](#trap_base_type_sonic_charge_minor)
      - [`TRAP_BASE_TYPE_SONIC_CHARGE_STRONG`](#trap_base_type_sonic_charge_strong)
      - [`TUTORIAL_WINDOW_TEMP1`](#tutorial_window_temp1)
      - [`TUTORIAL_WINDOW_TEMP10`](#tutorial_window_temp10)
      - [`TUTORIAL_WINDOW_TEMP11`](#tutorial_window_temp11)
      - [`TUTORIAL_WINDOW_TEMP12`](#tutorial_window_temp12)
      - [`TUTORIAL_WINDOW_TEMP13`](#tutorial_window_temp13)
      - [`TUTORIAL_WINDOW_TEMP14`](#tutorial_window_temp14)
      - [`TUTORIAL_WINDOW_TEMP15`](#tutorial_window_temp15)
      - [`TUTORIAL_WINDOW_TEMP2`](#tutorial_window_temp2)
      - [`TUTORIAL_WINDOW_TEMP3`](#tutorial_window_temp3)
      - [`TUTORIAL_WINDOW_TEMP4`](#tutorial_window_temp4)
      - [`TUTORIAL_WINDOW_TEMP5`](#tutorial_window_temp5)
      - [`TUTORIAL_WINDOW_TEMP6`](#tutorial_window_temp6)
      - [`TUTORIAL_WINDOW_TEMP7`](#tutorial_window_temp7)
      - [`TUTORIAL_WINDOW_TEMP8`](#tutorial_window_temp8)
      - [`TUTORIAL_WINDOW_TEMP9`](#tutorial_window_temp9)
      - [`VIDEO_EFFECT_CLAIRVOYANCE`](#video_effect_clairvoyance)
      - [`VIDEO_EFFECT_CLAIRVOYANCEFULL`](#video_effect_clairvoyancefull)
      - [`VIDEO_EFFECT_FORCESIGHT`](#video_effect_forcesight)
      - [`VIDEO_EFFECT_FURY_1`](#video_effect_fury_1)
      - [`VIDEO_EFFECT_FURY_2`](#video_effect_fury_2)
      - [`VIDEO_EFFECT_FURY_3`](#video_effect_fury_3)
      - [`VIDEO_EFFECT_VISAS_FREELOOK`](#video_effect_visas_freelook)
      - [`VIDEO_FFECT_SECURITY_NO_LABEL`](#video_ffect_security_no_label)
    - [Planet Constants](#planet-constants-2)
      - [`PLANET_DXUN`](#planet_dxun)
      - [`PLANET_HARBINGER`](#planet_harbinger)
      - [`PLANET_LIVE_06`](#planet_live_06)
      - [`PLANET_M4_78`](#planet_m4_78)
      - [`PLANET_MALACHOR_V`](#planet_malachor_v)
      - [`PLANET_NAR_SHADDAA`](#planet_nar_shaddaa)
      - [`PLANET_ONDERON`](#planet_onderon)
      - [`PLANET_PERAGUS`](#planet_peragus)
      - [`PLANET_TELOS`](#planet_telos)
    - [Visual Effects (VFX)](#visual-effects-vfx-1)
      - [`VFX_DUR_ELECTRICAL_SPARK`](#vfx_dur_electrical_spark)
      - [`VFX_DUR_HOLO_PROJECT`](#vfx_dur_holo_project)
  - [KOTOR Library Files](#kotor-library-files)
    - [`k_inc_cheat`](#k_inc_cheat)
    - [`k_inc_dan`](#k_inc_dan)
    - [`k_inc_debug`](#k_inc_debug)
    - [`k_inc_drop`](#k_inc_drop)
    - [`k_inc_ebonhawk`](#k_inc_ebonhawk)
    - [`k_inc_end`](#k_inc_end)
    - [`k_inc_endgame`](#k_inc_endgame)
    - [`k_inc_force`](#k_inc_force)
    - [`k_inc_generic`](#k_inc_generic)
    - [`k_inc_gensupport`](#k_inc_gensupport)
    - [`k_inc_kas`](#k_inc_kas)
    - [`k_inc_lev`](#k_inc_lev)
    - [`k_inc_man`](#k_inc_man)
    - [`k_inc_stunt`](#k_inc_stunt)
    - [`k_inc_switch`](#k_inc_switch)
    - [`k_inc_tar`](#k_inc_tar)
    - [`k_inc_tat`](#k_inc_tat)
    - [`k_inc_treasure`](#k_inc_treasure)
    - [`k_inc_unk`](#k_inc_unk)
    - [`k_inc_utility`](#k_inc_utility)
    - [`k_inc_walkways`](#k_inc_walkways)
    - [`k_inc_zone`](#k_inc_zone)
  - [TSL Library Files](#tsl-library-files)
    - [`a_global_inc`](#a_global_inc)
    - [`a_influence_inc`](#a_influence_inc)
    - [`a_localn_inc`](#a_localn_inc)
    - [`k_inc_cheat`](#k_inc_cheat-1)
    - [`k_inc_debug`](#k_inc_debug-1)
    - [`k_inc_disguise`](#k_inc_disguise)
    - [`k_inc_drop`](#k_inc_drop-1)
    - [`k_inc_fab`](#k_inc_fab)
    - [`k_inc_fakecombat`](#k_inc_fakecombat)
    - [`k_inc_force`](#k_inc_force-1)
    - [`k_inc_generic`](#k_inc_generic-1)
    - [`k_inc_gensupport`](#k_inc_gensupport-1)
    - [`k_inc_glob_party`](#k_inc_glob_party)
    - [`k_inc_hawk`](#k_inc_hawk)
    - [`k_inc_item_gen`](#k_inc_item_gen)
    - [`k_inc_npckill`](#k_inc_npckill)
    - [`k_inc_q_crystal`](#k_inc_q_crystal)
    - [`k_inc_quest_hk`](#k_inc_quest_hk)
    - [`k_inc_switch`](#k_inc_switch-1)
    - [`k_inc_treas_k2`](#k_inc_treas_k2)
    - [`k_inc_treasure`](#k_inc_treasure-1)
    - [`k_inc_utility`](#k_inc_utility-1)
    - [`k_inc_walkways`](#k_inc_walkways-1)
    - [`k_inc_zone`](#k_inc_zone-1)
    - [`k_oei_hench_inc`](#k_oei_hench_inc)
  - [Compilation Process](#compilation-process)
    - [Attempts to Uncomment or Modify](#attempts-to-uncomment-or-modify)
    - [Commented-Out Elements in nwscript.nss](#commented-out-elements-in-nwscriptnss)
    - [Common Modder Workarounds](#common-modder-workarounds)
    - [Forum Discussions and Community Knowledge](#forum-discussions-and-community-knowledge)
    - [Key Citations](#key-citations)
    - [Key Examples of Commented Elements](#key-examples-of-commented-elements)
    - [Reasons for Commented-Out Elements](#reasons-for-commented-out-elements)
  - [Reference Implementations](#reference-implementations)
    - [Other Constants](#other-constants-3)
      - [`TRUE` **(K1 \& TSL)**](#true-k1--tsl)
      - [`FALSE` **(K1 \& TSL)**](#false-k1--tsl)
      - [`PI` **(K1 \& TSL)**](#pi-k1--tsl)
      - [`ATTITUDE_NEUTRAL` **(K1 \& TSL)**](#attitude_neutral-k1--tsl)
      - [`ATTITUDE_AGGRESSIVE` **(K1 \& TSL)**](#attitude_aggressive-k1--tsl)
      - [`ATTITUDE_DEFENSIVE` **(K1 \& TSL)**](#attitude_defensive-k1--tsl)
      - [`ATTITUDE_SPECIAL` **(K1 \& TSL)**](#attitude_special-k1--tsl)
      - [`RADIUS_SIZE_SMALL` **(K1 \& TSL)**](#radius_size_small-k1--tsl)
      - [`RADIUS_SIZE_MEDIUM` **(K1 \& TSL)**](#radius_size_medium-k1--tsl)
      - [`RADIUS_SIZE_LARGE` **(K1 \& TSL)**](#radius_size_large-k1--tsl)
      - [`RADIUS_SIZE_HUGE` **(K1 \& TSL)**](#radius_size_huge-k1--tsl)
      - [`RADIUS_SIZE_GARGANTUAN` **(K1 \& TSL)**](#radius_size_gargantuan-k1--tsl)
      - [`RADIUS_SIZE_COLOSSAL` **(K1 \& TSL)**](#radius_size_colossal-k1--tsl)
      - [`ATTACK_RESULT_INVALID` **(K1 \& TSL)**](#attack_result_invalid-k1--tsl)
      - [`ATTACK_RESULT_HIT_SUCCESSFUL` **(K1 \& TSL)**](#attack_result_hit_successful-k1--tsl)
      - [`ATTACK_RESULT_CRITICAL_HIT` **(K1 \& TSL)**](#attack_result_critical_hit-k1--tsl)
      - [`ATTACK_RESULT_AUTOMATIC_HIT` **(K1 \& TSL)**](#attack_result_automatic_hit-k1--tsl)
      - [`ATTACK_RESULT_MISS` **(K1 \& TSL)**](#attack_result_miss-k1--tsl)
      - [`ATTACK_RESULT_ATTACK_RESISTED` **(K1 \& TSL)**](#attack_result_attack_resisted-k1--tsl)
      - [`ATTACK_RESULT_ATTACK_FAILED` **(K1 \& TSL)**](#attack_result_attack_failed-k1--tsl)
      - [`ATTACK_RESULT_PARRIED` **(K1 \& TSL)**](#attack_result_parried-k1--tsl)
      - [`ATTACK_RESULT_DEFLECTED` **(K1 \& TSL)**](#attack_result_deflected-k1--tsl)
      - [`AOE_PER_FOGACID` **(K1 \& TSL)**](#aoe_per_fogacid-k1--tsl)
      - [`AOE_PER_FOGFIRE` **(K1 \& TSL)**](#aoe_per_fogfire-k1--tsl)
      - [`AOE_PER_FOGSTINK` **(K1 \& TSL)**](#aoe_per_fogstink-k1--tsl)
      - [`AOE_PER_FOGKILL` **(K1 \& TSL)**](#aoe_per_fogkill-k1--tsl)
      - [`AOE_PER_FOGMIND` **(K1 \& TSL)**](#aoe_per_fogmind-k1--tsl)
      - [`AOE_PER_WALLFIRE` **(K1 \& TSL)**](#aoe_per_wallfire-k1--tsl)
      - [`AOE_PER_WALLWIND` **(K1 \& TSL)**](#aoe_per_wallwind-k1--tsl)
      - [`AOE_PER_WALLBLADE` **(K1 \& TSL)**](#aoe_per_wallblade-k1--tsl)
      - [`AOE_PER_WEB` **(K1 \& TSL)**](#aoe_per_web-k1--tsl)
      - [`AOE_PER_ENTANGLE` **(K1 \& TSL)**](#aoe_per_entangle-k1--tsl)
      - [`AOE_PER_DARKNESS` **(K1 \& TSL)**](#aoe_per_darkness-k1--tsl)
      - [`AOE_MOB_CIRCEVIL` **(K1 \& TSL)**](#aoe_mob_circevil-k1--tsl)
      - [`AOE_MOB_CIRCGOOD` **(K1 \& TSL)**](#aoe_mob_circgood-k1--tsl)
      - [`AOE_MOB_CIRCLAW` **(K1 \& TSL)**](#aoe_mob_circlaw-k1--tsl)
      - [`AOE_MOB_CIRCCHAOS` **(K1 \& TSL)**](#aoe_mob_circchaos-k1--tsl)
      - [`AOE_MOB_FEAR` **(K1 \& TSL)**](#aoe_mob_fear-k1--tsl)
      - [`AOE_MOB_BLINDING` **(K1 \& TSL)**](#aoe_mob_blinding-k1--tsl)
      - [`AOE_MOB_UNEARTHLY` **(K1 \& TSL)**](#aoe_mob_unearthly-k1--tsl)
      - [`AOE_MOB_MENACE` **(K1 \& TSL)**](#aoe_mob_menace-k1--tsl)
      - [`AOE_MOB_UNNATURAL` **(K1 \& TSL)**](#aoe_mob_unnatural-k1--tsl)
      - [`AOE_MOB_STUN` **(K1 \& TSL)**](#aoe_mob_stun-k1--tsl)
      - [`AOE_MOB_PROTECTION` **(K1 \& TSL)**](#aoe_mob_protection-k1--tsl)
      - [`AOE_MOB_FIRE` **(K1 \& TSL)**](#aoe_mob_fire-k1--tsl)
      - [`AOE_MOB_FROST` **(K1 \& TSL)**](#aoe_mob_frost-k1--tsl)
      - [`AOE_MOB_ELECTRICAL` **(K1 \& TSL)**](#aoe_mob_electrical-k1--tsl)
      - [`AOE_PER_FOGGHOUL` **(K1 \& TSL)**](#aoe_per_fogghoul-k1--tsl)
      - [`AOE_MOB_TYRANT_FOG` **(K1 \& TSL)**](#aoe_mob_tyrant_fog-k1--tsl)
      - [`AOE_PER_STORM` **(K1 \& TSL)**](#aoe_per_storm-k1--tsl)
      - [`AOE_PER_INVIS_SPHERE` **(K1 \& TSL)**](#aoe_per_invis_sphere-k1--tsl)
      - [`AOE_MOB_SILENCE` **(K1 \& TSL)**](#aoe_mob_silence-k1--tsl)
      - [`AOE_PER_DELAY_BLAST_FIREBALL` **(K1 \& TSL)**](#aoe_per_delay_blast_fireball-k1--tsl)
      - [`AOE_PER_GREASE` **(K1 \& TSL)**](#aoe_per_grease-k1--tsl)
      - [`AOE_PER_CREEPING_DOOM` **(K1 \& TSL)**](#aoe_per_creeping_doom-k1--tsl)
      - [`AOE_PER_EVARDS_BLACK_TENTACLES` **(K1 \& TSL)**](#aoe_per_evards_black_tentacles-k1--tsl)
      - [`AOE_MOB_INVISIBILITY_PURGE` **(K1 \& TSL)**](#aoe_mob_invisibility_purge-k1--tsl)
      - [`AOE_MOB_DRAGON_FEAR` **(K1 \& TSL)**](#aoe_mob_dragon_fear-k1--tsl)
      - [`FORCE_POWER_ALL_FORCE_POWERS` **(K1 \& TSL)**](#force_power_all_force_powers-k1--tsl)
      - [`FORCE_POWER_MASTER_ALTER` **(K1 \& TSL)**](#force_power_master_alter-k1--tsl)
      - [`FORCE_POWER_MASTER_CONTROL` **(K1 \& TSL)**](#force_power_master_control-k1--tsl)
      - [`FORCE_POWER_MASTER_SENSE` **(K1 \& TSL)**](#force_power_master_sense-k1--tsl)
      - [`FORCE_POWER_FORCE_JUMP_ADVANCED` **(K1 \& TSL)**](#force_power_force_jump_advanced-k1--tsl)
      - [`FORCE_POWER_LIGHT_SABER_THROW_ADVANCED` **(K1 \& TSL)**](#force_power_light_saber_throw_advanced-k1--tsl)
      - [`FORCE_POWER_REGNERATION_ADVANCED` **(K1 \& TSL)**](#force_power_regneration_advanced-k1--tsl)
      - [`FORCE_POWER_AFFECT_MIND` **(K1 \& TSL)**](#force_power_affect_mind-k1--tsl)
      - [`FORCE_POWER_AFFLICTION` **(K1 \& TSL)**](#force_power_affliction-k1--tsl)
      - [`FORCE_POWER_SPEED_BURST` **(K1 \& TSL)**](#force_power_speed_burst-k1--tsl)
      - [`FORCE_POWER_CHOKE` **(K1 \& TSL)**](#force_power_choke-k1--tsl)
      - [`FORCE_POWER_CURE` **(K1 \& TSL)**](#force_power_cure-k1--tsl)
      - [`FORCE_POWER_DEATH_FIELD` **(K1 \& TSL)**](#force_power_death_field-k1--tsl)
      - [`FORCE_POWER_DROID_DISABLE` **(K1 \& TSL)**](#force_power_droid_disable-k1--tsl)
      - [`FORCE_POWER_DROID_DESTROY` **(K1 \& TSL)**](#force_power_droid_destroy-k1--tsl)
      - [`FORCE_POWER_DOMINATE` **(K1 \& TSL)**](#force_power_dominate-k1--tsl)
      - [`FORCE_POWER_DRAIN_LIFE` **(K1 \& TSL)**](#force_power_drain_life-k1--tsl)
      - [`FORCE_POWER_FEAR` **(K1 \& TSL)**](#force_power_fear-k1--tsl)
      - [`FORCE_POWER_FORCE_ARMOR` **(K1 \& TSL)**](#force_power_force_armor-k1--tsl)
      - [`FORCE_POWER_FORCE_AURA` **(K1 \& TSL)**](#force_power_force_aura-k1--tsl)
      - [`FORCE_POWER_FORCE_BREACH` **(K1 \& TSL)**](#force_power_force_breach-k1--tsl)
      - [`FORCE_POWER_FORCE_IMMUNITY` **(K1 \& TSL)**](#force_power_force_immunity-k1--tsl)
      - [`FORCE_POWER_FORCE_JUMP` **(K1 \& TSL)**](#force_power_force_jump-k1--tsl)
      - [`FORCE_POWER_FORCE_MIND` **(K1 \& TSL)**](#force_power_force_mind-k1--tsl)
      - [`FORCE_POWER_FORCE_PUSH` **(K1 \& TSL)**](#force_power_force_push-k1--tsl)
      - [`FORCE_POWER_FORCE_SHIELD` **(K1 \& TSL)**](#force_power_force_shield-k1--tsl)
      - [`FORCE_POWER_FORCE_STORM` **(K1 \& TSL)**](#force_power_force_storm-k1--tsl)
      - [`FORCE_POWER_FORCE_WAVE` **(K1 \& TSL)**](#force_power_force_wave-k1--tsl)
      - [`FORCE_POWER_FORCE_WHIRLWIND` **(K1 \& TSL)**](#force_power_force_whirlwind-k1--tsl)
      - [`FORCE_POWER_HEAL` **(K1 \& TSL)**](#force_power_heal-k1--tsl)
      - [`FORCE_POWER_HOLD` **(K1 \& TSL)**](#force_power_hold-k1--tsl)
      - [`FORCE_POWER_HORROR` **(K1 \& TSL)**](#force_power_horror-k1--tsl)
      - [`FORCE_POWER_INSANITY` **(K1 \& TSL)**](#force_power_insanity-k1--tsl)
      - [`FORCE_POWER_KILL` **(K1 \& TSL)**](#force_power_kill-k1--tsl)
      - [`FORCE_POWER_KNIGHT_MIND` **(K1 \& TSL)**](#force_power_knight_mind-k1--tsl)
      - [`FORCE_POWER_KNIGHT_SPEED` **(K1 \& TSL)**](#force_power_knight_speed-k1--tsl)
      - [`FORCE_POWER_LIGHTNING` **(K1 \& TSL)**](#force_power_lightning-k1--tsl)
      - [`FORCE_POWER_MIND_MASTERY` **(K1 \& TSL)**](#force_power_mind_mastery-k1--tsl)
      - [`FORCE_POWER_SPEED_MASTERY` **(K1 \& TSL)**](#force_power_speed_mastery-k1--tsl)
      - [`FORCE_POWER_PLAGUE` **(K1 \& TSL)**](#force_power_plague-k1--tsl)
      - [`FORCE_POWER_REGENERATION` **(K1 \& TSL)**](#force_power_regeneration-k1--tsl)
      - [`FORCE_POWER_RESIST_COLD_HEAT_ENERGY` **(K1 \& TSL)**](#force_power_resist_cold_heat_energy-k1--tsl)
      - [`FORCE_POWER_RESIST_FORCE` **(K1 \& TSL)**](#force_power_resist_force-k1--tsl)
      - [`FORCE_POWER_SHOCK` **(K1 \& TSL)**](#force_power_shock-k1--tsl)
      - [`FORCE_POWER_SLEEP` **(K1 \& TSL)**](#force_power_sleep-k1--tsl)
      - [`FORCE_POWER_SLOW` **(K1 \& TSL)**](#force_power_slow-k1--tsl)
      - [`FORCE_POWER_STUN` **(K1 \& TSL)**](#force_power_stun-k1--tsl)
      - [`FORCE_POWER_DROID_STUN` **(K1 \& TSL)**](#force_power_droid_stun-k1--tsl)
      - [`FORCE_POWER_SUPRESS_FORCE` **(K1 \& TSL)**](#force_power_supress_force-k1--tsl)
      - [`FORCE_POWER_LIGHT_SABER_THROW` **(K1 \& TSL)**](#force_power_light_saber_throw-k1--tsl)
      - [`FORCE_POWER_WOUND` **(K1 \& TSL)**](#force_power_wound-k1--tsl)
      - [`PERSISTENT_ZONE_ACTIVE` **(K1 \& TSL)**](#persistent_zone_active-k1--tsl)
      - [`PERSISTENT_ZONE_FOLLOW` **(K1 \& TSL)**](#persistent_zone_follow-k1--tsl)
      - [`INVALID_STANDARD_FACTION` **(K1 \& TSL)**](#invalid_standard_faction-k1--tsl)
      - [`STANDARD_FACTION_HOSTILE_1` **(K1 \& TSL)**](#standard_faction_hostile_1-k1--tsl)
      - [`STANDARD_FACTION_FRIENDLY_1` **(K1 \& TSL)**](#standard_faction_friendly_1-k1--tsl)
      - [`STANDARD_FACTION_HOSTILE_2` **(K1 \& TSL)**](#standard_faction_hostile_2-k1--tsl)
      - [`STANDARD_FACTION_FRIENDLY_2` **(K1 \& TSL)**](#standard_faction_friendly_2-k1--tsl)
      - [`STANDARD_FACTION_NEUTRAL` **(K1 \& TSL)**](#standard_faction_neutral-k1--tsl)
      - [`STANDARD_FACTION_INSANE` **(K1 \& TSL)**](#standard_faction_insane-k1--tsl)
      - [`STANDARD_FACTION_PTAT_TUSKAN` **(K1 \& TSL)**](#standard_faction_ptat_tuskan-k1--tsl)
      - [`STANDARD_FACTION_GLB_XOR` **(K1 \& TSL)**](#standard_faction_glb_xor-k1--tsl)
      - [`STANDARD_FACTION_SURRENDER_1` **(K1 \& TSL)**](#standard_faction_surrender_1-k1--tsl)
      - [`STANDARD_FACTION_SURRENDER_2` **(K1 \& TSL)**](#standard_faction_surrender_2-k1--tsl)
      - [`STANDARD_FACTION_PREDATOR` **(K1 \& TSL)**](#standard_faction_predator-k1--tsl)
      - [`STANDARD_FACTION_PREY` **(K1 \& TSL)**](#standard_faction_prey-k1--tsl)
      - [`STANDARD_FACTION_TRAP` **(K1 \& TSL)**](#standard_faction_trap-k1--tsl)
      - [`STANDARD_FACTION_ENDAR_SPIRE` **(K1 \& TSL)**](#standard_faction_endar_spire-k1--tsl)
      - [`STANDARD_FACTION_RANCOR` **(K1 \& TSL)**](#standard_faction_rancor-k1--tsl)
      - [`STANDARD_FACTION_GIZKA_1` **(K1 \& TSL)**](#standard_faction_gizka_1-k1--tsl)
      - [`STANDARD_FACTION_GIZKA_2` **(K1 \& TSL)**](#standard_faction_gizka_2-k1--tsl)
      - [`SUBSKILL_FLAGTRAP` **(K1 \& TSL)**](#subskill_flagtrap-k1--tsl)
      - [`SUBSKILL_RECOVERTRAP` **(K1 \& TSL)**](#subskill_recovertrap-k1--tsl)
      - [`SUBSKILL_EXAMINETRAP` **(K1 \& TSL)**](#subskill_examinetrap-k1--tsl)
      - [`TALENT_TYPE_FORCE` **(K1 \& TSL)**](#talent_type_force-k1--tsl)
      - [`TALENT_TYPE_SPELL` **(K1 \& TSL)**](#talent_type_spell-k1--tsl)
      - [`TALENT_TYPE_FEAT` **(K1 \& TSL)**](#talent_type_feat-k1--tsl)
      - [`TALENT_TYPE_SKILL` **(K1 \& TSL)**](#talent_type_skill-k1--tsl)
      - [`TALENT_EXCLUDE_ALL_OF_TYPE` **(K1 \& TSL)**](#talent_exclude_all_of_type-k1--tsl)
      - [`GUI_PANEL_PLAYER_DEATH` **(K1 \& TSL)**](#gui_panel_player_death-k1--tsl)
      - [`POLYMORPH_TYPE_WEREWOLF` **(K1 \& TSL)**](#polymorph_type_werewolf-k1--tsl)
      - [`POLYMORPH_TYPE_WERERAT` **(K1 \& TSL)**](#polymorph_type_wererat-k1--tsl)
      - [`POLYMORPH_TYPE_WERECAT` **(K1 \& TSL)**](#polymorph_type_werecat-k1--tsl)
      - [`POLYMORPH_TYPE_GIANT_SPIDER` **(K1 \& TSL)**](#polymorph_type_giant_spider-k1--tsl)
      - [`POLYMORPH_TYPE_TROLL` **(K1 \& TSL)**](#polymorph_type_troll-k1--tsl)
      - [`POLYMORPH_TYPE_UMBER_HULK` **(K1 \& TSL)**](#polymorph_type_umber_hulk-k1--tsl)
      - [`POLYMORPH_TYPE_PIXIE` **(K1 \& TSL)**](#polymorph_type_pixie-k1--tsl)
      - [`POLYMORPH_TYPE_ZOMBIE` **(K1 \& TSL)**](#polymorph_type_zombie-k1--tsl)
      - [`POLYMORPH_TYPE_RED_DRAGON` **(K1 \& TSL)**](#polymorph_type_red_dragon-k1--tsl)
      - [`POLYMORPH_TYPE_FIRE_GIANT` **(K1 \& TSL)**](#polymorph_type_fire_giant-k1--tsl)
      - [`POLYMORPH_TYPE_BALOR` **(K1 \& TSL)**](#polymorph_type_balor-k1--tsl)
      - [`POLYMORPH_TYPE_DEATH_SLAAD` **(K1 \& TSL)**](#polymorph_type_death_slaad-k1--tsl)
      - [`POLYMORPH_TYPE_IRON_GOLEM` **(K1 \& TSL)**](#polymorph_type_iron_golem-k1--tsl)
      - [`POLYMORPH_TYPE_HUGE_FIRE_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_huge_fire_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_HUGE_WATER_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_huge_water_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_HUGE_EARTH_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_huge_earth_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_HUGE_AIR_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_huge_air_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_ELDER_FIRE_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_elder_fire_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_ELDER_WATER_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_elder_water_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_ELDER_EARTH_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_elder_earth_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_ELDER_AIR_ELEMENTAL` **(K1 \& TSL)**](#polymorph_type_elder_air_elemental-k1--tsl)
      - [`POLYMORPH_TYPE_BROWN_BEAR` **(K1 \& TSL)**](#polymorph_type_brown_bear-k1--tsl)
      - [`POLYMORPH_TYPE_PANTHER` **(K1 \& TSL)**](#polymorph_type_panther-k1--tsl)
      - [`POLYMORPH_TYPE_WOLF` **(K1 \& TSL)**](#polymorph_type_wolf-k1--tsl)
      - [`POLYMORPH_TYPE_BOAR` **(K1 \& TSL)**](#polymorph_type_boar-k1--tsl)
      - [`POLYMORPH_TYPE_BADGER` **(K1 \& TSL)**](#polymorph_type_badger-k1--tsl)
      - [`POLYMORPH_TYPE_PENGUIN` **(K1 \& TSL)**](#polymorph_type_penguin-k1--tsl)
      - [`POLYMORPH_TYPE_COW` **(K1 \& TSL)**](#polymorph_type_cow-k1--tsl)
      - [`POLYMORPH_TYPE_DOOM_KNIGHT` **(K1 \& TSL)**](#polymorph_type_doom_knight-k1--tsl)
      - [`POLYMORPH_TYPE_YUANTI` **(K1 \& TSL)**](#polymorph_type_yuanti-k1--tsl)
      - [`POLYMORPH_TYPE_IMP` **(K1 \& TSL)**](#polymorph_type_imp-k1--tsl)
      - [`POLYMORPH_TYPE_QUASIT` **(K1 \& TSL)**](#polymorph_type_quasit-k1--tsl)
      - [`POLYMORPH_TYPE_SUCCUBUS` **(K1 \& TSL)**](#polymorph_type_succubus-k1--tsl)
      - [`POLYMORPH_TYPE_DIRE_BROWN_BEAR` **(K1 \& TSL)**](#polymorph_type_dire_brown_bear-k1--tsl)
      - [`POLYMORPH_TYPE_DIRE_PANTHER` **(K1 \& TSL)**](#polymorph_type_dire_panther-k1--tsl)
      - [`POLYMORPH_TYPE_DIRE_WOLF` **(K1 \& TSL)**](#polymorph_type_dire_wolf-k1--tsl)
      - [`POLYMORPH_TYPE_DIRE_BOAR` **(K1 \& TSL)**](#polymorph_type_dire_boar-k1--tsl)
      - [`POLYMORPH_TYPE_DIRE_BADGER` **(K1 \& TSL)**](#polymorph_type_dire_badger-k1--tsl)
      - [`CREATURE_SIZE_INVALID` **(K1 \& TSL)**](#creature_size_invalid-k1--tsl)
      - [`CREATURE_SIZE_TINY` **(K1 \& TSL)**](#creature_size_tiny-k1--tsl)
      - [`CREATURE_SIZE_SMALL` **(K1 \& TSL)**](#creature_size_small-k1--tsl)
      - [`CREATURE_SIZE_MEDIUM` **(K1 \& TSL)**](#creature_size_medium-k1--tsl)
      - [`CREATURE_SIZE_LARGE` **(K1 \& TSL)**](#creature_size_large-k1--tsl)
      - [`CREATURE_SIZE_HUGE` **(K1 \& TSL)**](#creature_size_huge-k1--tsl)
      - [`CAMERA_MODE_CHASE_CAMERA` **(K1 \& TSL)**](#camera_mode_chase_camera-k1--tsl)
      - [`CAMERA_MODE_TOP_DOWN` **(K1 \& TSL)**](#camera_mode_top_down-k1--tsl)
      - [`CAMERA_MODE_STIFF_CHASE_CAMERA` **(K1 \& TSL)**](#camera_mode_stiff_chase_camera-k1--tsl)
      - [`GAME_DIFFICULTY_VERY_EASY` **(K1 \& TSL)**](#game_difficulty_very_easy-k1--tsl)
      - [`GAME_DIFFICULTY_EASY` **(K1 \& TSL)**](#game_difficulty_easy-k1--tsl)
      - [`GAME_DIFFICULTY_NORMAL` **(K1 \& TSL)**](#game_difficulty_normal-k1--tsl)
      - [`GAME_DIFFICULTY_CORE_RULES` **(K1 \& TSL)**](#game_difficulty_core_rules-k1--tsl)
      - [`GAME_DIFFICULTY_DIFFICULT` **(K1 \& TSL)**](#game_difficulty_difficult-k1--tsl)
      - [`ACTION_MOVETOPOINT` **(K1 \& TSL)**](#action_movetopoint-k1--tsl)
      - [`ACTION_PICKUPITEM` **(K1 \& TSL)**](#action_pickupitem-k1--tsl)
      - [`ACTION_DROPITEM` **(K1 \& TSL)**](#action_dropitem-k1--tsl)
      - [`ACTION_ATTACKOBJECT` **(K1 \& TSL)**](#action_attackobject-k1--tsl)
      - [`ACTION_CASTSPELL` **(K1 \& TSL)**](#action_castspell-k1--tsl)
      - [`ACTION_OPENDOOR` **(K1 \& TSL)**](#action_opendoor-k1--tsl)
      - [`ACTION_CLOSEDOOR` **(K1 \& TSL)**](#action_closedoor-k1--tsl)
      - [`ACTION_DIALOGOBJECT` **(K1 \& TSL)**](#action_dialogobject-k1--tsl)
      - [`ACTION_DISABLETRAP` **(K1 \& TSL)**](#action_disabletrap-k1--tsl)
      - [`ACTION_RECOVERTRAP` **(K1 \& TSL)**](#action_recovertrap-k1--tsl)
      - [`ACTION_FLAGTRAP` **(K1 \& TSL)**](#action_flagtrap-k1--tsl)
      - [`ACTION_EXAMINETRAP` **(K1 \& TSL)**](#action_examinetrap-k1--tsl)
      - [`ACTION_SETTRAP` **(K1 \& TSL)**](#action_settrap-k1--tsl)
      - [`ACTION_OPENLOCK` **(K1 \& TSL)**](#action_openlock-k1--tsl)
      - [`ACTION_LOCK` **(K1 \& TSL)**](#action_lock-k1--tsl)
      - [`ACTION_USEOBJECT` **(K1 \& TSL)**](#action_useobject-k1--tsl)
      - [`ACTION_ANIMALEMPATHY` **(K1 \& TSL)**](#action_animalempathy-k1--tsl)
      - [`ACTION_REST` **(K1 \& TSL)**](#action_rest-k1--tsl)
      - [`ACTION_TAUNT` **(K1 \& TSL)**](#action_taunt-k1--tsl)
      - [`ACTION_ITEMCASTSPELL` **(K1 \& TSL)**](#action_itemcastspell-k1--tsl)
      - [`ACTION_COUNTERSPELL` **(K1 \& TSL)**](#action_counterspell-k1--tsl)
      - [`ACTION_HEAL` **(K1 \& TSL)**](#action_heal-k1--tsl)
      - [`ACTION_PICKPOCKET` **(K1 \& TSL)**](#action_pickpocket-k1--tsl)
      - [`ACTION_FOLLOW` **(K1 \& TSL)**](#action_follow-k1--tsl)
      - [`ACTION_WAIT` **(K1 \& TSL)**](#action_wait-k1--tsl)
      - [`ACTION_SIT` **(K1 \& TSL)**](#action_sit-k1--tsl)
      - [`ACTION_FOLLOWLEADER` **(K1 \& TSL)**](#action_followleader-k1--tsl)
      - [`ACTION_INVALID` **(K1 \& TSL)**](#action_invalid-k1--tsl)
      - [`ACTION_QUEUEEMPTY` **(K1 \& TSL)**](#action_queueempty-k1--tsl)
      - [`SWMINIGAME_TRACKFOLLOWER_SOUND_ENGINE` **(K1 \& TSL)**](#swminigame_trackfollower_sound_engine-k1--tsl)
      - [`SWMINIGAME_TRACKFOLLOWER_SOUND_DEATH` **(K1 \& TSL)**](#swminigame_trackfollower_sound_death-k1--tsl)
      - [`PLOT_O_DOOM` **(K1 \& TSL)**](#plot_o_doom-k1--tsl)
      - [`PLOT_O_SCARY_STUFF` **(K1 \& TSL)**](#plot_o_scary_stuff-k1--tsl)
      - [`PLOT_O_BIG_MONSTERS` **(K1 \& TSL)**](#plot_o_big_monsters-k1--tsl)
      - [`FORMATION_WEDGE` **(K1 \& TSL)**](#formation_wedge-k1--tsl)
      - [`FORMATION_LINE` **(K1 \& TSL)**](#formation_line-k1--tsl)
      - [`SUBSCREEN_ID_NONE` **(K1 \& TSL)**](#subscreen_id_none-k1--tsl)
      - [`SUBSCREEN_ID_EQUIP` **(K1 \& TSL)**](#subscreen_id_equip-k1--tsl)
      - [`SUBSCREEN_ID_ITEM` **(K1 \& TSL)**](#subscreen_id_item-k1--tsl)
      - [`SUBSCREEN_ID_CHARACTER_RECORD` **(K1 \& TSL)**](#subscreen_id_character_record-k1--tsl)
      - [`SUBSCREEN_ID_ABILITY` **(K1 \& TSL)**](#subscreen_id_ability-k1--tsl)
      - [`SUBSCREEN_ID_MAP` **(K1 \& TSL)**](#subscreen_id_map-k1--tsl)
      - [`SUBSCREEN_ID_QUEST` **(K1 \& TSL)**](#subscreen_id_quest-k1--tsl)
      - [`SUBSCREEN_ID_OPTIONS` **(K1 \& TSL)**](#subscreen_id_options-k1--tsl)
      - [`SUBSCREEN_ID_MESSAGES` **(K1 \& TSL)**](#subscreen_id_messages-k1--tsl)
      - [`SHIELD_DROID_ENERGY_1` **(K1 \& TSL)**](#shield_droid_energy_1-k1--tsl)
      - [`SHIELD_DROID_ENERGY_2` **(K1 \& TSL)**](#shield_droid_energy_2-k1--tsl)
      - [`SHIELD_DROID_ENERGY_3` **(K1 \& TSL)**](#shield_droid_energy_3-k1--tsl)
      - [`SHIELD_DROID_ENVIRO_1` **(K1 \& TSL)**](#shield_droid_enviro_1-k1--tsl)
      - [`SHIELD_DROID_ENVIRO_2` **(K1 \& TSL)**](#shield_droid_enviro_2-k1--tsl)
      - [`SHIELD_DROID_ENVIRO_3` **(K1 \& TSL)**](#shield_droid_enviro_3-k1--tsl)
      - [`SHIELD_ENERGY` **(K1 \& TSL)**](#shield_energy-k1--tsl)
      - [`SHIELD_ENERGY_SITH` **(K1 \& TSL)**](#shield_energy_sith-k1--tsl)
      - [`SHIELD_ENERGY_ARKANIAN` **(K1 \& TSL)**](#shield_energy_arkanian-k1--tsl)
      - [`SHIELD_ECHANI` **(K1 \& TSL)**](#shield_echani-k1--tsl)
      - [`SHIELD_MANDALORIAN_MELEE` **(K1 \& TSL)**](#shield_mandalorian_melee-k1--tsl)
      - [`SHIELD_MANDALORIAN_POWER` **(K1 \& TSL)**](#shield_mandalorian_power-k1--tsl)
      - [`SHIELD_DUELING_ECHANI` **(K1 \& TSL)**](#shield_dueling_echani-k1--tsl)
      - [`SHIELD_DUELING_YUSANIS` **(K1 \& TSL)**](#shield_dueling_yusanis-k1--tsl)
      - [`SHIELD_VERPINE_PROTOTYPE` **(K1 \& TSL)**](#shield_verpine_prototype-k1--tsl)
      - [`SHIELD_ANTIQUE_DROID` **(K1 \& TSL)**](#shield_antique_droid-k1--tsl)
      - [`SHIELD_PLOT_TAR_M09AA` **(K1 \& TSL)**](#shield_plot_tar_m09aa-k1--tsl)
      - [`SHIELD_PLOT_UNK_M44AA` **(K1 \& TSL)**](#shield_plot_unk_m44aa-k1--tsl)
      - [`VIDEO_EFFECT_NONE` **(K1 \& TSL)**](#video_effect_none-k1--tsl)
      - [`VIDEO_EFFECT_SECURITY_CAMERA` **(K1 \& TSL)**](#video_effect_security_camera-k1--tsl)
      - [`VIDEO_EFFECT_FREELOOK_T3M4` **(K1 \& TSL)**](#video_effect_freelook_t3m4-k1--tsl)
      - [`VIDEO_EFFECT_FREELOOK_HK47` **(K1 \& TSL)**](#video_effect_freelook_hk47-k1--tsl)
      - [`TUTORIAL_WINDOW_START_SWOOP_RACE` **(K1 \& TSL)**](#tutorial_window_start_swoop_race-k1--tsl)
      - [`TUTORIAL_WINDOW_RETURN_TO_BASE` **(K1 \& TSL)**](#tutorial_window_return_to_base-k1--tsl)
      - [`TUTORIAL_WINDOW_MOVEMENT_KEYS` **(K1)**](#tutorial_window_movement_keys-k1)
      - [`LIVE_CONTENT_PKG1` **(K1 \& TSL)**](#live_content_pkg1-k1--tsl)
      - [`LIVE_CONTENT_PKG2` **(K1 \& TSL)**](#live_content_pkg2-k1--tsl)
      - [`LIVE_CONTENT_PKG3` **(K1 \& TSL)**](#live_content_pkg3-k1--tsl)
      - [`LIVE_CONTENT_PKG4` **(K1 \& TSL)**](#live_content_pkg4-k1--tsl)
      - [`LIVE_CONTENT_PKG5` **(K1 \& TSL)**](#live_content_pkg5-k1--tsl)
      - [`LIVE_CONTENT_PKG6` **(K1 \& TSL)**](#live_content_pkg6-k1--tsl)
      - [`sLanguage` **(K1)**](#slanguage-k1)
      - [`FORM_MASK_FORCE_FOCUS` **(TSL)**](#form_mask_force_focus-tsl)
      - [`FORM_MASK_ENDURING_FORCE` **(TSL)**](#form_mask_enduring_force-tsl)
      - [`FORM_MASK_FORCE_AMPLIFICATION` **(TSL)**](#form_mask_force_amplification-tsl)
      - [`FORM_MASK_FORCE_POTENCY` **(TSL)**](#form_mask_force_potency-tsl)
      - [`FORM_MASK_REGENERATION` **(TSL)**](#form_mask_regeneration-tsl)
      - [`FORM_MASK_POWER_OF_THE_DARK_SIDE` **(TSL)**](#form_mask_power_of_the_dark_side-tsl)
      - [`FORCE_POWER_MASTER_ENERGY_RESISTANCE` **(TSL)**](#force_power_master_energy_resistance-tsl)
      - [`FORCE_POWER_MASTER_HEAL` **(TSL)**](#force_power_master_heal-tsl)
      - [`FORCE_POWER_FORCE_BARRIER` **(TSL)**](#force_power_force_barrier-tsl)
      - [`FORCE_POWER_IMPROVED_FORCE_BARRIER` **(TSL)**](#force_power_improved_force_barrier-tsl)
      - [`FORCE_POWER_MASTER_FORCE_BARRIER` **(TSL)**](#force_power_master_force_barrier-tsl)
      - [`FORCE_POWER_BATTLE_MEDITATION_PC` **(TSL)**](#force_power_battle_meditation_pc-tsl)
      - [`FORCE_POWER_IMPROVED_BATTLE_MEDITATION_PC` **(TSL)**](#force_power_improved_battle_meditation_pc-tsl)
      - [`FORCE_POWER_MASTER_BATTLE_MEDITATION_PC` **(TSL)**](#force_power_master_battle_meditation_pc-tsl)
      - [`FORCE_POWER_BAT_MED_ENEMY` **(TSL)**](#force_power_bat_med_enemy-tsl)
      - [`FORCE_POWER_IMP_BAT_MED_ENEMY` **(TSL)**](#force_power_imp_bat_med_enemy-tsl)
      - [`FORCE_POWER_MAS_BAT_MED_ENEMY` **(TSL)**](#force_power_mas_bat_med_enemy-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_I` **(TSL)**](#force_power_crush_opposition_i-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_II` **(TSL)**](#force_power_crush_opposition_ii-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_III` **(TSL)**](#force_power_crush_opposition_iii-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_IV` **(TSL)**](#force_power_crush_opposition_iv-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_V` **(TSL)**](#force_power_crush_opposition_v-tsl)
      - [`FORCE_POWER_CRUSH_OPPOSITION_VI` **(TSL)**](#force_power_crush_opposition_vi-tsl)
      - [`FORCE_POWER_FORCE_BODY` **(TSL)**](#force_power_force_body-tsl)
      - [`FORCE_POWER_IMPROVED_FORCE_BODY` **(TSL)**](#force_power_improved_force_body-tsl)
      - [`FORCE_POWER_MASTER_FORCE_BODY` **(TSL)**](#force_power_master_force_body-tsl)
      - [`FORCE_POWER_DRAIN_FORCE` **(TSL)**](#force_power_drain_force-tsl)
      - [`FORCE_POWER_IMPROVED_DRAIN_FORCE` **(TSL)**](#force_power_improved_drain_force-tsl)
      - [`FORCE_POWER_MASTER_DRAIN_FORCE` **(TSL)**](#force_power_master_drain_force-tsl)
      - [`FORCE_POWER_FORCE_CAMOUFLAGE` **(TSL)**](#force_power_force_camouflage-tsl)
      - [`FORCE_POWER_IMPROVED_FORCE_CAMOUFLAGE` **(TSL)**](#force_power_improved_force_camouflage-tsl)
      - [`FORCE_POWER_MASTER_FORCE_CAMOUFLAGE` **(TSL)**](#force_power_master_force_camouflage-tsl)
      - [`FORCE_POWER_FORCE_SCREAM` **(TSL)**](#force_power_force_scream-tsl)
      - [`FORCE_POWER_IMPROVED_FORCE_SCREAM` **(TSL)**](#force_power_improved_force_scream-tsl)
      - [`FORCE_POWER_MASTER_FORCE_SCREAM` **(TSL)**](#force_power_master_force_scream-tsl)
      - [`FORCE_POWER_FORCE_REPULSION` **(TSL)**](#force_power_force_repulsion-tsl)
      - [`FORCE_POWER_FURY` **(TSL)**](#force_power_fury-tsl)
      - [`FORCE_POWER_IMPROVED_FURY` **(TSL)**](#force_power_improved_fury-tsl)
      - [`FORCE_POWER_MASTER_FURY` **(TSL)**](#force_power_master_fury-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_I` **(TSL)**](#force_power_inspire_followers_i-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_II` **(TSL)**](#force_power_inspire_followers_ii-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_III` **(TSL)**](#force_power_inspire_followers_iii-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_IV` **(TSL)**](#force_power_inspire_followers_iv-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_V` **(TSL)**](#force_power_inspire_followers_v-tsl)
      - [`FORCE_POWER_INSPIRE_FOLLOWERS_VI` **(TSL)**](#force_power_inspire_followers_vi-tsl)
      - [`FORCE_POWER_REVITALIZE` **(TSL)**](#force_power_revitalize-tsl)
      - [`FORCE_POWER_IMPROVED_REVITALIZE` **(TSL)**](#force_power_improved_revitalize-tsl)
      - [`FORCE_POWER_MASTER_REVITALIZE` **(TSL)**](#force_power_master_revitalize-tsl)
      - [`FORCE_POWER_FORCE_SIGHT` **(TSL)**](#force_power_force_sight-tsl)
      - [`FORCE_POWER_FORCE_CRUSH` **(TSL)**](#force_power_force_crush-tsl)
      - [`FORCE_POWER_PRECOGNITION` **(TSL)**](#force_power_precognition-tsl)
      - [`FORCE_POWER_BATTLE_PRECOGNITION` **(TSL)**](#force_power_battle_precognition-tsl)
      - [`FORCE_POWER_FORCE_ENLIGHTENMENT` **(TSL)**](#force_power_force_enlightenment-tsl)
      - [`FORCE_POWER_MIND_TRICK` **(TSL)**](#force_power_mind_trick-tsl)
      - [`FORCE_POWER_CONFUSION` **(TSL)**](#force_power_confusion-tsl)
      - [`FORCE_POWER_BEAST_TRICK` **(TSL)**](#force_power_beast_trick-tsl)
      - [`FORCE_POWER_BEAST_CONFUSION` **(TSL)**](#force_power_beast_confusion-tsl)
      - [`FORCE_POWER_DROID_TRICK` **(TSL)**](#force_power_droid_trick-tsl)
      - [`FORCE_POWER_DROID_CONFUSION` **(TSL)**](#force_power_droid_confusion-tsl)
      - [`FORCE_POWER_BREATH_CONTROL` **(TSL)**](#force_power_breath_control-tsl)
      - [`FORCE_POWER_WOOKIEE_RAGE_I` **(TSL)**](#force_power_wookiee_rage_i-tsl)
      - [`FORCE_POWER_WOOKIEE_RAGE_II` **(TSL)**](#force_power_wookiee_rage_ii-tsl)
      - [`FORCE_POWER_WOOKIEE_RAGE_III` **(TSL)**](#force_power_wookiee_rage_iii-tsl)
      - [`FORM_LIGHTSABER_PADAWAN_I` **(TSL)**](#form_lightsaber_padawan_i-tsl)
      - [`FORM_LIGHTSABER_PADAWAN_II` **(TSL)**](#form_lightsaber_padawan_ii-tsl)
      - [`FORM_LIGHTSABER_PADAWAN_III` **(TSL)**](#form_lightsaber_padawan_iii-tsl)
      - [`FORM_LIGHTSABER_DAKLEAN_I` **(TSL)**](#form_lightsaber_daklean_i-tsl)
      - [`FORM_LIGHTSABER_DAKLEAN_II` **(TSL)**](#form_lightsaber_daklean_ii-tsl)
      - [`FORM_LIGHTSABER_DAKLEAN_III` **(TSL)**](#form_lightsaber_daklean_iii-tsl)
      - [`FORM_LIGHTSABER_SENTINEL_I` **(TSL)**](#form_lightsaber_sentinel_i-tsl)
      - [`FORM_LIGHTSABER_SENTINEL_II` **(TSL)**](#form_lightsaber_sentinel_ii-tsl)
      - [`FORM_LIGHTSABER_SENTINEL_III` **(TSL)**](#form_lightsaber_sentinel_iii-tsl)
      - [`FORM_LIGHTSABER_SODAK_I` **(TSL)**](#form_lightsaber_sodak_i-tsl)
      - [`FORM_LIGHTSABER_SODAK_II` **(TSL)**](#form_lightsaber_sodak_ii-tsl)
      - [`FORM_LIGHTSABER_SODAK_III` **(TSL)**](#form_lightsaber_sodak_iii-tsl)
      - [`FORM_LIGHTSABER_ANCIENT_I` **(TSL)**](#form_lightsaber_ancient_i-tsl)
      - [`FORM_LIGHTSABER_ANCIENT_II` **(TSL)**](#form_lightsaber_ancient_ii-tsl)
      - [`FORM_LIGHTSABER_ANCIENT_III` **(TSL)**](#form_lightsaber_ancient_iii-tsl)
      - [`FORM_LIGHTSABER_MASTER_I` **(TSL)**](#form_lightsaber_master_i-tsl)
      - [`FORM_LIGHTSABER_MASTER_II` **(TSL)**](#form_lightsaber_master_ii-tsl)
      - [`FORM_LIGHTSABER_MASTER_III` **(TSL)**](#form_lightsaber_master_iii-tsl)
      - [`FORM_CONSULAR_FORCE_FOCUS_I` **(TSL)**](#form_consular_force_focus_i-tsl)
      - [`FORM_CONSULAR_FORCE_FOCUS_II` **(TSL)**](#form_consular_force_focus_ii-tsl)
      - [`FORM_CONSULAR_FORCE_FOCUS_III` **(TSL)**](#form_consular_force_focus_iii-tsl)
      - [`FORM_CONSULAR_ENDURING_FORCE_I` **(TSL)**](#form_consular_enduring_force_i-tsl)
      - [`FORM_CONSULAR_ENDURING_FORCE_II` **(TSL)**](#form_consular_enduring_force_ii-tsl)
      - [`FORM_CONSULAR_ENDURING_FORCE_III` **(TSL)**](#form_consular_enduring_force_iii-tsl)
      - [`FORM_CONSULAR_FORCE_AMPLIFICATION_I` **(TSL)**](#form_consular_force_amplification_i-tsl)
      - [`FORM_CONSULAR_FORCE_AMPLIFICATION_II` **(TSL)**](#form_consular_force_amplification_ii-tsl)
      - [`FORM_CONSULAR_FORCE_AMPLIFICATION_III` **(TSL)**](#form_consular_force_amplification_iii-tsl)
      - [`FORM_CONSULAR_FORCE_SHELL_I` **(TSL)**](#form_consular_force_shell_i-tsl)
      - [`FORM_CONSULAR_FORCE_SHELL_II` **(TSL)**](#form_consular_force_shell_ii-tsl)
      - [`FORM_CONSULAR_FORCE_SHELL_III` **(TSL)**](#form_consular_force_shell_iii-tsl)
      - [`FORM_CONSULAR_FORCE_POTENCY_I` **(TSL)**](#form_consular_force_potency_i-tsl)
      - [`FORM_CONSULAR_FORCE_POTENCY_II` **(TSL)**](#form_consular_force_potency_ii-tsl)
      - [`FORM_CONSULAR_FORCE_POTENCY_III` **(TSL)**](#form_consular_force_potency_iii-tsl)
      - [`FORM_CONSULAR_REGENERATION_I` **(TSL)**](#form_consular_regeneration_i-tsl)
      - [`FORM_CONSULAR_REGENERATION_II` **(TSL)**](#form_consular_regeneration_ii-tsl)
      - [`FORM_CONSULAR_REGENERATION_III` **(TSL)**](#form_consular_regeneration_iii-tsl)
      - [`FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_I` **(TSL)**](#form_consular_power_of_the_dark_side_i-tsl)
      - [`FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_II` **(TSL)**](#form_consular_power_of_the_dark_side_ii-tsl)
      - [`FORM_CONSULAR_POWER_OF_THE_DARK_SIDE_III` **(TSL)**](#form_consular_power_of_the_dark_side_iii-tsl)
      - [`FORM_SABER_I_SHII_CHO` **(TSL)**](#form_saber_i_shii_cho-tsl)
      - [`FORM_SABER_II_MAKASHI` **(TSL)**](#form_saber_ii_makashi-tsl)
      - [`FORM_SABER_III_SORESU` **(TSL)**](#form_saber_iii_soresu-tsl)
      - [`FORM_SABER_IV_ATARU` **(TSL)**](#form_saber_iv_ataru-tsl)
      - [`FORM_SABER_V_SHIEN` **(TSL)**](#form_saber_v_shien-tsl)
      - [`FORM_SABER_VI_NIMAN` **(TSL)**](#form_saber_vi_niman-tsl)
      - [`FORM_SABER_VII_JUYO` **(TSL)**](#form_saber_vii_juyo-tsl)
      - [`FORM_FORCE_I_FOCUS` **(TSL)**](#form_force_i_focus-tsl)
      - [`FORM_FORCE_II_POTENCY` **(TSL)**](#form_force_ii_potency-tsl)
      - [`FORM_FORCE_III_AFFINITY` **(TSL)**](#form_force_iii_affinity-tsl)
      - [`FORM_FORCE_IV_MASTERY` **(TSL)**](#form_force_iv_mastery-tsl)
      - [`STANDARD_FACTION_SELF_LOATHING` **(TSL)**](#standard_faction_self_loathing-tsl)
      - [`STANDARD_FACTION_ONE_ON_ONE` **(TSL)**](#standard_faction_one_on_one-tsl)
      - [`STANDARD_FACTION_PARTYPUPPET` **(TSL)**](#standard_faction_partypuppet-tsl)
      - [`ACTION_FOLLOWOWNER` **(TSL)**](#action_followowner-tsl)
      - [`PUP_SENSORBALL` **(TSL)**](#pup_sensorball-tsl)
      - [`PUP_OTHER1` **(TSL)**](#pup_other1-tsl)
      - [`PUP_OTHER2` **(TSL)**](#pup_other2-tsl)
      - [`SHIELD_PLOT_MAN_M28AA` **(TSL)**](#shield_plot_man_m28aa-tsl)
      - [`SHIELD_HEAT` **(TSL)**](#shield_heat-tsl)
      - [`SHIELD_DREXL` **(TSL)**](#shield_drexl-tsl)
      - [`VIDEO_EFFECT_CLAIRVOYANCE` **(TSL)**](#video_effect_clairvoyance-tsl)
      - [`VIDEO_EFFECT_FORCESIGHT` **(TSL)**](#video_effect_forcesight-tsl)
      - [`VIDEO_EFFECT_VISAS_FREELOOK` **(TSL)**](#video_effect_visas_freelook-tsl)
      - [`VIDEO_EFFECT_CLAIRVOYANCEFULL` **(TSL)**](#video_effect_clairvoyancefull-tsl)
      - [`VIDEO_EFFECT_FURY_1` **(TSL)**](#video_effect_fury_1-tsl)
      - [`VIDEO_EFFECT_FURY_2` **(TSL)**](#video_effect_fury_2-tsl)
      - [`VIDEO_EFFECT_FURY_3` **(TSL)**](#video_effect_fury_3-tsl)
      - [`VIDEO_FFECT_SECURITY_NO_LABEL` **(TSL)**](#video_ffect_security_no_label-tsl)
      - [`TUTORIAL_WINDOW_TEMP1` **(TSL)**](#tutorial_window_temp1-tsl)
      - [`TUTORIAL_WINDOW_TEMP2` **(TSL)**](#tutorial_window_temp2-tsl)
      - [`TUTORIAL_WINDOW_TEMP3` **(TSL)**](#tutorial_window_temp3-tsl)
      - [`TUTORIAL_WINDOW_TEMP4` **(TSL)**](#tutorial_window_temp4-tsl)
      - [`TUTORIAL_WINDOW_TEMP5` **(TSL)**](#tutorial_window_temp5-tsl)
      - [`TUTORIAL_WINDOW_TEMP6` **(TSL)**](#tutorial_window_temp6-tsl)
      - [`TUTORIAL_WINDOW_TEMP7` **(TSL)**](#tutorial_window_temp7-tsl)
      - [`TUTORIAL_WINDOW_TEMP8` **(TSL)**](#tutorial_window_temp8-tsl)
      - [`TUTORIAL_WINDOW_TEMP9` **(TSL)**](#tutorial_window_temp9-tsl)
      - [`TUTORIAL_WINDOW_TEMP10` **(TSL)**](#tutorial_window_temp10-tsl)
      - [`TUTORIAL_WINDOW_TEMP11` **(TSL)**](#tutorial_window_temp11-tsl)
      - [`TUTORIAL_WINDOW_TEMP12` **(TSL)**](#tutorial_window_temp12-tsl)
      - [`TUTORIAL_WINDOW_TEMP13` **(TSL)**](#tutorial_window_temp13-tsl)
      - [`TUTORIAL_WINDOW_TEMP14` **(TSL)**](#tutorial_window_temp14-tsl)
      - [`TUTORIAL_WINDOW_TEMP15` **(TSL)**](#tutorial_window_temp15-tsl)
      - [`AI_LEVEL_VERY_HIGH` **(TSL)**](#ai_level_very_high-tsl)
      - [`AI_LEVEL_HIGH` **(TSL)**](#ai_level_high-tsl)
      - [`AI_LEVEL_NORMAL` **(TSL)**](#ai_level_normal-tsl)
      - [`AI_LEVEL_LOW` **(TSL)**](#ai_level_low-tsl)
      - [`AI_LEVEL_VERY_LOW` **(TSL)**](#ai_level_very_low-tsl)
      - [`IMPLANT_NONE` **(TSL)**](#implant_none-tsl)
      - [`IMPLANT_REGEN` **(TSL)**](#implant_regen-tsl)
      - [`IMPLANT_STR` **(TSL)**](#implant_str-tsl)
      - [`IMPLANT_END` **(TSL)**](#implant_end-tsl)
      - [`IMPLANT_AGI` **(TSL)**](#implant_agi-tsl)
      - [`FORFEIT_NO_FORCE_POWERS` **(TSL)**](#forfeit_no_force_powers-tsl)
      - [`FORFEIT_NO_ITEMS` **(TSL)**](#forfeit_no_items-tsl)
      - [`FORFEIT_NO_WEAPONS` **(TSL)**](#forfeit_no_weapons-tsl)
      - [`FORFEIT_DXUN_SWORD_ONLY` **(TSL)**](#forfeit_dxun_sword_only-tsl)
      - [`FORFEIT_NO_ARMOR` **(TSL)**](#forfeit_no_armor-tsl)
      - [`FORFEIT_NO_RANGED` **(TSL)**](#forfeit_no_ranged-tsl)
      - [`FORFEIT_NO_LIGHTSABER` **(TSL)**](#forfeit_no_lightsaber-tsl)
      - [`FORFEIT_NO_ITEM_BUT_SHIELD` **(TSL)**](#forfeit_no_item_but_shield-tsl)
  - [Cross-References](#cross-references)
<!-- TOC_END -->

## PyKotor Implementation

PyKotor implements `nwscript.nss` definitions in three Python modules:

### Data Structures

**`Libraries/PyKotor/src/pykotor/common/script.py`:**

- `ScriptFunction`: Represents a function signature with return type, name, parameters, description, and raw string
- `ScriptParam`: Represents a function parameter with type, name, and optional default value
- `ScriptConstant`: Represents a constant with type, name, and value
- `DataType`: Enumeration of all NWScript data types (INT, FLOAT, STRING, OBJECT, VECTOR, etc.)

**`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`:**

- `KOTOR_FUNCTIONS`: List of 772 `ScriptFunction` objects for KotOR 1
- `TSL_FUNCTIONS`: List of functions for KotOR 2 (The Sith Lords)
- `KOTOR_CONSTANTS`: List of 1489 `ScriptConstant` objects for KotOR 1
- `TSL_CONSTANTS`: List of constants for KotOR 2

**`Libraries/PyKotor/src/pykotor/common/scriptlib.py`:**

- `KOTOR_LIBRARY`: Dictionary mapping library file names to their source code content (e.g., `"k_inc_generic"`, `"k_inc_utility"`)
- `TSL_LIBRARY`: Dictionary for KotOR 2 library files

### Compilation Integration

During NSS compilation (see [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205)):

1. **Parser Initialization**: The `NssParser` is created with game-specific functions and constants:

   ```python
   nss_parser = NssParser(
       functions=KOTOR_FUNCTIONS if game.is_k1() else TSL_FUNCTIONS,
       constants=KOTOR_CONSTANTS if game.is_k1() else TSL_CONSTANTS,
       library=KOTOR_LIBRARY if game.is_k1() else TSL_LIBRARY,
       library_lookup=lookup_arg,
   )
   ```

2. **Function Resolution**: When the parser encounters a function call, it:
   - Looks up the function name in the functions list
   - Validates parameter types and counts
   - Resolves the routine number (index in the functions list)
   - Generates an `ACTION` instruction with the routine number

3. **Constant Resolution**: When the parser encounters a constant:
   - Looks up the constant name in the constants list
   - Replaces the constant with its value
   - Generates appropriate `CONSTx` instruction

4. **Library Inclusion**: When the parser encounters `#include`:
   - Looks up the library name in the library dictionary
   - Parses the included source code
   - Merges functions and constants into the current scope

**Reference:** [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) (data structures), [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) (function/constant definitions), [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) (library files)

---

## Shared Functions (K1 & TSL)

<!-- SHARED_FUNCTIONS_START -->

### Abilities and Stats

See [Abilities and Stats](NSS-Shared-Functions-Abilities-and-Stats) for detailed documentation.

### Actions

See [Actions](NSS-Shared-Functions-Actions) for detailed documentation.

### Alignment System

See [Alignment System](NSS-Shared-Functions-Alignment-System) for detailed documentation.

### Class System

See [Class System](NSS-Shared-Functions-Class-System) for detailed documentation.

### Combat Functions

See [Combat Functions](NSS-Shared-Functions-Combat-Functions) for detailed documentation.

### Dialog and Conversation Functions

See [Dialog and Conversation Functions](NSS-Shared-Functions-Dialog-and-Conversation-Functions) for detailed documentation.

### Effects System

See [Effects System](NSS-Shared-Functions-Effects-System) for detailed documentation.

### Global Variables

See [Global Variables](NSS-Shared-Functions-Global-Variables) for detailed documentation.

### Item Management

See [Item Management](NSS-Shared-Functions-Item-Management) for detailed documentation.

### Item Properties

See [Item Properties](NSS-Shared-Functions-Item-Properties) for detailed documentation.

### Local Variables

See [Local Variables](NSS-Shared-Functions-Local-Variables) for detailed documentation.

### Module and Area Functions

See [Module and Area Functions](NSS-Shared-Functions-Module-and-Area-Functions) for detailed documentation.

### Object Query and Manipulation

See [Object Query and Manipulation](NSS-Shared-Functions-Object-Query-and-Manipulation) for detailed documentation.

### Other Functions

See [Other Functions](NSS-Shared-Functions-Other-Functions) for detailed documentation.

### Party Management

<a id="addavailablenpcbyobject"></a>

#### `AddAvailableNPCByObject(nNPC, oCreature)` - Routine 694

- `694. AddAvailableNPCByObject`
- This adds a NPC to the list of available party members using
- a game object as the template
- Returns if true if successful, false if the NPC had already
- been added or the object specified is invalid

- `nNPC`: int
- `oCreature`: object

<a id="addavailablenpcbytemplate"></a>

#### `AddAvailableNPCByTemplate(nNPC, sTemplate)` - Routine 697

- `697. AddAvailableNPCByTemplate`
- This adds a NPC to the list of available party members using
- a template
- Returns if true if successful, false if the NPC had already
- been added or the template specified is invalid

- `nNPC`: int
- `sTemplate`: string

<a id="addpartymember"></a>

#### `AddPartyMember(nNPC, oCreature)` - Routine 574

- `574. AddPartyMember`
- Adds a creature to the party
- Returns whether the addition was successful
- AddPartyMember

- `nNPC`: int
- `oCreature`: object

<a id="addtoparty"></a>

#### `AddToParty(oPC, oPartyLeader)` - Routine 572

- `572. AddToParty`
- Add oPC to oPartyLeader's party.  This will only work on two PCs.
- - oPC: player to add to a party
- - oPartyLeader: player already in the party

- `oPC`: object
- `oPartyLeader`: object

<a id="getpartyaistyle"></a>

#### `GetPartyAIStyle()` - Routine 704

- `704. GetPartyAIStyle`
- Returns the party ai style

<a id="getpartymemberbyindex"></a>

#### `GetPartyMemberByIndex(nIndex)` - Routine 577

- `577. GetPartyMemberByIndex`
- Returns the party member at a given index in the party.
- The order of members in the party can vary based on
- who the current leader is (member 0 is always the current
- party leader).
- GetPartyMemberByIndex

- `nIndex`: int

<a id="getpartymembercount"></a>

#### `GetPartyMemberCount()` - Routine 126

- `126. GetPartyMemberCount`
- GetPartyMemberCount
- Returns a count of how many members are in the party including the player character

<a id="isnpcpartymember"></a>

#### `IsNPCPartyMember(nNPC)` - Routine 699

- `699. IsNPCPartyMember`
- Returns if a given NPC constant is in the party currently

- `nNPC`: int

<a id="isobjectpartymember"></a>

#### `IsObjectPartyMember(oCreature)` - Routine 576

- `576. IsObjectPartyMember`
- Returns whether a specified creature is a party member
- IsObjectPartyMember

- `oCreature`: object

<a id="removefromparty"></a>

#### `RemoveFromParty(oPC)` - Routine 573

- `573. RemoveFromParty`
- Remove oPC from their current party. This will only work on a PC.
- - oPC: removes this player from whatever party they're currently in.

- `oPC`: object

<a id="removepartymember"></a>

#### `RemovePartyMember(nNPC)` - Routine 575

- `575. RemovePartyMember`
- Removes a creature from the party
- Returns whether the removal was syccessful
- RemovePartyMember

- `nNPC`: int

<a id="setpartyaistyle"></a>

#### `SetPartyAIStyle(nStyle)` - Routine 706

- `706. SetPartyAIStyle`
- Sets the party ai style

- `nStyle`: int

<a id="setpartyleader"></a>

#### `SetPartyLeader(nNPC)` - Routine 13

- `13. SetPartyLeader`
- Sets (by NPC constant) which party member should be the controlled
- character

- `nNPC`: int

<a id="showpartyselectiongui"></a>

#### `ShowPartySelectionGUI(sExitScript, nForceNPC1, nForceNPC2)` - Routine 712

- `712. ShowPartySelectionGUI`
- ShowPartySelectionGUI
- Brings up the party selection GUI for the player to
- select the members of the party from
- if exit script is specified, will be executed when
- the GUI is exited

- `sExitScript`: string (default: ``)
- `nForceNPC1`: int
- `nForceNPC2`: int

<a id="switchplayercharacter"></a>

#### `SwitchPlayerCharacter(nNPC)` - Routine 11

- `11. SwitchPlayerCharacter`
- Switches the main character to a specified NPC
- -1 specifies to switch back to the original PC

- `nNPC`: int

### Player Character Functions

See [Player Character Functions](NSS-Shared-Functions-Player-Character-Functions) for detailed documentation.

### Skills and Feats

See [Skills and Feats](NSS-Shared-Functions-Skills-and-Feats) for detailed documentation.

### Sound and Music Functions

See [Sound and Music Functions](NSS-Shared-Functions-Sound-and-Music-Functions) for detailed documentation.

## K1-Only Functions

<!-- K1_ONLY_FUNCTIONS_START -->

### Other Functions

See [Other Functions](NSS-K1-Only-Functions-Other-Functions) for detailed documentation.

## TSL-Only Functions

<!-- TSL_ONLY_FUNCTIONS_START -->

### Actions

See [Actions](NSS-TSL-Only-Functions-Actions) for detailed documentation.

### Class System

See [Class System](NSS-TSL-Only-Functions-Class-System) for detailed documentation.

### Combat Functions

See [Combat Functions](NSS-TSL-Only-Functions-Combat-Functions) for detailed documentation.

### Dialog and Conversation Functions

See [Dialog and Conversation Functions](NSS-TSL-Only-Functions-Dialog-and-Conversation-Functions) for detailed documentation.

### Effects System

See [Effects System](NSS-TSL-Only-Functions-Effects-System) for detailed documentation.

### Global Variables

See [Global Variables](NSS-TSL-Only-Functions-Global-Variables) for detailed documentation.

### Item Management

See [Item Management](NSS-TSL-Only-Functions-Item-Management) for detailed documentation.

### Object Query and Manipulation

See [Object Query and Manipulation](NSS-TSL-Only-Functions-Object-Query-and-Manipulation) for detailed documentation.

### Other Functions

See [Other Functions](NSS-TSL-Only-Functions-Other-Functions) for detailed documentation.

### Party Management

<a id="addavailablepupbyobject"></a>

#### `AddAvailablePUPByObject(nPUP, oPuppet)`

- 837
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- creature ID
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `oPuppet`: object

<a id="addavailablepupbytemplate"></a>

#### `AddAvailablePUPByTemplate(nPUP, sTemplate)`

- 836
- RWT-OEI 07/17/04
- This function adds a Puppet to the Puppet Table by
- template.
- Returns 1 if successful, 0 if there was an error

- `nPUP`: int
- `sTemplate`: string

<a id="addpartypuppet"></a>

#### `AddPartyPuppet(nPUP, oidCreature)`

- 840
- RWT-OEI 07/18/04
- This adds an existing puppet object to the party. The
- puppet object must already exist via SpawnAvailablePUP
- and must already be available via AddAvailablePUP*

- `nPUP`: int
- `oidCreature`: object

<a id="getispartyleader"></a>

#### `GetIsPartyLeader(oCharacter)`

- 844
- RWT-OEI 07/21/04
- Returns TRUE if the object ID passed is the character
- that the player is actively controlling at that point.
- Note that this function is *NOT* able to return correct

- `oCharacter`: object

<a id="getpartyleader"></a>

#### `GetPartyLeader()`

- 845
- RWT-OEI 07/21/04
- Returns the object ID of the character that the player
- is actively controlling. This is the 'Party Leader'.
- Returns object Invalid on error

<a id="removenpcfrompartytobase"></a>

#### `RemoveNPCFromPartyToBase(nNPC)`

- 846
- JAB-OEI 07/22/04
- Will remove the CNPC from the 3 person party, and remove
- him/her from the area, effectively sending the CNPC back
- to the base. The CNPC data is still stored in the

- `nNPC`: int

### Player Character Functions

See [Player Character Functions](NSS-TSL-Only-Functions-Player-Character-Functions) for detailed documentation.

### Skills and Feats

See [Skills and Feats](NSS-TSL-Only-Functions-Skills-and-Feats) for detailed documentation.

### Sound and Music Functions

See [Sound and Music Functions](NSS-TSL-Only-Functions-Sound-and-Music-Functions) for detailed documentation.

## Shared Constants (K1 & TSL)

<!-- SHARED_CONSTANTS_START -->

### Ability Constants

See [Ability Constants](NSS-Shared-Constants-Ability-Constants) for detailed documentation.

### Alignment Constants

See [Alignment Constants](NSS-Shared-Constants-Alignment-Constants) for detailed documentation.

### Class Type Constants

See [Class Type Constants](NSS-Shared-Constants-Class-Type-Constants) for detailed documentation.

### Inventory Constants

See [Inventory Constants](NSS-Shared-Constants-Inventory-Constants) for detailed documentation.

### NPC Constants

See [NPC Constants](NSS-Shared-Constants-NPC-Constants) for detailed documentation.

### Object Type Constants

See [Object Type Constants](NSS-Shared-Constants-Object-Type-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-Shared-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-Shared-Constants-Planet-Constants) for detailed documentation.

### Visual Effects (VFX)

See [Visual Effects (VFX)](NSS-Shared-Constants-Visual-Effects-(VFX)) for detailed documentation.

## K1-Only Constants

<!-- K1_ONLY_CONSTANTS_START -->

### NPC Constants

See [NPC Constants](NSS-K1-Only-Constants-NPC-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-K1-Only-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-K1-Only-Constants-Planet-Constants) for detailed documentation.

## TSL-Only Constants

<!-- TSL_ONLY_CONSTANTS_START -->

### Class Type Constants

See [Class Type Constants](NSS-TSL-Only-Constants-Class-Type-Constants) for detailed documentation.

### Inventory Constants

See [Inventory Constants](NSS-TSL-Only-Constants-Inventory-Constants) for detailed documentation.

### NPC Constants

See [NPC Constants](NSS-TSL-Only-Constants-NPC-Constants) for detailed documentation.

### Other Constants

See [Other Constants](NSS-TSL-Only-Constants-Other-Constants) for detailed documentation.

### Planet Constants

See [Planet Constants](NSS-TSL-Only-Constants-Planet-Constants) for detailed documentation.

### Visual Effects (VFX)

See [Visual Effects (VFX)](NSS-TSL-Only-Constants-Visual-Effects-(VFX)) for detailed documentation.

## KOTOR Library Files

<!-- KOTOR_LIBRARY_START -->

<a id="k_inc_cheat"></a>

#### `k_inc_cheat`

**Description**: :: k_inc_cheat

**Usage**: `#include "k_inc_cheat"`

**Source Code**:

```nss
//:: k_inc_cheat
/*
    This will be localized area for all
    Cheat Bot scripting.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Takes a PLANET_ Constant
void CH_SetPlanetaryGlobal(int nPlanetConstant);
//Makes the specified party member available to the PC
void CH_SetPartyMemberAvailable(int nNPC);
//::///////////////////////////////////////////////
//:: Set Planet Local
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    VARIABLE = K_CURRENT_PLANET
        Endar Spire     5
        Taris           10
        Dantooine       15
        --Kashyyk       20
        --Manaan        25
        --Korriban      30
        --Tatooine      35
        Leviathan       40
        Unknown World   45
        Star Forge      50
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 16, 2002
//:://////////////////////////////////////////////
void CH_SetPlanetaryGlobal(int nPlanetConstant)
{
    if(nPlanetConstant == PLANET_ENDAR_SPIRE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 5);
    }
    else if(nPlanetConstant == PLANET_TARIS)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 10);
    }
    else if(nPlanetConstant == PLANET_DANTOOINE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 15);
    }
    else if(nPlanetConstant == PLANET_KASHYYYK)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 20);
... (77 more lines)
```

<a id="k_inc_dan"></a>

#### `k_inc_dan`

**Description**: Dan

**Usage**: `#include "k_inc_dan"`

**Source Code**:

```nss
#include "k_inc_generic"
#include "k_inc_utility"
int ROMANCE_DONE = 4;
int JUHANI_RESCUED = 1;
int JEDI_TRAINING_DONE = 7;
int JEDI_PATH_GUARDIAN = 1;
int JEDI_PATH_SENTINEL = 2;
int JEDI_PATH_CONSULAR = 3;
int DROID_STARTED = 1;
int DROID_DESTROYED = 2;
int DROID_DECEIVED = 3;
int DROID_RETURNED = 4;
int DROID_HELPED = 5;
int DROID_FINISHED = 6;
string sBastilaTag = "bastila";
string sCarthTag = "carth";
string sCouncilTag = "dan13_WP_council";
string SABER_BLUE = "g_w_lghtsbr01";
string SABER_GREEN = "g_w_lghtsbr03";
string SABER_GOLD = "g_w_lghtsbr04";
string WANDERING_HOUND_TAG = "dan_wanderhound";
//places an instance of a character based on the tag/template
// **TAG MUST BE THE SAME AS TEMPLATE**
void PlaceNPC(string sTag, string sLocation = "");
//Get Carth's Object
object GetCarth();
//Gets Bastila's object
object GetBastila();
//gets the center of the council chamber
vector GetChamberCenter();
// creature move along a waypoint path. Not interuptable.
void PlotMove(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
// creature move along a waypoint path. Not interuptable. Destroys self at the end
void PlotLeave(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
// returns true is a trigger has not been fired yet
// intended for one shot triggers
int HasNeverTriggered();
//returns true if, on Korriban, the player has convinced Yuthura to come to Dantooine.
int YuthuraHasDefected();
//Sets the progression of the Elise plot on Dantooine
void SetElisePlot(int nValue);
// returns true if the player has started the Elise plot
int ElisePlotStarted();
// returns true if the player has agreed to help the droid after it has returned to elise
int GetDroidHelped();
// returns true if c369 has been spoken to
int GetEliseDroidMet();
//  the Elise plot has not started yet
int GetElisePlotNeverStared();
// returns true if Elise has gone to the Jedi compund
... (283 more lines)
```

<a id="k_inc_debug"></a>

#### `k_inc_debug`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_debug"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Debug Include
//:: k_inc_debug
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This contains the functions for inserting
    debug information into the scripts.
    This include will use Db as its two letter
    function prefix.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
//Inserts a print string into the log file for debugging purposes.
void Db_MyPrintString(string sString);
//Makes the object running the script say a speak string.
void Db_MySpeakString(string sString);
//Makes the nearest PC say a speakstring.
void Db_AssignPCDebugString(string sString);
//Basically, a wrapper for AurPostString
void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0);
//::///////////////////////////////////////////////
//:: Debug Print String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Inserts a print string into the log file for
    debugging purposes.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
void Db_MyPrintString(string sString)
{
    if(!ShipBuild())
    {
        PrintString(sString);
    }
}
//::///////////////////////////////////////////////
//:: Debug Speak String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Makes the object running the script say a
    speak string.
*/
... (47 more lines)
```

<a id="k_inc_drop"></a>

#### `k_inc_drop`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_drop"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Treasure drop Include
//:: k_inc_drop
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
// Contains the functions for handling creatures dropping random treasure
//Only human creatures not of the beast subrace willdrop treasure dependant
//on their hit dice
//:://////////////////////////////////////////////
//:: Created By: Aidan Scanlan On: 02/06/03
//:://////////////////////////////////////////////
int DR_HIGH_LEVEL = 15;
int DR_MEDIUM_LEVEL = 10;
int DR_LOW_LEVEL = 5;
int DR_SUBRACE_BEAST = 2;
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF);
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF);
// creates a low level treasure: med pack/repair, frag grenade, credits
void DR_CreateLowTreasure();
// creates midlevel treasure: adv-med/repair, any gredade, stims, credits
void DR_CreateMidTreasure();
// creates high treasure: adv stims, grenades, ultra med/repair, credits
void DR_CreateHighTreasure();
// Creates 1-4 credits
void DR_CreateFillerCredits();
/////////////////////////////////////////////////////////////////////////
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF)
{
    int nRace = GetRacialType(oTarget);
    int nFaction = GetStandardFaction(oTarget);
    int nSubRace = GetSubRace(oTarget);
    if(Random(4) == 0 &&
       nRace != RACIAL_TYPE_DROID &&
       nSubRace != DR_SUBRACE_BEAST)
    {
        //AurPostString("will drop",5,5,5.0);
        DR_CreateRandomTreasure(oTarget);
        return TRUE;
    }
    return FALSE;
}
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF)
{
    int nLevel = GetHitDice(oTarget);
    if (nLevel > DR_HIGH_LEVEL)
    {
... (185 more lines)
```

<a id="k_inc_ebonhawk"></a>

#### `k_inc_ebonhawk`

**Description**: :: k_inc_ebonhawk

**Usage**: `#include "k_inc_ebonhawk"`

**Source Code**:

```nss
//:: k_inc_ebonhawk
/*
     Ebon Hawk include file
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//This checks the Star Map plot to see if it is at state 30.
int EBO_CheckStarMapPlot();
//Bastila intiates conversation with the PC
void EBO_BastilaStartConversation2();
//Should Bastila intiates conversation with the PC
int EBO_ShouldBastilaStartConversation();
//Bastila intiates conversation with the PC
void EBO_BastilaStartConversation2();
//Advances the state of the bounty hunters plot after galaxy map selections are made
void EBO_PlayBountyHunterCutScene();
//Play the current cutscene for taking off from the planet.
void EBO_PlayTakeOff(int nCurrentPlanet);
//Play the corrent cutscene for landing on the planet.
void EBO_PlayLanding(int nDestination);
//Creates items on the PC based on the NPC they are talking to.
void EBO_CreateEquipmentOnPC();
//Checks if the PC needs equipment based on the NPC they are talking to.
int EBO_GetIsEquipmentNeeded();
//Determines the number items held with specific tags
int EBO_CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "");
//Returns the scripting constant for the current planet.
int EBO_GetCurrentPlanet();
//Returns the scripting constant for the future planet.
int EBO_GetFuturePlanet();
//Returns the correct K_CURRENT_PLANET value when a Planetary.2DA index is passed in.
int EBO_GetPlanetFrom2DA(int nPlanetIndex);
//Starts the correct sequence based on the planet being traveled to.
void EBO_PlayRenderSequence();
//::///////////////////////////////////////////////
//:: Check Star Map
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    If the variable K_STAR_MAP is at 30 and
    the variable K_CAPTURED_LEV = 5 then
    run the leviathan module.
    K_CAPTURED_LEV States
    0 = Pre Leviathan
    5 = Captured
    10 = Escaped
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 3, 2002
... (800 more lines)
```

<a id="k_inc_end"></a>

#### `k_inc_end`

**Description**: End

**Usage**: `#include "k_inc_end"`

**Source Code**:

```nss
#include "k_inc_utility"
#include "k_inc_generic"
string sTraskTag = "end_trask";
string sTraskWP = "endwp_tarsk01";
string sCarthTag = "Carth";
string SOLDIER_WEAPON = "g_w_blstrrfl001";
string SOLDIER_ITEM01 = "g_i_adrnaline003";
string SOLDIER_ITEM02 = "";
string SCOUT_WEAPON = "g_w_blstrpstl001";
string SCOUT_ITEM01 = "g_i_adrnaline002";
string SCOUT_ITEM02 = "g_i_implant101";
string SCOUNDREL_WEAPON = "g_w_blstrpstl001";
string SCOUNDREL_ITEM01 = "g_i_secspike01";
string SCOUNDREL_ITEM02 = "g_i_progspike01";
int ROOM3_DEAD = 3;
int ROOM5_DEAD = 4;
int ROOM7_DEAD = 2;
int TRASK_DEFAULT = -1;
int TRASK_MUST_GET_GEAR = 0;
int TRASK_GEAR_DONE = 1;
int TRASK_TARGET_DONE = 2;
int TRASK_MUST_EQUIP = 3;
int TRASK_EQUIP_DONE = 4;
int TRASK_MUST_MAP = 5;
int TRASK_MAP_DONE = 6;
int TRASK_MUST_SWITCH = 7;
int TRASK_SWITCH_DONE = 8;
int TRASK_SWITCH_REMIND = 9;
int TRASK_CARTH_BRIDGE = 10;
int TRASK_BRIDGE_DONE = 11;
int TRASK_MUST_DOOR = 12;
int TRASK_DOOR_DONE = 13;
int TRASK_ROOM3_DONE = 14;
int TRASK_MUST_MEDPACK = 15;
int TRASK_COMBAT_WARNING = 16;
int TRASK_COMBAT_WARNING2 = 17;
int TRASK_COMPUTER_DONE = 18;
int TRASK_MUST_DROID = 19;
int TRASK_DROID_DONE = 20;
int TRASK_MUST_MAP_02 = 21;
int TRASK_NOTHING_02 = 22;
//int TRASK_COMBAT_WARNING = 27;
int TRASK_LEVEL_INIT = 28;
int TRASK_MUST_LEVEL = 29;
int TRASK_PARTY_LEVEL = 30;
int TRASK_LEVEL_DONE = 31;
string LOCKER_TAG = "end_locker01";
string STEALTH_UNIT = "g_i_belt010";
//returns Trask's object id
object GetTrask();
... (194 more lines)
```

<a id="k_inc_endgame"></a>

#### `k_inc_endgame`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_endgame"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Name k_inc_endgame
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     This include houses all of the stunt/render
     calls for the end game. This will be for
     modules sta_m45ac and sta_m45ad.
*/
//:://////////////////////////////////////////////
//:: Created By: Brad Prince
//:: Created On: Mar 6, 2003
//:://////////////////////////////////////////////
///////////////////////
// LIGHT SIDE scenes //
///////////////////////
// SCENE 1 BO2 - Player kills Bastila on sta_m45ac
void ST_PlayBastilaLight();
// SCENE 2 C01 - Player returns after watching SCENE 1.
void ST_PlayReturnToStarForgeLight();
// SCENE 3 A - Star Forge under attack.
void ST_PlayStarForgeUnderAttack();
// SCENE 4 B - End game credits - Light.
void ST_PlayEndCreditsLight();
//////////////////////////////////////////////////
//////////////////////
// DARK SIDE scenes //
//////////////////////
// SCENE 1 B01 - Bastila leaves party to meditate before generator puzzle.
void ST_PlayBastilaDark();
// SCENE 2 C - Player returns after watching SCENE 1.
void ST_PlayReturnToStarForgeDark();
// SCENE 3 A - The Republic dies.
void ST_PlayRepublicDies();
// SCENE 4 B - The Sith Ceremony.
void ST_PlaySithCeremony();
// SCENE 5 C - End game credits - Dark.
void ST_PlayEndCreditsDark();
//////////////////////////////////////////////////
//                  FUNCTIONS                   //
//////////////////////////////////////////////////
///////////////////////
// LIGHT SIDE scenes //
///////////////////////
// SCENE 1 BO2 - Player kills Bastila on sta_m45ac
void ST_PlayBastilaLight()
{
    StartNewModule("STUNT_50a","", "50b");
}
// SCENE 2 C01 - Player returns after watching SCENE 1.
... (44 more lines)
```

<a id="k_inc_force"></a>

#### `k_inc_force`

**Description**: :: k_inc_force

**Usage**: `#include "k_inc_force"`

**Source Code**:

```nss
//:: k_inc_force
/*
    v1.0
    Force Powers Include for KOTOR
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
float fLightningDuration = 1.0;
//These variables are set in the script run area.
int SWFP_PRIVATE_SAVE_TYPE;
int SWFP_PRIVATE_SAVE_VERSUS_TYPE;
int SWFP_DAMAGE;
int SWFP_DAMAGE_TYPE;
int SWFP_DAMAGE_VFX;
int SWFP_HARMFUL;
int SWFP_SHAPE;
//Runs the script section for the particular force power.
void  Sp_RunForcePowers();
//Immunity and Resist Spell check for the force power.
//The eDamage checks whether the target is immune to the damage effect
int Sp_BlockingChecks(object oTarget, effect eEffect, effect eEffect2, effect eDamage);
//Makes the necessary saving throws
int Sp_MySavingThrows(object oTarget);
//Remove an effect of a specific type
void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget);
//Remove an effect from a specific force power.
void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget);
// Delays the application of a spell effect by an amount determined by distance.
float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget);
//Randomly delays the effect application for a default of 0.0 to 0.75 seconds
float Sp_GetRandomDelay(float fMinimumTime = 0.0, float MaximumTime = 0.75);
//Gets a saving throw appropriate to the jedi using the force power.
int Sp_GetJediDCSave();
///Apply effects in a sphere shape.
void Sp_SphereSaveHalf(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
//Apply effects to a single target.
void Sp_SingleTarget(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effect to an area and negate on a save.
void Sp_SphereBlocking(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
// /Apply effect to an object and negate on a save.
void Sp_SingleTargetBlocking(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effects for a for power.
void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget);
//Apply effects to targets.
void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL);
//Removes all effects from the spells , Knights Mind, Mind Mastery and Battle Meditation
void Sp_RemoveBuffSpell();
//Prints a string for the spell stript
void SP_MyPrintString(string sString);
//Posts a string for the spell script
... (2163 more lines)
```

<a id="k_inc_generic"></a>

#### `k_inc_generic`

**Description**: :: k_inc_generic

**Usage**: `#include "k_inc_generic"`

**Source Code**:

```nss
//:: k_inc_generic
/*
    v1.5
    Generic Include for KOTOR
    Post Clean Up as of March 3, 2003
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_gensupport"
#include "k_inc_walkways"
#include "k_inc_drop"
struct tLastRound
{
    int nLastAction;
    int nLastActionID;
    int nLastTalentCode;
    object oLastTarget;
    int nTalentSuccessCode;
    int nIsLastTargetDebil;
    int nLastCombo;
    int nLastComboIndex;
    int nCurrentCombo;
    int nBossSwitchCurrent;
};
struct tLastRound tPR;
//LOCAL BOOLEANS RANGE FROM 0 to 96
int AMBIENT_PRESENCE_DAY_ONLY = 1;        //POSSIBLE CUT
int AMBIENT_PRESENCE_NIGHT_ONLY = 2;      //POSSIBLE CUT
int AMBIENT_PRESENCE_ALWAYS_PRESENT = 3;
int SW_FLAG_EVENT_ON_PERCEPTION =   20;
int SW_FLAG_EVENT_ON_ATTACKED   =   21;
int SW_FLAG_EVENT_ON_DAMAGED    =   22;
int SW_FLAG_EVENT_ON_FORCE_AFFECTED = 23;
int SW_FLAG_EVENT_ON_DISTURBED = 24;
int SW_FLAG_EVENT_ON_COMBAT_ROUND_END = 25;
int SW_FLAG_EVENT_ON_DIALOGUE    = 26;
int SW_FLAG_EVENT_ON_DEATH       = 27;
int SW_FLAG_EVENT_ON_HEARTBEAT   = 28;
//int SW_FLAG_AMBIENT_ANIMATIONS = 29;          located in k_inc_walkways
//int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 30;   located in k_inc_walkways
int SW_FLAG_FAST_BUFF            = 31;   //POSSIBLE CUT
int SW_FLAG_ASC_IS_BUSY          = 32;   //POSSIBLE CUT
int SW_FLAG_ASC_AGGRESSIVE_MODE  = 33;   //POSSIBLE CUT
int SW_FLAG_AMBIENT_DAY_ONLY     = 40;   //POSSIBLE CUT
int SW_FLAG_AMBIENT_NIGHT_ONLY   = 43;   //POSSIBLE CUT
int SW_FLAG_EVENT_ON_SPELL_CAST_AT = 44;
int SW_FLAG_EVENT_ON_BLOCKED     = 45;
int SW_FLAG_ON_DIALOGUE_COMPUTER = 48;
int SW_FLAG_FORMATION_POSITION_0 = 49;   //POSSIBLE CUT
int SW_FLAG_FORMATION_POSITION_1 = 50;   //POSSIBLE CUT
... (2182 more lines)
```

<a id="k_inc_gensupport"></a>

#### `k_inc_gensupport`

**Description**: :: k_inc_gensupport

**Usage**: `#include "k_inc_gensupport"`

**Source Code**:

```nss
//:: k_inc_gensupport
/*
    v1.0
    Support Include for k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//BOSS ATTACK TYPES
int SW_BOSS_ATTACK_TYPE_GRENADE = 1;
int SW_BOSS_ATTACK_TYPE_FORCE_POWER = 2;
int SW_BOSS_ATTACK_TYPE_NPC = 3;
int SW_BOSS_ATTACK_TYPE_PC = 4;
int SW_BOSS_ATTACK_ANY = 5;
int SW_BOSS_ATTACK_DROID = 6;
//LOCAL NUMBERS
int SW_NUMBER_COMBO_ROUTINE = 3;
int SW_NUMBER_COMBO_INDEX = 4;
int SW_NUMBER_LAST_COMBO = 5;
int SW_NUMBER_ROUND_COUNTER = 6;
int SW_NUMBER_COMBAT_ZONE = 7;
//COMBO CONSTANTS
int SW_COMBO_RANGED_FEROCIOUS = 1;
int SW_COMBO_RANGED_AGGRESSIVE = 2;
int SW_COMBO_RANGED_DISCIPLINED = 3;
int SW_COMBO_RANGED_CAUTIOUS = 4;
int SW_COMBO_MELEE_FEROCIOUS = 5;
int SW_COMBO_MELEE_AGGRESSIVE = 6;
int SW_COMBO_MELEE_DISCIPLINED = 7;
int SW_COMBO_MELEE_CAUTIOUS = 8;
int SW_COMBO_BUFF_PARTY = 9;
int SW_COMBO_BUFF_DEBILITATE = 10;
int SW_COMBO_BUFF_DAMAGE = 11;
int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;
int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;
int SW_COMBO_SITH_ATTACK = 14;
int SW_COMBO_BUFF_ATTACK = 15;
int SW_COMBO_SITH_CONFOUND = 16;
int SW_COMBO_JEDI_SMITE = 17;
int SW_COMBO_SITH_TAUNT = 18;
int SW_COMBO_SITH_BLADE = 19;
int SW_COMBO_SITH_CRUSH = 20;
int SW_COMBO_JEDI_CRUSH = 21;
int SW_COMBO_SITH_BRUTALIZE = 22;
int SW_COMBO_SITH_DRAIN = 23;
int SW_COMBO_SITH_ESCAPE = 24;
int SW_COMBO_JEDI_BLITZ = 25;
int SW_COMBO_SITH_SPIKE = 26;
int SW_COMBO_SITH_SCYTHE = 27;
... (3004 more lines)
```

<a id="k_inc_kas"></a>

#### `k_inc_kas`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_kas"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Include
//:: k_inc_kas
//:: Copyright (c) 2002 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This is the include file for Kashyyyk.
*/
//:://////////////////////////////////////////////
//:: Created By: John Winski
//:: Created On: July 29, 2002
//:://////////////////////////////////////////////
#include "k_inc_utility"
#include "k_inc_generic"
int GetGorwookenSpawnGlobal()
{
    return GetGlobalBoolean("kas_SpawnGorwook");
}
void SetGorwookenSpawnGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_SpawnGorwook", bValue);
    }
    return;
}
int GetEliBeenKilledGlobal()
{
    return GetGlobalBoolean("kas_elikilled");
}
void SetEliBeenKilledGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_elikilled", bValue);
    }
    return;
}
int GetJaarakConfessedGlobal()
{
    return GetGlobalBoolean("kas_JaarakConfessed");
}
void SetJaarakConfessedGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("kas_JaarakConfessed", bValue);
    }
    return;
}
... (1263 more lines)
```

<a id="k_inc_lev"></a>

#### `k_inc_lev`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_lev"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_lev
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for leviathan
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
//mark an object for cleanup by the LEV_CleanupDeadObjects function
void LEV_MarkForCleanup(object obj);
//destroy all objects whose PLOT_10 flag has been set
void LEV_CleanupDeadObjects(object oArea);
//mark object for cleanup and move to nearest exit
void LEV_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);
//fill container with treasure from table
void LEV_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
//strip inventory from oTarget and put it in oDest
void LEV_StripCharacter(object oTarget,object oDest);
//::///////////////////////////////////////////////
//:: LEV_MarkForCleanup
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//mark an object for cleanup by the TAR_CleanupDeadObjects function
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
void LEV_MarkForCleanup(object obj)
{
  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);
}
//::///////////////////////////////////////////////
//:: LEV_CleanupDeadObjects
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//destroy all objects whose PLOT_10 flag has been set
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 15, 2002
//:://////////////////////////////////////////////
void LEV_CleanupDeadObjects(object oArea)
... (117 more lines)
```

<a id="k_inc_man"></a>

#### `k_inc_man`

**Description**: :: Name

**Usage**: `#include "k_inc_man"`

**Source Code**:

```nss
//:: Name
/*
     Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
#include "k_inc_utility"
int SHIP_TAKEOFF_CUTSCENE = 1;
int SHIP_LANDING_CUTSCENE = 2;
int NONE = 0;
int QUEEDLE = 1;
int CASSANDRA = 2;
int JAX = 3;
int QUEEDLE_CHAMP = 4;
int QUEEDLE_TIME = 3012;
int CASSANDRA_TIME = 2702;
int JAX_TIME = 2548;
int CHAMP_TIME = 2348;
int PLOT_HARVEST_STOPPED = 3;
int PLOT_KOLTO_DESTROYED = 4;
//effect EFFECT_STEAM = EffectDamage(15);
int STEAM_DAMAGE_AMOUNT = 25;
string RACE_DEFAULT = GetStringByStrRef(32289);
string STEAM_PLACEABLE = "man27_visstm0";
string ROLAND_TAG = "man26_repdip";
void PlaceShip(string sTag,location lLoc);
void RemoveShip(string sTag);
void PlaceNPC(string sTag);
// switches current player models to envirosuit models.
void DonSuits();
// switches the envirosuit model back to the regular player models
void RemoveSuits();
// deactivates all turrets on the map with the corresponding tag
// if no tag is given it will default to the tag of the calling object
void DeactivateTurrets(string sTag = "");
//used to make a given condition only fire once
//***note uses SW_PLOT_BOOLEAN_10***
int HasNeverTriggered();
// Sets a global to track who the player is racing
void SetOpponent(int nOpponent);
//Returns thte current race opponent
int GetOpponent();
//Sets a cutom token in racetime format
void SetTokenRaceTime(int nToken, int nRacerTime);
//returns the main plot global for Manaan
int GetManaanMainPlotVariable();
// returns true if poison has been released if the Hrakert rift
int KoltoDestroyed();
// Removes instances and deactives Selkath encounters
... (748 more lines)
```

<a id="k_inc_stunt"></a>

#### `k_inc_stunt`

**Description**: :: Stunt/Render Include

**Usage**: `#include "k_inc_stunt"`

**Source Code**:

```nss
//:: Stunt/Render Include
/*
     This Include File runs
     the stunt and cutscenes
     for the game.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//INDIVIDUAL STUNT MODULE CALLS ******************************************************************************************************
//LEV_A: Pulled out of hyperspace by the Leviathan, load STUNT_16
void ST_PlayLevCaptureStunt();
//LEV_A: Capture by the Leviathan, load ebo_m40aa
void ST_PlayLevCaptureStunt02();
//Load Turret Module Opening 07_3
void ST_PlayStuntTurret_07_3();
//Plays the Bastila torture scene
void ST_PlayBastilaTorture();
//Load Turret Module Opening 07_4
void ST_PlayStuntTurret_07_4();
//Load Leviathan Bombardment Stunt_06 covered by Render 5
void ST_PlayTarisEscape();
//Load Stunt_07 covered by Render 6a and 05_1C
void ST_PlayTarisEscape02();
//Load the Fighter Mini-Game m12ab covered by Render 07_3
void ST_PlayTarisEscape03();
//Load Dantooine module covered by hyperspace and dant landing
void ST_PlayDantooineLanding();
//Leaving Dantooine for the first time, going to STUNT_12 covered by Dant takeoff and hyperspace
void ST_PlayDantooineTakeOff();
//Plays the correct vision based on the value of K_FUTURE_PLANET from a stunt module
void ST_PlayVisionStunt();
//Plays the correct vision based on the value of K_FUTURE_PLANET with a take-off
void ST_PlayVisionStunt02();
//Plays the starforge approach
void ST_PlayStarForgeApproach();
//Plays the Damage Ebon Hawk Stunt scene
void ST_PlayStunt35();
//Shows the crash landing on the Unknown World
void ST_PlayUnknownWorldLanding();
//Shows the take-off from the Unknown World
void ST_PlayUnknownWorldTakeOff();
//Landing on the Star Forge
void ST_PlayStarForgeLanding();
//Goes to the Leviathan Mini-Game covered by the Escape Render
void ST_PlayLeviathanEscape01();
//UBER FUNCTIONS *********************************************************************************************************************
//This determines what to play after a Fighter Mini Game is run
void ST_PlayPostTurret();
//Play the appropriate take off render
string ST_GetTakeOffRender();
... (685 more lines)
```

<a id="k_inc_switch"></a>

#### `k_inc_switch`

**Description**: :: k_inc_switch

**Usage**: `#include "k_inc_switch"`

**Source Code**:

```nss
//:: k_inc_switch
/*
     A simple include defining all of the
     events in the game as constants.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//DEFAULT AI EVENTS
int KOTOR_DEFAULT_EVENT_ON_HEARTBEAT           = 1001;
int KOTOR_DEFAULT_EVENT_ON_PERCEPTION          = 1002;
int KOTOR_DEFAULT_EVENT_ON_COMBAT_ROUND_END    = 1003;
int KOTOR_DEFAULT_EVENT_ON_DIALOGUE            = 1004;
int KOTOR_DEFAULT_EVENT_ON_ATTACKED            = 1005;
int KOTOR_DEFAULT_EVENT_ON_DAMAGE              = 1006;
int KOTOR_DEFAULT_EVENT_ON_DEATH               = 1007;
int KOTOR_DEFAULT_EVENT_ON_DISTURBED           = 1008;
int KOTOR_DEFAULT_EVENT_ON_BLOCKED             = 1009;
int KOTOR_DEFAULT_EVENT_ON_FORCE_AFFECTED      = 1010;
int KOTOR_DEFAULT_EVENT_ON_GLOBAL_DIALOGUE_END = 1011;
int KOTOR_DEFAULT_EVENT_ON_PATH_BLOCKED        = 1012;
//HENCHMEN AI EVENTS
int KOTOR_HENCH_EVENT_ON_HEARTBEAT           = 2001;
int KOTOR_HENCH_EVENT_ON_PERCEPTION          = 2002;
int KOTOR_HENCH_EVENT_ON_COMBAT_ROUND_END    = 2003;
int KOTOR_HENCH_EVENT_ON_DIALOGUE            = 2004;
int KOTOR_HENCH_EVENT_ON_ATTACKED            = 2005;
int KOTOR_HENCH_EVENT_ON_DAMAGE              = 2006;
int KOTOR_HENCH_EVENT_ON_DEATH               = 2007;
int KOTOR_HENCH_EVENT_ON_DISTURBED           = 2008;
int KOTOR_HENCH_EVENT_ON_BLOCKED             = 2009;
int KOTOR_HENCH_EVENT_ON_FORCE_AFFECTED      = 2010;
int KOTOR_HENCH_EVENT_ON_GLOBAL_DIALOGUE_END = 2011;
int KOTOR_HENCH_EVENT_ON_PATH_BLOCKED        = 2012;
int KOTOR_HENCH_EVENT_ON_ENTER_5m            = 2013;
int KOTOR_HENCH_EVENT_ON_EXIT_5m             = 2014;
//MISC AI EVENTS
int KOTOR_MISC_DETERMINE_COMBAT_ROUND                = 3001;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_PC          = 3002;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_INDEX_ZERO  = 3003;

```

<a id="k_inc_tar"></a>

#### `k_inc_tar`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_tar"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_tar
//:: k_inc_tar
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for taris
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: July 16, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
//performs a standard creature transformation where the original creature
//is destroyed and a new creature is put in its place.  returns a reference
//to the new creature.
object TAR_TransformCreature(object oTarget = OBJECT_INVALID,string sTemplate = "");
//test routine for walking waypoints
void TAR_WalkWaypoints();
//mark an object for cleanup by the TAR_CleanupDeadObjects function
void TAR_MarkForCleanup(object obj = OBJECT_SELF);
//destroy all objects whose PLOT_10 flag has been set
void TAR_CleanupDeadObjects(object oArea);
//make object do an uninterruptible path move
void TAR_PlotMovePath(string sWayPointTag,int nFirst, int nLast, int nRun = FALSE);
//make object do an uninterruptible move to an object
void TAR_PlotMoveObject(object oTarget,int nRun = FALSE);
//make object do an uninterruptible move to a location
void TAR_PlotMoveLocation(location lTarget,int nRun = FALSE);
//check for rukil's apprentice journal
int TAR_PCHasApprenticeJournal();
//return number of promised land journals player has
int TAR_GetNumberPromisedLandJournals();
//toggle the state of sith armor
void TAR_ToggleSithArmor();
//fill container with treasure from table
void TAR_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
//returns TRUE if object is wearing sith armor
int TAR_GetWearingSithArmor(object oTarget = OBJECT_INVALID);
//strip sith armor from party, equipping another appropriate item (if available)
//returns the sith armor object if it was being worn
object TAR_StripSithArmor();
//teleport party member
void TAR_TeleportPartyMember(object oPartyMember, location lDest);
//makes the sith armor equippable
void TAR_EnableSithArmor();
//strip all items from an object
void TAR_StripCharacter(object oTarget,object oDest);
//::///////////////////////////////////////////////
... (488 more lines)
```

<a id="k_inc_tat"></a>

#### `k_inc_tat`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_tat"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: Include
//:: k_inc_tat
//:: Copyright (c) 2002 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This is the include file for Tatooine.
*/
//:://////////////////////////////////////////////
//:: Created By: John Winski
//:: Created On: September 3, 2002
//:://////////////////////////////////////////////
#include "k_inc_utility"
#include "k_inc_generic"
// racer constants
int NONE = 0;
int GARM = 1;
int YUKA = 2;
int ZORIIS = 3;
// race time constants
int GARM_TIME = 2600;
int YUKA_TIME = 2470;
int ZORIIS_TIME = 2350;
string RACE_DEFAULT = GetStringByStrRef(32289);
int GetGammoreansDeadGlobal()
{
    return GetGlobalBoolean("tat_GammoreansDead");
}
void SetGammoreansDeadGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("tat_GammoreansDead", bValue);
    }
    return;
}
int GetMetKomadLodgeGlobal()
{
    return GetGlobalBoolean("tat_MetKomadLodge");
}
void SetMetKomadLodgeGlobal(int bValue)
{
    if (bValue == TRUE || bValue == FALSE)
    {
        SetGlobalBoolean("tat_MetKomadLodge", bValue);
    }
    return;
}
int GetSharinaAccusedGurkeGlobal()
{
... (2055 more lines)
```

<a id="k_inc_treasure"></a>

#### `k_inc_treasure`

**Description**: :: k_inc_treasure

**Usage**: `#include "k_inc_treasure"`

**Source Code**:

```nss
//:: k_inc_treasure
/*
     contains code for filling containers using treasure tables
*/
//:: Created By:  Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
//
//  March 15, 2003  J.B.
//      removed parts and spikes from tables
//
//constants for container types
int SWTR_DEBUG = TRUE;  //set to false to disable console/file logging
int SWTR_TABLE_CIVILIAN_CONTAINER = 1;
int SWTR_TABLE_MILITARY_CONTAINER_LOW = 2;
int SWTR_TABLE_MILITARY_CONTAINER_MID = 3;
int SWTR_TABLE_MILITARY_CONTAINER_HIGH = 4;
int SWTR_TABLE_CORPSE_CONTAINER_LOW = 5;
int SWTR_TABLE_CORPSE_CONTAINER_MID = 6;
int SWTR_TABLE_CORPSE_CONTAINER_HIGH = 7;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_LOW = 8;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_MID = 9;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_HIGH = 10;
int SWTR_TABLE_DROID_CONTAINER_LOW = 11;
int SWTR_TABLE_DROID_CONTAINER_MID = 12;
int SWTR_TABLE_DROID_CONTAINER_HIGH = 13;
int SWTR_TABLE_RAKATAN_CONTAINER = 14;
int SWTR_TABLE_SANDPERSON_CONTAINER = 15;
//Fill an object with treasure from the specified table
//This is the only function that should be used outside this include file
void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE);
//for internal debugging use only, output string to the log file and console if desired
void SWTR_Debug_PostString(string sStr,int bConsole = TRUE,int x = 5,int y = 5,float fTime = 5.0)
{
  if(SWTR_DEBUG)
  {
    if(bConsole)
    {
      AurPostString("SWTR_DEBUG - " + sStr,x,y,fTime);
    }
    PrintString("SWTR_DEBUG - " + sStr);
  }
}
//return whether i>=iLow and i<=iHigh
int SWTR_InRange(int i,int iLow,int iHigh)
{
  if(i >= iLow && i <= iHigh)
  {
    return(TRUE);
  }
  else
... (773 more lines)
```

<a id="k_inc_unk"></a>

#### `k_inc_unk`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_unk"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: k_inc_unk
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
  include file for unknown world
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: Sept. 9, 2002
//:://////////////////////////////////////////////
#include "k_inc_debug"
#include "k_inc_utility"
#include "k_inc_generic"
//mark an object for cleanup by the UNK_CleanupDeadObjects function
void UNK_MarkForCleanup(object obj);
//destroy all objects whose PLOT_10 flag has been set
void UNK_CleanupDeadObjects(object oArea);
//mark object for cleanup and move to nearest exit
void UNK_LeaveArea(object obj = OBJECT_SELF, int bRun = FALSE);
//test if red rakata are hostile
int UNK_GetRedRakataHostile();
//test if black rakata are hostile
int UNK_GetBlackRakataHostile();
//make red rakatans hostile
void UNK_SetRedRakataHostile();
//make black rakatans hostile
void UNK_SetBlackRakataHostile();
//make black rakatans neutral
void UNK_SetBlackRakataNeutral();
//fill container with treasure from table
void UNK_AddTreasureToContainer(object oContainer,int iTable,int iAmount);
// unavoidable damage to all within radius
void UNK_RakDefence(string sObjectTag, float fDistance, int bIndiscriminant = TRUE);
//::///////////////////////////////////////////////
//:: UNK_MarkForCleanup
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
//mark an object for cleanup by the TAR_CleanupDeadObjects function
*/
//:://////////////////////////////////////////////
//:: Created By: Jason Booth
//:: Created On: August 26, 2002
//:://////////////////////////////////////////////
void UNK_MarkForCleanup(object obj)
{
  UT_SetPlotBooleanFlag(obj,SW_PLOT_BOOLEAN_10,TRUE);
}
//::///////////////////////////////////////////////
... (254 more lines)
```

<a id="k_inc_utility"></a>

#### `k_inc_utility`

**Description**: :: k_inc_utility

**Usage**: `#include "k_inc_utility"`

**Source Code**:

```nss
//:: k_inc_utility
/*
    common functions used throughout various scripts
    Modified by Peter T. 17/03/03
    - Added UT_MakeNeutral2(), UT_MakeHostile1(), UT_MakeFriendly1() and UT_MakeFriendly2()
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
// Plot Flag Constants.
int SW_PLOT_BOOLEAN_01 = 0;
int SW_PLOT_BOOLEAN_02 = 1;
int SW_PLOT_BOOLEAN_03 = 2;
int SW_PLOT_BOOLEAN_04 = 3;
int SW_PLOT_BOOLEAN_05 = 4;
int SW_PLOT_BOOLEAN_06 = 5;
int SW_PLOT_BOOLEAN_07 = 6;
int SW_PLOT_BOOLEAN_08 = 7;
int SW_PLOT_BOOLEAN_09 = 8;
int SW_PLOT_BOOLEAN_10 = 9;
int SW_PLOT_HAS_TALKED_TO = 10;
int SW_PLOT_COMPUTER_OPEN_DOORS = 11;
int SW_PLOT_COMPUTER_USE_GAS = 12;
int SW_PLOT_COMPUTER_DEACTIVATE_TURRETS = 13;
int SW_PLOT_COMPUTER_DEACTIVATE_DROIDS = 14;
int SW_PLOT_COMPUTER_MODIFY_DROID = 15;
int SW_PLOT_REPAIR_WEAPONS = 16;
int SW_PLOT_REPAIR_TARGETING_COMPUTER = 17;
int SW_PLOT_REPAIR_SHIELDS = 18;
int SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE = 19;
// UserDefined events
int HOSTILE_RETREAT = 1100;
//Alignment Adjustment Constants
int SW_CONSTANT_DARK_HIT_HIGH = -6;
int SW_CONSTANT_DARK_HIT_MEDIUM = -5;
int SW_CONSTANT_DARK_HIT_LOW = -4;
int SW_CONSTANT_LIGHT_HIT_LOW = -2;
int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;
int SW_CONSTANT_LIGHT_HIT_HIGH = 0;
// Returns a pass value based on the object's level and DC rating of 0, 1, or 2 (easy, medium, difficult)
// December 20 2001: Changed so that the difficulty is determined by the
// NPC's Hit Dice
int AutoDC(int DC, int nSkill, object oTarget);
//  checks for high charisma
int IsCharismaHigh();
//  checks for low charisma
int IsCharismaLow();
//  checks for normal charisma
int IsCharismaNormal();
//  checks for high intelligence
int IsIntelligenceHigh();
... (2759 more lines)
```

<a id="k_inc_walkways"></a>

#### `k_inc_walkways`

**Description**: :: k_inc_walkways

**Usage**: `#include "k_inc_walkways"`

**Source Code**:

```nss
//:: k_inc_walkways
/*
    v1.0
    Walk Way Points Include
    used by k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
int WALKWAYS_CURRENT_POSITION = 0;
int WALKWAYS_END_POINT = 1;
int WALKWAYS_SERIES_NUMBER = 2;
int    SW_FLAG_AMBIENT_ANIMATIONS    =    29;
int    SW_FLAG_AMBIENT_ANIMATIONS_MOBILE =    30;
int    SW_FLAG_WAYPOINT_WALK_ONCE    =    34;
int    SW_FLAG_WAYPOINT_WALK_CIRCULAR    =    35;
int    SW_FLAG_WAYPOINT_WALK_PATH    =    36;
int    SW_FLAG_WAYPOINT_WALK_STOP    =    37; //One to three
int    SW_FLAG_WAYPOINT_WALK_RANDOM    =    38;
int SW_FLAG_WAYPOINT_WALK_RUN    =   39;
int SW_FLAG_WAYPOINT_DIRECTION = 41;
int SW_FLAG_WAYPOINT_DEACTIVATE = 42;
int SW_FLAG_WAYPOINT_WALK_STOP_LONG = 46;
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 47;
//Makes OBJECT_SELF walk way points based on the spawn in conditions set out.
void GN_WalkWayPoints();
//Sets the series number from 01 to 99 on a creature so that the series number and not the creature's tag is used for walkway points
void GN_SetWalkWayPointsSeries(int nSeriesNumber);
//Sets Generic Spawn In Conditions
void GN_SetSpawnInCondition(int nFlag, int nState = TRUE);
//Gets the boolean state of a generic spawn in condition.
int GN_GetSpawnInCondition(int nFlag);
//Moves an object to the last waypoint in a series
void GN_MoveToLastWayPoint(object oToMove);
//Moves an object to a random point in the series
void GN_MoveToRandomWayPoint(object oToMove);
//Moves an object to a sepcific point in the series
void GN_MoveToSpecificWayPoint(object oToMove, int nArrayNumber);
//Determines the correct direction to proceed in a walkway points array.
int GN_GetWayPointDirection(int nEndArray, int nCurrentPosition);
//Should only be called from within SetListendingPatterns
void GN_SetUpWayPoints();
//Play an animation between way points.
void GN_PlayWalkWaysAnimation();
//Inserts a print string into the log file for debugging purposes for the walkways include.
void WK_MyPrintString(string sString);
//Are valid walkway points available
int GN_CheckWalkWays(object oTarget);
//::///////////////////////////////////////////////
... (566 more lines)
```

<a id="k_inc_zone"></a>

#### `k_inc_zone`

**Description**: :: k_inc_zones

**Usage**: `#include "k_inc_zone"`

**Source Code**:

```nss
//:: k_inc_zones
/*
     Zone including for controlling
     the chaining of creatures
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
//Function run by the trigger to catalog the control nodes followers
void ZN_CatalogFollowers();
//Checks zone conditional on creature to if they belong to the zone
int ZN_CheckIsFollower(object oController, object oTarget);
//Checks the distance and creatures around the PC to see if it should return home.
int ZN_CheckReturnConditions();
//Gets the followers to move back to the controller object
void ZN_MoveToController(object oController, object oFollower);
//Checks to see if a specific individual needs to return to the controller.
int ZN_CheckFollowerReturnConditions(object oTarget);
//::///////////////////////////////////////////////
//:: Catalog Zone Followers
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     Catalogs all creatures within
     the trigger area and marks
     them with an integer which
     is part of the creature's
     tag.
     Use local number SW_NUMBER_LAST_COMBO
     as a test. A new local number will
     be defined if the system works.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: April 7, 2003
//:://////////////////////////////////////////////
void ZN_CatalogFollowers()
{
    GN_PostString("FIRING", 10,10, 10.0);
    if(GetLocalBoolean(OBJECT_SELF, 10) == FALSE) //Has talked to boolean
    {
        string sZoneTag = GetTag(OBJECT_SELF);
        int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));
        //Set up creature followers
        object oZoneFollower = GetFirstInPersistentObject();
        while(GetIsObjectValid(oZoneFollower))
        {
            SetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE, nZoneNumber);
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower = " + GN_ReturnDebugName(oZoneFollower));
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower Zone # = " + GN_ITS(GetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE)));
... (110 more lines)
```

<!-- KOTOR_LIBRARY_END -->

## TSL Library Files

<!-- TSL_LIBRARY_START -->

<a id="a_global_inc"></a>

#### `a_global_inc`

**Description**: Global Inc

**Usage**: `#include "a_global_inc"`

**Source Code**:

```nss

//:: a_global_inc
/*
    parameter 1 = string identifier for a global number
    parameter 2 = amount to increment GetGlobalNumber(param1)
*/
//:: Created By: Anthony Davis
#include "k_inc_debug"
void main()
{
    string tString = GetScriptStringParameter();
    int tInt = GetScriptParameter( 1 );
    SetGlobalNumber(tString, GetGlobalNumber(tString) + tInt);
}

```

<a id="a_influence_inc"></a>

#### `a_influence_inc`

**Description**: a_influence_inc

**Usage**: `#include "a_influence_inc"`

**Source Code**:

```nss
// a_influence_inc
/* Parameter Count: 2
Increases an NPC's influence.
Param1 - The NPC value of the player whose influence is increased.
Param2 - magnitude of influence change:
    1 - low
    2 - medium
    3 - high
    all others - medium
NPC numbers, as specified in NPC.2da
0       Atton
1       BaoDur
2       Mand
3       g0t0
4       Handmaiden
5       hk47
6       Kreia
7       Mira
8       T3m4
9       VisasMarr
10      Hanharr
11      Disciple
*/
//
// KDS 06/16/04
void main()
{
int nInfluenceLow = 8;
int nInfluenceMedium = 8;
int nInfluenceHigh = 8;
int nNPC = GetScriptParameter(1);
int nImpact = GetScriptParameter(2);
int nInfluenceChange;
switch (nImpact)
{
    case 1:
        nInfluenceChange = nInfluenceLow;
        break;
    case 2:
        nInfluenceChange = nInfluenceMedium;
        break;
    case 3:
        nInfluenceChange = nInfluenceHigh;
        break;
    default:
        nInfluenceChange = nInfluenceMedium;
        break;
}
ModifyInfluence (nNPC, nInfluenceChange);
}
... (1 more lines)
```

<a id="a_localn_inc"></a>

#### `a_localn_inc`

**Description**: a_localn_inc

**Usage**: `#include "a_localn_inc"`

**Source Code**:

```nss
// a_localn_inc
// Parameter Count: 2
// Param1 - The local number # to increment (range 12-31)
// Param2 - the amount to increment Param1 by (default = 1)
// Param3 - Optional string parameter to refer to another object's local #
//
// KDS 06/15/04
// Modified TDE 7/31/04
#include "k_inc_debug"
#include "k_inc_utility"
void main()
{
    int nLocalNumber = GetScriptParameter( 1 );
    int nValue = GetScriptParameter ( 2 );
    // Added optional string parameter to refer to another object's local #
    string sTag = GetScriptStringParameter();
    object oObject;
    // If sTag is empty, use the object that called the script
    if ( sTag == "" ) oObject = OBJECT_SELF;
    else oObject = GetObjectByTag(sTag);
    if (nValue == 0) nValue = 1;
    SetLocalNumber(oObject, nLocalNumber,
        GetLocalNumber(oObject, nLocalNumber) + nValue);
}

```

<a id="k_inc_cheat"></a>

#### `k_inc_cheat`

**Description**: :: k_inc_cheat

**Usage**: `#include "k_inc_cheat"`

**Source Code**:

```nss
//:: k_inc_cheat
/*
    This will be localized area for all
    Cheat Bot scripting.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Takes a PLANET_ Constant
void CH_SetPlanetaryGlobal(int nPlanetConstant);
//Makes the specified party member available to the PC
void CH_SetPartyMemberAvailable(int nNPC);
//::///////////////////////////////////////////////
//:: Set Planet Local
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    VARIABLE = K_CURRENT_PLANET
        Endar Spire     5
        Taris           10
        Dantooine       15
        --Kashyyk       20
        --Manaan        25
        --Korriban      30
        --Tatooine      35
        Leviathan       40
        Unknown World   45
        Star Forge      50
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: Oct 16, 2002
//:://////////////////////////////////////////////
void CH_SetPlanetaryGlobal(int nPlanetConstant)
{
/*
    if(nPlanetConstant == PLANET_ENDAR_SPIRE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 5);
    }
    else if(nPlanetConstant == PLANET_TARIS)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 10);
    }
    else if(nPlanetConstant == PLANET_DANTOOINE)
    {
        SetGlobalNumber("K_CURRENT_PLANET", 15);
    }
    else if(nPlanetConstant == PLANET_KASHYYYK)
    {
... (81 more lines)
```

<a id="k_inc_debug"></a>

#### `k_inc_debug`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_debug"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Debug Include
//:: k_inc_debug
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    This contains the functions for inserting
    debug information into the scripts.
    This include will use Db as its two letter
    function prefix.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
//Inserts a print string into the log file for debugging purposes.
void Db_MyPrintString(string sString);
//Makes the object running the script say a speak string.
void Db_MySpeakString(string sString);
//Makes the nearest PC say a speakstring.
void Db_AssignPCDebugString(string sString);
//Basically, a wrapper for AurPostString
void Db_PostString(string sString = "",int x = 5,int y = 5,float fShow = 1.0);
//::///////////////////////////////////////////////
//:: Debug Print String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Inserts a print string into the log file for
    debugging purposes.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: June 12, 2002
//:://////////////////////////////////////////////
void Db_MyPrintString(string sString)
{
    if(!ShipBuild())
    {
        PrintString(sString);
    }
}
//::///////////////////////////////////////////////
//:: Debug Speak String
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
    Makes the object running the script say a
    speak string.
*/
... (47 more lines)
```

<a id="k_inc_disguise"></a>

#### `k_inc_disguise`

**Description**: :: k_inc_disguise

**Usage**: `#include "k_inc_disguise"`

**Source Code**:

```nss
//:: k_inc_disguise
/*
    This script contains all functions necessary to add and
    remove disguises on all party members.
*/
void DonEnvironmentSuit() {
    object oPC;
    int nMax = GetPartyMemberCount();
    int nIdx;
    effect eChange = EffectDisguise(DISGUISE_TYPE_ENVIRONMENTSUIT);
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        ApplyEffectToObject(DURATION_TYPE_PERMANENT,eChange,GetPartyMemberByIndex(nIdx));
    }
}
void DonSpaceSuit() {
    int nMax = GetPartyMemberCount();
    int nIdx;
    effect eChange = EffectDisguise(DISGUISE_TYPE_ENVIRONMENTSUIT_02);
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        object oPartyMember = GetPartyMemberByIndex(nIdx);
        ApplyEffectToObject(DURATION_TYPE_PERMANENT,eChange,oPartyMember);
    }
}
void RemoveDisguises() {
    int nDisguise = EFFECT_TYPE_DISGUISE;
    object oPC;
    effect eEffect;
    int nMax = GetPartyMemberCount();
    int nIdx;
    for(nIdx = 0;nIdx < nMax; nIdx++)
    {
        oPC = GetPartyMemberByIndex(nIdx);
        eEffect = GetFirstEffect(oPC);
        while(GetIsEffectValid(eEffect))
        {
            if(GetEffectType(eEffect) == nDisguise)
            {
                RemoveEffect(oPC,eEffect);
            }
            eEffect = GetNextEffect(oPC);
        }
    }
}

```

<a id="k_inc_drop"></a>

#### `k_inc_drop`

**Description**: ::///////////////////////////////////////////////

**Usage**: `#include "k_inc_drop"`

**Source Code**:

```nss
//::///////////////////////////////////////////////
//:: KOTOR Treasure drop Include
//:: k_inc_drop
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
// Contains the functions for handling creatures dropping random treasure
//Only human creatures not of the beast subrace willdrop treasure dependant
//on their hit dice
//:://////////////////////////////////////////////
//:: Created By: Aidan Scanlan On: 02/06/03
//:://////////////////////////////////////////////
int DR_HIGH_LEVEL = 15;
int DR_MEDIUM_LEVEL = 10;
int DR_LOW_LEVEL = 5;
int DR_SUBRACE_BEAST = 2;
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF);
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF);
// creates a low level treasure: med pack/repair, frag grenade, credits
void DR_CreateLowTreasure();
// creates midlevel treasure: adv-med/repair, any gredade, stims, credits
void DR_CreateMidTreasure();
// creates high treasure: adv stims, grenades, ultra med/repair, credits
void DR_CreateHighTreasure();
// Creates 1-4 credits
void DR_CreateFillerCredits();
/////////////////////////////////////////////////////////////////////////
//Checks for treasure drop conditions. Returns True if treasure will drop
int DR_SpawnCreatureTreasure(object oTarget = OBJECT_SELF)
{
    int nRace = GetRacialType(oTarget);
    int nFaction = GetStandardFaction(oTarget);
    int nSubRace = GetSubRace(oTarget);
    if(Random(4) == 0 &&
       nRace != RACIAL_TYPE_DROID &&
       nSubRace != DR_SUBRACE_BEAST)
    {
        //AurPostString("will drop",5,5,5.0);
        DR_CreateRandomTreasure(oTarget);
        return TRUE;
    }
    return FALSE;
}
//Dependant on the level of a creature drops treasure from a list
void DR_CreateRandomTreasure(object oTarget = OBJECT_SELF)
{
    int nLevel = GetHitDice(oTarget);
    if (nLevel > DR_HIGH_LEVEL)
    {
... (185 more lines)
```

<a id="k_inc_fab"></a>

#### `k_inc_fab`

**Description**: k_inc_fab

**Usage**: `#include "k_inc_fab"`

**Source Code**:

```nss
// k_inc_fab
/*
    Ferret's Wacky Include Script - YAY
    A running compilation of short cuts
    to make life easier
*/
// FAB 3/11
// This spawns in a creature with resref sCreature
// in waypoint location "sp_<sCreature><nInstance>"
object FAB_Spawn( string sCreature, int nInstance = 0 );
// This makes oAct face in the direction of oFace
// if oFace is left blank it defaults to the PC
void FAB_Face( object oAct, object oFace = OBJECT_INVALID );
// This function teleports the PC to oWP then any
// other CNPCs are teleported behind the PC.
// WARNING: Make sure that behind the waypoint there
// are valid points for the CNPCs to teleport to.
void FAB_PCPort( object oWP );
// This function returns a location directly behind the object
// you pass it. The float can be changed to determine how far
// behind the PC.
location FAB_Behind( object oTarg, float fMult = 2.5 );
// This spawns in a creature with resref sCreature
// in waypoint location "sp_<sCreature><nInstance>"
object FAB_Spawn( string sCreature, int nInstance = 0 )
{
    string sWP;
    if ( nInstance == 0 ) sWP = "sp_" + sCreature ;
    else sWP = "sp_" + sCreature + IntToString( nInstance );
    return CreateObject( OBJECT_TYPE_CREATURE, sCreature, GetLocation( GetObjectByTag( sWP ) ));
}
// This makes oAct face in the direction of oFace
// if oFace is left blank it defaults to the PC
void FAB_Face( object oAct, object oFace = OBJECT_INVALID )
{
    if ( oFace == OBJECT_INVALID ) oFace = GetFirstPC();
    AssignCommand( oAct, SetFacingPoint( GetPositionFromLocation(GetLocation(oFace)) ));
}
// This function teleports the PC to oWP then any
// other CNPCs are teleported behind the PC.
// WARNING: Make sure that behind the waypoint there
// are valid points for the CNPCs to teleport to.
void FAB_PCPort( object oWP )
{
    AurPostString("Testing!",5,4,2.0);
    //object oWP = GetObjectByTag( "tp_test" );
    //object oTarg = GetFirstPC();
    object oTarg = GetPartyMemberByIndex(0);
    DelayCommand( 0.1, AssignCommand( oTarg, ClearAllActions() ));
    DelayCommand( 0.2, AssignCommand( oTarg, ActionJumpToObject(oWP) ) );
... (72 more lines)
```

<a id="k_inc_fakecombat"></a>

#### `k_inc_fakecombat`

**Description**: :: k_inc_fakecombat

**Usage**: `#include "k_inc_fakecombat"`

**Source Code**:

```nss
//:: k_inc_fakecombat
/*
     routines for doing fake combat
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
void FAI_EnableFakeMode(object oTarget,int iFaction);
void FAI_DisableFakeMode(object oTarget,int iFaction);
void FAI_PerformFakeAttack(object oAttacker,object oTarget,int bLethal = FALSE);
void FAI_PerformFakeTalent(object oAttacker,object oTarget,talent t,int bLethal = FALSE);
void FAI_EnableFakeMode(object oTarget,int iFaction)
{
  if(!GetIsObjectValid(oTarget))
  {
    return;
  }
  SetCommandable(TRUE,oTarget);
  AssignCommand(oTarget,ClearAllActions());
  SetLocalBoolean(oTarget,SW_FLAG_AI_OFF,TRUE);
  AurPostString("TURNING AI OFF - " + GetTag(oTarget),5,5,5.0);
  ChangeToStandardFaction(oTarget,iFaction);
  SetMinOneHP(oTarget,TRUE);
}
void FAI_DisableFakeMode(object oTarget,int iFaction)
{
  if(!GetIsObjectValid(oTarget))
  {
    return;
  }
  SetCommandable(TRUE,oTarget);
  SetLocalBoolean(oTarget,SW_FLAG_AI_OFF,FALSE);
  ChangeToStandardFaction(oTarget,iFaction);
  SetMinOneHP(oTarget,FALSE);
}
void DoFakeAttack(object oTarget,int bLethal)
{
  if(bLethal)
  {
    SetMinOneHP(oTarget,FALSE);
    ApplyEffectToObject(DURATION_TYPE_INSTANT,EffectDamage(GetCurrentHitPoints(oTarget)-1),
      oTarget);
    //CutsceneAttack(oTarget,ACTION_ATTACKOBJECT,ATTACK_RESULT_HIT_SUCCESSFUL,1000);
  }
  //else
  //{
    ApplyEffectToObject(DURATION_TYPE_TEMPORARY,EffectAssuredHit(),OBJECT_SELF,3.0);
    ActionAttack(oTarget);
 //}
}
... (28 more lines)
```

<a id="k_inc_force"></a>

#### `k_inc_force`

**Description**: :: k_inc_force

**Usage**: `#include "k_inc_force"`

**Source Code**:

```nss
//:: k_inc_force
/*
    v1.0
    Force Powers Include for KOTOR
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
float fLightningDuration = 1.0;
//These variables are set in the script run area.
int SWFP_PRIVATE_SAVE_TYPE;
int SWFP_PRIVATE_SAVE_VERSUS_TYPE;
int SWFP_DAMAGE;
int SWFP_DAMAGE_TYPE;
int SWFP_DAMAGE_VFX;
int SWFP_HARMFUL;
int SWFP_SHAPE;
//Runs the script section for the particular force power.
void  Sp_RunForcePowers();
//Immunity and Resist Spell check for the force power.
//The eDamage checks whether the target is immune to the damage effect
int Sp_BlockingChecks(object oTarget, effect eEffect, effect eEffect2, effect eDamage);
//Makes the necessary saving throws
int Sp_MySavingThrows(object oTarget, int iSpellDC = 0);
//Remove an effect of a specific type
void Sp_RemoveSpecificEffect(int nEffectTypeID, object oTarget);
//Remove an effect from a specific force power.
void Sp_RemoveSpellEffects(int nSpell_ID, object oCaster, object oTarget);
// Delays the application of a spell effect by an amount determined by distance.
float Sp_GetSpellEffectDelay(location SpellTargetLocation, object oTarget);
//Randomly delays the effect application for a default of 0.0 to 0.75 seconds
float Sp_GetRandomDelay(float fMinimumTime = 0.0, float MaximumTime = 0.75);
//Gets a saving throw appropriate to the jedi using the force power.
int Sp_GetJediDCSave();
///Apply effects in a sphere shape.
void Sp_SphereSaveHalf(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
//Apply effects to a single target.
void Sp_SingleTarget(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effect to an area and negate on a save.
void Sp_SphereBlocking(object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration);
// /Apply effect to an object and negate on a save.
void Sp_SingleTargetBlocking(object oAnchor, effect eLink1, float fDuration1, effect eLink2, float fDuration2);
//Apply effects for a for power.
void Sp_ApplyForcePowerEffects(float fTime, effect eEffect, object oTarget);
//Apply effects to targets.
void Sp_ApplyEffects(int nBlocking, object oAnchor, float fSize, int nCounter, effect eLink1, float fDuration1, effect eLink2, float fDuration2, int nRacial = RACIAL_TYPE_ALL);
//Removes all effects from the spells , Knights Mind, Mind Mastery and Battle Meditation
void Sp_RemoveBuffSpell();
//Prints a string for the spell stript
void SP_MyPrintString(string sString);
//Posts a string for the spell script
... (6373 more lines)
```

<a id="k_inc_generic"></a>

#### `k_inc_generic`

**Description**: :: k_inc_generic

**Usage**: `#include "k_inc_generic"`

**Source Code**:

```nss
//:: k_inc_generic
/*
    v1.5
    Generic Include for KOTOR
    Post Clean Up as of March 3, 2003
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_gensupport"
#include "k_inc_walkways"
#include "k_inc_drop"
struct tLastRound
{
    int nLastAction;
    int nLastActionID;
    int nLastTalentCode;
    object oLastTarget;
    int nTalentSuccessCode;
    int nIsLastTargetDebil;
    int nLastCombo;
    int nLastComboIndex;
    int nCurrentCombo;
    int nBossSwitchCurrent;
};
struct tLastRound tPR;
//LOCAL BOOLEANS RANGE FROM 0 to 96
int AMBIENT_PRESENCE_DAY_ONLY = 1;        //POSSIBLE CUT
int AMBIENT_PRESENCE_NIGHT_ONLY = 2;      //POSSIBLE CUT
int AMBIENT_PRESENCE_ALWAYS_PRESENT = 3;
int SW_FLAG_EVENT_ON_PERCEPTION =   20;
int SW_FLAG_EVENT_ON_ATTACKED   =   21;
int SW_FLAG_EVENT_ON_DAMAGED    =   22;
int SW_FLAG_EVENT_ON_FORCE_AFFECTED = 23;
int SW_FLAG_EVENT_ON_DISTURBED = 24;
int SW_FLAG_EVENT_ON_COMBAT_ROUND_END = 25;
int SW_FLAG_EVENT_ON_DIALOGUE    = 26;
int SW_FLAG_EVENT_ON_DEATH       = 27;
int SW_FLAG_EVENT_ON_HEARTBEAT   = 28;
//int SW_FLAG_AMBIENT_ANIMATIONS = 29;          located in k_inc_walkways
// DJS-OEI 3/31/2004
// Since I misinformed the designers early on about the
// number of local boolean the game was using internally,
// they started using flags 30 thru 64 for plot-related
// stuff. This started causing problems since it was signalling
// the AI to perform incorrect behaviors. I've set aside the
// 30-64 range for designer use and increased the values of
// the remaining flags (as well as the engine's total storage
// capacity) so their current scripts will still work. We need
// to recompile all global and MOD embedded scripts so they use
// the new values.
... (3672 more lines)
```

<a id="k_inc_gensupport"></a>

#### `k_inc_gensupport`

**Description**: :: k_inc_gensupport

**Usage**: `#include "k_inc_gensupport"`

**Source Code**:

```nss
//:: k_inc_gensupport
/*
    v1.0
    Support Include for k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//BOSS ATTACK TYPES
int SW_BOSS_ATTACK_TYPE_GRENADE = 1;
int SW_BOSS_ATTACK_TYPE_FORCE_POWER = 2;
int SW_BOSS_ATTACK_TYPE_NPC = 3;
int SW_BOSS_ATTACK_TYPE_PC = 4;
int SW_BOSS_ATTACK_ANY = 5;
int SW_BOSS_ATTACK_DROID = 6;
//LOCAL NUMBERS
int SW_NUMBER_COMBO_ROUTINE = 3;
int SW_NUMBER_COMBO_INDEX = 4;
int SW_NUMBER_LAST_COMBO = 5;
int SW_NUMBER_ROUND_COUNTER = 6;
int SW_NUMBER_COMBAT_ZONE = 7;
int SW_NUMBER_HEALERAI_THRESHOLD = 8;
int SW_NUMBER_HEALERAI_PERCENTAGE = 9;
int SW_NUMBER_COOLDOWN = 10; // fak - oei, rounds before firing again
int SW_NUMBER_COOLDOWN_FIRE = 11; // fak - oei, threshold at which turret fires
//COMBO CONSTANTS
int SW_COMBO_RANGED_FEROCIOUS = 1;
int SW_COMBO_RANGED_AGGRESSIVE = 2;
int SW_COMBO_RANGED_DISCIPLINED = 3;
int SW_COMBO_RANGED_CAUTIOUS = 4;
int SW_COMBO_MELEE_FEROCIOUS = 5;
int SW_COMBO_MELEE_AGGRESSIVE = 6;
int SW_COMBO_MELEE_DISCIPLINED = 7;
int SW_COMBO_MELEE_CAUTIOUS = 8;
int SW_COMBO_BUFF_PARTY = 9;
int SW_COMBO_BUFF_DEBILITATE = 10;
int SW_COMBO_BUFF_DAMAGE = 11;
int SW_COMBO_BUFF_DEBILITATE_DESTROY = 12;
int SW_COMBO_SUPRESS_DEBILITATE_DESTROY = 13;
int SW_COMBO_SITH_ATTACK = 14;
int SW_COMBO_BUFF_ATTACK = 15;
int SW_COMBO_SITH_CONFOUND = 16;
int SW_COMBO_JEDI_SMITE = 17;
int SW_COMBO_SITH_TAUNT = 18;
int SW_COMBO_SITH_BLADE = 19;
int SW_COMBO_SITH_CRUSH = 20;
int SW_COMBO_JEDI_CRUSH = 21;
int SW_COMBO_SITH_BRUTALIZE = 22;
int SW_COMBO_SITH_DRAIN = 23;
... (3828 more lines)
```

<a id="k_inc_glob_party"></a>

#### `k_inc_glob_party`

**Description**: Glob Party

**Usage**: `#include "k_inc_glob_party"`

**Source Code**:

```nss

//:: k_inc_glob_party
/*
These global scripts are to be used to spawn actual party member objects with thier correct equipment, stats, levels, etc.
Use this to place party members for required scripts and cutscenes.
*/
#include "k_inc_debug"
// FUNCTION DECLARATIONS
string  GetNPCTag( int nNPC );
int     GetNPCConstant( string sTag );
void    ClearPlayerParty();
void    SetPlayerParty(int aNPC_CONSTANT_1, int aNPC_CONSTANT_2);
object  SpawnIndividualPartyMember(int aNPC_CONSTANT, string sWP = "WP_gspawn_");
void    SpawnAllAvailablePartyMembers();
object  SpawnIndividualPuppet(int aNPC_CONSTANT, string sWP = "WP_gspawn_");
string  GetPuppetTag( int nNPC );
int     GetPuppetConstant( string sTag );
// FUNCTION DEFINITIONS:
// Sets the Player created character to be the party leader
// and returns all other party members to the 'party base'.
void ClearPlayerParty()
{
    SetPartyLeader(NPC_PLAYER);
    int i;
    for(i = 0; i < 12; i++)
    {
        if(IsNPCPartyMember( i ))
            RemoveNPCFromPartyToBase( i );
    }
}
// sets the Player created character to be the party leader and then fills the party
// with the passed in constants PROVIDED that they have been previously add to the
// 'party base'
void SetPlayerParty(int aNPC_CONSTANT_1, int aNPC_CONSTANT_2)
{
    ClearPlayerParty();
    object oPartyMember1 = SpawnIndividualPartyMember(aNPC_CONSTANT_1);
    object oPartyMember2 = SpawnIndividualPartyMember(aNPC_CONSTANT_2);
    if(GetIsObjectValid(oPartyMember1) )
    {
        AddPartyMember(aNPC_CONSTANT_1, oPartyMember1);
    }
    if(GetIsObjectValid(oPartyMember2) )
    {
        AddPartyMember(aNPC_CONSTANT_2, oPartyMember2);
    }
}
// Will return the tag of the party member constant passed in.
// Will return 'ERROR' if an invalid constant is passed in.
string GetNPCTag( int nNPC )
... (205 more lines)
```

<a id="k_inc_hawk"></a>

#### `k_inc_hawk`

**Description**: Hawk

**Usage**: `#include "k_inc_hawk"`

**Source Code**:

```nss

//:: Script Name
/*
    Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_glob_party"
#include "k_oei_hench_inc"
void StopCombat()
{
    object oPC = GetFirstPC();
    CancelCombat(oPC);
    int i;
    object oEnemy;
    for(i = 0;i < 20;i++)
    {
        oEnemy = GetObjectByTag("REThug4", i);
        if(GetIsObjectValid(oEnemy))
        {
            ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
            CancelCombat(oEnemy);
        }
        oEnemy = GetObjectByTag("REThug5", i);
        if(GetIsObjectValid(oEnemy))
        {
            ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
            CancelCombat(oEnemy);
        }
    }
    //take care of the captain
    oEnemy = GetObjectByTag("RECapt");
    if(GetIsObjectValid(oEnemy))
    {
        ChangeToStandardFaction( oEnemy,STANDARD_FACTION_NEUTRAL );
        CancelCombat(oEnemy);
    }
}
void ClearEnemies()
{
    int i;
    object oEnemy;
    for(i = 0;i < 20;i++)
    {
        oEnemy = GetObjectByTag("REThug4", i);
        if(GetIsObjectValid(oEnemy))
            DestroyObject(oEnemy);
        oEnemy = GetObjectByTag("REThug5", i);
        if(GetIsObjectValid(oEnemy))
            DestroyObject(oEnemy);
... (346 more lines)
```

<a id="k_inc_item_gen"></a>

#### `k_inc_item_gen`

**Description**: Item Gen

**Usage**: `#include "k_inc_item_gen"`

**Source Code**:

```nss

//:: k_inc_item_gen.nss
/*
    Global script used to generate items on the PC based on the
    NPC being spoken to.
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_debug"
//Checks the Player's inventory and determines based on OBJECT_SELF
//whether the Player needs equipment.
//Returns TRUE if the Player needs equipment.
//Returns FALSE if the Player does NOT equipment.
int  GetIsEquipmentNeeded();
//Creates equipment on the PC based on the NPC they are talking to.
void CreateEquipmentOnPC();
//Counts and totals up to four different items within the Player's inventory.
int  CheckInventoryNumbers(string sTag1, string sTag2 = "", string sTag3 = "", string sTag4 = "");
//Checks the Player's inventory and determines based on OBJECT_SELF
//whether the Player needs equipment.
//Returns TRUE if the Player needs equipment.
//Returns FALSE if the Player does NOT equipment.
//Global and modified version of EBO_GetIsEquipmentNeeded() from Kotor1
int GetIsEquipmentNeeded()
{
    int nNumber, nGlobal;
    string sTag = GetTag(OBJECT_SELF);
    int nJediFound = (GetGlobalNumber("000_Jedi_Found")*2) + 10;
    if(sTag == "mira")//Mira
    {
        int bMakeLethalGrenades = GetLocalBoolean( OBJECT_SELF, 31 );
        if(bMakeLethalGrenades)
        {//lethals only
            nNumber = CheckInventoryNumbers("g_w_fraggren01","G_W_FIREGREN001");
            nGlobal = GetGlobalNumber("K_MIRA_ITEMS");
            if((nNumber <= 10 && nGlobal < nJediFound) || nGlobal == 0)
            {
                return TRUE;
            }
            return FALSE;
        }
        else
        {//non lethal grenades only, stuns and adhesives
            nNumber = CheckInventoryNumbers("G_w_StunGren01","g_w_adhsvgren001","G_W_CRYOBGREN001","g_w_iongren01");
            nGlobal = GetGlobalNumber("K_MIRA_ITEMS");
            if((nNumber <= 10 && nGlobal < nJediFound) || nGlobal == 0)
            {
                return TRUE;
            }
            return FALSE;
... (222 more lines)
```

<a id="k_inc_npckill"></a>

#### `k_inc_npckill`

**Description**: Richard Taylor

**Usage**: `#include "k_inc_npckill"`

**Source Code**:

```nss
//Richard Taylor
//OEI 08/08/04
//Various functions to help with killing creatures in
//violent and damaging explosions.
//When this function is called on something it will
//destroy the oCreature after nDelay seconds and do nDamage to
//everyone within 4 meters radius.
void DamagingExplosion(object oCreature, int nDelay, int nDamage );
//When this function is called on something it will
//destroy the oCreature after nDelay seconds but not
//damage anyone in the explosion
void NonDamagingExplosion(object oCreature, int nDelay);
//When this function is called on something it will do
//an EffectDeath on oCreature after nSeconds
void KillCreature(object oCreature, int nDelay);
int GR_GetGrenadeDC(object oTarget);
void DamagingExplosion( object oCreature, int nDelay, int nDamage )
{
    //IF there is a delay just call ourselves after ndelay seconds and
    //not have a delay next time
    if ( nDelay > 0 )
    {
        //AurPostString( "Delaying Damaging", 10, 25, 5.0f );
        DelayCommand( IntToFloat(nDelay), DamagingExplosion(oCreature, 0, nDamage ));
        return;
    }
    //AurPostString( "Executing Damaging", 10, 26, 5.0f );
    int nDC = 15;
    int nDCCheck = 0;
    location oLoc = GetLocation(oCreature);
    float oOri = GetFacing(oCreature);
    vector vPos = GetPositionFromLocation( oLoc );
    vPos.z = vPos.z + 1.0f ;
    location oExplosionLoc = Location( vPos, oOri );
    object oTarget = GetFirstObjectInShape(SHAPE_SPHERE, 4.0, oLoc, FALSE, 65);
    while (GetIsObjectValid(oTarget) && nDamage > 0 )
    {
        int nFaction = GetStandardFaction( oTarget );
        if ( oTarget != OBJECT_SELF && nFaction != STANDARD_FACTION_NEUTRAL )
        {
            nDCCheck = nDC;
            nDCCheck -= GR_GetGrenadeDC(oTarget);
            if ( !ReflexSave(oTarget, nDCCheck, SAVING_THROW_TYPE_NONE))
            {
                ApplyEffectToObject(DURATION_TYPE_INSTANT, EffectDamage(nDamage, DAMAGE_TYPE_PIERCING), oTarget);
            }
            else
            {//Do a evasion check
                int nApply = 0;
                if ( GetHasFeat( FEAT_EVASION, oTarget ) )
... (70 more lines)
```

<a id="k_inc_q_crystal"></a>

#### `k_inc_q_crystal`

**Description**: :: a_q_cryst_change

**Usage**: `#include "k_inc_q_crystal"`

**Source Code**:

```nss
//:: a_q_cryst_change
/*
Takes the quest crystal the player has, if any.
Gives the player the appropriate quest crystal for their alignment/level
*/
//:: Created By: Kevin Saunders, 06/26/04
//:: Copyright 2004 Obsidian Entertainment
#include "k_inc_utility"
int GetPCLevel()
{
    int n = GetGlobalNumber("G_PC_LEVEL");
    return(n);
}
string GetPCAlignType()
{
    string s;
    if(IsDark()) s = "1";
    if(IsNeutral()) s = "2";
    if(IsLight()) s = "3";
    if(IsDarkComplete()) s = "0";
    if(IsLightComplete()) s = "4";
    return(s);
}
int GetCrystalLevel()
{
    int n = 1 + (GetPCLevel() - 9)/3;
    if(n < 1) n = 1;
    if(n > 9) n = 9;
    return(n);
}

```

<a id="k_inc_quest_hk"></a>

#### `k_inc_quest_hk`

**Description**: Gives the player the next component needed for the HK quest.

**Usage**: `#include "k_inc_quest_hk"`

**Source Code**:

```nss
// Gives the player the next component needed for the HK quest.
// kds, 09/06/04
#include "k_inc_treas_k2"
void GiveHKPart(string sString)
{
    int k = 1;
    string sHKpart = "hkpart0";
    string sItem;
    object oItem = OBJECT_SELF;
    object oRecipient;
    if(sString != "") oRecipient = GetObjectByTag(sString);
        else oRecipient = OBJECT_SELF;
if(GetJournalEntry("RebuildHK47") < 80)
{
    for(k; GetIsObjectValid(oItem); k++)
    {
    sItem = sHKpart + IntToString(k);
    oItem = GetItemPossessedBy (GetPartyLeader(),sItem);
    }
    //AddJournalQuestEntry("LightsaberQuest",10*i);
}
CreateItemOnObject( sItem, oRecipient, 1 );
}

```

<a id="k_inc_switch"></a>

#### `k_inc_switch`

**Description**: :: k_inc_switch

**Usage**: `#include "k_inc_switch"`

**Source Code**:

```nss
//:: k_inc_switch
/*
     A simple include defining all of the
     events in the game as constants.
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
//DEFAULT AI EVENTS
int KOTOR_DEFAULT_EVENT_ON_HEARTBEAT           = 1001;
int KOTOR_DEFAULT_EVENT_ON_PERCEPTION          = 1002;
int KOTOR_DEFAULT_EVENT_ON_COMBAT_ROUND_END    = 1003;
int KOTOR_DEFAULT_EVENT_ON_DIALOGUE            = 1004;
int KOTOR_DEFAULT_EVENT_ON_ATTACKED            = 1005;
int KOTOR_DEFAULT_EVENT_ON_DAMAGE              = 1006;
int KOTOR_DEFAULT_EVENT_ON_DEATH               = 1007;
int KOTOR_DEFAULT_EVENT_ON_DISTURBED           = 1008;
int KOTOR_DEFAULT_EVENT_ON_BLOCKED             = 1009;
int KOTOR_DEFAULT_EVENT_ON_FORCE_AFFECTED      = 1010;
int KOTOR_DEFAULT_EVENT_ON_GLOBAL_DIALOGUE_END = 1011;
int KOTOR_DEFAULT_EVENT_ON_PATH_BLOCKED        = 1012;
//HENCHMEN AI EVENTS
int KOTOR_HENCH_EVENT_ON_HEARTBEAT           = 2001;
int KOTOR_HENCH_EVENT_ON_PERCEPTION          = 2002;
int KOTOR_HENCH_EVENT_ON_COMBAT_ROUND_END    = 2003;
int KOTOR_HENCH_EVENT_ON_DIALOGUE            = 2004;
int KOTOR_HENCH_EVENT_ON_ATTACKED            = 2005;
int KOTOR_HENCH_EVENT_ON_DAMAGE              = 2006;
int KOTOR_HENCH_EVENT_ON_DEATH               = 2007;
int KOTOR_HENCH_EVENT_ON_DISTURBED           = 2008;
int KOTOR_HENCH_EVENT_ON_BLOCKED             = 2009;
int KOTOR_HENCH_EVENT_ON_FORCE_AFFECTED      = 2010;
int KOTOR_HENCH_EVENT_ON_GLOBAL_DIALOGUE_END = 2011;
int KOTOR_HENCH_EVENT_ON_PATH_BLOCKED        = 2012;
int KOTOR_HENCH_EVENT_ON_ENTER_5m            = 2013;
int KOTOR_HENCH_EVENT_ON_EXIT_5m             = 2014;
//MISC AI EVENTS
int KOTOR_MISC_DETERMINE_COMBAT_ROUND                = 3001;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_PC          = 3002;
int KOTOR_MISC_DETERMINE_COMBAT_ROUND_ON_INDEX_ZERO  = 3003;
// DJS-OEI 6/12/2004
// Miscellaneous KotOR2 events
// This user-defined event is sent to the Area when the player's
// created character has performed an action that is currently
// considered forbidden for combats in the area.
int KOTOR2_MISC_PC_COMBAT_FORFEIT                    = 4001;

```

<a id="k_inc_treas_k2"></a>

#### `k_inc_treas_k2`

**Description**: Treas K2

**Usage**: `#include "k_inc_treas_k2"`

**Source Code**:

```nss
#include "k_inc_q_crystal"
#include "k_inc_treasure"
/*
This include files contains the functions used to randomly generate item treasure
based upon the players' level.
Item classifications
hundreds digit = item class
tens digit = item sub-class
ones digit = specifies specific item resref
(* = these items have been created through at least level 10)
Weapons 100
*  111 - Blaster
*  121 - Blaster Rifle
*  131 - Melee
*  141 - Lightsaber (regular)
*  142 - Lightsaber (short)
*  143 - Lightsaber (Double)
Upgrades 200
Upgrade - Ranged 210
*  211 - Targeting scope
*  212 - Firing Chamber
*  213 - Power Pack
Upgrade - Melee 220
*  221 - Grip
*  222 - Edge
*  223 - Energy Cell
Upgrade - Armor 230
*  231 - Overlay
*  232 - Underlay
Upgrades - Lightsaber 240
  241 - Emitter
*  242 - Lens
  243 - Energy Cell
  244 - Crystals
  245 - Color Crystals
Equipment - 300
*  311 - Belts
*  321 - Gloves
*  331 - Head Gear
   Implants - 340
*   341 - Level 1
*   342 - Level 2
*   343 - Level 3
*   344 - Level 4
Armor - 400
*  411 - Light armor
*  421 - Medium armor
*  431 - Heavy armor
*  441 - Jedi Robes
Droid Items - 500
... (816 more lines)
```

<a id="k_inc_treasure"></a>

#### `k_inc_treasure`

**Description**: :: k_inc_treasure

**Usage**: `#include "k_inc_treasure"`

**Source Code**:

```nss
//:: k_inc_treasure
/*
     contains code for filling containers using treasure tables
*/
//:: Created By:  Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
//
//  March 15, 2003  J.B.
//      removed parts and spikes from tables
//
//constants for container types
int SWTR_DEBUG = TRUE;  //set to false to disable console/file logging
int SWTR_TABLE_CIVILIAN_CONTAINER = 1;
int SWTR_TABLE_MILITARY_CONTAINER_LOW = 2;
int SWTR_TABLE_MILITARY_CONTAINER_MID = 3;
int SWTR_TABLE_MILITARY_CONTAINER_HIGH = 4;
int SWTR_TABLE_CORPSE_CONTAINER_LOW = 5;
int SWTR_TABLE_CORPSE_CONTAINER_MID = 6;
int SWTR_TABLE_CORPSE_CONTAINER_HIGH = 7;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_LOW = 8;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_MID = 9;
int SWTR_TABLE_SHADOWLANDS_CONTAINER_HIGH = 10;
int SWTR_TABLE_DROID_CONTAINER_LOW = 11;
int SWTR_TABLE_DROID_CONTAINER_MID = 12;
int SWTR_TABLE_DROID_CONTAINER_HIGH = 13;
int SWTR_TABLE_RAKATAN_CONTAINER = 14;
int SWTR_TABLE_SANDPERSON_CONTAINER = 15;
//Fill an object with treasure from the specified table
//This is the only function that should be used outside this include file
void SWTR_PopulateTreasure(object oContainer,int iTable,int iItems = 1,int bUnique = TRUE);
//for internal debugging use only, output string to the log file and console if desired
void SWTR_Debug_PostString(string sStr,int bConsole = TRUE,int x = 5,int y = 5,float fTime = 5.0)
{
  if(SWTR_DEBUG)
  {
    if(bConsole)
    {
      AurPostString("SWTR_DEBUG - " + sStr,x,y,fTime);
    }
    PrintString("SWTR_DEBUG - " + sStr);
  }
}
//return whether i>=iLow and i<=iHigh
int SWTR_InRange(int i,int iLow,int iHigh)
{
  if(i >= iLow && i <= iHigh)
  {
    return(TRUE);
  }
  else
... (773 more lines)
```

<a id="k_inc_utility"></a>

#### `k_inc_utility`

**Description**: :: k_inc_utility

**Usage**: `#include "k_inc_utility"`

**Source Code**:

```nss
//:: k_inc_utility
/*
    common functions used throughout various scripts
    Modified by Peter T. 17/03/03
    - Added UT_MakeNeutral2(), UT_MakeHostile1(), UT_MakeFriendly1() and UT_MakeFriendly2()
*/
//:: Created By: Jason Booth
//:: Copyright (c) 2002 Bioware Corp.
// Plot Flag Constants.
int SW_PLOT_BOOLEAN_01 = 0;
int SW_PLOT_BOOLEAN_02 = 1;
int SW_PLOT_BOOLEAN_03 = 2;
int SW_PLOT_BOOLEAN_04 = 3;
int SW_PLOT_BOOLEAN_05 = 4;
int SW_PLOT_BOOLEAN_06 = 5;
int SW_PLOT_BOOLEAN_07 = 6;
int SW_PLOT_BOOLEAN_08 = 7;
int SW_PLOT_BOOLEAN_09 = 8;
int SW_PLOT_BOOLEAN_10 = 9;
int SW_PLOT_HAS_TALKED_TO = 10;
int SW_PLOT_COMPUTER_OPEN_DOORS = 11;
int SW_PLOT_COMPUTER_USE_GAS = 12;
int SW_PLOT_COMPUTER_DEACTIVATE_TURRETS = 13;
int SW_PLOT_COMPUTER_DEACTIVATE_DROIDS = 14;
int SW_PLOT_COMPUTER_MODIFY_DROID = 15;
int SW_PLOT_REPAIR_WEAPONS = 16;
int SW_PLOT_REPAIR_TARGETING_COMPUTER = 17;
int SW_PLOT_REPAIR_SHIELDS = 18;
int SW_PLOT_REPAIR_ACTIVATE_PATROL_ROUTE = 19;
// UserDefined events
int HOSTILE_RETREAT = 1100;
//Alignment Adjustment Constants
int SW_CONSTANT_DARK_HIT_HIGH = -6;
int SW_CONSTANT_DARK_HIT_MEDIUM = -5;
int SW_CONSTANT_DARK_HIT_LOW = -4;
int SW_CONSTANT_LIGHT_HIT_LOW = -2;
int SW_CONSTANT_LIGHT_HIT_MEDIUM = -1;
int SW_CONSTANT_LIGHT_HIT_HIGH = 0;
// Returns a pass value based on the object's level and DC rating of 0, 1, or 2 (easy, medium, difficult)
// December 20 2001: Changed so that the difficulty is determined by the
// NPC's Hit Dice
int AutoDC(int DC, int nSkill, object oTarget);
//  checks for high charisma
int IsCharismaHigh();
//  checks for low charisma
int IsCharismaLow();
//  checks for normal charisma
int IsCharismaNormal();
//  checks for high intelligence
int IsIntelligenceHigh();
... (2998 more lines)
```

<a id="k_inc_walkways"></a>

#### `k_inc_walkways`

**Description**: :: k_inc_walkways

**Usage**: `#include "k_inc_walkways"`

**Source Code**:

```nss
//:: k_inc_walkways
/*
    v1.0
    Walk Way Points Include
    used by k_inc_generic
    NOTE - To get these functions
    use k_inc_generic
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
int WALKWAYS_CURRENT_POSITION = 0;
int WALKWAYS_END_POINT = 1;
int WALKWAYS_SERIES_NUMBER = 2;
int SW_FLAG_AMBIENT_ANIMATIONS  =   29;
// DJS-OEI 3/31/2004
// Modified to make room for designer-reserved values.
/*
int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 30;
int SW_FLAG_WAYPOINT_WALK_ONCE  =   34;
int SW_FLAG_WAYPOINT_WALK_CIRCULAR  =   35;
int SW_FLAG_WAYPOINT_WALK_PATH  =   36;
int SW_FLAG_WAYPOINT_WALK_STOP  =   37; //One to three
int SW_FLAG_WAYPOINT_WALK_RANDOM    =   38;
int SW_FLAG_WAYPOINT_WALK_RUN    =   39;
int SW_FLAG_WAYPOINT_DIRECTION = 41;
int SW_FLAG_WAYPOINT_DEACTIVATE = 42;
int SW_FLAG_WAYPOINT_WALK_STOP_LONG = 46;
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 47;
int SW_FLAG_WAYPOINT_START_AT_NEAREST = 73;
*/
int SW_FLAG_AMBIENT_ANIMATIONS_MOBILE = 65;
int SW_FLAG_WAYPOINT_START_AT_NEAREST = 98;
int SW_FLAG_WAYPOINT_WALK_ONCE  =   99;
int SW_FLAG_WAYPOINT_WALK_CIRCULAR  =   100;
int SW_FLAG_WAYPOINT_WALK_PATH  =   101;
int SW_FLAG_WAYPOINT_WALK_RANDOM    =   103;
int SW_FLAG_WAYPOINT_WALK_RUN    =   104;
int SW_FLAG_WAYPOINT_DIRECTION = 105;
int SW_FLAG_WAYPOINT_DEACTIVATE = 106;
//new constants for WAYPOINT PAUSING
int SW_FLAG_WAYPOINT_PAUSE_SHORT  = 102;
int SW_FLAG_WAYPOINT_PAUSE_LONG   = 107;
int SW_FLAG_WAYPOINT_PAUSE_RANDOM = 108;
//old constants for WAYPOINT PAUSING. kept for backwards compatibility
int SW_FLAG_WAYPOINT_WALK_STOP        = 102;// DON'T USE ANYMORE
int SW_FLAG_WAYPOINT_WALK_STOP_LONG   = 107;// DON'T USE ANYMORE
int SW_FLAG_WAYPOINT_WALK_STOP_RANDOM = 108;// DON'T USE ANYMORE
//AWD-OEI 06/23/04 adding a local to store the waypoint animation
int SW_FLAG_USE_WAYPOINT_ANIMATION = 109;
//Makes OBJECT_SELF walk way points based on the spawn in conditions set out.
... (676 more lines)
```

<a id="k_inc_zone"></a>

#### `k_inc_zone`

**Description**: :: k_inc_zones

**Usage**: `#include "k_inc_zone"`

**Source Code**:

```nss
//:: k_inc_zones
/*
     Zone including for controlling
     the chaining of creatures
*/
//:: Created By: Preston Watamaniuk
//:: Copyright (c) 2002 Bioware Corp.
#include "k_inc_generic"
//Function run by the trigger to catalog the control nodes followers
void ZN_CatalogFollowers();
//Checks zone conditional on creature to if they belong to the zone
int ZN_CheckIsFollower(object oController, object oTarget);
//Checks the distance and creatures around the PC to see if it should return home.
int ZN_CheckReturnConditions();
//Gets the followers to move back to the controller object
void ZN_MoveToController(object oController, object oFollower);
//Checks to see if a specific individual needs to return to the controller.
int ZN_CheckFollowerReturnConditions(object oTarget);
//::///////////////////////////////////////////////
//:: Catalog Zone Followers
//:: Copyright (c) 2001 Bioware Corp.
//:://////////////////////////////////////////////
/*
     Catalogs all creatures within
     the trigger area and marks
     them with an integer which
     is part of the creature's
     tag.
     Use local number SW_NUMBER_LAST_COMBO
     as a test. A new local number will
     be defined if the system works.
*/
//:://////////////////////////////////////////////
//:: Created By: Preston Watamaniuk
//:: Created On: April 7, 2003
//:://////////////////////////////////////////////
void ZN_CatalogFollowers()
{
    GN_PostString("FIRING", 10,10, 10.0);
    if(GetLocalBoolean(OBJECT_SELF, 10) == FALSE) //Has talked to boolean
    {
        string sZoneTag = GetTag(OBJECT_SELF);
        int nZoneNumber = StringToInt(GetStringRight(sZoneTag, 2));
        //Set up creature followers
        object oZoneFollower = GetFirstInPersistentObject();
        while(GetIsObjectValid(oZoneFollower))
        {
            SetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE, nZoneNumber);
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower = " + GN_ReturnDebugName(oZoneFollower));
            //GN_MyPrintString("ZONING DEBUG ***************** Setup Follower Zone # = " + GN_ITS(GetLocalNumber(oZoneFollower, SW_NUMBER_COMBAT_ZONE)));
... (110 more lines)
```

<a id="k_oei_hench_inc"></a>

#### `k_oei_hench_inc`

**Description**: K Oei Hench Inc

**Usage**: `#include "k_oei_hench_inc"`

**Source Code**:

```nss

//:: Script Name
/*
    Desc
*/
//:: Created By:
//:: Copyright (c) 2002 Bioware Corp.
// Modified by JAB-OEI 7/23/04
// Added special scripts for the 711KOR fight with the entire party
#include "k_inc_generic"
#include "k_inc_utility"
void DoSpecialSpawnIn(object pObject);
void DoSpecialUserDefined(object pObject, int pUserEvent);
//Party Member SpawnIns
void DoAttonSpawnIn(object oPartyMember, string sModuleName);
void DoBaoDurSpawnIn(object oPartyMember, string sModuleName);
void DoMandSpawnIn(object oPartyMember, string sModuleName);
void DoDiscipleSpawnIn(object oPartyMember, string sModuleName);
void DoG0T0SpawnIn(object oPartyMember, string sModuleName);
void DoHandmaidenSpawnIn(object oPartyMember, string sModuleName);
void DoHanharrSpawnIn(object oPartyMember, string sModuleName);
void DoHK47SpawnIn(object oPartyMember, string sModuleName);
void DoKreiaSpawnIn(object oPartyMember, string sModuleName);
void DoMiraSpawnIn(object oPartyMember, string sModuleName);
void DoRemoteSpawnIn(object oPartyMember, string sModuleName);
void DoT3M4SpawnIn(object oPartyMember, string sModuleName);
void DoVisasMarrSpawnIn(object oPartyMember, string sModuleName);
//Party Member UserDefs
void DoAttonUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoBaoDurUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoMandUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoDiscipleUserDef(object oPartyMember, int pUserEvent, string sModuleName);
void DoG0T0UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHandmaidenUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHanharrUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoHK47UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoKreiaUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoMiraUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoRemoteUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoT3M4UserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoVisasMarrUserDef(object oPartyMember,int pUserEvent, string sModuleName);
void DoRemoteDefaultUserDef(object oPartyMember, int pUserEvent);
void Do711UserDef(object oPartyMember,int pUserEvent);
void DoSpecialSpawnIn(object pObject)
{
    AurPostString("DoSpecialSpawnIn" + GetTag(pObject), 18, 18, 3.0);
    if(GetIsObjectValid(pObject))
    {
        string tTag = GetTag(pObject);//should be a party member tag
        string sModuleName = GetModuleName();
... (1373 more lines)
```

<!-- TSL_LIBRARY_END -->

## Compilation Process

When compiling NSS to NCS (see [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205)):

1. **Parser Creation**: `NssParser` initialized with game-specific functions/constants
2. **Source Parsing**: NSS source code parsed into Abstract Syntax Tree (AST)
3. **Function Resolution**: Function calls resolved to routine numbers via function list lookup
4. **Constant Substitution**: Constants replaced with their literal values
5. **Bytecode Generation**: AST compiled to NCS bytecode instructions
6. **Optimization**: Post-compilation optimizers applied (NOP removal, etc.)

**Function Call Resolution:**

```nss
// Source code
int result = GetGlobalNumber("K_QUEST_COMPLETED");
```

```nss
// Compiler looks up "GetGlobalNumber" in KOTOR_FUNCTIONS
// Finds it at index 159 (routine number)
// Generates: ACTION 159 with 1 argument (string "K_QUEST_COMPLETED")
```

**Constant Resolution:**

```nss
// Source code
if (nPlanet == PLANET_TARIS) { ... }
```

```nss
// Compiler looks up PLANET_TARIS in KOTOR_CONSTANTS
// Finds value: 1
// Generates: CONSTI 1 (pushes integer 1 onto stack)
```

**Reference:** [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205), [`wiki/NCS-File-Format.md#engine-function-calls`](NCS-File-Format#engine-function-calls)

---

## Commented-Out Elements in nwscript.nss

The `nwscript.nss` files in KOTOR 1 and 2 contain numerous constants and functions that are commented out (prefixed with `//`). These represent features from the original Neverwinter Nights (NWN) scripting system that were not implemented or supported in the Aurora engine variant used by KOTOR. BioWare deliberately disabled these elements to prevent crashes, errors, or undefined behavior if used.

### Reasons for Commented-Out Elements

KOTOR's `nwscript.nss` retains many NWN-era declarations but prefixes unsupported ones with `//` to disable them during compilation. This deliberate choice by BioWare ensures:

- **Engine Compatibility**: KOTOR's Aurora implementation lacks opcodes or assets for certain NWN features (e.g., advanced animations, UI behaviors), leading to crashes or no-ops if invoked.

- **Modder Safety**: Prevents accidental use in custom scripts, which would fail at runtime. File-internal comments often explicitly state `// disabled` (e.g., for creature orientation in dialogues).

- **Game-Specific Differences**: K1 and K2/TSL `nwscript.nss` vary slightly; K2 has a notorious syntax error in `SetOrientOnClick` (fixed by modders via override).

No official BioWare documentation explains this (as KOTOR predates widespread modding support), but forum consensus attributes it to engine streamlining for single-player RPG vs. NWN's multiplayer focus.

### Key Examples of Commented Elements

| Category | Examples | Notes from nwscript.nss |
|----------|----------|-------------------------|
| Animations | `//int ANIMATION_LOOPING_LOOK_FAR = 5;`<br>`//int ANIMATION_LOOPING_SIT_CHAIR = 6;`<br>`//int ANIMATION_LOOPING_SIT_CROSS = 7;` | Not usable in KOTOR; modders note them when scripting custom behaviors. |
| Effects/Functions | `EffectMovementSpeedIncrease` (with detailed commented description) | Function exists but capped (~200%); higher values ignored, despite "turbo" cheat allowing more. |
| Behaviors | `SetOrientOnClick` | Syntax-broken in early K2; comments note `// disabled` for orient-to-player on click. |

### Common Modder Workarounds

Modders have developed several strategies for working with commented-out elements:

- **Override nwscript.nss**: Extract from `scripts.bif` via Holocron Toolset, fix issues (e.g., K2 syntax error at line ~5710), place in `Override` folder for compilers/DeNCS.

- **Add custom constants**: Modders append new ones (e.g., for feats) rather than uncommenting old.

- **Avoid direct edits**: Messing with core declarations risks compilation failures across all scripts.

**Standard Override Workflow:**

1. Extract via Holocron Toolset (`scripts.bif > Script, Source > nwscript.nss`).
2. Edit (fix/add), save as `.nss` in `Override`.
3. Use with `nwnnsscomp` for compilation.

**K2 Syntax Fix:**

The notorious K2 syntax error in `SetOrientOnClick` can be fixed by changing:

```nss
void SetOrientOnClick( object = OBJECT_SELF, ... )
```

to:

```nss
void SetOrientOnClick( object oCreature = OBJECT_SELF, ... )
```

### Forum Discussions and Community Knowledge

Modding communities actively reference these commented sections, especially on **Deadly Stream** (primary KOTOR hub), **LucasForums archives**, **Holowan Laboratories** (via MixNMojo/Mixmojo forums), and Reddit.

| Forum | Key Threads | Topics Covered |
|-------|-------------|----------------|
| Deadly Stream | [Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/), [nwscript.nss Request](https://deadlystream.com/topic/6892-nwscriptnss/) | Animations, overrides |
| LucasForums Archive | [Syntax Error](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss), [Don't Mess with It](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da) | Fixes, warnings |
| Reddit r/kotor | [Movement Speed](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/) | Effect caps |
| Czerka R&D Wiki | [nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss) | General documentation |

**Notable Discussion Points:**

- **Deadly Stream - Fair Strides' Script Shack** (2016 thread, 100+ pages): Users troubleshooting animations flag the exact commented lines (e.g., `ANIMATION_LOOPING_*`), confirming they can't be used natively. No successful uncommenting reported; focus on alternatives like `ActionPlayAnimation` workarounds.

- **Reddit r/kotor** (2018): Thread on speed boosts quotes the commented description for `EffectMovementSpeedIncrease` (line ~165). Users test values >200% (no effect due to cap), note "turbo" cheat bypasses it partially.

- **LucasForums Archive** (2004-2007 threads): Multiple posts warn against editing `nwscript.nss` ("very bad idea... loads of trouble"). Syntax fix for K2 widely shared; `// disabled` snippets appear in context of `SetOrientOnClick`.

### Attempts to Uncomment or Modify

- **Direct Uncommenting**: No documented successes; implied to cause runtime crashes (engine lacks implementation). Forums advise against.

- **Overrides & Additions**: Standard modding workflow (see above). Examples: TSLPatcher/TSL Patcher tools bundle fixed versions; mods like Hardcore/Improved AI reference custom includes (not core uncomments).

- **Advanced Usage**: DeNCS/ncs2nss require game-specific `nwscript.nss` for accurate decompiles; modders parse it for custom tools.

In summary, while no one has publicly shared a "uncomment everything" patch (likely futile), the modding scene thrives on careful overrides, with thousands of posts across these sites confirming the practice since 2003.

### Key Citations

- [Deadly Stream: Fair Strides' Script Shack](https://deadlystream.com/topic/4808-fair-strides-script-shack/page/7/)
- [Czerka Wiki: nwscript.nss](https://czerka-rd.fandom.com/wiki/Nwscript.nss)
- [LucasForums: Syntax Error in K2 nwscript.nss](https://www.lucasforumsarchive.com/thread/142901-syntax-error-in-kotor2-nwscriptnss)
- [Reddit: Movement Speed Modding](https://www.reddit.com/r/kotor/comments/9dr8iy/modding_question_movement_speed_increase_in_k2/)
- [Deadly Stream: nwscript.nss Thread](https://deadlystream.com/topic/6892-nwscriptnss/)
- [LucasForums: Warning on Editing nwscript.nss](https://www.lucasforumsarchive.com/thread/168643-im-trying-to-change-classes2da)

---

## Reference Implementations

**Parsing nwscript.nss:**

- [`vendor/reone/src/apps/dataminer/routines.cpp:149-184`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp#L149-L184) - Parses nwscript.nss using regex patterns for constants and functions
- [`vendor/reone/src/apps/dataminer/routines.cpp:382-427`](https://github.com/th3w1zard1/reone/blob/master/src/apps/dataminer/routines.cpp#L382-L427) - Extracts functions from nwscript.nss in chitin.key for K1 and K2
- [`vendor/xoreos-tools/src/nwscript/actions.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/actions.cpp) - Actions data parsing for decompilation
- [`vendor/xoreos-tools/src/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/ncsfile.cpp) - NCS file parsing with actions data integration
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Unity C# actions table
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript.cs) - Unity C# NWScript class
- [`vendor/KotOR-Scripting-Tool/NWN Script/NWScriptParser.cs`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/NWScriptParser.cs) - C# parser for nwscript.nss

**Function Definitions:**

- [`vendor/KotOR.js/src/nwscript/NWScript.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScript.ts) - TypeScript function definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK1.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK1.ts) - KotOR 1 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptDefK2.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptDefK2.ts) - KotOR 2 definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptParser.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptParser.ts) - TypeScript parser for nwscript.nss
- [`vendor/KotOR.js/src/nwscript/NWScriptCompiler.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptCompiler.ts) - TypeScript NSS compiler
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionSet.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionSet.ts) - Instruction set definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptConstants.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptConstants.ts) - Constant definitions
- [`vendor/HoloLSP/server/src/nwscript/`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript/) - Language server definitions
- [`vendor/HoloLSP/server/src/nwscript-parser.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-parser.ts) - Language server parser
- [`vendor/HoloLSP/server/src/nwscript-lexer.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-lexer.ts) - Language server lexer
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Language server AST
- [`vendor/HoloLSP/syntaxes/nwscript.tmLanguage.json`](https://github.com/th3w1zard1/HoloLSP/blob/master/syntaxes/nwscript.tmLanguage.json) - TextMate syntax definition
- [`vendor/nwscript-mode.el/nwscript-mode.el`](https://github.com/th3w1zard1/nwscript-mode.el/blob/master/nwscript-mode.el) - Emacs mode for NWScript
- [`vendor/nwscript-ts-mode/`](https://github.com/th3w1zard1/nwscript-ts-mode) - TypeScript mode for NWScript

**Original Sources:**

- [`vendor/Vanilla_KOTOR_Script_Source`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source) - Original KotOR script sources including nwscript.nss
- [`vendor/Vanilla_KOTOR_Script_Source/K1/Data/scripts.bif/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/K1/Data/scripts.bif) - KotOR 1 script sources from BIF
- [`vendor/Vanilla_KOTOR_Script_Source/TSL/Vanilla/Data/Scripts/`](https://github.com/th3w1zard1/Vanilla_KOTOR_Script_Source/tree/master/TSL/Vanilla/Data/Scripts) - KotOR 2 script sources
- [`vendor/KotOR-Scripting-Tool/NWN Script/k1/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k1/nwscript.nss) - KotOR 1 nwscript.nss
- [`vendor/KotOR-Scripting-Tool/NWN Script/k2/nwscript.nss`](https://github.com/th3w1zard1/KotOR-Scripting-Tool/blob/master/NWN%20Script/k2/nwscript.nss) - KotOR 2 nwscript.nss
- [`vendor/NorthernLights/Scripts/k1_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k1_nwscript.nss) - KotOR 1 nwscript.nss (NorthernLights)
- [`vendor/NorthernLights/Scripts/k2_nwscript.nss`](https://github.com/th3w1zard1/NorthernLights/blob/master/Scripts/k2_nwscript.nss) - KotOR 2 nwscript.nss (NorthernLights)

**PyKotor Implementation:**

- [`Libraries/PyKotor/src/pykotor/common/script.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/script.py) - Data structures (ScriptFunction, ScriptConstant, DataType)
- [`Libraries/PyKotor/src/pykotor/common/scriptdefs.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptdefs.py) - Function and constant definitions (772 K1 functions, 1489 K1 constants)
- [`Libraries/PyKotor/src/pykotor/common/scriptlib.py`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/common/scriptlib.py) - Library file definitions (k_inc_generic, k_inc_utility, etc.)
- [`Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py:126-205`](https://github.com/th3w1zard1/PyKotor/blob/master/Libraries/PyKotor/src/pykotor/resource/formats/ncs/ncs_auto.py#L126-L205) - Compilation integration

**Other Implementations:**

- [`vendor/Kotor.NET/Kotor.NET/Formats/KotorNCS/NCS.cs`](https://github.com/th3w1zard1/Kotor.NET/blob/master/Kotor.NET/Formats/KotorNCS/NCS.cs) - C# NCS format with actions data support
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptHeader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptHeader.cs) - C# NWScript header parser
- [`vendor/KotORModSync/KOTORModSync.Core/Data/NWScriptFileReader.cs`](https://github.com/th3w1zard1/KotORModSync/blob/master/KOTORModSync.Core/Data/NWScriptFileReader.cs) - C# NWScript file reader

**NWScript VM and Execution:**

- [`vendor/reone/src/libs/script/routine/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine) - Routine implementations for engine functions
- [`vendor/reone/src/libs/script/format/ncsreader.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncsreader.cpp) - NCS bytecode reader
- [`vendor/reone/src/libs/script/format/ncswriter.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/format/ncswriter.cpp) - NCS bytecode writer
- [`vendor/xoreos/src/aurora/nwscript/`](https://github.com/th3w1zard1/xoreos/tree/master/src/aurora/nwscript) - NWScript VM implementation
- [`vendor/xoreos/src/aurora/nwscript/ncsfile.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/ncsfile.cpp) - NCS file parsing and execution
- [`vendor/xoreos/src/aurora/nwscript/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/object.h) - NWScript object type definitions
- [`vendor/xoreos/src/engines/kotorbase/object.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/object.h) - KotOR object implementation
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# NCS VM control
- [`vendor/NorthernLights/Assets/Scripts/ncs/NCSReader.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/NCSReader.cs) - Unity C# NCS reader
- [`vendor/KotOR.js/src/odyssey/controllers/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/odyssey/controllers/NWScriptController.ts) - TypeScript NWScript VM controller
- [`vendor/KotOR.js/src/nwscript/NWScriptInstance.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstance.ts) - TypeScript NWScript instance
- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - TypeScript stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptSubroutine.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptSubroutine.ts) - TypeScript subroutine handling

**Documentation and Specifications:**

- [`vendor/xoreos-docs/`](https://github.com/th3w1zard1/xoreos-docs) - xoreos documentation including format specifications
- [`vendor/xoreos-docs/specs/torlack/ncs.html`](https://github.com/th3w1zard1/xoreos-docs/blob/master/specs/torlack/ncs.html) - NCS format specification (if available)

**NWScript Language Support:**

- [`vendor/HoloLSP/server/src/kotor-definitions.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/kotor-definitions.ts) - KotOR function and constant definitions for language server
- [`vendor/HoloLSP/server/src/nwscript-runtime.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-runtime.ts) - NWScript runtime definitions
- [`vendor/HoloLSP/server/src/server.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/server.ts) - Language server implementation with NWScript support

**NWScript Parsing and Compilation:**

- [`vendor/reone/src/libs/script/parser/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/parser) - NSS parser implementation
- [`vendor/reone/src/libs/script/compiler/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/compiler) - NSS to NCS compiler
- [`vendor/xoreos-tools/src/nwscript/compiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/compiler.cpp) - NSS compiler implementation
- [`vendor/xoreos-tools/src/nwscript/decompiler.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/decompiler.cpp) - NCS decompiler implementation

**NWScript Execution:**

- [`vendor/reone/src/libs/script/execution/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/execution) - NWScript VM execution engine
- [`vendor/reone/src/libs/script/vm/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/vm) - Virtual machine implementation
- [`vendor/xoreos/src/aurora/nwscript/execution.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/execution.cpp) - NWScript execution engine
- [`vendor/xoreos/src/aurora/nwscript/variable.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/variable.cpp) - Variable handling
- [`vendor/xoreos/src/aurora/nwscript/function.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/function.cpp) - Function call handling
- [`vendor/NorthernLights/Assets/Scripts/ncs/control.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/control.cs) - Unity C# NCS VM control and execution
- [`vendor/KotOR.js/src/nwscript/NWScriptController.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptController.ts) - TypeScript NWScript controller and execution

**Routine Implementations:**

- [`vendor/reone/src/libs/script/routine/main/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/main) - Main routine implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/xoreos/src/aurora/nwscript/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/routines.cpp) - Routine implementations
- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations

**NWScript Type System:**

- [`vendor/xoreos/src/aurora/nwscript/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.h) - NWScript type definitions
- [`vendor/xoreos/src/aurora/nwscript/types.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/aurora/nwscript/types.cpp) - Type system implementation
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptDataType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptDataType.ts) - TypeScript data type enumerations
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptTypes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptTypes.ts) - TypeScript type definitions

**NWScript Events:**

- [`vendor/KotOR.js/src/nwscript/events/NWScriptEvent.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEvent.ts) - Event handling
- [`vendor/KotOR.js/src/nwscript/events/NWScriptEventFactory.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/events/NWScriptEventFactory.ts) - Event factory
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptEventType.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptEventType.ts) - Event type enumerations

**NWScript Bytecode:**

- [`vendor/KotOR.js/src/nwscript/NWScriptOPCodes.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptOPCodes.ts) - Opcode definitions
- [`vendor/KotOR.js/src/nwscript/NWScriptInstruction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstruction.ts) - Instruction handling
- [`vendor/KotOR.js/src/nwscript/NWScriptInstructionInfo.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptInstructionInfo.ts) - Instruction information
- [`vendor/KotOR.js/src/enums/nwscript/NWScriptByteCode.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/enums/nwscript/NWScriptByteCode.ts) - Bytecode enumerations

**NWScript Stack:**

- [`vendor/KotOR.js/src/nwscript/NWScriptStack.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStack.ts) - Stack implementation
- [`vendor/KotOR.js/src/nwscript/NWScriptStackVariable.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/NWScriptStackVariable.ts) - Stack variable handling

**NWScript Interface Definitions:**

- [`vendor/KotOR.js/src/interface/nwscript/INWScriptStoreState.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptStoreState.ts) - Store state interface
- [`vendor/KotOR.js/src/interface/nwscript/INWScriptDefAction.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/interface/nwscript/INWScriptDefAction.ts) - Action definition interface

**NWScript AST and Parsing:**

- [`vendor/KotOR.js/src/nwscript/AST/nwscript.jison.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/nwscript/AST/nwscript.jison.ts) - Jison parser grammar
- [`vendor/HoloLSP/server/src/nwscript-ast.ts`](https://github.com/th3w1zard1/HoloLSP/blob/master/server/src/nwscript-ast.ts) - Abstract syntax tree definitions

**Game-Specific NWScript Extensions:**

- [`vendor/xoreos/src/engines/kotorbase/script/routines.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/script/routines.cpp) - KotOR-specific routine implementations
- [`vendor/reone/src/libs/script/routine/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine) - Routine implementations for K1 and K2
- [`vendor/xoreos/src/engines/nwn/script/functions_action.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_action.cpp) - NWN action function implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/constants.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/constants.cs) - NWScript constant definitions
- [`vendor/reone/src/libs/script/routine.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/script/routine.cpp) - Routine base class implementation
- [`vendor/reone/src/libs/game/script/routines.cpp`](https://github.com/th3w1zard1/reone/blob/master/src/libs/game/script/routines.cpp) - Game-specific routine implementations
- [`vendor/reone/include/reone/script/routines.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/script/routines.h) - Routine header definitions
- [`vendor/reone/include/reone/script/routine.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/script/routine.h) - Routine base class header
- [`vendor/reone/include/reone/game/script/routines.h`](https://github.com/th3w1zard1/reone/blob/master/include/reone/game/script/routines.h) - Game routine header
- [`vendor/xoreos-tools/src/nwscript/subroutine.cpp`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.cpp) - Subroutine handling
- [`vendor/xoreos-tools/src/nwscript/subroutine.h`](https://github.com/th3w1zard1/xoreos-tools/blob/master/src/nwscript/subroutine.h) - Subroutine header
- [`vendor/xoreos/src/engines/kotorbase/types.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/kotorbase/types.h) - KotOR type definitions including base item types
- [`vendor/KotOR.js/src/module/Module.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/Module.ts) - Module loading and management
- [`vendor/KotOR.js/src/module/ModuleArea.ts`](https://github.com/th3w1zard1/KotOR.js/blob/master/src/module/ModuleArea.ts) - Area management and transitions
- [`vendor/xoreos/src/engines/nwn/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/module.cpp) - NWN module implementation
- [`vendor/xoreos/src/engines/nwn2/module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.cpp) - NWN2 module implementation
- [`vendor/xoreos/src/engines/nwn2/module.h`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/module.h) - NWN2 module header
- [`vendor/xoreos/src/engines/dragonage2/script/functions_module.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/dragonage2/script/functions_module.cpp) - Dragon Age 2 module functions
- [`vendor/xoreos/src/engines/nwn/script/functions_effect.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_effect.cpp) - NWN effect function implementations
- [`vendor/xoreos/src/engines/nwn/script/functions_object.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn/script/functions_object.cpp) - NWN object function implementations
- [`vendor/xoreos/src/engines/nwn2/script/functions.cpp`](https://github.com/th3w1zard1/xoreos/blob/master/src/engines/nwn2/script/functions.cpp) - NWN2 function implementations
- [`vendor/reone/src/libs/script/routine/action/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/action) - Action routine implementations
- [`vendor/reone/src/libs/script/routine/effect/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/effect) - Effect routine implementations
- [`vendor/reone/src/libs/script/routine/object/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/object) - Object routine implementations
- [`vendor/reone/src/libs/script/routine/party/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/party) - Party routine implementations
- [`vendor/reone/src/libs/script/routine/combat/`](https://github.com/th3w1zard1/reone/tree/master/src/libs/script/routine/combat) - Combat routine implementations
- [`vendor/NorthernLights/Assets/Scripts/ncs/nwscript_actions.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/ncs/nwscript_actions.cs) - Complete actions table mapping routine numbers to function names
- [`vendor/NorthernLights/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs`](https://github.com/th3w1zard1/NorthernLights/blob/master/Assets/Scripts/Systems/AuroraActions/AuroraAction.cs) - Action system implementation

---

### Other Constants

See [Other Constants](NSS-TSL-Only-Constants-Other-Constants) for detailed documentation.

## Cross-References

- **[NCS File Format](NCS-File-Format.md)**: Compiled bytecode format that NSS compiles to
- **[GFF File Format](GFF-File-Format.md)**: Scripts are stored in GFF files (UTC, UTD, etc.)
- **[KEY File Format](KEY-File-Format.md)**: nwscript.nss is stored in chitin.key
