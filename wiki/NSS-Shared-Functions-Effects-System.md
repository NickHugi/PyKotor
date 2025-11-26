# Effects System

Part of the [NSS File Format Documentation](NSS-File-Format).

**Category:** Shared Functions (K1 & TSL)


<a id="actionequipmosteffectivearmor"></a>

## `ActionEquipMostEffectiveArmor()` - Routine 404

- `404. ActionEquipMostEffectiveArmor`
- The creature will equip the armour in its possession that has the highest
- armour class.

<a id="applyeffectatlocation"></a>

## `ApplyEffectAtLocation(nDurationType, eEffect, lLocation, fDuration)` - Routine 216

- `216. ApplyEffectAtLocation`
- Apply eEffect at lLocation.

- `nDurationType`: int
- `eEffect`: effect
- `lLocation`: location
- `fDuration`: float (default: `0.0`)

<a id="applyeffecttoobject"></a>

## `ApplyEffectToObject(nDurationType, eEffect, oTarget, fDuration)` - Routine 220

- `220. ApplyEffectToObject`
- Apply eEffect to oTarget.

- `nDurationType`: int
- `eEffect`: effect
- `oTarget`: object
- `fDuration`: float (default: `0.0`)

<a id="clearalleffects"></a>

## `ClearAllEffects()` - Routine 710

- `710. ClearAllEffects`
- Clear all the effects of the caller.
- - No return value, but if an error occurs, the log file will contain
- "ClearAllEffects failed.".

<a id="disablevideoeffect"></a>

## `DisableVideoEffect()` - Routine 508

- `508. DisableVideoEffect`
- EnableVideoEffect
- Enables the video frame buffer effect specified by nEffectType, which is
- an index into VideoEffects.2da. This video effect will apply indefinitely,
- and so it should *always* be cleared by a call to DisableVideoEffect().

<a id="effectabilitydecrease"></a>

## `EffectAbilityDecrease(nAbility, nModifyBy)` - Routine 446

- `446. EffectAbilityDecrease`
- Create an Ability Decrease effect.
- - nAbility: ABILITY_*
- - nModifyBy: This is the amount by which to decrement the ability

- `nAbility`: int
- `nModifyBy`: int

<a id="effectabilityincrease"></a>

## `EffectAbilityIncrease(nAbilityToIncrease, nModifyBy)` - Routine 80

- `80. EffectAbilityIncrease`
- Create an Ability Increase effect
- - bAbilityToIncrease: ABILITY_*

- `nAbilityToIncrease`: int
- `nModifyBy`: int

<a id="effectacdecrease"></a>

## `EffectACDecrease(nValue, nModifyType, nDamageType)` - Routine 450

- `450. EffectACDecrease`
- Create an AC Decrease effect.
- - nValue
- - nModifyType: AC_*
- - nDamageType: DAMAGE_TYPE_*
- - Default value for nDamageType should only ever be used in this function prototype.

- `nValue`: int
- `nModifyType`: int (default: `0`)
- `nDamageType`: int (default: `8199`)

<a id="effectacincrease"></a>

## `EffectACIncrease(nValue, nModifyType, nDamageType)` - Routine 115

- `115. EffectACIncrease`
- Create an AC Increase effect
- - nValue: size of AC increase
- - nModifyType: AC_*_BONUS
- - nDamageType: DAMAGE_TYPE_*
- - Default value for nDamageType should only ever be used in this function prototype.

- `nValue`: int
- `nModifyType`: int (default: `0`)
- `nDamageType`: int (default: `8199`)

<a id="effectareaofeffect"></a>

## `EffectAreaOfEffect(nAreaEffectId, sOnEnterScript, sHeartbeatScript, sOnExitScript)` - Routine 171

- `171. EffectAreaOfEffect`
- Create an Area Of Effect effect in the area of the creature it is applied to.
- If the scripts are not specified, default ones will be used.

- `nAreaEffectId`: int
- `sOnEnterScript`: string (default: ``)
- `sHeartbeatScript`: string (default: ``)
- `sOnExitScript`: string (default: ``)

<a id="effectassureddeflection"></a>

## `EffectAssuredDeflection(nReturn)` - Routine 252

- `252. EffectAssuredDeflection`
- Assured Deflection
- This effect ensures that all projectiles shot at a jedi will be deflected
- without doing an opposed roll.  It takes an optional parameter to say whether
- the deflected projectile will return to the attacker and cause damage

- `nReturn`: int (default: `0`)

<a id="effectassuredhit"></a>

## `EffectAssuredHit()` - Routine 51

- `51. EffectAssuredHit`
- EffectAssuredHit
- Create an Assured Hit effect, which guarantees that all attacks are successful

<a id="effectattackdecrease"></a>

## `EffectAttackDecrease(nPenalty, nModifierType)` - Routine 447

- `447. EffectAttackDecrease`
- Create an Attack Decrease effect.
- - nPenalty
- - nModifierType: ATTACK_BONUS_*

- `nPenalty`: int
- `nModifierType`: int (default: `0`)

<a id="effectattackincrease"></a>

## `EffectAttackIncrease(nBonus, nModifierType)` - Routine 118

- `118. EffectAttackIncrease`
- Create an Attack Increase effect
- - nBonus: size of attack bonus
- - nModifierType: ATTACK_BONUS_*

- `nBonus`: int
- `nModifierType`: int (default: `0`)

<a id="effectbeam"></a>

## `EffectBeam(nBeamVisualEffect, oEffector, nBodyPart, bMissEffect)` - Routine 207

- `207. EffectBeam`
- Create a Beam effect.
- - nBeamVisualEffect: VFX_BEAM_*
- - oEffector: the beam is emitted from this creature
- - nBodyPart: BODY_NODE_*
- - bMissEffect: If this is TRUE, the beam will fire to a random vector near or

- `nBeamVisualEffect`: int
- `oEffector`: object
- `nBodyPart`: int
- `bMissEffect`: int (default: `0`)

<a id="effectblasterdeflectiondecrease"></a>

## `EffectBlasterDeflectionDecrease(nChange)` - Routine 470

- `470. EffectBlasterDeflectionDecrease`
- decrease the blaster deflection rate

- `nChange`: int

<a id="effectblasterdeflectionincrease"></a>

## `EffectBlasterDeflectionIncrease(nChange)` - Routine 469

- `469. EffectBlasterDeflectionIncrease`
- Increase the blaster deflection rate, i think...

- `nChange`: int

<a id="effectbodyfuel"></a>

## `EffectBodyFuel()` - Routine 224

- `224. EffectBodyFuel`
- the effect of body fule.. convers HP -> FP i think

<a id="effectchoke"></a>

## `EffectChoke()` - Routine 159

- `159. EffectChoke`
- Choke the bugger...

<a id="effectconcealment"></a>

## `EffectConcealment(nPercentage)` - Routine 458

- `458. EffectConcealment`
- Create a Concealment effect.
- - nPercentage: 1-100 inclusive
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nPercentage < 1 or
- nPercentage > 100.

- `nPercentage`: int

<a id="effectconfused"></a>

## `EffectConfused()` - Routine 157

- `157. EffectConfused`
- Create a Confuse effect

<a id="effectcutscenehorrified"></a>

## `EffectCutSceneHorrified()` - Routine 754

- `754. EffectCutSceneHorrified`
- EffectCutSceneHorrified
- Get a horrified effect for cutscene purposes (ie. this effect will ignore immunities).

<a id="effectcutsceneparalyze"></a>

## `EffectCutSceneParalyze()` - Routine 755

- `755. EffectCutSceneParalyze`
- EffectCutSceneParalyze
- Get a paralyze effect for cutscene purposes (ie. this effect will ignore immunities).

<a id="effectcutscenestunned"></a>

## `EffectCutSceneStunned()` - Routine 756

- `756. EffectCutSceneStunned`
- EffectCutSceneStunned
- Get a stun effect for cutscene purposes (ie. this effect will ignore immunities).

<a id="effectdamage"></a>

## `EffectDamage(nDamageAmount, nDamageType, nDamagePower)` - Routine 79

- `79. EffectDamage`
- Create a Damage effect
- - nDamageAmount: amount of damage to be dealt. This should be applied as an
- instantaneous effect.
- - nDamageType: DAMAGE_TYPE_*
- - nDamagePower: DAMAGE_POWER_*

- `nDamageAmount`: int
- `nDamageType`: int (default: `8`)
- `nDamagePower`: int (default: `0`)

<a id="effectdamagedecrease"></a>

## `EffectDamageDecrease(nPenalty, nDamageType)` - Routine 448

- `448. EffectDamageDecrease`
- Create a Damage Decrease effect.
- - nPenalty
- - nDamageType: DAMAGE_TYPE_*

- `nPenalty`: int
- `nDamageType`: int (default: `8`)

<a id="effectdamageforcepoints"></a>

## `EffectDamageForcePoints(nDamage)` - Routine 372

- `372. EffectDamageForcePoints`
- Damages the creatures force points

- `nDamage`: int

<a id="effectdamageimmunitydecrease"></a>

## `EffectDamageImmunityDecrease(nDamageType, nPercentImmunity)` - Routine 449

- `449. EffectDamageImmunityDecrease`
- Create a Damage Immunity Decrease effect.
- - nDamageType: DAMAGE_TYPE_*
- - nPercentImmunity

- `nDamageType`: int
- `nPercentImmunity`: int

<a id="effectdamageimmunityincrease"></a>

## `EffectDamageImmunityIncrease(nDamageType, nPercentImmunity)` - Routine 275

- `275. EffectDamageImmunityIncrease`
- Creates a Damage Immunity Increase effect.
- - nDamageType: DAMAGE_TYPE_*
- - nPercentImmunity

- `nDamageType`: int
- `nPercentImmunity`: int

<a id="effectdamageincrease"></a>

## `EffectDamageIncrease(nBonus, nDamageType)` - Routine 120

- `120. EffectDamageIncrease`
- Create a Damage Increase effect
- - nBonus: DAMAGE_BONUS_*
- - nDamageType: DAMAGE_TYPE_*

- `nBonus`: int
- `nDamageType`: int (default: `8`)

<a id="effectdamagereduction"></a>

## `EffectDamageReduction(nAmount, nDamagePower, nLimit)` - Routine 119

- `119. EffectDamageReduction`
- Create a Damage Reduction effect
- - nAmount: amount of damage reduction
- - nDamagePower: DAMAGE_POWER_*
- - nLimit: How much damage the effect can absorb before disappearing.
- Set to zero for infinite

- `nAmount`: int
- `nDamagePower`: int
- `nLimit`: int (default: `0`)

<a id="effectdamageresistance"></a>

## `EffectDamageResistance(nDamageType, nAmount, nLimit)` - Routine 81

- `81. EffectDamageResistance`
- Create a Damage Resistance effect that removes the first nAmount points of
- damage of type nDamageType, up to nLimit (or infinite if nLimit is 0)
- - nDamageType: DAMAGE_TYPE_*
- - nAmount
- - nLimit

- `nDamageType`: int
- `nAmount`: int
- `nLimit`: int (default: `0`)

<a id="effectdamageshield"></a>

## `EffectDamageShield(nDamageAmount, nRandomAmount, nDamageType)` - Routine 487

- `487. EffectDamageShield`
- Create a Damage Shield effect which does (nDamageAmount + nRandomAmount)
- damage to any melee attacker on a successful attack of damage type nDamageType.
- - nDamageAmount: an integer value
- - nRandomAmount: DAMAGE_BONUS_*
- - nDamageType: DAMAGE_TYPE_*

- `nDamageAmount`: int
- `nRandomAmount`: int
- `nDamageType`: int

<a id="effectdeath"></a>

## `EffectDeath(nSpectacularDeath, nDisplayFeedback)` - Routine 133

- `133. EffectDeath`
- Create a Death effect
- - nSpectacularDeath: if this is TRUE, the creature to which this effect is
- applied will die in an extraordinary fashion
- - nDisplayFeedback

- `nSpectacularDeath`: int (default: `0`)
- `nDisplayFeedback`: int (default: `1`)

<a id="effectdisguise"></a>

## `EffectDisguise(nDisguiseAppearance)` - Routine 463

- `463. EffectDisguise`
- Create a Disguise effect.
- - - nDisguiseAppearance: DISGUISE_TYPE_*s

- `nDisguiseAppearance`: int

<a id="effectdispelmagicall"></a>

## `EffectDispelMagicAll(nCasterLevel)` - Routine 460

- `460. EffectDispelMagicAll`
- Create a Dispel Magic All effect.

- `nCasterLevel`: int

<a id="effectdispelmagicbest"></a>

## `EffectDispelMagicBest(nCasterLevel)` - Routine 473

- `473. EffectDispelMagicBest`
- Create a Dispel Magic Best effect.

- `nCasterLevel`: int

<a id="effectdroidstun"></a>

## `EffectDroidStun()` - Routine 391

- `391. EffectDroidStun`
- Stunn the droid

<a id="effectentangle"></a>

## `EffectEntangle()` - Routine 130

- `130. EffectEntangle`
- Create an Entangle effect
- When applied, this effect will restrict the creature's movement and apply a
- (-2) to all attacks and a -4 to AC.

<a id="effectforcedrain"></a>

## `EffectForceDrain(nDamage)` - Routine 675

- `675. EffectForceDrain`
- EffectForceDrain
- This command will reduce the force points of a creature.

- `nDamage`: int

<a id="effectforcefizzle"></a>

## `EffectForceFizzle()` - Routine 420

- `420. EffectForceFizzle`
- Effect that will display a visual effect on the specified object's hand to
- indicate a force power has fizzled out.

<a id="effectforcejump"></a>

## `EffectForceJump(oTarget, nAdvanced)` - Routine 153

- `153. EffectForceJump`
- EffectForceJump
- The effect required for force jumping

- `oTarget`: object
- `nAdvanced`: int (default: `0`)

<a id="effectforcepushed"></a>

## `EffectForcePushed()` - Routine 392

- `392. EffectForcePushed`
- Force push the creature...

<a id="effectforcepushtargeted"></a>

## `EffectForcePushTargeted(lCentre, nIgnoreTestDirectLine)` - Routine 269

- `269. EffectForcePushTargeted`
- EffectForcePushTargeted
- This effect is exactly the same as force push, except it takes a location parameter that specifies
- where the location of the force push is to be done from.  All orientations are also based on this location.
- AMF:  The new ignore test direct line variable should be used with extreme caution
- It overrides geometry checks for force pushes, so that the object that the effect is applied to

- `lCentre`: location
- `nIgnoreTestDirectLine`: int (default: `0`)

<a id="effectforceresistancedecrease"></a>

## `EffectForceResistanceDecrease(nValue)` - Routine 454

- `454. EffectForceResistanceDecrease`
- Create a Force Resistance Decrease effect.

- `nValue`: int

<a id="effectforceresistanceincrease"></a>

## `EffectForceResistanceIncrease(nValue)` - Routine 212

- `212. EffectForceResistanceIncrease`
- Create a Force Resistance Increase effect.
- - nValue: size of Force Resistance increase

- `nValue`: int

<a id="effectforceresisted"></a>

## `EffectForceResisted(oSource)` - Routine 402

- `402. EffectForceResisted`
- Effect that will play an animation and display a visual effect to indicate the
- target has resisted a force power.

- `oSource`: object

<a id="effectforceshield"></a>

## `EffectForceShield(nShield)` - Routine 459

- `459. EffectForceShield`
- Create a Force Shield that has parameters from the guven index into the forceshields.2da

- `nShield`: int

<a id="effectfrightened"></a>

## `EffectFrightened()` - Routine 158

- `158. EffectFrightened`
- Create a Frighten effect

<a id="effecthaste"></a>

## `EffectHaste()` - Routine 270

- `270. EffectHaste`
- Create a Haste effect.

<a id="effectheal"></a>

## `EffectHeal(nDamageToHeal)` - Routine 78

- `78. EffectHeal`
- Create a Heal effect. This should be applied as an instantaneous effect.
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nDamageToHeal < 0.

- `nDamageToHeal`: int

<a id="effecthealforcepoints"></a>

## `EffectHealForcePoints(nHeal)` - Routine 373

- `373. EffectHealForcePoints`
- Heals the creatures force points

- `nHeal`: int

<a id="effecthitpointchangewhendying"></a>

## `EffectHitPointChangeWhenDying(fHitPointChangePerRound)` - Routine 387

- `387. EffectHitPointChangeWhenDying`
- Create a Hit Point Change When Dying effect.
- - fHitPointChangePerRound: this can be positive or negative, but not zero.
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if fHitPointChangePerRound is 0.

- `fHitPointChangePerRound`: float

<a id="effecthorrified"></a>

## `EffectHorrified()` - Routine 471

- `471. EffectHorrified`
- Make the creature horified. BOO!

<a id="effectimmunity"></a>

## `EffectImmunity(nImmunityType)` - Routine 273

- `273. EffectImmunity`
- Create an Immunity effect.
- - nImmunityType: IMMUNITY_TYPE_*

- `nImmunityType`: int

<a id="effectinvisibility"></a>

## `EffectInvisibility(nInvisibilityType)` - Routine 457

- `457. EffectInvisibility`
- Create an Invisibility effect.
- - nInvisibilityType: INVISIBILITY_TYPE_*
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nInvisibilityType
- is invalid.

- `nInvisibilityType`: int

<a id="effectknockdown"></a>

## `EffectKnockdown()` - Routine 134

- `134. EffectKnockdown`
- Create a Knockdown effect
- This effect knocks creatures off their feet, they will sit until the effect
- is removed. This should be applied as a temporary effect with a 3 second
- duration minimum (1 second to fall, 1 second sitting, 1 second to get up).

<a id="effectlightsaberthrow"></a>

## `EffectLightsaberThrow(oTarget1, oTarget2, oTarget3, nAdvancedDamage)` - Routine 702

- `702. EffectLightsaberThrow`
- This function throws a lightsaber at a target
- If multiple targets are specified, then the lightsaber travels to them
- sequentially, returning to the first object specified
- This effect is applied to an object, so an effector is not needed

- `oTarget1`: object
- `oTarget2`: object
- `oTarget3`: object
- `nAdvancedDamage`: int (default: `0`)

<a id="effectlinkeffects"></a>

## `EffectLinkEffects(eChildEffect, eParentEffect)` - Routine 199

- `199. EffectLinkEffects`
- Link the two supplied effects, returning eChildEffect as a child of
- eParentEffect.
- Note: When applying linked effects if the target is immune to all valid
- effects all other effects will be removed as well. This means that if you
- apply a visual effect and a silence effect (in a link) and the target is

- `eChildEffect`: effect
- `eParentEffect`: effect

<a id="effectmisschance"></a>

## `EffectMissChance(nPercentage)` - Routine 477

- `477. EffectMissChance`
- Create a Miss Chance effect.
- - nPercentage: 1-100 inclusive
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nPercentage < 1 or
- nPercentage > 100.

- `nPercentage`: int

<a id="effectmodifyattacks"></a>

## `EffectModifyAttacks(nAttacks)` - Routine 485

- `485. EffectModifyAttacks`
- Create a Modify Attacks effect to add attacks.
- - nAttacks: maximum is 5, even with the effect stacked
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nAttacks > 5.

- `nAttacks`: int

<a id="effectmovementspeeddecrease"></a>

## `EffectMovementSpeedDecrease(nPercentChange)` - Routine 451

- `451. EffectMovementSpeedDecrease`
- Create a Movement Speed Decrease effect.
- - nPercentChange: This is expected to be a positive integer between 1 and 99 inclusive.
- If a negative integer is supplied then a movement speed increase will result,
- and if a number >= 100 is supplied then the effect is deleted.

- `nPercentChange`: int

<a id="effectmovementspeedincrease"></a>

## `EffectMovementSpeedIncrease(nNewSpeedPercent)` - Routine 165

- `165. EffectMovementSpeedIncrease`
- Create a Movement Speed Increase effect.
- - nNewSpeedPercent: This works in a dodgy way so please read this notes carefully.
- If you supply an integer under 100, 100 gets added to it to produce the final speed.
- e.g. if you supply 50, then the resulting speed is 150% of the original speed.
- If you supply 100 or above, then this is used directly as the resulting speed.

- `nNewSpeedPercent`: int

<a id="effectparalyze"></a>

## `EffectParalyze()` - Routine 148

- `148. EffectParalyze`
- Create a Paralyze effect

<a id="effectpoison"></a>

## `EffectPoison(nPoisonType)` - Routine 250

- `250. EffectPoison`
- Create a Poison effect.
- - nPoisonType: POISON_*

- `nPoisonType`: int

<a id="effectpsychicstatic"></a>

## `EffectPsychicStatic()` - Routine 676

- `676. EffectPsychicStatic`
- EffectTemporaryForcePoints

<a id="effectregenerate"></a>

## `EffectRegenerate(nAmount, fIntervalSeconds)` - Routine 164

- `164. EffectRegenerate`
- Create a Regenerate effect.
- - nAmount: amount of damage to be regenerated per time interval
- - fIntervalSeconds: length of interval in seconds

- `nAmount`: int
- `fIntervalSeconds`: float

<a id="effectresurrection"></a>

## `EffectResurrection()` - Routine 82

- `82. EffectResurrection`
- Create a Resurrection effect. This should be applied as an instantaneous effect.

<a id="effectsavingthrowdecrease"></a>

## `EffectSavingThrowDecrease(nSave, nValue, nSaveType)` - Routine 452

- `452. EffectSavingThrowDecrease`
- Create a Saving Throw Decrease effect.
- - nSave
- - nValue
- - nSaveType: SAVING_THROW_TYPE_*

- `nSave`: int
- `nValue`: int
- `nSaveType`: int (default: `0`)

<a id="effectsavingthrowincrease"></a>

## `EffectSavingThrowIncrease(nSave, nValue, nSaveType)` - Routine 117

- `117. EffectSavingThrowIncrease`
- Create an AC Decrease effect
- - nSave: SAVING_THROW_*(not SAVING_THROW_TYPE_*)
- - nValue: size of AC decrease
- - nSaveType: SAVING_THROW_TYPE_*

- `nSave`: int
- `nValue`: int
- `nSaveType`: int (default: `0`)

<a id="effectseeinvisible"></a>

## `EffectSeeInvisible()` - Routine 466

- `466. EffectSeeInvisible`
- Create a See Invisible effect.

<a id="effectskilldecrease"></a>

## `EffectSkillDecrease(nSkill, nValue)` - Routine 453

- `453. EffectSkillDecrease`
- Create a Skill Decrease effect.
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nSkill is invalid.

- `nSkill`: int
- `nValue`: int

<a id="effectskillincrease"></a>

## `EffectSkillIncrease(nSkill, nValue)` - Routine 351

- `351. EffectSkillIncrease`
- Create a Skill Increase effect.
- - nSkill: SKILL_*
- - nValue
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nSkill is invalid.

- `nSkill`: int
- `nValue`: int

<a id="effectsleep"></a>

## `EffectSleep()` - Routine 154

- `154. EffectSleep`
- Create a Sleep effect

<a id="effectspellimmunity"></a>

## `EffectSpellImmunity(nImmunityToSpell)` - Routine 149

- `149. EffectSpellImmunity`
- Create a Spell Immunity effect.
- There is a known bug with this function. There *must* be a parameter specified
- when this is called (even if the desired parameter is SPELL_ALL_SPELLS),
- otherwise an effect of type EFFECT_TYPE_INVALIDEFFECT will be returned.
- - nImmunityToSpell: SPELL_*

- `nImmunityToSpell`: int (default: `-1`)

<a id="effectspelllevelabsorption"></a>

## `EffectSpellLevelAbsorption(nMaxSpellLevelAbsorbed, nTotalSpellLevelsAbsorbed, nSpellSchool)` - Routine 472

- `472. EffectSpellLevelAbsorption`
- Create a Spell Level Absorption effect.
- - nMaxSpellLevelAbsorbed: maximum spell level that will be absorbed by the
- effect
- - nTotalSpellLevelsAbsorbed: maximum number of spell levels that will be
- absorbed by the effect

- `nMaxSpellLevelAbsorbed`: int
- `nTotalSpellLevelsAbsorbed`: int (default: `0`)
- `nSpellSchool`: int (default: `0`)

<a id="effectstunned"></a>

## `EffectStunned()` - Routine 161

- `161. EffectStunned`
- Create a Stun effect

<a id="effecttemporaryforcepoints"></a>

## `EffectTemporaryForcePoints(nTempForce)` - Routine 156

- `156. EffectTemporaryForcePoints`
- This was previously EffectCharmed();

- `nTempForce`: int

<a id="effecttemporaryhitpoints"></a>

## `EffectTemporaryHitpoints(nHitPoints)` - Routine 314

- `314. EffectTemporaryHitpoints`
- Create a Temporary Hitpoints effect.
- - nHitPoints: a positive integer
- - Returns an effect of type EFFECT_TYPE_INVALIDEFFECT if nHitPoints < 0.

- `nHitPoints`: int

<a id="effecttimestop"></a>

## `EffectTimeStop()` - Routine 467

- `467. EffectTimeStop`
- Create a Time Stop effect.

<a id="effecttrueseeing"></a>

## `EffectTrueSeeing()` - Routine 465

- `465. EffectTrueSeeing`
- Create a True Seeing effect.

<a id="effectvisualeffect"></a>

## `EffectVisualEffect(nVisualEffectId, nMissEffect)` - Routine 180

- `180. EffectVisualEffect`
- - Create a Visual Effect that can be applied to an object.
- - nVisualEffectId
- - nMissEffect: if this is TRUE, a random vector near or past the target will
- be generated, on which to play the effect

- `nVisualEffectId`: int
- `nMissEffect`: int (default: `0`)

<a id="effectwhirlwind"></a>

## `EffectWhirlWind()` - Routine 703

- `703. EffectWhirlWind`
- creates the effect of a whirl wind.

<a id="enablevideoeffect"></a>

## `EnableVideoEffect(nEffectType)` - Routine 508

- `508. EnableVideoEffect`
- EnableVideoEffect
- Enables the video frame buffer effect specified by nEffectType, which is
- an index into VideoEffects.2da. This video effect will apply indefinitely,
- and so it should *always* be cleared by a call to DisableVideoEffect().

- `nEffectType`: int

<a id="extraordinaryeffect"></a>

## `ExtraordinaryEffect(eEffect)` - Routine 114

- `114. ExtraordinaryEffect`
- Set the subtype of eEffect to Extraordinary and return eEffect.
- (Effects default to magical if the subtype is not set)

- `eEffect`: effect

<a id="getareaofeffectcreator"></a>

## `GetAreaOfEffectCreator(oAreaOfEffectObject)` - Routine 264

- `264. GetAreaOfEffectCreator`
- This returns the creator of oAreaOfEffectObject.
- - Returns OBJECT_INVALID if oAreaOfEffectObject is not a valid Area of Effect object.

- `oAreaOfEffectObject`: object

<a id="geteffectcreator"></a>

## `GetEffectCreator(eEffect)` - Routine 91

- `91. GetEffectCreator`
- Get the object that created eEffect.
- - Returns OBJECT_INVALID if eEffect is not a valid effect.

- `eEffect`: effect

<a id="geteffectdurationtype"></a>

## `GetEffectDurationType(eEffect)` - Routine 89

- `89. GetEffectDurationType`
- Get the duration type (DURATION_TYPE_*) of eEffect.
- - Return value if eEffect is not valid: -1

- `eEffect`: effect

<a id="geteffectspellid"></a>

## `GetEffectSpellId(eSpellEffect)` - Routine 305

- `305. GetEffectSpellId`
- Get the spell (SPELL_*) that applied eSpellEffect.
- - Returns -1 if eSpellEffect was applied outside a spell script.

- `eSpellEffect`: effect

<a id="geteffectsubtype"></a>

## `GetEffectSubType(eEffect)` - Routine 90

- `90. GetEffectSubType`
- Get the subtype (SUBTYPE_*) of eEffect.
- - Return value on error: 0

- `eEffect`: effect

<a id="geteffecttype"></a>

## `GetEffectType(eEffect)` - Routine 170

- `170. GetEffectType`
- Get the effect type (EFFECT_TYPE_*) of eEffect.
- - Return value if eEffect is invalid: EFFECT_INVALIDEFFECT

- `eEffect`: effect

<a id="getfirsteffect"></a>

## `GetFirstEffect(oCreature)` - Routine 85

- `85. GetFirstEffect`
- Get the first in-game effect on oCreature.

- `oCreature`: object

<a id="gethasfeateffect"></a>

## `GetHasFeatEffect(nFeat, oObject)` - Routine 543

- `543. GetHasFeatEffect`
- - nFeat: FEAT_*
- - oObject
- - Returns TRUE if oObject has effects on it originating from nFeat.

- `nFeat`: int
- `oObject`: object

<a id="gethasspelleffect"></a>

## `GetHasSpellEffect(nSpell, oObject)` - Routine 304

- `304. GetHasSpellEffect`
- Determine if oObject has effects originating from nSpell.
- - nSpell: SPELL_*
- - oObject

- `nSpell`: int
- `oObject`: object

<a id="getiseffectvalid"></a>

## `GetIsEffectValid(eEffect)` - Routine 88

- `88. GetIsEffectValid`
- - Returns TRUE if eEffect is a valid effect.

- `eEffect`: effect

<a id="getisweaponeffective"></a>

## `GetIsWeaponEffective(oVersus, bOffHand)` - Routine 422

- `422. GetIsWeaponEffective`
- - Returns TRUE if the weapon equipped is capable of damaging oVersus.

- `oVersus`: object
- `bOffHand`: int (default: `0`)

<a id="getnexteffect"></a>

## `GetNextEffect(oCreature)` - Routine 86

- `86. GetNextEffect`
- Get the next in-game effect on oCreature.

- `oCreature`: object

<a id="magicaleffect"></a>

## `MagicalEffect(eEffect)` - Routine 112

- `112. MagicalEffect`
- Set the subtype of eEffect to Magical and return eEffect.
- (Effects default to magical if the subtype is not set)

- `eEffect`: effect

<a id="playvisualareaeffect"></a>

## `PlayVisualAreaEffect(nEffectID, lTarget)` - Routine 677

- `677. PlayVisualAreaEffect`
- PlayVisualAreaEffect

- `nEffectID`: int
- `lTarget`: location

<a id="removeeffect"></a>

## `RemoveEffect(oCreature, eEffect)` - Routine 87

- `87. RemoveEffect`
- Remove eEffect from oCreature.
- - No return value

- `oCreature`: object
- `eEffect`: effect

<a id="seteffecticon"></a>

## `SetEffectIcon(eEffect, nIcon)` - Routine 552

- `552. SetEffectIcon`
- SetEffectIcon
- This will link the specified effect icon to the specified effect.  The
- effect returned will contain the link to the effect icon and applying this
- effect will cause an effect icon to appear on the portrait/charsheet gui.
- eEffect: The effect which should cause the effect icon to appear.

- `eEffect`: effect
- `nIcon`: int

<a id="supernaturaleffect"></a>

## `SupernaturalEffect(eEffect)` - Routine 113

- `113. SupernaturalEffect`
- Set the subtype of eEffect to Supernatural and return eEffect.
- (Effects default to magical if the subtype is not set)

- `eEffect`: effect

<a id="swmg_setspeedblureffect"></a>

## `SWMG_SetSpeedBlurEffect(bEnabled, fRatio)` - Routine 563

- `563. SWMG_SetSpeedBlurEffect`
- Turns on or off the speed blur effect in rendered scenes.
- bEnabled: Set TRUE to turn it on, FALSE to turn it off.
- fRatio: Sets the frame accumulation ratio.

- `bEnabled`: int
- `fRatio`: float (default: `0.75`)

<a id="versusracialtypeeffect"></a>

## `VersusRacialTypeEffect(eEffect, nRacialType)` - Routine 356

- `356. VersusRacialTypeEffect`
- Set eEffect to be versus nRacialType.
- - eEffect
- - nRacialType: RACIAL_TYPE_*

- `eEffect`: effect
- `nRacialType`: int

<a id="versustrapeffect"></a>

## `VersusTrapEffect(eEffect)` - Routine 357

- `357. VersusTrapEffect`
- Set eEffect to be versus traps.

- `eEffect`: effect

